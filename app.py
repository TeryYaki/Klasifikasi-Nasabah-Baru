from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
import csv
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_super_aman'

# KONFIGURASI
UPLOAD_FOLDER = 'uploads'
DATASET_PATH = os.path.join(UPLOAD_FOLDER, 'dataset.csv')
HISTORY_PATH = os.path.join(UPLOAD_FOLDER, 'history.csv')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inisialisasi file history
def init_history():
    if not os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Tanggal', 'Ketepatan Waktu', 'Frekuensi', 'Tunggakan', 'Konsistensi', 'Hasil Prediksi'])

init_history()

FITUR = [
    'ketepatan_waktu',
    'frekuensi_terlambat',
    'jumlah_tunggakan',
    'konsistensi'
]

# FUNGSI BANTUAN
def get_dataset_options(df):
    options = {}
    for f in FITUR:
        if f in df.columns:
            unik = sorted(df[f].unique())
            options[f] = unik
    return options

def cast_input_type(df, fitur, nilai_input):
    dtype = df[fitur].dtype
    try:
        if pd.api.types.is_integer_dtype(dtype):
            return int(nilai_input)
        elif pd.api.types.is_float_dtype(dtype):
            return float(nilai_input)
    except:
        pass
    return nilai_input

def extract_number(text):
    try:
        text_clean = str(text).lower()
        multiplier = 1
        if 'juta' in text_clean:
            multiplier = 1000000
        elif 'ribu' in text_clean:
            multiplier = 1000
        text_clean = text_clean.replace('.', '').replace(',', '')
        angka_ditemukan = re.findall(r'\d+', text_clean)
        if not angka_ditemukan:
            return 0
        angka_max = max(map(int, angka_ditemukan))
        return angka_max * multiplier
    except:
        return 0

def generate_new_id(df):
    """Membuat ID Nasabah baru secara otomatis (N-XXX)"""
    try:
        # Cek apakah kolom id_nasabah ada
        col_id = [c for c in df.columns if 'id' in c.lower()]
        if not col_id:
            return f"N-{len(df)+1:03d}"
        
        last_id = df[col_id[0]].iloc[-1]
        # Ambil angka dari ID terakhir
        num = int(re.search(r'\d+', str(last_id)).group())
        return f"N-{num+1:03d}"
    except:
        return f"N-{len(df)+1:03d}"

# VALIDASI & ALGORITMA
def validasi_logika_ketat(df, input_data):
    daftar_error = []
    freq_input = extract_number(input_data['frekuensi_terlambat'])
    tunggakan_input = extract_number(input_data['jumlah_tunggakan'])
    
    batas_max_telat = 0
    batas_max_tunggakan = 0
    
    try:
        df_tepat = df[df['ketepatan_waktu'].astype(str).str.contains('Tepat', case=False, na=False)]
        if not df_tepat.empty:
            batas_max_telat = df_tepat['frekuensi_terlambat'].apply(extract_number).max()
            batas_max_tunggakan = df_tepat['jumlah_tunggakan'].apply(extract_number).max()
    except:
        pass

    if freq_input > batas_max_telat and 'Tepat' in input_data['ketepatan_waktu'] and 'Tidak' not in input_data['ketepatan_waktu']:
        daftar_error.append(f"⛔ DATA DITOLAK: Berdasarkan dataset, nasabah 'Tepat Waktu' tercatat paling parah hanya terlambat {batas_max_telat} kali. Input Anda ({freq_input} kali) dianggap tidak logis.")

    if freq_input == 0 and 'Terlambat' in input_data['ketepatan_waktu']:
        daftar_error.append("⛔ DATA DITOLAK: Anda memilih status 'Terlambat' tetapi Frekuensi 0 Kali. Jika 0 kali, harusnya status 'Tepat Waktu'.")
        
    return daftar_error

def naive_bayes(df, input_data):
    kelas_unik = df['kelas'].unique()
    total_data = len(df)
    hasil_prob = {}
    langkah_manual = {}

    for kelas in kelas_unik:
        data_kelas = df[df['kelas'] == kelas]
        prior = len(data_kelas) / total_data
        likelihood = prior
        detail_atribut = []

        for fitur in FITUR:
            nilai_asli = cast_input_type(df, fitur, input_data[fitur])
            jumlah_cocok = len(data_kelas[data_kelas[fitur] == nilai_asli])
            jumlah_unik_fitur = len(df[fitur].unique())
            prob = (jumlah_cocok + 1) / (len(data_kelas) + jumlah_unik_fitur)
            likelihood *= prob
            detail_atribut.append({
                "fitur": fitur, "nilai": nilai_asli, "jumlah": jumlah_cocok, "probabilitas": round(prob, 4)
            })

        hasil_prob[kelas] = likelihood
        langkah_manual[kelas] = {"prior": round(prior, 4), "detail": detail_atribut, "likelihood": "{:.8f}".format(likelihood)}

    hasil_akhir = max(hasil_prob, key=hasil_prob.get)
    return hasil_akhir, langkah_manual

def hitung_akurasi_model(df):
    data_acak = df.sample(frac=1, random_state=42).reset_index(drop=True)
    split_index = int(len(data_acak) * 0.8)
    train_data = data_acak.iloc[:split_index]
    test_data = data_acak.iloc[split_index:]
    if len(test_data) == 0: return 0, 0
    benar = 0
    total = len(test_data)
    for index, row in test_data.iterrows():
        input_test = {f: row[f] for f in FITUR}
        prediksi, _ = naive_bayes(train_data, input_test)
        if prediksi == row['kelas']: benar += 1
    return round((benar / total) * 100, 2), total

def get_chart_data(df):
    kelas_counts = df['kelas'].value_counts().to_dict()
    konsistensi_counts = df['konsistensi'].value_counts().to_dict()
    return {
        'kelas_labels': list(kelas_counts.keys()),
        'kelas_values': list(kelas_counts.values()),
        'konsistensi_labels': list(konsistensi_counts.keys()),
        'konsistensi_values': list(konsistensi_counts.values())
    }

def save_history(input_data, hasil):
    with open(HISTORY_PATH, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            input_data['ketepatan_waktu'],
            input_data['frekuensi_terlambat'],
            input_data['jumlah_tunggakan'],
            input_data['konsistensi'],
            hasil
        ])

def load_history():
    if not os.path.exists(HISTORY_PATH): return []
    try:
        with open(HISTORY_PATH, mode='r') as f:
            reader = csv.DictReader(f)
            history = list(reader)
            history.reverse()
            return history
    except:
        return []

# ROUTES UTAMA
@app.route('/', methods=['GET', 'POST'])
def index():
    hasil = None
    langkah_manual = None
    dataset_ready = False
    options = None
    chart_data = None
    akurasi_info = None
    input_data = None # Untuk menyimpan inputan user agar bisa dipass ke form tambah data

    if os.path.exists(DATASET_PATH):
        try:
            df = pd.read_csv(DATASET_PATH)
            # Pastikan kolom minimal ada
            if all(col in df.columns for col in FITUR + ['kelas']):
                dataset_ready = True
                options = get_dataset_options(df)
                chart_data = get_chart_data(df)
        except:
            pass

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload':
            file = request.files.get('dataset')
            if file and file.filename.endswith('.csv'):
                file.save(DATASET_PATH)
                flash('Dataset baru berhasil diupload!', 'success')
                return redirect(url_for('index'))

        elif action == 'klasifikasi' and dataset_ready:
            input_data = {
                'ketepatan_waktu': request.form['ketepatan_waktu'],
                'frekuensi_terlambat': request.form['frekuensi_terlambat'],
                'jumlah_tunggakan': request.form['jumlah_tunggakan'],
                'konsistensi': request.form['konsistensi']
            }
            try:
                df = pd.read_csv(DATASET_PATH)
                daftar_error = validasi_logika_ketat(df, input_data)
                
                if daftar_error:
                    for pesan in daftar_error:
                        flash(pesan, 'error')
                else:
                    hasil, langkah_manual = naive_bayes(df, input_data)
                    save_history(input_data, hasil)
                    flash(f'Analisa Selesai. Hasil: {hasil}', 'success')
            except Exception as e:
                flash(f'Terjadi error sistem: {str(e)}', 'error')

        # TAMBAH DATA KE DATASET 
        elif action == 'tambah_data' and dataset_ready:
            try:
                df = pd.read_csv(DATASET_PATH)
                
                # Buat data baru
                new_row = {
                    # Mencari nama kolom ID (bisa id_nasabah, ID, dll)
                    df.columns[0]: generate_new_id(df), 
                    'ketepatan_waktu': request.form['ketepatan_waktu'],
                    'frekuensi_terlambat': request.form['frekuensi_terlambat'],
                    'jumlah_tunggakan': request.form['jumlah_tunggakan'],
                    'konsistensi': request.form['konsistensi'],
                    'kelas': request.form['final_kelas'] # Kelas pilihan user (bisa beda dari prediksi)
                }
                
                # Simpan ke CSV
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(DATASET_PATH, index=False)
                
                flash('Data berhasil ditambahkan ke dataset! Model Anda sekarang lebih pintar.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Gagal menyimpan data: {str(e)}', 'error')

        elif action == 'cek_akurasi' and dataset_ready:
            df = pd.read_csv(DATASET_PATH)
            skor, jumlah_test = hitung_akurasi_model(df)
            akurasi_info = {'skor': skor, 'jumlah': jumlah_test}
            if skor >= 70:
                flash(f'Model Bagus! Akurasi: {skor}%', 'success')
            else:
                flash(f'Akurasi: {skor}%', 'warning')

    riwayat_list = load_history()

    return render_template(
        'index.html',
        hasil=hasil,
        langkah_manual=langkah_manual,
        options=options,
        dataset_ready=dataset_ready,
        chart_data=chart_data,
        akurasi_info=akurasi_info,
        riwayat=riwayat_list,
        # Kita kirim inputan terakhir ke template jika user mau simpan
        last_input=input_data if hasil else None 
    )

# ROUTE BARU: DOWNLOAD DATASET 
@app.route('/download')
def download():
    if os.path.exists(DATASET_PATH):
        return send_file(DATASET_PATH, as_attachment=True, download_name='dataset_updated.csv')
    flash('Dataset tidak ditemukan.', 'error')
    return redirect(url_for('index'))

@app.route('/clear', methods=['POST'])
def clear():
    return redirect(url_for('index'))

@app.route('/reset_dataset', methods=['POST'])
def reset_dataset():
    if os.path.exists(DATASET_PATH):
        os.remove(DATASET_PATH)
    if os.path.exists(HISTORY_PATH):
        os.remove(HISTORY_PATH)
    init_history() 
    flash('Dataset dan Riwayat telah dihapus total.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
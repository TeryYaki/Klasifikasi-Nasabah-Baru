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
# Path untuk menyimpan hasil prediksi massal sementara
BATCH_RESULT_PATH = os.path.join(UPLOAD_FOLDER, 'hasil_prediksi_batch.csv')

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

# --- FUNGSI BANTUAN ---
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
        col_id = [c for c in df.columns if 'id' in c.lower()]
        if not col_id:
            return f"N-{len(df)+1:03d}"
        
        last_id = df[col_id[0]].iloc[-1]
        num = int(re.search(r'\d+', str(last_id)).group())
        return f"N-{num+1:03d}"
    except:
        return f"N-{len(df)+1:03d}"

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

# --- VALIDASI & ALGORITMA NAIVE BAYES ---
def validasi_logika_ketat(df, input_data):
    daftar_error = []
    freq_input = extract_number(input_data['frekuensi_terlambat'])
    
    batas_max_telat = 0
    
    try:
        df_tepat = df[df['ketepatan_waktu'].astype(str).str.contains('Tepat', case=False, na=False)]
        if not df_tepat.empty:
            batas_max_telat = df_tepat['frekuensi_terlambat'].apply(extract_number).max()
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

    # Konsep dasar Naive Bayes dengan Laplace Smoothing
    for kelas in kelas_unik:
        data_kelas = df[df['kelas'] == kelas]
        prior = len(data_kelas) / total_data
        likelihood = prior
        detail_atribut = []

        for fitur in FITUR:
            nilai_asli = cast_input_type(df, fitur, input_data[fitur])
            jumlah_cocok = len(data_kelas[data_kelas[fitur] == nilai_asli])
            jumlah_unik_fitur = len(df[fitur].unique())
            
            # Rumus Laplace Smoothing
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
    """Menghitung akurasi internal (Split Train-Test otomatis)"""
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

# --- ROUTES UTAMA ---

@app.route('/', methods=['GET', 'POST'])
def index():
    hasil = None
    langkah_manual = None
    dataset_ready = False
    options = None
    chart_data = None
    akurasi_info = None
    input_data = None 

    if os.path.exists(DATASET_PATH):
        try:
            df = pd.read_csv(DATASET_PATH)
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

        elif action == 'tambah_data' and dataset_ready:
            try:
                df = pd.read_csv(DATASET_PATH)
                new_row = {
                    df.columns[0]: generate_new_id(df), 
                    'ketepatan_waktu': request.form['ketepatan_waktu'],
                    'frekuensi_terlambat': request.form['frekuensi_terlambat'],
                    'jumlah_tunggakan': request.form['jumlah_tunggakan'],
                    'konsistensi': request.form['konsistensi'],
                    'kelas': request.form['final_kelas']
                }
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(DATASET_PATH, index=False)
                flash('Data berhasil ditambahkan ke dataset!', 'success')
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
        last_input=input_data if hasil else None 
    )

# --- [UPDATE] ROUTE TESTING BATCH / UJI MASSAL ---
@app.route('/test_batch', methods=['POST'])
def test_batch():
    """
    Melakukan prediksi massal terhadap file CSV baru.
    Bisa menangani file dengan 'kelas' (untuk cek akurasi) 
    ATAU tanpa 'kelas' (untuk prediksi murni).
    """
    if not os.path.exists(DATASET_PATH):
        flash('Dataset Training belum ada. Upload dataset utama dulu.', 'error')
        return redirect(url_for('index'))

    file = request.files.get('test_file')
    if not file or not file.filename.endswith('.csv'):
        flash('File harus format CSV.', 'error')
        return redirect(url_for('index'))

    # Load dataset utama untuk menjadi "Otak" (Model Training)
    df_train = pd.read_csv(DATASET_PATH)
    options = get_dataset_options(df_train)
    chart_data = get_chart_data(df_train)
    riwayat = load_history()

    try:
        # Load file yang mau diprediksi
        df_test = pd.read_csv(file)
        
        # Validasi Kolom Fitur (Wajib ada), tapi 'kelas' TIDAK wajib
        if not all(col in df_test.columns for col in FITUR):
            flash(f'Format salah! File wajib memiliki kolom: {", ".join(FITUR)}', 'error')
            return redirect(url_for('index'))

        # Cek apakah ini mode Testing (ada kunci jawaban) atau Prediksi (data buta)
        has_label = 'kelas' in df_test.columns
        
        batch_results = []
        benar = 0
        total = len(df_test)
        
        # List untuk menyimpan hasil lengkap agar bisa didownload
        export_data = []

        # Loop Prediksi
        for index, row in df_test.iterrows():
            input_test = {f: row[f] for f in FITUR}
            
            # Lakukan prediksi menggunakan dataset training
            prediksi, _ = naive_bayes(df_train, input_test)
            
            item_result = {
                'no': index + 1,
                'input': input_test,
                'prediksi': prediksi,
            }

            # Siapkan baris untuk export CSV
            row_export = input_test.copy()
            row_export['Hasil_Prediksi'] = prediksi

            if has_label:
                # Jika file upload punya kolom kelas, hitung akurasi
                aktual = row['kelas']
                is_correct = (str(prediksi) == str(aktual))
                if is_correct: benar += 1
                
                item_result['aktual'] = aktual
                item_result['status'] = '✅' if is_correct else '❌'
                row_export['Kelas_Asli'] = aktual
                row_export['Status_Prediksi'] = 'Benar' if is_correct else 'Salah'
            else:
                # Jika tidak ada kolom kelas, kosongkan bagian aktual
                item_result['aktual'] = '-'
                item_result['status'] = '🔮' # Ikon prediksi
                row_export['Kelas_Asli'] = '-'
                row_export['Status_Prediksi'] = 'Prediksi Baru'
            
            batch_results.append(item_result)
            export_data.append(row_export)

        # Simpan hasil ke CSV sementara agar user bisa download
        pd.DataFrame(export_data).to_csv(BATCH_RESULT_PATH, index=False)

        # [BARU] Hitung ringkasan total per kelas untuk ditampilkan
        batch_summary = pd.DataFrame(batch_results)['prediksi'].value_counts().to_dict()

        # Pesan Feedback
        if has_label:
            batch_accuracy = round((benar / total) * 100, 2) if total > 0 else 0
            flash(f'Pengujian Selesai! Akurasi: {batch_accuracy}%', 'success')
        else:
            batch_accuracy = None # None menandakan tidak ada perhitungan akurasi
            flash(f'Prediksi Selesai! {total} data berhasil diprediksi.', 'success')

        return render_template('index.html',
                               dataset_ready=True,
                               options=options,
                               chart_data=chart_data,
                               riwayat=riwayat,
                               batch_results=batch_results,
                               batch_accuracy=batch_accuracy,
                               batch_summary=batch_summary,  # <-- Variabel baru dikirim ke template
                               show_download_batch=True) 

    except Exception as e:
        flash(f'Error saat proses data: {str(e)}', 'error')
        return redirect(url_for('index'))

# --- [BARU] ROUTE DOWNLOAD HASIL BATCH ---
@app.route('/download_batch_result')
def download_batch_result():
    if os.path.exists(BATCH_RESULT_PATH):
        return send_file(BATCH_RESULT_PATH, as_attachment=True, download_name='hasil_prediksi.csv')
    flash('Belum ada hasil prediksi.', 'error')
    return redirect(url_for('index'))

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
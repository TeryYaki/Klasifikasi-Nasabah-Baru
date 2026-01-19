# 🚀 Smart Naïve Bayes: Sistem Klasifikasi Potensi Nasabah

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)
![Framework](https://img.shields.io/badge/Framework-Flask-green?style=flat&logo=flask)
![Algorithm](https://img.shields.io/badge/Algorithm-Naïve%20Bayes-orange)

**Aplikasi cerdas berbasis web** untuk memprediksi potensi nasabah (Potensial/Tidak) berdasarkan data historis pembayaran. Sistem ini tidak hanya menghitung peluang statistik, tetapi juga dilengkapi dengan **Active Learning** dan **Validasi Adaptif** yang membuatnya semakin pintar seiring penggunaan.

---

## 🌟 Mengapa Sistem Ini Berbeda?

Berbeda dengan aplikasi klasifikasi biasa, sistem ini memiliki "penjaga" logika yang dinamis. Ia **mempelajari pola dataset Anda** terlebih dahulu sebelum menerima input baru, mencegah data tidak wajar masuk ke dalam sistem, serta mampu membaca input bahasa manusia yang fleksibel.

### Fitur Unggulan

1.  **🧠 Validasi Logika Adaptif (The Guardian)**
    Fitur keamanan data yang tidak kaku, melainkan belajar dari sejarah.
    * *Historical Boundary:* Jika nasabah 'Tepat Waktu' di masa lalu maksimal hanya pernah terlambat 2 kali, sistem akan **menolak** input baru yang mengaku 'Tepat Waktu' tapi terlambat 5 kali.
    * *Logical Guard:* Mencegah kontradiksi fatal, seperti status 'Terlambat' namun frekuensi '0 Kali'.

2.  **🔢 Smart Input Parsing (Regex Engine)**
    Input data tidak harus kaku. Sistem memahami format manusia.
    * Mengetik `1-2 Juta`? Sistem otomatis membacanya sebagai **2.000.000**.
    * Mengetik `Rp 500 Ribu`, `< 500rb`, atau `10 Juta`? Semua terbaca akurat sebagai angka numerik.

3.  **🔄 Active Learning System**
    Sistem ini tumbuh bersama bisnis Anda. Hasil prediksi yang sudah dikonfirmasi dapat disimpan kembali ke dataset utama, membuat AI semakin akurat di masa depan.

4.  **🔍 Self-Diagnostic (Cek Akurasi)**
    Sistem menguji dirinya sendiri dengan memisahkan 20% data secara acak sebagai soal ujian, lalu memberikan skor kepercayaan (%) kepada pengguna.

---

## 📖 Panduan Penggunaan Aplikasi (User Guide)

Setelah aplikasi berjalan di browser, ikuti langkah-langkah berikut untuk melakukan analisis:

### 1. 📂 Tahap 1: Upload Dataset
Saat pertama kali membuka aplikasi, sistem masih kosong.
1.  Siapkan file data nasabah dalam format **.CSV**.
2.  Klik tombol **"Choose File"** pada kotak *Manajemen Dataset*.
3.  Klik **"Upload"**. (Sistem akan otomatis menampilkan riwayat data jika berhasil).

### 2. 📊 Tahap 2: Cek Kesehatan Model (Opsional)
1.  Klik tombol biru **"🔍 Cek Sekarang"** di panel *Statistik Performa*.
2.  **Hasil:**
    * 🟢 **Hijau (>70%):** Model pintar & siap digunakan.
    * 🔴 **Merah (<60%):** Data latih mungkin kurang konsisten, namun tetap bisa digunakan.

### 3. 🧮 Tahap 3: Input Data Nasabah Baru
Isi formulir prediksi. Fitur **Smart Input** aktif di sini:
* **Ketepatan Waktu:** Pilih status (Tepat Waktu / Terlambat).
* **Frekuensi:** Ketik angka biasa (misal `2`) atau teks (misal `2 Kali`).
* **Tunggakan:** Ketik nominal bebas (Contoh: `1.5 Juta`, `Rp 500 Ribu`, atau `1-2 Juta`).
* **Konsistensi:** Pilih tingkat kestabilan pembayaran.

> **⚠️ Catatan:** Sistem akan menampilkan Error Merah jika Anda memasukkan data yang tidak logis atau bertentangan dengan sejarah dataset.

### 4. ⚡ Tahap 4: Lihat & Simpan (Active Learning)
1.  Klik **"Analisa Sekarang"**.
2.  Hasil akan muncul dengan badge **Hijau (Potensial)** atau **Merah (Tidak Potensial)**.
3.  Jika Anda setuju dengan hasilnya, lihat kotak **"Simpan Data Ini?"** di bawah hasil.
4.  Klik **"💾 Simpan & Perbarui Model"**. Data tersebut kini menjadi bagian dari kecerdasan AI.

### 5. 📥 Tahap 5: Download & Reset
* **Download:** Klik tombol hijau **"📥 Download / Export Dataset"** untuk mengambil file CSV terbaru.
* **Reset:** Klik tombol merah **"🗑️ Reset Semua"** jika ingin menghapus seluruh data dan memulai sesi baru.

---

## 🛠️ Cara Instalasi & Menjalankan (Technical Guide)

Ikuti langkah ini untuk menjalankan aplikasi di komputer lokal (Localhost).

### Prasyarat
Pastikan komputer Anda sudah terinstal **Python 3.x**.

### Langkah-Langkah

1.  **Clone / Download Repository**
    Download source code ini dan ekstrak ke dalam satu folder.

2.  **Install Library**
    Buka terminal/CMD di folder tersebut, lalu jalankan:
    ```bash
    pip install flask pandas
    ```

3.  **Jalankan Aplikasi**
    Ketik perintah berikut di terminal:
    ```bash
    python app.py
    ```

   ---

## 📸 Dokumentasi Antarmuka (UI)

Berikut adalah tampilan langkah-langkah penggunaan aplikasi Smart Naïve Bayes:

<p align="center">
  <b>1. Tampilan Utama & Manajemen Dataset</b><br>
  <img src="Images/gambar1.png" width="800" style="border-radius: 10px; margin-bottom: 20px;">
</p>

<p align="center">
  <b>2. Statistik Performa & Cek Akurasi</b><br>
  <img src="Images/gambar2.png" width="800" style="border-radius: 10px; margin-bottom: 20px;">
</p>

<p align="center">
  <b>3. Form Input Prediksi Nasabah</b><br>
  <img src="Images/gambar3.png" width="800" style="border-radius: 10px; margin-bottom: 20px;">
</p>

<p align="center">
  <b>4. Hasil Analisa & Detail Perhitungan</b><br>
  <img src="Images/gambar4.png" width="800" style="border-radius: 10px; margin-bottom: 20px;">
</p>

<p align="center">
  <b>5. Riwayat Analisa & Fitur Simpan Data</b><br>
  <img src="Images/gambar5.png" width="800" style="border-radius: 10px;">
</p>

---

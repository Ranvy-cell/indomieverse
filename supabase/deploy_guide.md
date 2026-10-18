# Panduan Lengkap Setup Supabase Backend & Hosting INDOMIEVERSE

Dokumen ini memandu Anda langkah-demi-langkah untuk menyiapkan **Database Backend di Supabase** serta **Hosting Frontend** agar aplikasi INDOMIEVERSE dapat diakses online secara publik.

---

## Bagian 1: Menyiapkan Supabase Project & Database

### Langkah 1: Buat Proyek di Supabase
1. Buka [https://supabase.com](https://supabase.com) dan login/daftar akun gratis.
2. Klik **"New Project"**.
3. Isi informasi proyek:
   - **Name**: `indomieverse` (atau nama lain pilihan Anda).
   - **Database Password**: Buat password yang kuat dan catat.
   - **Region**: Pilih yang terdekat (contoh: `Singapore - ap-southeast-1`).
4. Klik **"Create new project"** dan tunggu 1-2 menit hingga status database aktif (Active).

---

### Langkah 2: Menjalankan Database Schema (Tabel, RLS & RPC)
1. Di dashboard Supabase, buka menu **SQL Editor** (ikon terminal di bilah kiri).
2. Klik **"New query"**.
3. Buka file [`supabase/schema.sql`](./schema.sql), salin seluruh isinya, lalu tempelkan (paste) ke editor SQL Supabase.
4. Klik tombol **"Run"** (atau tekan `Ctrl+Enter`).
5. Pastikan muncul pesan sukses: `Success. No rows returned`.

> [!NOTE]
> File `schema.sql` secara otomatis telah menyiapkan:
> - Tabel: `profiles`, `owned_characters`, `redeem_codes`, `used_codes`, `chat_sessions`, `chat_messages`, `character_stats`, dan `system_settings`.
> - Keamanan: **Row Level Security (RLS)** untuk melindungi data pengguna.
> - Stored Procedure (RPC): `redeem_code`, `save_chat_turn`, `get_chat_state`, `new_chat_session`, `delete_chat_session`, dan `update_user_flags`.
> - Data Awal: Kode kupon aktif (`NOODLE-NUSA-2026`, `MYSTERY-GOLD-77`, `PEDAS-BOOST-10`, `ORIGINAL-WARM-01`).
> - Trigger Akun Baru: Otomatis memberikan karakter pemula **Original** (Lv 4) dan **Agent Pedas** (Lv 2).

---

### Langkah 3: Konfigurasi Supabase Auth (Penting)
1. Di dashboard Supabase, buka menu **Authentication** -> **Providers** -> **Email**.
2. Jika Anda ingin pengguna dapat langsung login setelah registrasi tanpa harus menunggu klik link verifikasi email:
   - Nonaktifkan toggle **"Confirm email"**.
   - Klik **Save**.

---

### Langkah 4: Mengambil Kunci API Supabase
1. Di dashboard Supabase, buka **Project Settings** (ikon roda gigi di pojok kiri bawah) -> **API**.
2. Salin 2 nilai berikut:
   - **Project URL**: contoh `https://abcdefghijklmn.supabase.co`
   - **Project API keys (anon public)**: contoh `eyJhbGciOi...`

---

## Bagian 2: Menghubungkan Frontend ke Supabase

Anda memiliki 2 cara mudah untuk menghubungkan frontend ke Supabase:

### Cara A: Melalui Menu Account di Web (Tanpa Edit Kode)
1. Buka aplikasi `index.html` di browser Anda.
2. Masuk ke tab **Account**.
3. Pada panel **⚡ Supabase Cloud Backend**, masukkan:
   - `Supabase URL`
   - `Supabase Anon Key`
4. Klik tombol **"Connect Supabase"**.
5. Status akan berubah menjadi **Connected** dan Anda langsung bisa Register, Login, Redeem Code, dan Chat dengan database Supabase!

### Cara B: Menyimpan Permanen di `supabase-config.js`
Buka file [`supabase-config.js`](../supabase-config.js) dan isi:
```javascript
window.SUPABASE_CONFIG = {
  url: 'https://xyzproject.supabase.co',
  anonKey: 'eyJhbGciOi...'
};
```

---

## Bagian 3: Hosting Frontend ke Internet (Gratis)

Supabase menangani seluruh backend (Database, Auth, Logic). Untuk hosting web frontend (`index.html` dan aset multimedia), platform berikut adalah yang paling cepat dan gratis:

### Opsi 1: Vercel (Sangat Direkomendasikan - 1 Menit)
File konfigurasi [`vercel.json`](../vercel.json) sudah kami sediakan di dalam folder proyek.

1. Buka [https://vercel.com](https://vercel.com) dan login dengan akun GitHub Anda.
2. Upload folder `indomieverse` ke repository GitHub Anda:
   ```bash
   git init
   git add .
   git commit -m "INDOMIEVERSE with Supabase"
   git branch -M main
   git remote add origin https://github.com/username/indomieverse.git
   git push -u origin main
   ```
3. Di dashboard Vercel, klik **"Add New"** -> **"Project"** -> pilih repository GitHub Anda.
4. Klik **Deploy**.
5. Selesai! Web Anda langsung aktif dengan domain HTTPS gratis (contoh: `https://indomieverse.vercel.app`).

---

### Opsi 2: Netlify
File konfigurasi [`netlify.toml`](../netlify.toml) sudah kami sediakan.
1. Buka [https://netlify.com](https://netlify.com) dan login.
2. Anda bisa langsung **Drag & Drop** folder `indomieverse` ke halaman Netlify Drop, atau sambungkan via GitHub.
3. Web Anda langsung live dalam beberapa detik.

---

### Opsi 3: GitHub Pages
1. Push proyek ke repository GitHub publik.
2. Masuk ke **Settings** repository di GitHub -> **Pages**.
3. Di bagian **Branch**, pilih `main` / `root`, lalu klik **Save**.
4. Website akan live di `https://username.github.io/indomieverse`.

---

## Bagian 4: Menyiapkan Supabase Storage untuk Video & Gambar (Opsional)

Jika Anda ingin menyimpan video kampanye atau ilustrasi karakter di Cloud Storage Supabase:
1. Buka menu **Storage** di Supabase Dashboard.
2. Klik **"New Bucket"**.
3. Beri nama: `assets` dan centang opsi **"Public bucket"**.
4. Upload file gambar dan video dari folder `assets/` lokal ke bucket tersebut.
5. Anda dapat mengarahkan link di `assets/assets.js` ke URL publik Supabase Storage tersebut.

---

## Verifikasi & Kode Test
Setelah terhubung ke Supabase, coba lakukan pengujian berikut:
1. Buat akun baru di menu **Account** -> **Register**.
2. Masuk ke menu **Redeem** dan masukkan salah satu kode:
   - `NOODLE-NUSA-2026` -> Membuka karakter **Nusantara**
   - `MYSTERY-GOLD-77` -> Membuka karakter **Secret Recipe**
   - `PEDAS-BOOST-10` -> Menambah bonus +40 XP untuk **Agent Pedas**
3. Masuk ke menu **Chat** -> kirim pesan ke karakter dan periksa apakah progress, afinitas, dan sesi tersimpan di Supabase!

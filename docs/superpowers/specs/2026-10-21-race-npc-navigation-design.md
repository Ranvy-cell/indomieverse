# Desain: Navigasi Balapan NPC dan Difficulty Gemini

Tanggal: 2026-10-21

## Tujuan

Perbaiki balapan map After the Rain agar NPC Original tidak berputar di batas atau terus mengejar mangkuk mie yang tidak terjangkau. Tambahkan pilihan kesulitan Normal dan Hard. Normal harus bergerak memakai navigasi lokal yang deterministik; Hard boleh memakai Gemini untuk keputusan strategis, sementara gerak dan koreksi tabrakan tetap berlangsung lokal setiap frame.

## Temuan pada implementasi saat ini

`findWalkables()` menghasilkan sampel lantai yang belum menyimpan hubungan antar titik. `chooseRaceBowl()` memilih mangkuk berdasar jarak lurus, penalti satu pemeriksaan dinding, dan lebar koridor lokal. `npcRaceHeading()` hanya menguji sepuluh arah dalam jarak sekitar satu langkah. Saat pilihan arah ini tetap valid tetapi tidak mengarah ke rute yang tersambung, deteksi macet berbasis jarak gerak tidak selalu terpicu. Escape saat ini berputar ke heading lain dan memberi blacklist sementara pada mangkuk, sehingga dapat mengulang pola yang sama di batas map.

## Arsitektur yang dipilih

### Graf jalur lokal

- Saat map After the Rain dimuat, ubah kandidat lantai menjadi graf node dan edge. Edge hanya dibuat di antara node tetangga yang lolos pemeriksaan dinding, ketinggian lantai, dan drop yang sudah dipakai NPC.
- Beri edge biaya berdasarkan jarak dan lebar ruang bebas; jalur yang lebih lebar dan node dengan beberapa koneksi mendapat preferensi ringan agar NPC cenderung menggunakan jalan utama.
- Petakan NPC dan mangkuk mie yang tersisa ke node terdekat yang bisa dijangkau. Jalankan A* untuk menghitung rute dan jarak jalur, bukan jarak garis lurus.
- Target dipilih dari mangkuk yang punya rute valid. Bila jarak biaya sebanding, pilih mangkuk yang berada dekat koridor dengan konektivitas/lebar lebih besar dan kelompok mangkuk yang masih tersisa.
- NPC mengikuti waypoint satu per satu dengan steering serta pemeriksaan collision lokal yang sudah ada. Jika tidak ada kemajuan menuju waypoint, tandai node/edge tersebut sementara sebagai gagal, cari ulang rute, dan mundur di rute yang tersimpan menuju node dengan cabang lain. Jika target tidak terjangkau, lepaskan target dan pilih mangkuk terjangkau berikutnya.
- Batas waktu dan jumlah replanning mencegah loop tanpa akhir. Jika semua mangkuk terputus dari node NPC, NPC berhenti dengan aman dan mencoba ulang setelah kondisi graph berubah; ia tidak berputar di tempat.

### Difficulty

- Tambahkan pilihan Normal/Hard yang tampil untuk map After the Rain. Simpan pilihan hanya untuk sesi balapan saat ini; nilai awal Normal.
- Normal memakai graf, A*, pemilihan jalan lebar, deteksi dead-end, dan replanning lokal. Kesulitan ini tidak memerlukan API key atau jaringan.
- Hard memakai sistem navigasi lokal yang sama, tetapi meminta Gemini memilih ID target mangkuk strategis dari kandidat yang sudah tervalidasi. Keputusan hanya diminta saat balapan dimulai, sesudah NPC mengambil mie, atau setelah beberapa kali gagal membuat progres; bukan setiap frame.
- Kegagalan jaringan, jawaban yang tidak valid, timeout, atau proxy tidak tersedia selalu kembali ke pemilihan Normal tanpa menghentikan balapan.
- UI menampilkan status yang jelas bila Hard sedang memakai fallback lokal.

### Proxy Gemini Node

- Tambahkan layanan Node.js ringan tanpa dependency eksternal di `tools/race-ai-proxy.mjs`, menggunakan modul bawaan Node. Kunci API hanya dibaca dari environment `GEMINI_API_KEY`; model dan port dapat dikonfigurasi lewat environment.
- Endpoint menerima konteks ringkas yang divalidasi (ID target yang masih tersedia, jarak jalur, konektivitas jalan, serta ringkasan tujuan). Proxy meminta Gemini mengembalikan satu ID target terpilih dalam JSON terstruktur.
- Proxy membatasi ukuran request, origin yang diizinkan, metode, timeout, dan frekuensi request per klien. Ia tidak menerima URL/model arbitrer dari browser dan tidak mengembalikan secret.
- Browser hanya boleh menerima ID yang termasuk dalam allowlist kandidat aktif dan tetap menghitung rute/gerakan di dalam game. JSON dari Gemini diperlakukan sebagai saran yang tidak tepercaya.
- Dokumentasikan cara menjalankan proxy lokal bersama server statis. Deploy Hard memerlukan proxy Node yang tersedia melalui HTTPS dan origin game yang diizinkan. Tanpa konfigurasi itu, Normal tetap berfungsi.

## Alur data

1. Map dimuat dan sampel lantai yang lulus pemeriksaan membentuk graf.
2. Balapan dimulai setelah pemain menerima tantangan Original; kesulitan sesi sudah dipilih dari pemilih map.
3. Pengendali lokal menghitung kandidat mie terjangkau dan rute A*.
4. Normal memilih kandidat terbaik secara lokal. Hard mengirim daftar kandidat terbatas ke proxy, yang meminta Gemini mengembalikan satu ID.
5. Game memvalidasi ID dan menghitung ulang rute lokal. NPC bergerak menuju waypoint dengan collision dan stamina lokal.
6. Jika gerak tidak membuat progres, edge ditandai gagal sementara, lalu rute dicari ulang atau NPC mundur ke persimpangan.
7. Saat target didapat atau rute buntu, proses pemilihan berjalan lagi. Proxy gagal berarti fallback ke Normal.

## Komponen yang berubah

- `game.html`: kontrol kesulitan After the Rain, graf dan pathfinding balapan, logika target/replanning, serta pemanggilan proxy berfrekuensi rendah dan fallback.
- `tools/race-ai-proxy.mjs`: endpoint proxy Gemini Node yang dibatasi dan memakai environment untuk secret.
- `README.md`: instruksi konfigurasi dan menjalankan layanan proxy secara lokal serta catatan bahwa Hard membutuhkan endpoint publik HTTPS untuk deploy.

## Batasan dan keamanan

- Gemini tidak mengendalikan posisi, yaw, kecepatan, collision, stamina, atau memilih titik di luar kandidat graph. Ia hanya menyarankan target strategis.
- Tidak ada API key yang dimasukkan ke HTML, localStorage, query string, atau respons endpoint.
- Proxy publik tetap dapat menimbulkan biaya API; batasi origin, request rate, ukuran payload, dan timeout. Jangan deploy tanpa batasan tersebut.
- Map harus dilayani melalui HTTP(S); mode `file://` tidak dapat diandalkan untuk memanggil proxy lintas origin. Gameplay Normal tidak bergantung pada proxy.

## Verifikasi yang direncanakan

- Tinjau secara statis keterhubungan node, pemeriksaan edge, dan validasi kandidat target.
- Periksa syntax JavaScript modul proxy dan script game, serta format patch.
- Jalankan game/proxy lokal bila environment tersedia untuk memeriksa perjalanan NPC dari dead end ke persimpangan dan fallback ketika Gemini gagal.
- Jangan mengklaim Gemini atau perilaku runtime berfungsi sebelum jalur tersebut benar-benar dapat dijalankan. API key nyata tidak disimpan atau diminta dalam repository.


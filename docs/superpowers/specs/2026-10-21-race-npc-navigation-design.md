# Desain: Navigasi Balapan NPC dan Difficulty Lokal

Tanggal: 2026-10-21

## Tujuan

Perbaiki balapan map After the Rain agar NPC Original tidak berputar di batas atau terus mengejar mangkuk mie yang tidak terjangkau. Tambahkan pilihan kesulitan Normal dan Hard yang sepenuhnya lokal tanpa layanan AI eksternal. Normal memakai target dari rute lokal; Hard membuat Original melihat satu target berikutnya dan merespons lebih cepat, sementara kecepatan standar pemain tetap.

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
- Hard memakai graf jalur lokal dan memilih mie dengan skor dua langkah: biaya menuju target saat ini ditambah perkiraan biaya ke mie berikutnya, dengan preferensi kecil untuk cluster dan koridor lebar. Pencarian dibatasi ke enam kandidat teratas agar keputusan strategis tetap ringan.
- Hard mempertahankan kecepatan jalan dan sprint pemain seperti biasa. Original bereaksi lebih cepat: belokan dan akselerasi lebih sigap, memulai sprint dari jarak lebih jauh, dan mulai mencari ulang jalur setelah terhambat selama 0,65 detik (Normal 1,15 detik). Kecepatan maksimum Original tetap sama.
- Gerak pemain dan Original, collision, stamina, pengumpulan mie, serta replanning tetap lokal setiap frame. Tidak ada request AI, fallback jaringan, API key, atau proxy untuk mode balapan.

## Alur data

1. Map dimuat dan sampel lantai yang lulus pemeriksaan membentuk graf.
2. Balapan dimulai setelah pemain menerima tantangan Original; kesulitan sesi sudah dipilih dari pemilih map.
3. Pengendali lokal menghitung kandidat mie terjangkau dan rute A*.
4. Normal memilih kandidat terbaik secara lokal. Hard membandingkan biaya rute menuju kandidat dan biaya perkiraan menuju mie berikutnya.
5. Game menetapkan rute dari graf lokal. NPC bergerak menuju waypoint dengan collision dan stamina lokal.
6. Jika gerak tidak membuat progres, edge ditandai gagal sementara, lalu rute dicari ulang atau NPC mundur ke persimpangan.
7. Saat target didapat atau rute buntu, proses pemilihan lokal berjalan lagi.

## Komponen yang berubah

- `game.html`: kontrol kesulitan After the Rain, graf dan pathfinding balapan, logika target/replanning, strategi Hard dua langkah, dan respons NPC Hard yang lebih sigap.
- `README.md`: instruksi menjalankan game dan perbedaan aturan Normal/Hard tanpa layanan eksternal.

## Batasan dan keamanan

- Balapan tidak mengirim data ke layanan AI dan tidak memerlukan API key.
- Map harus dilayani melalui HTTP(S) agar modul dan aset game dapat dimuat.

## Verifikasi yang direncanakan

- Tinjau secara statis keterhubungan node, pemeriksaan edge, dan validasi kandidat target.
- Periksa syntax inline JavaScript dan format patch.
- Jalankan game lokal bila environment tersedia untuk memeriksa navigasi, kecepatan Hard, dan pengumpulan mie.


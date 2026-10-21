# INDOMIEVERSE 3D

Struktur folder (taruh di root website, sejajar dengan index.html):

```
game.html
setup-lib.mjs
supabase-config.js        <- sudah ada di website kamu
assets/
  original-character.v1.glb   (2,2 MB)
  campus.v2.glb               (56,3 MB, tekstur 8K)
  after-the-rain-map.v1.glb   (map kota, material PBR kompatibel)
  home-interior-map.v1.glb     (Home free roam)
lib/                      <- dibuat oleh: node setup-lib.mjs
```

1. `node setup-lib.mjs` (sekali saja, butuh internet) -> membuat folder `lib/`.
2. Jalankan lewat server (bukan klik dua kali file), mis. `npx serve .` lalu buka `/game.html`.
3. Pilih Campus atau After the Rain untuk misi koleksi, atau Home untuk free roam di interior.

## Balapan After the Rain

Pilih **After the Rain**, tentukan **Normal** atau **Hard · Strategi**, lalu mulai balapan. Kedua mode berjalan lokal tanpa API key atau koneksi AI eksternal. Normal memakai pilihan target lokal dan kecepatan pemain standar. Hard membuat Original merencanakan dua target mie yang bisa diraih, berbelok dan berakselerasi lebih cepat, lebih sigap melakukan sprint, serta lebih cepat mencari rute baru saat terhambat. Kecepatan jalan dan sprint pemain tetap normal; kecepatan maksimum Original tetap sama.

Untuk membuka game, jalankan melalui server HTTP, misalnya `npx serve . -l 3000`, lalu buka `/game.html`.

Map After the Rain diadaptasi dari “After the rain... - VR & Sound” oleh Aurélien Martel:
https://sketchfab.com/3d-models/after-the-rain-vr-sound-a1177381d3464f75b10cb8f462f0b9a5
Lisensi CC BY-NC 4.0: https://creativecommons.org/licenses/by-nc/4.0/
Material Specular-Glossiness dikonversi ke PBR untuk Three.js; tekstur sumber dipertahankan.

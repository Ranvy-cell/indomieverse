# INDOMIEVERSE 3D

Struktur folder (taruh di root website, sejajar dengan index.html):

```
game.html
setup-lib.mjs
supabase-config.js        <- sudah ada di website kamu
assets/
  original-character.v1.glb   (2,2 MB)
  campus.v1.glb               (3,1 MB)
lib/                      <- dibuat oleh: node setup-lib.mjs
```

1. `node setup-lib.mjs` (sekali saja, butuh internet) -> membuat folder `lib/`.
2. Jalankan lewat server (bukan klik dua kali file), mis. `npx serve .` lalu buka `/game.html`.
   Parameter opsional: `game.html?spawn=40` memilih titik awal lain.

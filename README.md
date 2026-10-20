# INDOMIEVERSE 3D

Struktur folder (taruh di root website, sejajar dengan index.html):

```
game.html
setup-lib.mjs
supabase-config.js        <- sudah ada di website kamu
assets/
  original-character.v1.glb   (2,2 MB)
  campus.v2.glb               (56,3 MB, tekstur 8K)
  postwar-city.v1.glb          (map Post-war)
  home-interior-map.v1.glb     (Home free roam)
lib/                      <- dibuat oleh: node setup-lib.mjs
```

1. `node setup-lib.mjs` (sekali saja, butuh internet) -> membuat folder `lib/`.
2. Jalankan lewat server (bukan klik dua kali file), mis. `npx serve .` lalu buka `/game.html`.
3. Pilih Campus atau Post-war untuk misi koleksi, atau Home untuk free roam di interior.

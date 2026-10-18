/* Edit this file to swap assets.
   Image paths work with .png, .jpg, .jpeg or .webp: the extension is optional and auto-detected.
   Empty characters entries use assets/characters/<id>.(png|jpg|...) if that file exists.
   Ad fields: type, src, title (tagline), caption, optional label, optional cta + go (page: home|collection|redeem|chat|missions). */
window.IV_ASSETS={
  logo:'assets/brand/indomie-logo',
  characters:{original:'assets/characters/original',pedas:'assets/characters/pedas',nusantara:'',secret:''},
  ads:[
    {type:'video',src:'assets/video/iklan-1.mp4',label:'INDOMIE · BRAND CAMPAIGN',title:'Indomie, Hadir untuk Semua.',caption:'Dari yang dekat sampai yang jauh, dari yang punya sampai yang butuh.',cta:'Jelajahi Cerita',go:'collection'},
    {type:'video',src:'assets/video/iklan-2.mp4',title:'Hangat di Setiap Cerita.',caption:'Kenyamanan, kenangan, dan momen sederhana.'},
    {type:'video',src:'assets/video/iklan-3.mp4',title:'Satu Mangkuk, Sejuta Kehangatan.',caption:'Setiap mangkuk membawa ceritanya sendiri.'},
    {type:'video',src:'assets/video/iklan-4.mp4',title:'Selalu Ada di Cerita Kita.',caption:'Untuk mahasiswa, pekerja, dan keluarga.'}
  ]
};

// Menyiapkan folder lib/ (three.js lokal, tanpa CDN).
// Jalankan sekali dari folder yang sama dengan game.html:   node setup-lib.mjs
// Butuh Node.js 18+ dan koneksi internet (hanya saat setup).
import {execSync} from 'node:child_process';
import {mkdirSync, copyFileSync, existsSync, mkdtempSync, rmSync, writeFileSync} from 'node:fs';
import {join, dirname} from 'node:path';
import {tmpdir} from 'node:os';

const THREE='0.170.0', BVH='0.8.3';
const tmp=mkdtempSync(join(tmpdir(),'iv-'));
try{
  writeFileSync(join(tmp,'package.json'),'{"name":"iv-tmp","private":true}');
  console.log(`Mengunduh three@${THREE} dan three-mesh-bvh@${BVH}…`);
  execSync(`npm install --no-audit --no-fund three@${THREE} three-mesh-bvh@${BVH}`,{cwd:tmp,stdio:'inherit'});
  const nm=join(tmp,'node_modules');
  const files=[
    [join(nm,'three/build/three.module.js'),        'lib/three.module.js'],
    [join(nm,'three/examples/jsm/loaders/GLTFLoader.js'),        'lib/addons/loaders/GLTFLoader.js'],
    [join(nm,'three/examples/jsm/libs/meshopt_decoder.module.js'),'lib/addons/libs/meshopt_decoder.module.js'],
    [join(nm,'three/examples/jsm/utils/BufferGeometryUtils.js'), 'lib/addons/utils/BufferGeometryUtils.js'],
    [join(nm,'three-mesh-bvh/build/index.module.js'),'lib/three-mesh-bvh.js'],
  ];
  for(const [src,dst] of files){
    if(!existsSync(src))throw new Error('File tidak ditemukan: '+src);
    mkdirSync(dirname(dst),{recursive:true});copyFileSync(src,dst);console.log('✓',dst);
  }
  console.log('\nSelesai. Folder lib/ siap dipakai.');
}finally{rmSync(tmp,{recursive:true,force:true})}

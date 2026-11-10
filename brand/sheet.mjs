// Önizleme: her logo kare + yuvarlak profil kırpımı + karanlık video karesi üstünde filigran
import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs';
const o = f => 'data:image/svg+xml;base64,' + fs.readFileSync('out/' + f).toString('base64');
const keys = ['1-kok', '2-rota', '3-muhur'];
const row = k => `<div class=r><img src="${o(k+'.svg')}" class=sq><img src="${o(k+'.svg')}" class=ci>
 <div class=vid><img src="${o(k+'-filigran.svg')}" class=wm></div></div>`;
const html = `<style>body{margin:0;background:#ddd;font-family:sans-serif}.r{display:flex;gap:30px;padding:30px;align-items:center}
.sq{width:300px;height:300px}.ci{width:150px;height:150px;border-radius:50%}
.vid{width:220px;height:390px;background:linear-gradient(160deg,#6b4f36,#2a3a2f);position:relative}
.wm{position:absolute;right:12px;top:12px;width:54px;opacity:.85}</style>
${keys.map(row).join('')}<div class=r><img src="${o('yazi.svg')}" style="width:600px;background:#F3EBDD"></div>`;
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 860, height: 100 } });
await p.setContent(html); await p.screenshot({ path: process.argv[2], fullPage: true }); await b.close();

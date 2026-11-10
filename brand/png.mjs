// out/*.svg -> out/png/*.png  (profil 1080px, filigran/şeffaf 512px, yazı 2x)
import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs';
fs.mkdirSync('out/png', { recursive: true });
const b = await chromium.launch(); const p = await b.newPage();
for (const f of fs.readdirSync('out').filter(f => f.endsWith('.svg'))) {
  const svg = fs.readFileSync('out/' + f, 'utf8');
  const [, w, h] = svg.match(/viewBox="0 0 (\d+) (\d+)"/).map(Number);
  const out = f.startsWith('yazi') ? [w * 2, h * 2] : f.match(/filigran|seffaf/) ? [512, 512] : [1080, 1080];
  await p.setViewportSize({ width: out[0], height: out[1] });
  await p.setContent(`<style>body{margin:0}svg{width:100vw;height:100vh;display:block}</style>${svg}`);
  await p.screenshot({ path: 'out/png/' + f.replace('.svg', '.png'), omitBackground: true });
}
await b.close();

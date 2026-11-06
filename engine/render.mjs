// Kare kare render: node engine/render.mjs topics/<konu> [--stills 0,90,300] [--scale 0.5] [--from 0 --to 10]
import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { readFileSync, mkdirSync, rmSync, existsSync } from 'fs';
import { execFileSync } from 'child_process';
import path from 'path';

const args = process.argv.slice(2), topic = path.resolve(args[0]);
const opt = k => { const i = args.indexOf('--' + k); return i < 0 ? null : args[i + 1]; };
const scale = +(opt('scale') || 1);
const timing = JSON.parse(readFileSync(path.join(topic, 'timing.json'), 'utf8'));
const script = JSON.parse(readFileSync(path.join(topic, 'script.json'), 'utf8'));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: scale });
await page.addInitScript(() => { window.__RENDER__ = true; });
page.on('pageerror', e => { console.error('Sayfa hatası:', e.message); process.exit(1); });
await page.goto('file://' + path.join(topic, 'scene.html'));
await page.evaluate(([t, s]) => T.init(t, s), [timing, script]);
await page.evaluate(() => document.fonts.ready);
// Türkçe glif ve font yüklemesi doğrulaması: eksik font sessizce sisteme düşmesin
const eksik = await page.evaluate(async () => {
  const fams = ['900 100px Fraunces', '300 100px Fraunces', '400 40px "IBM Plex Mono"', '600 40px Caveat', '500 40px "IBM Plex Sans"'];
  await Promise.all(fams.map(f => document.fonts.load(f, 'İŞĞÜÇÖıâ')));
  return fams.filter(f => !document.fonts.check(f, 'İŞĞÜÇÖıâ'));
});
if (eksik.length) { console.error('Yüklenmeyen font:', eksik); process.exit(1); }

const total = Math.round(timing.duration * 30);
const out = path.join(topic, 'out'); mkdirSync(out, { recursive: true });
const shot = async (f, file) => { await page.evaluate(f => window.renderFrame(f), f); await page.screenshot({ path: file, type: file.endsWith('.png') ? 'png' : 'jpeg', quality: file.endsWith('.png') ? undefined : 92 }); };

if (opt('stills')) {
  for (const f of opt('stills').split(',').map(Number)) await shot(f, path.join(out, `kare_${f}.png`));
  console.log('kareler:', out);
} else {
  const from = Math.round(+(opt('from') || 0) * 30), to = Math.min(total, opt('to') ? Math.round(+opt('to') * 30) : total);
  const dir = path.join(out, 'frames'); rmSync(dir, { recursive: true, force: true }); mkdirSync(dir);
  const t0 = Date.now();
  for (let f = from; f < to; f++) {
    await shot(f, path.join(dir, `${String(f - from).padStart(5, '0')}.jpg`));
    if (f % 150 === 0) console.log(`kare ${f}/${to} (${((Date.now() - t0) / 1000).toFixed(0)} sn)`);
  }
  const voice = path.join(topic, 'voice.mp3'), mp4 = path.join(out, 'video.mp4');
  const audio = existsSync(voice) ? ['-ss', String(from / 30), '-i', voice, '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11', '-shortest'] : [];
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-framerate', '30', '-i', path.join(dir, '%05d.jpg'), ...audio,
    '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-maxrate', '10M', '-bufsize', '20M', '-preset', 'medium', '-movflags', '+faststart', mp4]);
  console.log('video:', mp4);
}
await browser.close();

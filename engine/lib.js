// Ortak kare saati yardımcıları. Her konu kendi scene.html'inde bunu yükler.
// Animasyon yalnız kare numarasına bağlıdır (render deterministik olsun diye).
const FPS = 30;
const klamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
function bezier(x1, y1, x2, y2) {
  const cx = 3*x1, bx = 3*(x2-x1) - cx, ax = 1 - cx - bx;
  const cy = 3*y1, by = 3*(y2-y1) - cy, ay = 1 - cy - by;
  const X = t => ((ax*t + bx)*t + cx)*t, Y = t => ((ay*t + by)*t + cy)*t, dX = t => (3*ax*t + 2*bx)*t + cx;
  return x => { let t = klamp(x); for (let i = 0; i < 8; i++) { const e = X(t) - x, d = dX(t); if (Math.abs(e) < 1e-5 || Math.abs(d) < 1e-6) break; t -= e / d; } return Y(klamp(t)); };
}
const EASE = { dolly: bezier(0.55, 0, 0.1, 1), terk: bezier(0.7, 0, 0.84, 0), kalem: x => 0.5 - Math.cos(Math.PI * klamp(x)) / 2, duz: x => klamp(x) };
const lerp = (f, [f0, f1], [a, b], ease = EASE.duz) => a + (b - a) * ease(klamp((f - f0) / (f1 - f0)));
function rastgele(seed) { let t = seed + 0x6D2B79F5; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
const sec = s => Math.round(s * FPS);

// TIMING: tts.py çıktısı. Render'da enjekte edilir, tarayıcı önizlemesinde fetch ile yüklenir.
const T = {
  init(timing, script) {
    this.timing = timing; this.script = script; this.total = sec(timing.duration);
    // segment başlangıç/bitiş kareleri, sahne adıyla
    this.seg = {};
    script.segments.forEach((s, i) => {
      const ws = timing.words.filter(w => w.seg === i);
      this.seg[s.scene] = { start: sec(ws[0].start), end: sec(ws[ws.length - 1].end), words: ws };
    });
    this.chunks = captionChunks(timing.words);
  },
  // sahnenin kendi saatine göre kare (segment başından itibaren)
  local(scene, f) { return f - this.seg[scene].start; },
  // bir kelimenin (sahne içindeki sırası) başladığı kare, sahne başına göre
  wordAt(scene, idx) { const s = this.seg[scene]; return sec(s.words[idx].start) - s.start; },
  caption(f) { const t = f / FPS; return this.chunks.find(c => t >= c.start && t < c.end) || null; },
};

// Altyazı: anlam sınırında böl, satır başına en fazla ~26 karakter, en fazla 2 satır, segment aşmaz.
function captionChunks(words, maxLine = 26) {
  const chunks = []; let cur = [];
  const flush = () => { if (cur.length) chunks.push(cur); cur = []; };
  words.forEach((w, i) => {
    const prev = cur[cur.length - 1];
    if (prev && (prev.seg !== w.seg || /[.?!:,]$/.test(prev.w))) flush();
    else if (prev && lines(cur.concat(w), maxLine).length > 2) {
      // tek kelime yetim kalacaksa bir önceki kelimeyi de yeni parçaya taşı
      const orphan = /[.?!:,]$/.test(w.w) && cur.length > 2;
      const carry = orphan ? cur.pop() : null;
      flush(); if (carry) cur.push(carry);
    }
    cur.push(w);
  });
  flush();
  return chunks.map((c, i) => ({
    lines: lines(c, maxLine), start: c[0].start - 0.05,
    end: Math.min(chunks[i + 1] ? chunks[i + 1][0].start - 0.05 : Infinity, c[c.length - 1].end + 0.6),
  }));
}
function lines(ws, max) {
  const out = [""];
  ws.forEach(w => { const l = out[out.length - 1]; if (l && (l + " " + w.w).length > max) out.push(w.w); else out[out.length - 1] = l ? l + " " + w.w : w.w; });
  return out;
}

// Tarayıcıda önizleme: ?f=120 ile tek kare, yoksa oynat.
async function boot() {
  if (window.__RENDER__) return;
  const [timing, script] = await Promise.all(['timing.json', 'script.json'].map(u => fetch(u).then(r => r.json())));
  T.init(timing, script);
  await document.fonts.ready;
  const q = new URLSearchParams(location.search);
  if (q.has('f')) return window.renderFrame(+q.get('f'));
  const t0 = performance.now();
  (function loop(t) { window.renderFrame(Math.floor((t - t0) / 1000 * FPS) % T.total); requestAnimationFrame(loop); })(t0);
}
if (typeof module !== 'undefined') module.exports = { captionChunks, lines };
else addEventListener('load', boot);

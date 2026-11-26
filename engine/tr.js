// Türkçe kanal ortak yardımcıları (cute.js'in Türkçe sürümü): anahtar kare, Türkçe kelime ipucu, etiket, kelime vurgulu altyazı.
// lib.js'ten sonra yüklenir. Renkler window.ALT = {soluk, aktif, normal} ile, etiket fontu window.ETIKET_FONT ile ayarlanır.
const $ = id => document.getElementById(id);
const P = Math.PI, sin = Math.sin, cos = Math.cos;
const sm = x => { x = klamp(x); return x * x * (3 - 2 * x); };
const backOut = x => { x = klamp(x); const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const f2 = n => n.toFixed(1);
// anahtar kareler: [[kare, değer]], değer sayı ya da dizi; aralarda yumuşak geçiş
function kf(f, list) {
  if (f <= list[0][0]) return list[0][1];
  for (let i = 1; i < list.length; i++) if (f < list[i][0]) {
    const [f0, a] = list[i - 1], [f1, b] = list[i], t = sm((f - f0) / (f1 - f0));
    return Array.isArray(a) ? a.map((v, k) => v + (b[k] - v) * t) : a + (b - a) * t;
  }
  return list[list.length - 1][1];
}
// kelime ipucu: sahnedeki n'inci eşleşen kelimenin mutlak karesi
function cue(sc, onek, n = 0) {
  const ws = T.seg[sc].words; let k = -1;
  for (let i = 0; i < ws.length; i++) if (ws[i].w.toLocaleLowerCase('tr-TR').replace(/[^a-zçğıöşüâî0-9']/g, '').startsWith(onek) && n-- === 0) { k = i; break; }
  if (k < 0) throw new Error(`ipucu yok: ${sc}/${onek}`);
  return sec(ws[k].start);
}
function hex(c) { return [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)); }
function mix(a, b, t) { const A = hex(a), B = hex(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join(''); }
// zıplayarak beliren etiket; f0-f1 arasında görünür
function etiket(txt, x, y, f, f0, f1, size = 64, renk = '#FFF3DC', anchor = 'middle', kontur = '#151833') {
  if (f < f0 || f > f1 + 8) return '';
  const s = backOut((f - f0) / 12) * (1 - klamp((f - f1) / 8)), o = klamp((f - f0) / 4) * (1 - klamp((f - f1) / 8));
  return `<g transform="translate(${f2(x)},${f2(y)}) scale(${s.toFixed(3)})" opacity="${o.toFixed(2)}"><text class="lbl" font-family="${window.ETIKET_FONT || 'Archivo'}" text-anchor="${anchor}" font-size="${size}" fill="${renk}" stroke="${kontur}" stroke-width="${size * 0.16}" dy="${size * 0.35}">${txt}</text></g>`;
}
// altyazı: konuşulan kelime sarı, sıradakiler soluk
function altyazi(f, el) {
  const cp = T.caption(f), tt = f / FPS;
  if (!cp) { el.innerHTML = ''; return; }
  const seg = T.timing.words.find(y => y.start >= cp.start - 0.01).seg;
  const ws = T.timing.words.filter(x => x.start >= cp.start - 0.01 && x.start < cp.end && x.seg === seg);
  let i = 0;
  el.innerHTML = cp.lines.map(line => line.split(' ').map(() => {
    const x = ws[i++]; if (!x) return '';
    const A = window.ALT || { soluk: 'rgba(255,243,220,.35)', aktif: '#FFC94A', normal: '#FFF3DC' };
    const col = tt < x.start ? A.soluk : tt < x.end + 0.05 ? A.aktif : A.normal;
    return `<span style="color:${col}">${x.w}</span>`;
  }).join(' ')).join('<br>');
}

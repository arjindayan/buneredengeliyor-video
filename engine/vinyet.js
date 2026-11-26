// Sahne başına bir illüstrasyon (vinyet) düzeni: her segmentin SAHNE[ad](f,S,t) fonksiyonu çizer,
// komşularla 12 karede çapraz geçer, girişte hafif yakınlaşır. cute.js ya da tr.js'ten sonra yüklenir.
function vinyetler(f, SAHNE, el, cx = 540, cy = 1000, zoom = .06) {
  const S = T.seg, adlar = Object.keys(SAHNE); let g = '';
  adlar.forEach((ad, i) => {
    const bas = i ? S[ad].start - 4 : 0, son = i + 1 < adlar.length ? S[adlar[i + 1]].start - 4 : T.total + 10;
    if (f < bas - 2 || f > son + 12) return;
    const o = (i ? klamp((f - bas) / 12) : 1) * (1 - klamp((f - son) / 12));
    const z = 1 + (1 - (i ? sm((f - bas) / 16) : 1)) * zoom + (f - bas) * .00025; // girişte yakınlaşma + yavaş itme
    g += `<g opacity="${f2(o)}" transform="translate(${cx},${cy}) scale(${z.toFixed(4)}) translate(${-cx},${-cy})">${SAHNE[ad](f, S, f - bas)}</g>`;
  });
  el.innerHTML = g;
}
// f0'da zıplayarak beliren grup
const pop = (f, f0, d = 12) => f < f0 ? 0 : backOut((f - f0) / d);
const gir = (f, f0, d = 12) => sm((f - f0) / d);
const at = (x, y, s, ic, r = 0, o = 1) => `<g transform="translate(${f2(x)},${f2(y)}) rotate(${f2(r)}) scale(${(+s).toFixed(3)})" opacity="${(+o).toFixed(2)}">${ic}</g>`;
// yumuşak yer gölgesi
const golge = (x, y, rx, o = .25) => `<ellipse cx="${f2(x)}" cy="${f2(y)}" rx="${f2(rx)}" ry="${f2(rx * .18)}" fill="#000" opacity="${o}"/>`;
// sevimli yüz (karakterlere): göz aralığı d, gülümseme, yanaklar
function yuz(x, y, s, t, o = {}) {
  const blink = (Math.floor(t + (o.seed || 0) * 37) % 110) < 5, d = 34;
  const goz = gx => blink || o.kapali ? `<path d="M${gx - 11} 0 q11 9 22 0" stroke="${o.cizgi || '#2A1B14'}" stroke-width="6" fill="none" stroke-linecap="round"/>`
    : `<circle cx="${gx}" cy="0" r="${o.sur ? 15 : 12}" fill="${o.cizgi || '#2A1B14'}"/><circle cx="${gx - 4}" cy="-5" r="4.5" fill="#fff"/>`;
  const agiz = o.sur ? `<ellipse cx="0" cy="34" rx="12" ry="15" fill="${o.cizgi || '#2A1B14'}"/>` : o.esne ? `<ellipse cx="0" cy="40" rx="${f2(16 + o.esne * 10)}" ry="${f2(8 + o.esne * 26)}" fill="#5A2230"/>`
    : `<path d="M-20 26 q20 ${o.uzgun ? -10 : 18} 40 0" stroke="${o.cizgi || '#2A1B14'}" stroke-width="6" fill="none" stroke-linecap="round"/>`;
  return `<g transform="translate(${f2(x)},${f2(y)}) scale(${s})">${goz(-d)}${goz(d)}${agiz}<ellipse cx="-58" cy="24" rx="15" ry="9" fill="${o.yanak || '#FF8FA3'}" opacity=".55"/><ellipse cx="58" cy="24" rx="15" ry="9" fill="${o.yanak || '#FF8FA3'}" opacity=".55"/></g>`;
}
// yüzen toz/ışık parçacıkları
function parcacik(t, n, renk, op = .4, hiz = .0015, seed = 0) {
  let g = '';
  for (let k = 0; k < n; k++) { const u = (rastgele(k + seed) + t * hiz) % 1; g += `<circle cx="${f2(rastgele(k + 7 + seed) * 1080 + sin(t * .02 + k) * 30)}" cy="${f2(1950 - u * 2000)}" r="${f2(2.5 + rastgele(k + seed + 3) * 4)}" fill="${renk}" opacity="${f2(op * sin(u * P))}"/>`; }
  return g;
}

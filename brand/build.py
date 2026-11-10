"""Logo konseptlerini SVG olarak üretir (yazılar path'e çevrilir, font gerekmez).
Çalıştır: python3 brand/build.py  -> brand/out/*.svg ; PNG için brand/render.mjs"""
import math, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'engine', 'fonts')
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
PAPER, INK, RED = '#F3EBDD', '#1B1A17', '#C8372D'

def load(name):  # latin + latin-ext alt kümeleri birlikte (İ, ğ, ş için)
    return [TTFont(os.path.join(FONTS, f'{name}-{s}.woff2')) for s in ('latin', 'latin-ext')]
FR9, FR3, MONO = load('Fraunces-normal-900'), load('Fraunces-normal-300'), load('IBMPlexMono-normal-600')

def glyph(fonts, ch):
    for f in fonts:
        g = f.getBestCmap().get(ord(ch))
        if g: return f, g
    raise KeyError(ch)

def text_width(fonts, s, size, track=0):
    w = 0
    for ch in s:
        f, g = glyph(fonts, ch)
        w += f['hmtx'][g][0] * size / f['head'].unitsPerEm + track
    return w - track

def glyph_path(fonts, ch, x, y, size, rot=0):
    """Tek glif: taban çizgisi sol noktası (x,y), rot derece."""
    f, g = glyph(fonts, ch)
    s = size / f['head'].unitsPerEm
    pen = SVGPathPen(f.getGlyphSet())
    c, si = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    # font y yukarı, svg y aşağı: ölçek + ayna + döndürme + öteleme
    f.getGlyphSet()[g].draw(TransformPen(pen, (s*c, s*si, s*si, -s*c, x, y)))
    return pen.getCommands(), f['hmtx'][g][0] * s

def text_path(fonts, s, x, y, size, anchor='middle', track=0):
    if anchor == 'middle': x -= text_width(fonts, s, size, track) / 2
    out = []
    for ch in s:
        d, adv = glyph_path(fonts, ch, x, y, size)
        out.append(d); x += adv + track
    return ' '.join(out)

def circle_text(fonts, s, cx, cy, r, size, start=-90, track=0):
    """Metni çember üzerine saat yönünde dizer (start: ilk harfin açısı)."""
    out, ang = [], start
    for ch in s:
        f, g = glyph(fonts, ch)
        adv = f['hmtx'][g][0] * size / f['head'].unitsPerEm
        mid = ang + math.degrees((adv/2) / r)
        a = math.radians(ang)
        d, _ = glyph_path(fonts, ch, cx + r*math.cos(a), cy + r*math.sin(a), size, rot=ang+90)
        out.append(d); ang += math.degrees((adv + track) / r)
    return ' '.join(out)

def svg(body, w=1000, h=1000, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{rect}{body}</svg>\n'

# Ortak soru işareti kavisi (noktasız; noktanın yerine her konsept kendi işaretini koyar)
Q = 'M330 370 C330 245 415 175 505 175 C605 175 680 245 680 340 C680 430 612 468 562 500 C522 526 503 558 503 612 L503 655'

# 1) KÖK: soru işaretinin noktası yerine kökler. "Köken" = kök.
def kok(fg=INK, accent=RED):
    roots = ''.join(f'<path d="{d}" stroke-width="{w}"/>' for d, w in [
        ('M503 640 C503 720 500 790 503 840', 34),
        ('M503 830 C505 860 501 885 506 915', 18),
        ('M503 690 C470 735 420 758 396 800 C381 826 378 860 368 892', 22),
        ('M503 715 C540 748 590 768 610 808 C622 834 620 866 632 896', 20),
        ('M424 762 C398 758 368 744 348 718', 12),
        ('M592 776 C620 770 648 754 662 728', 12),
        ('M502 800 C480 828 462 850 455 886', 10),
        ('M504 836 C525 852 545 862 560 888', 9),
        ('M392 812 C370 828 352 846 344 870', 8)])
    return (f'<path d="{Q}" fill="none" stroke="{fg}" stroke-width="100" stroke-linecap="round"/>'
            f'<g fill="none" stroke="{accent}" stroke-linecap="round">{roots}</g>')

# 2) ROTA: soru işareti haritada kesik kesik bir yol, noktası konum pini.
def rota(fg=PAPER, accent=RED):
    pin = ('M503 905 C470 852 428 818 428 765 A75 75 0 1 1 578 765 C578 818 536 852 503 905 Z')
    hole = 'M531 765 A28 28 0 1 0 475 765 A28 28 0 1 0 531 765 Z'  # evenodd ile delik: arka plan görünür
    return (f'<path d="{Q.replace("L503 655", "L503 620")}" fill="none" stroke="{fg}" stroke-width="52" '
            f'stroke-linecap="round" stroke-dasharray="0 78"/>'
            f'<path d="{pin} {hole}" fill="{accent}" fill-rule="evenodd"/>')

# 3) MÜHÜR: arşiv damgası, ortada Fraunces "?", çevrede seri adı.
def muhur(fg=RED, inner=INK):
    t, r, size = 'BU NEREDEN GELİYOR? · KÖKEN HİKÂYELERİ · ', 392, 64
    track = (2*math.pi*r - text_width(MONO, t, size)) / len(t)
    head = text_width(MONO, 'BU NEREDEN GELİYOR?', size) + track * 18
    ring = circle_text(MONO, t, 500, 500, r, size, start=-90 - math.degrees(head / 2 / r), track=track)
    q = text_path(FR9, '?', 500, 690, 560)
    return (f'<circle cx="500" cy="500" r="470" fill="none" stroke="{fg}" stroke-width="16"/>'
            f'<circle cx="500" cy="500" r="340" fill="none" stroke="{fg}" stroke-width="6"/>'
            f'<path d="{ring}" fill="{fg}"/><path d="{q}" fill="{inner}"/>')

def wordmark(fg=INK, accent=RED):
    a = text_path(FR9, 'bu nereden', 0, 150, 190, anchor='start')
    w = text_width(FR9, 'geliyor', 190)
    b = text_path(FR9, 'geliyor', 0, 330, 190, anchor='start')
    q = text_path(FR9, '?', w + 8, 330, 190, anchor='start')
    return f'<path d="{a} {b}" fill="{fg}"/><path d="{q}" fill="{accent}"/>', max(text_width(FR9, 'bu nereden', 190), w + 120)

def write(name, s): open(os.path.join(OUT, name), 'w').write(s)

for key, fn, bg, white in [
    ('1-kok',   kok,   PAPER, lambda: kok('#fff', '#fff')),
    ('2-rota',  rota,  INK,   lambda: rota('#fff', '#fff')),
    ('3-muhur', muhur, PAPER, lambda: muhur('#fff', '#fff'))]:
    write(f'{key}.svg', svg(fn(), bg=bg))                       # profil / ana logo
    write(f'{key}-seffaf.svg', svg(fn()))                       # arka plansız
    write(f'{key}-filigran.svg', svg(white()))                  # videoda beyaz filigran

wm, ww = wordmark()
write('yazi.svg', svg(wm, w=round(ww)+10, h=410))
wm2, _ = wordmark('#fff', '#fff')
write('yazi-beyaz.svg', svg(wm2, w=round(ww)+10, h=410))
print('ok', sorted(os.listdir(OUT)))

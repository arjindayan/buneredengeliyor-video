"""AI logo görselinden profil (1080 kare, krem zemin) ve beyaz şeffaf filigran üretir.
Kullanım: python3 brand/finalize.py girdi.png cikti_on_eki"""
import sys
from PIL import Image, ImageOps
src, pre = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
g = ImageOps.grayscale(im)
# mürekkep (siyah) ve kırmızı, krem zeminden belirgin koyu: alfa = zemin farkı
alpha = g.point(lambda v: max(0, min(255, (215 - v) * 255 // 110)))
bbox = alpha.point(lambda v: 255 if v > 60 else 0).getbbox()
x0, y0, x1, y1 = bbox; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
side = max(x1 - x0, y1 - y0) / 0.62  # logo dairenin ~%62'sini kaplasın (IG yuvarlak kırpım)
box = tuple(round(v) for v in (cx - side/2, cy - side/2, cx + side/2, cy + side/2))
bg = im.getpixel((5, 5))
sq = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), bg); sq.paste(im, (-box[0], -box[1]))  # kare dışı zeminle dolar
sq.resize((1080, 1080), Image.LANCZOS).save(f'{pre}-profil.png')
# filigran: sıkı kırpım, beyaz + alfa
t = alpha.crop(bbox); w = Image.new('RGBA', t.size, (255, 255, 255, 0)); w.putalpha(t)
w.thumbnail((512, 512), Image.LANCZOS); w.save(f'{pre}-filigran-beyaz.png')
k = Image.new('RGBA', t.size); k.paste(im.crop(bbox)); k.putalpha(t); k.thumbnail((1024, 1024), Image.LANCZOS)
k.save(f'{pre}-seffaf.png')
print(pre, box, im.size)

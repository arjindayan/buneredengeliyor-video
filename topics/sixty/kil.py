# Kil tablet dokusu: fraktal gürültü yükseklik haritası + eğik ışık (sol üst). Bir kez üretilir: img/clay.jpg
import numpy as np
from PIL import Image, ImageFilter
W, H = 1080, 1920; rng = np.random.default_rng(7)
def gurultu(sc):
    a = rng.random((H // sc + 2, W // sc + 2)).astype(np.float32)
    return np.asarray(Image.fromarray(a).resize((W, H), Image.BICUBIC))
h = sum(gurultu(s) * w for s, w in [(240, 1.0), (90, .5), (30, .25), (8, .12), (3, .06)])
# parmak izi / spatula izleri: hafif yatay sürtünme
h += .05 * np.sin(np.linspace(0, 60, H))[:, None] * gurultu(120)
gy, gx = np.gradient(h)
lit = np.clip(.5 - (gx * -.7 + gy * -.7) * 9, 0, 1)
base = np.array([206, 160, 118], np.float32)  # pişmemiş kil
img = base * (.82 + .32 * lit[..., None]) * (.94 + .1 * gurultu(400)[..., None])
# kenar kararması (tablet kenarı)
yy, xx = np.mgrid[0:H, 0:W]; d = np.minimum.reduce([xx, W - xx, yy, H - yy]) / 140
img *= (.78 + .22 * np.clip(d, 0, 1))[..., None]
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
im.save('img/clay.jpg', quality=92)

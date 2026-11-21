# Eski baskı kâğıdı dokusu: lif gürültüsü + kenar sararması. Bir kez üretilir: img/paper.jpg
import numpy as np
from PIL import Image, ImageFilter
W, H = 1080, 1920; rng = np.random.default_rng(3)
def g(sc):
    a = rng.random((H // sc + 2, W // sc + 2)).astype(np.float32)
    return np.asarray(Image.fromarray(a).resize((W, H), Image.BICUBIC))
n = g(300) * .5 + g(60) * .3 + g(6) * .2
lif = np.asarray(Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur((6, .6))), np.float32) / 255  # yatay lifler
img = np.array([210, 207, 154], np.float32) * (.93 + .08 * n[..., None] + .05 * (lif[..., None] - .5))
yy, xx = np.mgrid[0:H, 0:W]; d = np.minimum.reduce([xx, W - xx, yy, H - yy]) / 180
img *= np.stack([.86 + .14 * np.clip(d, 0, 1)] * 3, -1) * np.array([1, 1, 1]) + np.array([0, 0, 0]) * np.clip(d, 0, 1)[..., None]
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save('img/paper.jpg', quality=92)

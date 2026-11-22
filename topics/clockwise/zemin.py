# Koyu yeşil zemin: hafif fırçalanmış metal gürültüsü + ortada açık yeşil hale, kenarlar mürekkebe kararır. img/bg.jpg
import numpy as np
from PIL import Image, ImageFilter
W, H = 1080, 1920; rng = np.random.default_rng(7)
INK, GREEN = np.array([0x28, 0x30, 0x1C], np.float32), np.array([0x32, 0x3D, 0x25], np.float32)
yy, xx = np.mgrid[0:H, 0:W]
r = np.hypot(xx - 540, yy - 960) / 1100
t = np.clip(1 - r, 0, 1)[..., None] ** 1.4
img = INK + (GREEN - INK) * t
# dairesel fırça izi: açıya göre bulanıklaştırılmış gürültü yerine halka bantları
ring = np.asarray(Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 - .5
band = np.sin(np.hypot(xx - 540, yy - 960) * .9) * .5
img *= (1 + .035 * ring + .012 * band)[..., None]
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save('img/bg.jpg', quality=93)

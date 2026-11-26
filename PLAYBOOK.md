# Video üretim akışı

Her konu `topics/<konu>/` altında: `script.json`, `scene.html`, `style.md`, `research.md`.

1. **Araştırma** → `research.md`. Her iddia için en az 2 kaynak; tek kaynaklı iddia atfedilir, çelişen atılır.
2. **Metin** → `script.json`. Segmentler sahnelere bağlı (`scene`). İlk cümle hook, son cümle soru/döngü.
   Yıl ve sayılar ekranda rakam, seste yazı: `{1773|bin yedi yüz yetmiş üç}`.
3. **Stil kartı** → `style.md`. Son iki videonun kartından en az 3 eksende farklı olmalı; aynı font ve imza öğe art arda tekrar etmez. Kartların listesi: `STYLES.md`.
4. **Ses ve zamanlama** → `python3 engine/tts.py topics/<konu>` (ElevenLabs, `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`).
   Ses yoksa `--dry` (tahmini zamanlama), kendi mp3'ün varsa `--mp3 dosya.mp3`.
5. **Sahne** → `scene.html`: `engine/lib.js` yüklenir, `window.renderFrame(f)` yalnız kare numarasına bağlı. Sahne zamanları `T.seg[sahne]`, kelime ipuçları `T.wordAt`.
5b. **Görseller (isteğe bağlı)** → `shots.json`: her çekim bir sahneye ve ipucu kelimeye bağlı; görseller `img/<id>.jpg`. Higgsfield `z_image` (ücretsiz plan, görsel başı 0,15 kredi, tek tek gönder: eşzamanlı istek 429 veriyor). Sahne `window.kurShots = d => Shots.init(d, katman)` tanımlar ve `Shots.render(f)` çağırır.
6. **Kare kontrolü** → `node engine/render.mjs topics/<konu> --scale 0.5 --stills 30,300,900`.
7. **Render** → `node engine/render.mjs topics/<konu>` → `topics/<konu>/out/video.mp4` (1080x1920, 30 fps, ses -15 LUFS).

Gereken: node, ffmpeg, playwright (Chromium).

## Gemini worker (`engine/gemini.py`)

İkinci görüş ve yardımcı işler için Gemini (`GEMINI_API_KEY`, yalnız Python stdlib). Sonuçları kaynakla doğrula; Gemini'nin söylediği gerçek değildir, taslaktır.

- Araştırma taslağı / karşı kontrol: `python3 engine/gemini.py "X'in kökeni hakkında iddiaları ve kaynaklarını listele"`
- Metin alternatifleri: `python3 engine/gemini.py -s topics/<konu>/style.md "Bu metne 5 farklı kanca yaz" - < metin.txt`
- Kare kontrolü (6. adımdan sonra): `python3 engine/gemini.py "Bu karelerde altyazı okunuyor mu, palet dışı renk var mı (#28301C #323D25 #9A7E3B #D2CF9A + beyaz)?" -f out/still_30.png -f out/still_300.png`
- JSON çıktı: `--json` (şemayı istemde yaz). Python'dan: `from gemini import ask`.

Model zinciri (`GEMINI_MODELS` ile değişir): gemini-3.8-flash → 3.5-flash → 3-flash-preview → 3.5-flash-lite. Ücretsiz katmanda Pro ve gemini-4-* kotası 0; Flash modelleri yoğunlukta 503 verir ya da asılı kalır, betik 60 sn sonra (`GEMINI_TIMEOUT`) sıradakine geçer. Dosya başı ~19 MB inline sınırı.

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
8. **Kapanış (varsayılan)** → `engine/cta.sh <tr|en> out/final.mp4 out/final_cta.mp4`: sona 3 sn "beğen + takip et" kartı. Yeni her videoya eklenir, eskilere değil.

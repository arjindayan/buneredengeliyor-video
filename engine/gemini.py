#!/usr/bin/env python3
"""Gemini worker: text, image/frame and short-video understanding.

  python3 engine/gemini.py "soru"                         # metin
  python3 engine/gemini.py "bu karede ne var?" -f kare.png # görsel/video/pdf ekle (-f tekrar edilebilir)
  python3 engine/gemini.py -s sistem.md "..." --json       # JSON çıktı iste
  echo "uzun metin" | python3 engine/gemini.py "özetle" -   # stdin'i metne ekle

Python'dan: from gemini import ask; ask("...", files=["a.png"]).
Anahtar: GEMINI_API_KEY. Model zinciri sırayla denenir (yoğunluk/kota hatasında sonrakine geçer).
"""
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

# Ücretsiz katman: Pro ve gemini-4-* modellerinde kota 0, bu yüzden Flash zinciri.
MODELS = os.environ.get("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.5-flash,"
                        "gemini-3-flash-preview,gemini-3.5-flash-lite").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
TIMEOUT = float(os.environ.get("GEMINI_TIMEOUT", 60))  # yoğun model bazen yanıtsız asılı kalıyor
INLINE_MAX = 19 * 1024 * 1024  # inline_data istek sınırı ~20 MB


def _part(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    data = open(path, "rb").read()
    if len(data) > INLINE_MAX:
        raise SystemExit(f"{path}: {len(data)>>20} MB, inline sınırı aşıyor (kareleri ayrı gönder)")
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}


def ask(prompt, files=(), system=None, json_out=False, models=None, temperature=None):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY tanımlı değil")
    body = {"contents": [{"role": "user", "parts": [_part(f) for f in files] + [{"text": prompt}]}]}
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}
    cfg = {}
    if json_out:
        cfg["response_mime_type"] = "application/json"
    if temperature is not None:
        cfg["temperature"] = temperature
    if cfg:
        body["generationConfig"] = cfg
    payload = json.dumps(body).encode()
    errors = []
    for model in models or MODELS:
        for attempt in range(2):
            req = urllib.request.Request(URL.format(model.strip()), payload, method="POST",
                                         headers={"x-goog-api-key": key, "content-type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    d = json.load(r)
                parts = d["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                return json.loads(text) if json_out else text
            except urllib.error.HTTPError as e:
                msg = json.loads(e.read() or b"{}").get("error", {}).get("message", "")[:120]
                errors.append(f"{model}: {e.code} {msg}")
                if e.code == 503 and attempt == 0:
                    time.sleep(3)
                    continue
                if e.code in (429, 503, 404, 400) and "API key" not in msg:
                    break  # sonraki model
                raise SystemExit("\n".join(errors))
            except TimeoutError:
                errors.append(f"{model}: {TIMEOUT:.0f} sn zaman aşımı")
                break
            except (KeyError, IndexError):
                errors.append(f"{model}: boş yanıt {json.dumps(d)[:200]}")
                break
    raise SystemExit("Hiçbir model yanıt vermedi:\n" + "\n".join(errors))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("stdin", nargs="?", help="'-' verilirse stdin metne eklenir")
    ap.add_argument("-f", "--file", action="append", default=[])
    ap.add_argument("-s", "--system", help="sistem talimatı dosyası")
    ap.add_argument("-m", "--model", help="tek model ya da virgüllü zincir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    p = a.prompt + ("\n\n" + sys.stdin.read() if a.stdin == "-" else "")
    out = ask(p, a.file, open(a.system).read() if a.system else None, a.json,
              a.model.split(",") if a.model else None)
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else out)

"""Seslendirme + kelime zamanlaması.

Kullanım:
  python3 engine/tts.py topics/<konu>          # ElevenLabs ile voice.mp3 + timing.json
  python3 engine/tts.py topics/<konu> --dry    # ses yok, hece sayısından tahmini timing.json (önizleme için)
  python3 engine/tts.py topics/<konu> --mp3 x.mp3  # kendi mp3'ün: ElevenLabs forced alignment ile hizala
Ortam: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (isteğe bağlı ELEVENLABS_MODEL)
"""
import base64, json, os, re, subprocess, sys, urllib.request

API = "https://api.elevenlabs.io/v1"


MARK = re.compile(r"\{([^|}]+)\|([^}]+)\}")  # {1770|bin yedi yüz yetmiş}: ekranda 1770, seste yazıyla


def spoken(t):
    return MARK.sub(lambda m: m.group(2), t)


TAG = re.compile(r"\[[^\]]*\]\s*")  # v3 ses etiketi: [curious], [short pause]; okunmaz, ekranda görünmez


def drop_tags(words):
    """Hizalamadan gelen etiket 'kelimelerini' at (etiket boşluk içerebilir)."""
    out, inside = [], False
    for w in words:
        if w["w"].startswith("["): inside = True
        if not inside: out.append(w)
        if w["w"].endswith("]"): inside = False
    return out


def display_tokens(t):
    """Her ekran kelimesi ve kaç sesli kelimeye karşılık geldiği."""
    t = TAG.sub("", t)
    out = []
    for part in re.split(r"(\{[^}]+\})", t):
        m = MARK.fullmatch(part)
        if m:
            out.append((m.group(1), len(m.group(2).split())))
        else:
            out += [(w, 1) for w in part.split()]
    return out


def merge_display(words, segments):
    """Sesli kelime zamanlamalarını ekran kelimelerine indir (1770 tek kelime olur)."""
    out, i = [], 0
    for si, seg in enumerate(segments):
        for disp, n in display_tokens(seg["text"]):
            g = words[i:i + n]; i += n
            # işaretin hemen arkasındaki ek/noktalama ("1770'te" gibi) sesli kelimede kalır
            out.append({"w": disp, "start": g[0]["start"], "end": g[-1]["end"], "seg": si})
    assert i == len(words), "kelime sayısı metinle uyuşmuyor"
    return out


def load(topic):
    s = json.load(open(os.path.join(topic, "script.json"), encoding="utf-8"))
    return s, " ".join(spoken(seg["text"]) for seg in s["segments"])


def seg_of_char(segments):
    """Birleşik metindeki her karakterin hangi segmente ait olduğu."""
    out = []
    for i, seg in enumerate(segments):
        out += [i] * len(spoken(seg["text"])) + [i]  # +1: araya giren boşluk
    return out


def words_from_chars(chars, starts, ends, segments):
    owner = seg_of_char(segments)
    words, cur = [], None
    for i, c in enumerate(chars):
        if c.isspace():
            if cur: words.append(cur); cur = None
            continue
        if cur is None:
            cur = {"w": "", "start": starts[i], "end": ends[i], "seg": owner[min(i, len(owner) - 1)]}
        cur["w"] += c
        cur["end"] = ends[i]
    if cur: words.append(cur)
    return words


def post(path, body=None, files=None):
    key = os.environ["ELEVENLABS_API_KEY"]
    if files:  # multipart
        b = "----bnd7f3"
        parts = []
        for k, v in (body or {}).items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        for k, (fn, data) in files.items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + data + b"\r\n")
        data, ctype = b"".join(parts) + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"
    else:
        data, ctype = json.dumps(body).encode(), "application/json"
    req = urllib.request.Request(API + path, data=data, headers={"xi-api-key": key, "Content-Type": ctype})
    try:
        return json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs hata {e.code}: {e.read()[:500].decode(errors='replace')}")


def duration(mp3):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3]))


def main():
    topic = sys.argv[1]
    s, text = load(topic)
    segs = s["segments"]
    if "--dry" in sys.argv:
        # shortcut: hece başına 0,17 sn tahmini, gerçek ses gelince ElevenLabs zamanlaması ile değişir
        words, t = [], 0.3
        for i, seg in enumerate(segs):
            for w in TAG.sub("", spoken(seg["text"])).split():
                d = max(1, len(re.findall(r"[aeıioöuüâîûAEIİOÖUÜ]", w))) * 0.17
                words.append({"w": w, "start": round(t, 3), "end": round(t + d, 3), "seg": i})
                t += d + (0.35 if w[-1] in ".:?!" else 0.12 if w[-1] == "," else 0.04)
        dur = t + 0.8
    elif "--mp3" in sys.argv:
        mp3 = sys.argv[sys.argv.index("--mp3") + 1]
        r = post("/forced-alignment", {"text": text}, {"file": (os.path.basename(mp3), open(mp3, "rb").read())})
        chars = r["characters"]
        words = words_from_chars([c["text"] for c in chars], [c["start"] for c in chars], [c["end"] for c in chars], segs)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, os.path.join(topic, "voice.mp3")], check=True)
        dur = duration(os.path.join(topic, "voice.mp3")) + 0.6
    else:
        voice = s.get("voice") or os.environ.get("ELEVENLABS_VOICE_ID", "uKigJX6jL7ZlAQRJHPGO")  # varsayılan: Arjin'in klonu
        r = post(f"/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
                 {"text": text, "model_id": s.get("model") or os.environ.get("ELEVENLABS_MODEL", "eleven_v4")})
        open(os.path.join(topic, "voice.mp3"), "wb").write(base64.b64decode(r["audio_base64"]))
        a = r["alignment"]
        words = words_from_chars(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"], segs)
        dur = duration(os.path.join(topic, "voice.mp3")) + 0.6
    words = merge_display(drop_tags(words), segs)
    json.dump({"duration": round(dur, 3), "words": words}, open(os.path.join(topic, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(words)} kelime, {dur:.1f} sn")


if __name__ == "__main__":
    main()

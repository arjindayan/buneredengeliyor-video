"""XTTS-v2 ile seslendirme + MMS forced alignment ile kelime zamanlaması.

tts.py, TTS_ENGINE=xtts iken bunu XTTS_PYTHON (coqui-tts kurulu ortam) ile çağırır:
  python engine/xtts.py <metin.json> <cikti.wav> <kelimeler.json>
metin.json: {"text": "...", "lang": "tr", "speaker_wav": "ref.wav" ya da wav klasörü (hepsi referans olur)}
Ortam: XTTS_MODEL_DIR = ince ayarlı model klasörü (model.pth, config.json, vocab.json); yoksa hazır XTTS-v2.
       XTTS_TEMPERATURE (varsayılan 0.6; düşük = daha sabit, tekdüze ses)
kelimeler.json: text.split() sırasıyla [{"w","start","end"}]
"""
import json, os, sys

os.environ.setdefault("COQUI_TOS_AGREED", "1")  # CPML: ticari olmayan kullanım

import torch, torchaudio

TR = str.maketrans({"ç": "c", "ş": "s", "ğ": "g", "ı": "i", "ö": "o", "ü": "u", "â": "a", "î": "i", "û": "u", "é": "e", "è": "e", "à": "a"})


def norm(w):
    """MMS_FA sözlüğü yalnız a-z ve kesme işareti bilir; Türkçe harfleri Latin'e indir."""
    w = w.replace("I", "ı").replace("İ", "i").lower().translate(TR)
    return "".join(c for c in w if "a" <= c <= "z")


def refs(path):
    if os.path.isdir(path):
        return sorted(os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".wav"))
    return path


def synth(text, lang, speaker_wav, out_wav):
    from TTS.api import TTS
    d = os.environ.get("XTTS_MODEL_DIR")
    tts = TTS(model_path=d, config_path=os.path.join(d, "config.json")) if d else TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.to("cuda" if torch.cuda.is_available() else "cpu")
    tts.tts_to_file(text=text, speaker_wav=refs(speaker_wav), language=lang, file_path=out_wav,
                    temperature=float(os.environ.get("XTTS_TEMPERATURE", "0.6")))


def align(wav_path, words):
    bundle = torchaudio.pipelines.MMS_FA
    model, tok, aligner = bundle.get_model(with_star=False), bundle.get_tokenizer(), bundle.get_aligner()
    wav, sr = torchaudio.load(wav_path)
    wav = torchaudio.functional.resample(wav.mean(0, keepdim=True), sr, bundle.sample_rate)
    keep = [i for i, w in enumerate(words) if norm(w)]  # rakam/işaret gibi okunmayan parçalar hizalanmaz
    with torch.inference_mode():
        em, _ = model(wav)
        spans = aligner(em[0], tok([norm(words[i]) for i in keep]))
    sec = wav.size(1) / em.size(1) / bundle.sample_rate
    t = {i: (s[0].start * sec, s[-1].end * sec) for i, s in zip(keep, spans)}
    out, last = [], 0.0
    for i, w in enumerate(words):
        a, b = t.get(i, (last, last))  # hizalanamayan kelime öncekinin sonuna sıfır süreyle yapışır
        out.append({"w": w, "start": round(a, 3), "end": round(b, 3)})
        last = b
    return out


if __name__ == "__main__":
    job, out_wav, out_words = sys.argv[1:4]
    j = json.load(open(job, encoding="utf-8"))
    synth(j["text"], j["lang"], j["speaker_wav"], out_wav)
    json.dump(align(out_wav, j["text"].split()), open(out_words, "w", encoding="utf-8"), ensure_ascii=False)

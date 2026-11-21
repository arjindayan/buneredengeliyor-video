"""XTTS-v2 ince ayarı, Colab'sız (Mac CPU ya da herhangi bir makine). Notebook ile aynı adımlar.

  python finetune/train_local.py <kayit_klasoru> <calisma_klasoru> [--epochs 6] [--prep-only]
kayit_klasoru: kayit-tr*.m4a/wav, kayit-en*.m4a/wav. Çıktı: <calisma_klasoru>/xtts-arjin (XTTS_MODEL_DIR olarak kullan).
Takılmalar: FT_SCRIPT=metin1.md,metin2.md verilirse yalnız okuma metnindeki bir (ya da art arda iki) satırla
  neredeyse birebir eşleşen parçalar tutulur ve metin olarak doğru yazımı kullanılır; yarım kalan/tekrarlanan okumalar elenir.
Devam eğitimi: FT_INIT=<önceki xtts-arjin/model.pth> (yoksa hazır XTTS-v2), FT_LANGS=tr (yalnız bu diller).
"""
import glob, os, re, shutil, subprocess, sys

os.environ.setdefault("COQUI_TOS_AGREED", "1")
import torch

SRC, WORK = sys.argv[1], sys.argv[2]
EPOCHS = int(sys.argv[sys.argv.index("--epochs") + 1]) if "--epochs" in sys.argv else 6
os.makedirs(WORK, exist_ok=True)


def wav(src, dst, a=None, b=None):
    cut = ["-ss", f"{a:.2f}", "-to", f"{b:.2f}"] if a is not None else []
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-v", "error", *cut, "-i", src, "-ac", "1", "-ar", "22050", dst], check=True)
    else:  # Mac'te ffmpeg yok: torchaudio ile kes
        import torchaudio
        x, sr = torchaudio.load(src)
        x = torchaudio.functional.resample(x.mean(0, keepdim=True), sr, 22050)
        if a is not None: x = x[:, int(a * 22050):int(b * 22050)]
        torchaudio.save(dst, x, 22050)


def norm(t):
    t = t.replace("I", "ı").replace("İ", "i").lower()
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def script_lines():
    out = []
    for f in filter(None, os.environ.get("FT_SCRIPT", "").split(",")):
        lines = [l.strip() for l in open(f, encoding="utf-8")]
        lines = [l for l in lines if l and not l.startswith(("#", "-", "`", "Kayıt", "Dosya", "Videoda"))]
        out += lines + [a + " " + b for a, b in zip(lines, lines[1:])]
    return {norm(l): l for l in out}


def match(text, ref, cut=0.9):
    import difflib
    if not ref: return text
    best = difflib.get_close_matches(norm(text), list(ref), n=1, cutoff=cut)
    return ref[best[0]] if best else None


def prep():
    import whisper
    asr = whisper.load_model(os.environ.get("WHISPER_MODEL", "turbo"))
    veri, ref, atilan = {}, script_lines(), 0
    for k in sorted(glob.glob(SRC + "/kayit-*")):
        lang = re.search(r"-(tr|en)", os.path.basename(k)).group(1)
        root = f"{WORK}/data-{lang}"; os.makedirs(root + "/wavs", exist_ok=True)
        full = f"{WORK}/{os.path.basename(k)}.wav"
        if not os.path.exists(full):
            if shutil.which("ffmpeg"): wav(k, full)
            else: subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@22050", "-c", "1", k, full], check=True)  # macOS
        import torchaudio
        x, sr = torchaudio.load(full)  # whisper'a dizi ver: kendi yükleyicisi ffmpeg istiyor
        x = torchaudio.functional.resample(x.mean(0), sr, 16000).numpy()
        r = asr.transcribe(x, language=lang, word_timestamps=True, condition_on_previous_text=False, fp16=False)
        words = [w for s in r["segments"] for w in s.get("words", [])]
        cur = []
        for w in words:  # cümle sonunda ya da 10 sn dolunca kes (XTTS en fazla ~11,6 sn alıyor)
            cur.append(w)
            dur = cur[-1]["end"] - cur[0]["start"]
            if (w["word"].strip()[-1:] in ".?!" and dur > 1.5) or dur > 10:
                text = "".join(x["word"] for x in cur).strip()
                a, b = max(0, cur[0]["start"] - 0.1), cur[-1]["end"] + 0.15
                text = match(text, ref) if lang == "tr" else text
                atilan += text is None
                if text and 1.5 <= b - a <= 11.5 and not re.search(r"\d", text):
                    i = f"{lang}_{len(veri.get(lang, [])):04d}"
                    wav(full, f"{root}/wavs/{i}.wav", a, b)
                    veri.setdefault(lang, []).append((i, text, b - a))
                cur = []
    print("metinle eşleşmediği için atılan parça:", atilan)
    for lang, rows in veri.items():
        with open(f"{WORK}/data-{lang}/metadata.csv", "w", encoding="utf-8") as f:
            f.writelines(f"{i}|{t}|{t}\n" for i, t, _ in rows)
        print(lang, len(rows), "parça,", round(sum(d for *_, d in rows) / 60, 1), "dk")
    return list(veri)


def base():
    b = f"{WORK}/base"; os.makedirs(b, exist_ok=True)
    from TTS.utils.manage import ModelManager
    hf = "https://huggingface.co/coqui/XTTS-v2/resolve/main/"
    need = [hf + n for n in ["model.pth", "config.json", "vocab.json", "dvae.pth", "mel_stats.pth", "speakers_xtts.pth"] if not os.path.exists(f"{b}/{n}")]
    if need: ModelManager._download_model_files(need, b, progress_bar=True)
    return b


def train(langs, B):
    from trainer import Trainer, TrainerArgs
    from TTS.config.shared_configs import BaseDatasetConfig
    from TTS.tts.configs.xtts_config import XttsAudioConfig
    from TTS.tts.datasets import load_tts_samples
    from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTArgs, GPTTrainer, GPTTrainerConfig
    out = f"{WORK}/run"
    ds = [BaseDatasetConfig(formatter="ljspeech", dataset_name=f"arjin-{l}", path=f"{WORK}/data-{l}", meta_file_train="metadata.csv", language=l) for l in langs]
    args = GPTArgs(max_conditioning_length=132300, min_conditioning_length=66150, max_wav_length=255995, max_text_length=200,
                   mel_norm_file=f"{B}/mel_stats.pth", dvae_checkpoint=f"{B}/dvae.pth", xtts_checkpoint=os.environ.get("FT_INIT", f"{B}/model.pth"), tokenizer_file=f"{B}/vocab.json",
                   gpt_num_audio_tokens=1026, gpt_start_audio_token=1024, gpt_stop_audio_token=1025,
                   gpt_use_masking_gt_prompt_approach=True, gpt_use_perceiver_resampler=True)
    bs = int(os.environ.get("BATCH", "2"))
    config = GPTTrainerConfig(
        output_path=out, model_args=args, datasets=ds, run_name="xtts-arjin", project_name="xtts", dashboard_logger="tensorboard",
        audio=XttsAudioConfig(sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000),
        epochs=EPOCHS, batch_size=bs, eval_batch_size=bs, batch_group_size=48, num_loader_workers=0,
        eval_split_max_size=256, eval_split_size=0.05, print_step=5, plot_step=100, log_model_step=1000,
        save_step=100000, save_n_checkpoints=1, save_checkpoints=True, save_best_after=0, print_eval=False,
        optimizer="AdamW", optimizer_wd_only_on_weights=True, optimizer_params={"betas": [0.9, 0.96], "eps": 1e-8, "weight_decay": 1e-2},
        lr=5e-6, lr_scheduler="MultiStepLR", lr_scheduler_params={"milestones": [900000], "gamma": 0.5, "last_epoch": -1}, test_sentences=[])
    model = GPTTrainer(config)
    tr, ev = load_tts_samples(config, eval_split=True, eval_split_max_size=256, eval_split_size=0.05)
    print(len(tr), "eğitim,", len(ev), "değerlendirme")
    Trainer(TrainerArgs(restore_path=None, skip_train_epoch=False, start_with_eval=False, grad_accum_steps=1),
            config, output_path=out, model=model, train_samples=tr, eval_samples=ev).fit()
    return out


def package(out, B, langs):
    ck = sorted(glob.glob(f"{out}/*/best_model*.pth") or glob.glob(f"{out}/*/checkpoint_*.pth"), key=os.path.getmtime)[-1]
    print("kullanılan:", ck)
    sd = torch.load(ck, map_location="cpu", weights_only=False)["model"]
    sd = {k: v for k, v in sd.items() if "dvae" not in k and "torch_mel_spectrogram" not in k}
    pkg = f"{WORK}/xtts-arjin"; os.makedirs(pkg + "/refs", exist_ok=True)
    torch.save({"model": sd}, f"{pkg}/model.pth")
    for n in ["config.json", "vocab.json", "speakers_xtts.pth"]: shutil.copy(f"{B}/{n}", pkg)
    l0 = "tr" if "tr" in langs else langs[0]
    for f in sorted(glob.glob(f"{WORK}/data-{l0}/wavs/*.wav"), key=os.path.getsize)[-6:]: shutil.copy(f, pkg + "/refs")
    print("hazır:", pkg)


if __name__ == "__main__":
    langs = [l for l in ("tr", "en") if os.path.exists(f"{WORK}/data-{l}/metadata.csv")] or prep()
    langs = [l for l in langs if l in os.environ.get("FT_LANGS", "tr,en").split(",")]
    if "--prep-only" in sys.argv: sys.exit()
    B = base()
    package(train(langs, B), B, langs)

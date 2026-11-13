#!/bin/bash
# Render sonrası: kod üretimi sakin fon müziği (-26 dB) + beğen/takip kartı.
# kullanım: engine/bitir.sh <tr|en> topics/<konu>  → topics/<konu>/out/final_cta.mp4
set -e; dil=$1; d=$2; E=$(dirname "$0")
v=$d/out/video.mp4; T=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")
python3 "$E/bgpad.py" "$T" "$d/out/pad.wav"
ffmpeg -y -v error -i "$v" -i "$d/out/pad.wav" -filter_complex "[1:a]volume=-26dB[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k "$d/out/final.mp4"
bash "$E/cta.sh" "$dil" "$d/out/final.mp4" "$d/out/final_cta.mp4"

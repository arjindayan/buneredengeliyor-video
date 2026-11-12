#!/bin/bash
# Her videonun sonuna 3 sn "beğen + takip et" kapanışı ekler (varsayılan, 2026-11-12 Arjin'in isteği).
# kullanım: engine/cta.sh <tr|en> <girdi.mp4> <çıktı.mp4>
set -e; dil=$1; in=$2; out=$3; D=3
kart=$(mktemp --suffix=.png)
node -e "
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto('file://$(cd "$(dirname "$0")" && pwd)/cta.html?dil=$dil'); await p.evaluate(() => document.fonts.ready);
await p.screenshot({ path: '$kart', omitBackground: true }); await b.close(); })();"
T=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
# son kare 3 sn uzar, uzayan kısım bulanıklaşıp kararır, kart yumuşakça belirir; ses sessizlikle uzar
ffmpeg -y -v error -i "$in" -loop 1 -i "$kart" -filter_complex "
[0:v]tpad=stop_mode=clone:stop_duration=$D,split[a][b];
[b]trim=start=$T,setpts=PTS-STARTPTS,boxblur=20:2,eq=brightness=-0.15,fade=in:st=0:d=0.4[bl];
[a]trim=end=$T,setpts=PTS-STARTPTS[ana];
[ana][bl]concat=n=2:v=1:a=0[v0];
[1:v]format=rgba,fade=in:st=$T:d=0.4:alpha=1[k];
[v0][k]overlay=shortest=1:enable='gte(t,$T)'[v]" -map "[v]" -map 0:a -af "apad=pad_dur=$D" \
  -t $(python3 -c "print($T+$D)") -c:v libx264 -pix_fmt yuv420p -crf 16 -preset slow -profile:v high -movflags +faststart -c:a aac -b:a 192k "$out"
rm -f "$kart"

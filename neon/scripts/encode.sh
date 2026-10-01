#!/bin/bash
# encode the neon full film: silent masters + versions with the song from the user's edit
set -e
D=/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad
O=${1:-$D/full/enc}
mkdir -p $O
A=$D/music/user_edit.mp4
X="-c:v libx264 -preset slow -tune animation -pix_fmt yuv420p -profile:v high -g 120 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart"
# light temporal denoise removes the per-frame film grain (bitrate hog) but keeps every line
ffmpeg -y -loglevel error -framerate 60 -i $D/full/out/n%04d.jpg -vf hqdn3d=1.5:1.5:6:6 $X -crf ${CRF1080:-27} $O/neon_1080p60.mp4
ffmpeg -y -loglevel error -framerate 60 -i $D/full/out/n%04d.jpg -vf hqdn3d=1.5:1.5:6:6,scale=1280:720:flags=lanczos $X -crf ${CRF720:-26} $O/neon_720p60.mp4
for r in 1080p60 720p60; do
  ffmpeg -y -loglevel error -i $O/neon_$r.mp4 -i $A -map 0:v -map 1:a -c:v copy -c:a copy -shortest $O/neon_${r}_music.mp4
done
ls -la $O

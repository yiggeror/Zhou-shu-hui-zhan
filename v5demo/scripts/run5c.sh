#!/bin/bash
cd /tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad/v5
rm -rf frames frames_rigid frames60 log_*.json logr_*.json
U="42 43 44 45 46 47 48 49 50 72 73 74 75 76 77 78 79 92 93 94 95 96 97 98 99 100 101 102 103 104"
for k in 0 1 2 3; do CVT=1 python3 crisp5.py $k 4 $U > c5_$k.log 2>&1 & done; wait
grep -l Traceback c5_*.log && { echo "crisp failed"; exit 1; }
python3 display.py
RIGID=1 CVT=4 python3 crisp5.py 0 1 > c5r.log 2>&1
echo "per-drawing frames done $(date +%T)"
for k in 0 1 2 3; do CVT=1 python3 crisp60.py $k 4 > c60_$k.log 2>&1 & done; wait
grep -l Traceback c60_*.log && { echo "crisp60 failed"; exit 1; }
echo "60fps base done $(date +%T) $(ls frames60 | wc -l)"
rm -rf out cmp
CVT=4 python3 fx5.py > fx5.log 2>&1 || { echo "fx5 failed"; exit 1; }
ffmpeg -y -loglevel error -framerate 60 -i out/f%04d.jpg -c:v libx264 -preset slow -tune animation -crf 18 -pix_fmt yuv420p -movflags +faststart demo_v5_1080p60.mp4
ffmpeg -y -loglevel error -framerate 60 -i out/f%04d.jpg -c:v libx264 -preset slow -tune animation -crf 22 -pix_fmt yuv420p -movflags +faststart demo_v5_send.mp4
ffmpeg -y -loglevel error -framerate 60 -i cmp/f%04d.jpg -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -movflags +faststart compare_v5_1080p60.mp4
echo "all done $(date +%T)"

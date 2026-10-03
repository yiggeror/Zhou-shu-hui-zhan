#!/bin/bash
# concat the chunk segments of one version, encode the 1080p master + a 720p preview,
# split the master into <95 MB parts (keyframe cuts, verified bit-exact) for the repo
# usage: finish.sh A|B
set -e
M=$1
D=/tmp/claude-0/-home-user-Zhou-shu-hui-zhan/6c60e79b-2db7-5a10-9eaf-a9e7833aa924/scratchpad/full2
R=/home/user/Zhou-shu-hui-zhan
cd $D/seg6$M
N=$(python3 -c "import json;print(len(json.load(open('plan.json'))['chunks']))")
: > list.txt
for i in $(seq 0 $((N-1))); do f=$(printf "c%03d.mp4" $i); [ -f $f ] || { echo "missing $f"; exit 1; }; echo "file '$f'" >> list.txt; done
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy joined.mp4
NAME=$([ $M = A ] && echo remake_redrawn_vfx || echo original_vfx_enhanced)
X="-c:v libx264 -preset slow -tune animation -pix_fmt yuv420p -profile:v high -g 120 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart"
ffmpeg -y -loglevel error -i joined.mp4 $X -crf 18 $D/${NAME}_1080p60.mp4
# preview under 30 MB for direct sending
ffmpeg -y -loglevel error -i joined.mp4 -vf scale=1280:720:flags=lanczos -c:v libx264 -preset slow -b:v 2300k -pass 1 -passlogfile pp$M -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i joined.mp4 -vf scale=1280:720:flags=lanczos -c:v libx264 -preset slow -b:v 2300k -pass 2 -passlogfile pp$M -pix_fmt yuv420p -movflags +faststart $D/${NAME}_preview.mp4
rm -f pp$M* joined.mp4
mkdir -p $R/final; rm -rf $R/final/$NAME
python3 $R/pipeline/split.py $D/${NAME}_1080p60.mp4 $R/final/$NAME ${NAME}_1080p60 92 || true
ls -la $D/${NAME}_*.mp4 $R/final/$NAME 2>/dev/null
echo "finish $M ok"

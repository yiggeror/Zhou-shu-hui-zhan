# join check: redraw_74frames_24fps_once.mp4

inputs (ffmpeg -f concat -c copy, in this order):
- $OUT/video_inputs/shot58.mp4: 19 frames, sha256 1503cb9e544f0bf4a104c8e86255768ed18c182e58324d6cc969074dd1f383de
- $OUT/video_inputs/shot59.mp4: 17 frames, sha256 ccbafd7ca4199b73592d11e6048fa54157c60151c7d33c83085126db39764143
- $OUT/video_inputs/shot60.mp4: 19 frames, sha256 b8a968246aee8d5c88df7cfdbffb7d04d956e2c3c5a4768aff73eee42ca513a6
- $OUT/video_inputs/shot61.mp4: 19 frames, sha256 7d8a403e52e711dac8d8c01e2d1ab92b81794bc83e3bcbb25614abcf8c2f9fe5

SPS / PPS md5 (12 hex): shot58_baseline.mp4 ['8a04d60ec789']/['3dc8b5730893']; shot59_baseline.mp4 ['8a04d60ec789']/['3dc8b5730893']; shot60_selected_endpoint_satsurf.mp4 ['8a04d60ec789']/['3dc8b5730893']; shot61_baseline.mp4 ['8a04d60ec789']/['3dc8b5730893']; redraw_74frames_24fps_once.mp4 ['8a04d60ec789']/['3dc8b5730893'] -> IDENTICAL
decoded RGB per-frame md5: concatenated inputs (74) == joined (74): IDENTICAL
PTS: 74 frames, first 0.000000 s, last 3.041667 s, every step 1/24: True
stream: width=1672|height=942|pix_fmt=yuv420p|r_frame_rate=24/1|duration=3.083333|nb_read_frames=74
output sha256 a3a00cc922125efc203bc03c60a7f895c2932eea8b878f431518b22f20a884e1

RESULT: PASS

# join check: redraw_372frames_24fps_once.mp4

inputs (ffmpeg -f concat -c copy, in this order):
- collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4: 298 frames, sha256 d0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853
- $PKG/redraw_74frames_24fps_once.mp4: 74 frames, sha256 a3a00cc922125efc203bc03c60a7f895c2932eea8b878f431518b22f20a884e1

SPS / PPS md5 (12 hex): redraw_298frames_24fps_once.mp4 ['8a04d60ec789']/['3dc8b5730893']; redraw_74frames_24fps_once.mp4 ['8a04d60ec789']/['3dc8b5730893']; redraw_372frames_24fps_once.mp4 ['8a04d60ec789']/['3dc8b5730893'] -> IDENTICAL
decoded RGB per-frame md5: concatenated inputs (372) == joined (372): IDENTICAL
PTS: 372 frames, first 0.000000 s, last 15.458333 s, every step 1/24: True
stream: width=1672|height=942|pix_fmt=yuv420p|r_frame_rate=24/1|duration=15.500000|nb_read_frames=372
output sha256 5d81b3a4a60d36a9be29a6293c5b8848d4a15aa0bc7eb600c6dd482bd287ac9a

RESULT: PASS

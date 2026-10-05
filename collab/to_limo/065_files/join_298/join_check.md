# 298-frame join check [1187,1485) (PROVISIONAL: B2 and R4 replaced from approved material)

inputs (ffmpeg -f concat -c copy):
- frozen 224: collab/to_limo/061_files/join_224/redraw_224frames_24fps_once.mp4 sha256 87a03a42e525fbfbe7f306f43c3e1d7b06f392676ba3f46886d78040f77fb0e7
- C2 74: ../batchC2_1411_1485/redraw_24fps_once.mp4 sha256 1e8a76f6c6c894871399007dc4db6c61212fd40817477729cd1283c1d4fe7e5b

SPS / PPS md5: all three streams 8a04d60ec789 / 3dc8b5730893

decoded RGB per-frame md5: cat(224, 74) == joined 298: IDENTICAL (lists in this folder)

PTS: 298 frames, 0 ... 12.375 s (297/24), every step 1/24

redraw_298frames_24fps_once.mp4 sha256 d0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853
stream: width=1672|height=942|pix_fmt=yuv420p|r_frame_rate=24/1|duration=12.416667|nb_read_frames=298

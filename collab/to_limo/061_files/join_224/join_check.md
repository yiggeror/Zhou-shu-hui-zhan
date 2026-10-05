# 224-frame join check [1187,1411) (PROVISIONAL: U4/V6 held)

inputs (ffmpeg -f concat -c copy):
- frozen 170: collab/to_limo/059_files/join_170/redraw_170frames_24fps_once.mp4 sha256 befbd40d1049b91bc65d39ae197d8bbcffb6654cf7890f8996f94e665b3954ea
- C1 54: ../batchC1_1357_1411/redraw_24fps_once.mp4 sha256 23e5b601d39bbd367145ddc53880182153c4b819e8cb0d57948215e5f4bc3484

SPS / PPS md5: both 8a04d60ec789 / 3dc8b5730893

decoded RGB per-frame md5: cat(170, 54) == joined 224: IDENTICAL

redraw_224frames_24fps_once.mp4 sha256 87a03a42e525fbfbe7f306f43c3e1d7b06f392676ba3f46886d78040f77fb0e7
stream: width=1672|height=942|pix_fmt=yuv420p|r_frame_rate=24/1|duration=9.333333|nb_read_frames=224

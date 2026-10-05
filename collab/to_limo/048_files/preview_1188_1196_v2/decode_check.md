# decode check of the v2 videos (native PNGs unchanged: identical to 047_files/preview_1188_1196/frames)

encoder: libx264 CRF 16 slow yuv420p, -sws_flags accurate_rnd+full_chroma_int

redraw_24fps_once.mp4 sha256 281fc2748fe53306665ec43f850818ce40ba52411df215716659803a90165ca8
stream: width=1672|height=942|pix_fmt=yuv420p|r_frame_rate=24/1|duration=0.333333|nb_read_frames=8
pts: 0.000000, 0.041667 0.083333 0.125000 0.166667 0.208333 0.250000 0.291667 

| n | decoded RGB values (white frames) | mean abs video - native PNG (8-bit levels, float64) | share all channels >= 250: native PNG / decoded video |
|---|---|---|---|
| 1188 | - | 2.29 | 2.72% / 2.41% |
| 1189 | - | 1.77 | 24.32% / 23.39% |
| 1190 | [[255, 255, 255]] | 0.00 | 100.00% / 100.00% |
| 1191 | [[255, 255, 255]] | 0.00 | 100.00% / 100.00% |
| 1192 | - | 1.03 | 59.73% / 41.34% |
| 1193 | - | 1.26 | 35.80% / 29.95% |
| 1194 | - | 1.93 | 9.36% / 8.87% |
| 1195 | - | 1.95 | 9.36% / 8.84% |

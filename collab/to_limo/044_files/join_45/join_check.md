# 45-frame join check

inputs: frozen v6 = deliveries/method_sample_1248_1284/重绘_原速单次_1.5秒.mp4 (md5 a4f12f509b9e3c253103097103bef38e); new 9 = composite_shot45_v3/redraw_24fps_once_new_frames_only.mp4 (md5 b5d5bac954f284e6475995484d209592)

command: ffmpeg -f concat -safe 0 -i list.txt -c copy -movflags +faststart  (stream copy, no re-encode)

SPS / PPS (Annex B NAL payload md5, first 12 hex): v6 SPS 8a04d60ec789, PPS 3dc8b5730893; new SPS 8a04d60ec789, PPS 3dc8b5730893 (identical)

stream: codec_name=h264|profile=High|width=1672|height=942|pix_fmt=yuv420p|level=40|r_frame_rate=24/1|duration=1.875000|nb_read_frames=45

decoded RGB (rgb24) per-frame md5: cat(v6 36, new 9) == joined 45: IDENTICAL

pts (s, frame type):
0.000000,I, 0.041667,I 0.083333,P 0.125000,P 0.166667,B 0.208333,P 0.250000,P 0.291667,I 0.333333,B 0.375000,P 0.416667,I 0.458333,P 0.500000,P 0.541667,P 0.583333,P 0.625000,P 0.666667,I 0.708333,P 0.750000,P 0.791667,P 0.833333,P 0.875000,P 0.916667,P 0.958333,P 1.000000,P 1.041667,P 1.083333,P 1.125000,P 1.166667,I 1.208333,B 1.250000,B 1.291667,P 1.333333,P 1.375000,P 1.416667,P 1.458333,P 1.500000,I, 1.541667,I 1.583333,P 1.625000,P 1.666667,B 1.708333,B 1.750000,B 1.791667,P 1.833333,P 

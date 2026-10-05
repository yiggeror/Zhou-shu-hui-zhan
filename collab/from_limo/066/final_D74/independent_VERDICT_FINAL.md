# D photography and 372-frame continuation: final independent verdict

PASS WITH DISCLOSED RESIDUALS. The final selected D74 and the stream-copied 372-frame continuation pass the independent technical and ordered-frame visual review below.

## Independent evidence

- 34 unique selected AI-generated original PNGs were checked against their recorded SHA-256 and Git-blob hashes. The photography copies are the same bytes, including selected retry choices.
- Every source reference PNG matches the RGB pixels decoded independently from the original AV1 at its assigned zero-based frame index. This includes the separate S06b source at n1532.
- The exposure table covers [1485,1559) exactly once: 74 frames, 34 drawing states and 40 repeated exposures. No n1559 is included.
- Native drawings are 1672 × 941 except D_D02, 1671 × 941. Its missing right column is replicated before the existing fixed similarity registration. It is not stretched to fill the width.
- The 17 photography snapshot files match their recorded hashes. The pixel-producing core matches the existing 73ff baseline; the 08562d6 changes add manifest CLI and grading-endpoint controls rather than replacing that core.
- Actual completed videos for shots 58, 59, 60 and 61 decode without errors. Their frame counts are 19, 17, 19 and 19, with 1672 × 942 coded size, 24 fps and exact rational PTS. All baseline holds repeat exactly at native RGB-pixel level.
- The baseline D74 assembly independently decodes to precisely the concatenation of those four completed baseline shots: 74 frames, 3.083333 seconds. It is a comparison candidate, not the recommended final selection.
- The original frozen 298-frame file has SHA-256 d0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853.

## Visual and method findings

Review used actual full-resolution frames and ordered source/output contacts, plus independent full-video decoding. This was not real-time video playback, and no original-speed playback assessment is claimed.

City depth, the major changing foreground occlusions and the final approach are preserved. The cyan eye is already faintly present at n1504, partial at n1506 and a distinct ring at n1507; the hand enters at n1508, reaches near the face at n1510 and settles at n1512. The blue band is legible. The separate S06 and S06b drawings preserve a real source-anchored step in red illumination. The approach into the red eye, the succeeding hand/face smear, and all four shot seams remain coherent. At n1548 the black onset is visible; n1552 retains the small rim/sky remnant, n1553 removes the rim while sky remains, and n1554 removes the background while leaving face, hand and red eyes readable.

The selected configuration uses complete full-drawing holds, no moving camera, zoom 1 and fixed light. Existing small static similarity registration is applied per hold. There is no body-local warp, optical-flow animation, source-RGB effect paste, synthetic flat-black frame, or fake whole-frame camera motion in the active configuration. Global source-led luminance curves and bounded white balance operate on the drawn artwork.

## Grading choice

Verified final selection: shot58 baseline, shot59 baseline, shot60 endpoint_satsurf, shot61 baseline.

The G06 endpoint-only test visibly raises face/hand luminance at n1516 and n1520 too much. Retain its fixed nine-frame quiet hold. Its late source viewpoint and band movement remain deliberately approximated; this is not nine new drawings.

The targeted shot60 comparison reduces some ordinary-surface highlight protection and gives S06/S06b a useful source-led increase in red light. The genuine red eyes and top band remain readable. Its 19-frame video separately passes decode/count/PTS checks; native frames outside n1525–1536 are byte-identical to baseline.

## Remaining ordinary residuals

- C06/C07 and S08/S09 retain firmer ink contours than the source motion blur. Their overall approach/smear direction remains clear in ordered frame inspection.
- Some S04–S06b skin/clothing is still a little brighter or warmer than the source. Saturation limiting is an imperfect surface/emission proxy; it is not a semantic light mask.
- Holds intentionally omit some original intra-shot drift and secondary changes. The nine-frame G06 hold is the longest and most visible example.

The selected D74 passes: 74 frames, 1672 × 942 coded size, 24 fps, 3.083333 seconds, exact PTS and error-free full decode. Every decoded RGB frame is identical to the selected shot-video concatenation. Its SHA-256 is a3a00cc922125efc203bc03c60a7f895c2932eea8b878f431518b22f20a884e1. All 74 native frame files match the selected run bytes, and the chosen master configuration correctly keeps G06 fixed while applying only the targeted S-state grading changes.

No blocking error has been found. The final continuation passes the checks below.


## 372-frame continuation verification

- Exact timeline: [1187,1559), 372 frames, 24 fps, 15.5 seconds.
- Coded image: 1672 × 942, H.264/yuv420p. Native artwork remains 1672 × 941; the encoder repeats one bottom row.
- Every frame fully decodes without error, with PTS exactly 0, 1/24, 2/24, …, 371/24.
- All first 298 decoded RGB frames equal the frozen original master. Its input file remained byte-identical before and after joining.
- All last 74 decoded RGB frames equal the approved new D74.
- SPS/PPS are identical across both inputs and the joined file. Independently extracted encoded H.264 picture-slice payloads are also exactly the old 298 plus new 74 in order. Neither portion was reencoded.
- The 34 unique source-anchored artwork states yield 74 exposures. Two graded holds vary light while repeating the drawing, producing 41 distinct native photographed RGB outputs. This does not increase the artwork count.

Final continuation SHA-256: 5d81b3a4a60d36a9be29a6293c5b8848d4a15aa0bc7eb600c6dd482bd287ac9a

New D74 SHA-256: a3a00cc922125efc203bc03c60a7f895c2932eea8b878f431518b22f20a884e1

No next-shot n1559, placeholder, repeated old-story test extension, or compressed preview was used as a production input.

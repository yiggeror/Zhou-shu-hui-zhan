# D photography selection

All candidates use the same 34 producer-selected original PNG byte streams and the locked 74 exposures [1485,1559), at 24 fps. No new art, replacement source imagery, per-body warp, optical-flow interpolation, camera animation or flat black field is introduced. Full-mode fixed holds use the existing single source registration, camera_only:none, zoom:1 and light:fixed.

## Selected runs

- [1485,1504): shot58_baseline
- [1504,1521): shot59_baseline
- [1521,1540): shot60_endpoint_satsurf
- [1540,1559): shot61_baseline

The final master sheet is D34_selected.json and the matching selected-art manifest is manifest_D34_selected.json. The final full sheet does not inherit unused G grading keys from the shot60 experimental sheet. Only the IDs actually inside that run affected its pixels.

## Grade settings

Existing luminance-distribution curve, strength1, sigma4; bounded global white balance ±10%; white neutrality protection0.85–0.97; bright-channel highlight protection0.7–0.9. Baseline holds fit at their own source frame. G06 remains grade_at[1512,1512]. S06 uses [1528,1531]; S06b uses [1532,1536]. Existing keep_sat[0.35,0.6] is selected only on S04, S05, S06 and S06b. It limits bright-channel protection to saturated pixels; this is a proxy, not an inferred semantic emission mask. No new pixel processing was added to the core.

## G06: endpoint alternative rejected

Actual nine-frame G06_endpoint was rendered and verified. The source is not monotonically brighter: grayscale mean42.59 at1512,38.40 at1516,53.59 at1520. A simple endpoint ramp gives43.21,49.51,55.84 and visibly over-lifts the held face/hand during the middle. Fixed baseline stays43.21. Across the hold, full-frame mean absolute luma error is3.94 fixed vs4.87 endpoint. Both preserve eye maximum255 and the same sampled bright-cyan count3418. Ordered source/output contact inspection, including independent review, favors the fixed baseline. The baseline deliberately omits small body/viewpoint drift and later band/background motion. Actual source color/flare progression is not claimed to be fully reproduced by the hold.

## S06/S06b: endpoint plus saturation-limited protection selected

Actual shot60_endpoint_satsurf was rendered and verified against baseline. It makes the n1531→1532 progression closer in direction and magnitude:

- Source full-frame grayscale mean46.64→50.36; baseline50.83→50.74; selected48.17→50.71.
- Source mean red/green1.724→1.826; baseline1.507→1.899; selected1.704→1.893.

At1536, source mean67.35; baseline50.74; selected67.01. Source top10%-height red mean140.81, selected93.52, so the stronger source top flare is still not fully reproduced. The bounded white balance is not an arbitrary red-light generator. The actual n1532 drawing supplies the later red/light/viewpoint phase.

S04–S06b full-frame luma MAE over1525–1536 falls3.82→2.11, but this is not the selection criterion on its own. The source-led color direction, retained red eyes and ordered visual comparisons support selection. Red eye peaks remain255 in the sampled region; white surface/rim highlights are allowed to grade rather than being classified as emission. Some near-white rim pixels move below240, notably in S04. These are not claimed pixel-invariant. The actual red eye/top-band structures remain visibly readable. Surface skin remains locally warmer/brighter, particularly late S06b; the sampled forehead MAE changes7.83→8.57. Do not call this a perfect photometric match or uniformly dim it to optimize a mean.

## Geometry and canvas

All selected art is opaque RGB.33 originals are1672×941. D_D02 is1671×941 and its original bytes are preserved; the existing loader copies one RIGHT edge column (adjacent-edge steps left0.85/right0.49 levels), with no resize/stretch. It then undergoes its one fixed source registration (scale1.0010, centre shift+0.6/−1.0px); therefore final rightmost columns need not remain equal after registration. Source logs retain exact registration and edge-fill records. Main videos are1672×942; the encoder repeats the last native row once.

## Remaining visual approximations

Discrete holds sample city parallax, modest view drift, hand/eye progression and black expansion. C06/C07 trouser/forearm contours and S08/S09 some ink edges are cleaner/harder than the source blur; no unsupported anatomy is added during photography. P3 darkening begins1548;1552 residual sky,1553 final sky sliver and rim extinction,1554 black background with structured person, and1557 later crop remain explicit drawing states. No D frame is full black. G06 stays a nine-frame drawing hold, S06 four and S06b five; these are not new poses per exposure.

Visual review here and by the independent reviewer used actual decoded frame sequences, contact sheets and comparisons. It is not described as real-time audiovisual playback. Frame timing and decode continuity are separately verified on the actual videos. The root coordinator owns final approval and delivery.

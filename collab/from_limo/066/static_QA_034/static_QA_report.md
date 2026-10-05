# D34 independent static QA

## Unified verdict

CONDITIONAL STATIC PASS for all 34 selected drawings. No consolidated material redraw request is warranted from the static review. This is image-only acceptance for photography, not certification of the final animation, temporal grading, encoding or frozen-master join.

The 34 states cover exactly 74 exposures, [1485,1559), at 24 fps, with 40 repeated exposures. P1 contributes 14 states/36 exposures; P2 10/19; P3 10/19. The authoritative D34 table is commit 245690f0195eba4c7dce168b618fb2d96da65b03. S06 is [1528,1532); S06b uses actual source n1532 over [1532,1537). G06 remains an intentional nine-frame quiet hold.

## Integrity and accounting

- Original video SHA256 rechecked: 9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447.
- All 34 original-source PNGs are 2560×1440 and match both the source cache manifest and corresponding final producer manifest hashes.
- All 34 selected PNGs decode as opaque RGB, have unique file hashes, and match their final producer SHA256 and locally recomputed Git blob SHA1. Final hashes equal the actual files visually reviewed.
- 33 selections are native 1672×941. D_D02 is native 1671×941 and needs a single compositor edge column, without nonuniform resizing or altering the retained selected PNG.
- 41 recorded image-generation calls, 41 complete locally saved prompt TXT files, 34 selected outputs and 7 retained rejected candidates reconcile: P1 16/14/2, P2 13/10/3, P3 12/10/2 (calls/selections/rejects). All producers report zero moderation failures. This audit checks saved records and candidates; it is not an independent service-log audit.
- Prompt storage was reconciled after the producer restored two rejected P1 first-call prompts into the prompts directory: there are now 41 public-safe TXT files across producer prompts directories, one per call, including 34 selected prompts. Two byte-identical private copies are retained with P1 candidates and are not counted as extra calls/prompts. All 41 public-safe prompt hashes are listed in prompt_integrity_41.csv; rejected images and raw tool logs remain excluded.
- Source and selected SHA256/Git blob values, selected prompt SHA256, call numbers, dimensions and per-state findings are in state_integrity.csv and state_findings.json. The exact 74-row exposure expansion is in exposure_audit_74.csv.
- Git blob hashes certify content identity locally; this review does not claim the selected files have been uploaded or published.

## Static visual findings

All actual source/output pairs were inspected. Composition, source-specific perspective, intentional crops, character identity and meaningful hand anatomy remain consistent. There is no evidence of a fixed-body chain being substituted for changed views. Source blur/occlusion remains intentional; drawn smear is not treated as a defect merely because it is dark or soft.

Verified event order:
- n1504 already has cyan iris; n1506 partially opens; n1507 reveals the ring; n1508 introduces the lower-edge hand and weak blue streak; n1510 has the hand near chin and a clear cyan band; n1512 settles.
- n1523 introduces lower red eye/top streak; n1525 opens the main lid before the iris clearly emerges at n1526. n1532 supplies its own later red light/viewpoint, and n1537–1539 remain distinct side-view blur/push states.
- n1540 is the dark frontal hand-obscured smear; n1542 assembles hands; n1543 first shows sharp joined fingertips; n1544 reveals the clear grin.
- Black expansion starts at n1548. n1552 retains small sky and tiny fingertip/knuckle highlights. n1553 extinguishes bright rim while retaining a small sky sliver. n1554 first blacks the background while keeping the person structured and visible. n1557 is a genuinely farther viewpoint.

## Conditions carried into photography

1. Ordinary skin, hair and clothing remain non-emissive and gradeable. P1 closeups, P2 S04–S06, and P3 D05/D06 have brighter ordinary surfaces. Preserve real cyan/red eye cores and actual top streaks selectively; do not blanket-protect every bright or saturated skin pixel.
2. P2 S06b has enhanced red surface wash and top flare. Inspect n1531→n1532 and the five-frame endpoint at 24 fps for a perceptual step. Do not import later red light before n1532, and do not force source mean brightness mechanically.
3. C06/C07 retain cleaner cel contours than their soft sources. S09 has somewhat firmer black contours; F01 interprets source blur as directional ink smear. Assess these one- or two-exposure focus transitions at actual speed. Do not reconstruct sharp hidden anatomy or substitute body warping.
4. Preserve exact eye/hand/darkness event boundaries. Keep tiny n1552 highlights, turn rim off only at n1553, and remove the last sky only at n1554 without replacing the person with black.
5. G06’s nine-frame quiet hold, the split S06/S06b light/view holds, city composition holds, and sampled darkening/pullback are declared limited-animation approximations. They are not new poses on every exposure or claims of full in-between reproduction.
6. Compositor padding may extend one D_D02 edge column to 1672×941 and pad a bottom row for 1672×942 video. Do not label this native 1080p or nonuniformly resize artwork.

Frozen prior material was not edited or processed by this static review. Prior closed C1/C2 states were not reopened. The next shot beginning n1559 is outside D34. Final 74-frame photography/playback verification and frozen-298 join integrity remain separate pending work.

## Per-state verdicts

### D_C01 · source n1485 · [1485,1486)

Conditional pass. City composition, left occluder, airborne figure and existing small debris retain the source layout.

Residual: Warmer, clearer clouds; distant character and building motion remain limited-animation samples.

### D_C02 · source n1486 · [1486,1489)

Conditional pass. Large foreground debris cluster appears with the actual changed city composition and intact fighter.

Residual: Three-frame discrete debris hold intentionally omits intermediate trajectories.

### D_C03 · source n1489 · [1489,1493)

Conditional pass. Transit tower arrangement and figure screen position match the actual source view.

Residual: Slightly sharper debris/building edges; four-frame viewpoint sample omits drift.

### D_C04 · source n1493 · [1493,1497)

Conditional pass. Dominant near tower has moved behind the fighter; relative occlusion and airborne silhouette are preserved.

Residual: Four-frame held composition; background details are stylistic redraws.

### D_C05 · source n1497 · [1497,1501)

Conditional pass. Passed-left tower and final small-figure view are preserved before the approach.

Residual: Warmer red cloud/building light; ordinary surfaces remain eligible for source-led grading.

### D_C06 · source n1501 · [1501,1502)

Conditional pass. The actual larger full-body approach view is retained, distinct from city holds and the following tighter view.

Residual: Figure contours are cleaner and shadows cooler than the soft warm source; verify the single-frame focus/color transition in photography without invented geometry.

### D_C07 · source n1502 · [1502,1503)

Conditional pass. Closer cool approach crop and directional edge smear remain distinct from n1501 and n1503.

Residual: Some cel contours are crisper than the source blur; no new anatomy is required and no static redraw request is warranted before playback review.

### D_C08 · source n1503 · [1503,1504)

Conditional pass. Large face/torso crop and genuine directional smear are retained; this is not a clean figure with decorative speed lines.

Residual: Smear distribution is a drawn interpretation; inspect the one-frame approach transition in sequence.

### D_G01 · source n1504 · [1504,1506)

Conditional pass. Half-lidded cyan iris already exists at n1504; hand stays below the frame.

Residual: Ordinary face/hair surfaces are brighter and cooler; protect eye core selectively during grading.

### D_G02 · source n1506 · [1506,1507)

Conditional pass. Partially opened luminous iris remains clipped by the upper lid; hand is absent.

Residual: Drawn eyelid and iris microshape differ slightly; preserve distinct eye-opening exposure.

### D_G03 · source n1507 · [1507,1508)

Conditional pass. Readable cyan-white ring appears at n1507 with upper-lid clipping and no premature hand entry.

Residual: Minor iris texture differences are acceptable; avoid suppressing the white core to match global mean.

### D_G04 · source n1508 · [1508,1510)

Conditional pass. First rising hand is present only at the lower edge at n1508, with open white-cyan iris and source-specific face crop.

Residual: The early top blue streak is faint; preserve its weak onset rather than importing the strong later band. Ordinary face/hair surfaces are brighter and should remain gradeable.

### D_G05 · source n1510 · [1510,1512)

Conditional pass. Actual extended fingers approach the chin at n1510; the upper cyan band is now clearly visible and the eye core remains white-cyan.

Residual: Ordinary face, arm and hand shading is brighter. Keep those surfaces separate from eye/streak effect protection.

### D_G06 · source n1512 · [1512,1521)

Conditional pass. Settled sign near the cheek, open cyan eye, quiet smile and actual n1512 crop are retained.

Residual: Nine-frame quiet pose intentionally omits minor drift/parallax. Increased hatching and surface brightness need playback/grade review; source-led endpoint light may evolve without inventing geometry.

### D_S01 · source n1521 · [1521,1522)

Conditional pass. Abrupt high-side cut retains the face at far left, joined fingers and rooftop geometry; no red eye is prematurely shown.

Residual: Minor background texture reinterpretation; one exposure only.

### D_S02 · source n1522 · [1522,1523)

Conditional pass. Face enters the actual side view with visible lids closed and stable joined fingers.

Residual: Surface tones are a little clearer; no geometry correction needed.

### D_S03 · source n1523 · [1523,1525)

Conditional pass. Lower red extra eye and top red streak appear at n1523 while the main upper lid remains closed.

Residual: Two-frame exposure samples source side travel and warm-up.

### D_S04 · source n1525 · [1525,1526)

Conditional pass. Upper lid begins separating at n1525 without importing the later fully visible red iris.

Residual: Ordinary skin/clothing is brighter than the source; selectively grade surfaces rather than treating them as emissive.

### D_S05 · source n1526 · [1526,1528)

Conditional pass. Red iris emerges beneath the opening lid at n1526; the actual hand-sign and face perspective are maintained.

Residual: Brighter face and hand surfaces; protect red eye/streak only as appropriate, then check temporal light progression.

### D_S06 · source n1528 · [1528,1532)

Conditional pass. Settled n1528 pose, open red eyes and source-specific crop retained for the corrected four-frame hold.

Residual: Ordinary skin/clothing brightness remains a photography constraint; do not import n1532 red lighting early.

### D_S06b · source n1532 · [1532,1537)

Conditional pass. Actual n1532 later crop, raised finger location and stronger source-existing top flare are preserved.

Residual: Red surface wash and flare are enhanced. Check the n1531-to-n1532 step and final hold endpoint in playback; do not blindly force global means or call the settled pose new body action.

### D_S07 · source n1537 · [1537,1538)

Conditional pass. Hand blur begins at n1537 while the side face remains readable; source-specific push onset and red top light retained.

Residual: Face contours are somewhat cleaner and ordinary skin brighter; preserve the hand blur and gradual light progression in photography.

### D_S08 · source n1538 · [1538,1539)

Conditional pass. The next tighter side-face crop and broad blurred hand across the right are present.

Residual: Stylized smear and strengthened red wash require sequence checking; this is still a side view, not frontal.

### D_S09 · source n1539 · [1539,1540)

Conditional pass. Extreme side-eye crop, red wash and broad horizontal smear remain at n1539, before the frontal view. The frame is not a flat flash.

Residual: Some black contours remain firmer than the original blur; inspect the single-frame transition at 24 fps without reconstructing crisp anatomy.

### D_F01 · source n1540 · [1540,1542)

Conditional pass. First frontal hand-obscured image remains dark with red eyes and directional smear; no clean hidden anatomy is reconstructed.

Residual: Source softness is interpreted as scratchy directional ink smear. Photography must not sharpen it into a clean illustration.

### D_F02 · source n1542 · [1542,1543)

Conditional pass. Actual frontal view clears while the assembling hands remain visibly blurred.

Residual: Hand warm highlights are somewhat stronger; preserve the blur-to-sharp transition at the next exposure.

### D_F03 · source n1543 · [1543,1544)

Conditional pass. Joined fingertips become sharp at n1543 while the expression is less fully revealed than n1544.

Residual: Minor ink/hatching differences do not change hand identity or onset.

### D_F04 · source n1544 · [1544,1548)

Conditional pass. Fully readable grin and frontal sign occur at n1544 against warm sky with no premature black halo.

Residual: Four-frame quiet hold intentionally omits a small pullback; ordinary surface lighting can be graded.

### D_D01 · source n1548 · [1548,1550)

Conditional pass. Ragged black patches first appear behind temple and neck at n1548 in the actual source crop.

Residual: Two-frame sample omits n1549 expansion; keep the effect onset fixed, not faded in early.

### D_D02 · source n1550 · [1550,1552)

Conditional pass. Large black halo and upper-left remaining sky retain the source occlusion boundary; hand rim remains on.

Residual: Native width is 1671 pixels. Add one compositor edge column without nonuniform resizing; preserve generated bytes.

### D_D03 · source n1552 · [1552,1553)

Conditional pass. Small upper-left sky wedge and tiny fingertip/knuckle rim highlights survive at n1552; visible face and hands remain structured.

Residual: Do not extinguish the residual white fragments early or label this fully black.

### D_D04 · source n1553 · [1553,1554)

Conditional pass. Bright hand rim is off at n1553 while a small upper-left sky sliver and warm lower-face underlight remain.

Residual: This is a light-state sample; preserve remaining sky until the next exposure.

### D_D05 · source n1554 · [1554,1557)

Conditional pass. Background first becomes fully black at n1554; red eyes, hands, linework and underlit face remain visible.

Residual: Lower-face/hand/clothing surfaces are brighter than source but gradeable. Do not protect all warm skin as glow, and never black out the person.

### D_D06 · source n1557 · [1557,1559)

Conditional pass. Late farther viewpoint reveals additional wrist/forearm and keeps the structured dark sign pose on black.

Residual: Warm surface underlight is enhanced; n1558 farther pullback is intentionally omitted by the two-frame hold.

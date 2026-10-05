# Bridge A selected-state static QA

Result: Conditional static pass for compositing. All 24 final selected states were visually inspected side-by-side with their corresponding local source frame. No material composition, viewpoint, body/hand identity, unexpected text, or full-frame exposure blocker was found. This is not a real-time animation/playback review and does not certify exposure-internal interpolation, white overlays, or joins to frozen neighbors.

Scope: A=[1202,1248), zero-based n and half-open exposure ranges. Selected outputs are 1672x941. n1246 uses the verified old023 1280x720 JPEG; the other supplied sources are 2560x1440 PNGs. Source frames were used as provided; no independent video decode was performed by this reviewer.

Non-blocking residuals: city/roof/window lines often cleaner; C1 sky streaks/glow stronger; S2 retry face somewhat darker; S3 larger white area; S4 darker and clearer face; W/X cloud/facade detail and highlight areas differ modestly. Selected-state full-frame mean-luma deltas range from -3.526 to +4.982 on a 0–255 scale. Mean-luma agreement is supporting evidence only, not geometry proof.

Next gate: Opus should assess temporal pop/hold rhythm, source-measured S2/S4 exposure changes, n1222 residual transition, and frozen-neighbor joins after unified compositing. No redraw recommendation from this static review.

## Per-state inspection

- C1 / n1202: Dominant roofs, skyline and off-screen energy position preserved. Sky energy streaks and glow are stronger/crisper than source; non-blocking residual.

- C2 / n1204: Dominant tower arrangement, crop and viewpoint preserved. Window/roof detail sharper than source.

- C3 / n1206: Tower arrangement, foreground overlap and crop preserved. Window lines and cloud structure cleaner than source.

- R1 / n1208: Correct small roof-edge motion-blurred figure and roof perspective. Architecture/foreground grooves cleaner.

- R2 / n1210: Correct closer silhouette with two spread-hand motion smears; source-specific camera scale preserved.

- R3 / n1211: Correct large near hand, smaller opposite palm, arm connections and directional smear. Figure/background edge clarity increased slightly.

- S1 / n1212: Open palms, finger silhouettes, body/arm connections and medium framing retained. Cleaner outlines and cooler/flatter skin color.

- S2 / n1213: Selected retry checked. Cropped foreground hands and face/robe geometry retained. Face no longer materially overbright; some face darkening and harder edges remain.

- S3 / n1216: Real n1216 perspective/hand expansion retained rather than S2 enlargement. Clipped-white area increases from 1.304% to 4.365%; face remains dim and total mean luma close.

- S4 / n1218: n1218 geometry and strong magenta-white bloom retained. Face darker and face/hair/hatching more legible than source. Later exposure overlay not assessed.

- W1 / n1224: Wall band/column layout and perspective retained. Panel lines sharper; mean luma +4.982/255.

- W2 / n1225: Distinct n1225 wall viewpoint and upper-left blast retained; not a reuse of W1 geometry.

- X1 / n1226: Selected softened retry checked. Correct building corner, projected facade and blast position. No hard-edged new blast shape blocker.

- X2 / n1228: Correct corner perspective, blast extent and lightning course. Local energy clarity/whiteness difference remains.

- X3 / n1230: Correct building and energy footprint. Some blast texture and lightning are more distinct than source.

- X4 / n1232: Correct defocused building/glow relationship. Diffuse white-magenta blast preserved.

- X5 / n1234: n1234 intentional defocus preserved; not improperly sharpened to n1240 appearance.

- X6 / n1236: Correct building perspective, expanding blast and tiny left-side ejected silhouette retained. Facade/energy detail cleaner.

- X7 / n1238: Correct expanded cloud, leftward trail and building perspective. Fine airborne particles reduced; non-blocking.

- X8 / n1240: Final selected retry checked; soft expanded cloud and correct building perspective. White250 area 7.473% versus 4.193% source; mean luma -3.041/255. Fine particles reduced.

- ST1 / n1242: Street corner and curved curb retained. Empty street; mild surface sharpness increase.

- ST2 / n1244: Street pan viewpoint and diagonal curb retained. No invented person/limb.

- ST3a / n1246: Checked against verified n1246 old023 1280x720 JPEG, not unavailable 2560 PNG. Street remains empty, no early hand.

- ST3b / n1247: Correct n1247 left-edge cropped forearm/open hand; not a leg or foot. No invented full figure.


Source-identity follow-up: the fixed original video was independently decoded by zero-based n. Nineteen unique frames exactly match known051 PNG RGB arrays (maximum error0). The n1246 full-resolution source also confirms the old023 JPEG used during production. n1222 is not pure white; right-side magenta silhouette remains. Public manifests retain the true input provenance. Source/output file hashes are recorded in the delivered package manifests.

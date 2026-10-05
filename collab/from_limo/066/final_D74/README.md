# Selected D74 and verified 372-frame continuation

D=[1485,1559), zero-based original frame n, PTS=n/24, half-open exposure ranges.34 original selected drawings supply74 exposures (40 repeated drawing exposures); source-led grading produces41 distinct native pixel frames. Native1672×941; video1672×942, bottom edge row copied once.24fps. D74 lasts74/24s; frozen298+D74 lasts15.5s/372frames.

## Files and verified hashes

The coordinator publishes redraw_74frames_24fps_once.mp4 beside this text package:
- D74:3,353,421bytes, SHA256 a3a00cc922125efc203bc03c60a7f895c2932eea8b878f431518b22f20a884e1.
- Existing frozen298: SHA256 d0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853, repository file collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4.
- Verified372 output:26,218,507bytes, SHA256 5d81b3a4a60d36a9be29a6293c5b8848d4a15aa0bc7eb600c6dd482bd287ac9a.
- Private original input: SHA256 9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447; AV1/2560×1440/yuv420p/bt709/tv/24fps/3499frames.

Original video and source PNGs are not included. This package also intentionally omits74 duplicate native output PNGs. The exact74 native BGR pixel MD5 list and PNG SHA256 list support reconstruction checks. Selected original drawing paths/hashes are in manifest_D34_selected.json; those34 assets were published in artwork commit36cbbdc and are preserved unchanged.

## Exact selection and residuals

- [1485,1504): shot58_baseline.
- [1504,1521): shot59_baseline, including fixed G06 grade_at[1512,1512].
- [1521,1540): shot60_endpoint_satsurf. S06 grade_at[1528,1531], S06b[1532,1536]. keep_sat[0.35,0.6] only S04/S05/S06/S06b.
- [1540,1559): shot61_baseline.

All other holds retain own-source grading; camera_only:none,zoom1,light:fixed. Existing luminance distribution grading strength1/sigma4; global white balance bounded±10%; white-neutrality protection0.85–0.97 and bright-channel protection0.7–0.9. keep_sat is a saturation proxy, not a semantic eye/light mask. G endpoint grading was actually tested and rejected because it lifted face/hand during source-dark middle frames. S endpoint/saturation-limited grading improved the red phase transition; its late top flare still progresses less than source and skin can remain warmer/brighter. See GRADING_SELECTION.md for measured comparisons and qualifications. C06/C07 and some S08/S09 contours remain sharper than source blur. Fixed holds intentionally omit small viewpoint/drift changes.

D_D02 retains native1671×941 original bytes. Existing padding replicates its smoother RIGHT edge column before the normal fixed source registration; measured adjacent-edge differences left0.85/right0.49levels. No stretch. No D frame is flat black; n1554 has a black background with structured person still present.

## Rebuild from34 drawings and the private source

Use a repository checkout containing the selected art and the exact runtime hashes in verified_code_manifest.json. Tool/code snapshot:08562d6df304c2cdc57accb3613d1d67b201e040; pixel-producing core is unchanged from73ff857dbb69945a36aa6eb0e751907b5358d48d. The helper rejects mismatched code/art/source before rendering.

Actual verified environment: Python3.12.14, numpy2.4.6, opencv-python-headless5.0.0.93, FFmpeg/ffprobe7.1.5. requirements.txt pins the two Python packages. Other system versions may produce different encoded bytes; the native pixel manifest is the pixel check. Do not claim bit-identical video on a changed encoder environment.

Set these paths to your checkout, this package, a fresh output directory and your private source/interpreter:

```sh
export REPO=/path/to/repository
export PKG=/path/to/published/final_D74
export OUT=/path/to/new_D_recovery
export JJK_SRC=/path/to/private/orig.mp4
export PYTHON=/path/to/pinned/environment/bin/python

# Read-only prerequisite check. This was run successfully in the production workspace.
"$PYTHON" "$PKG/reproduce_D34.py" --repo "$REPO" --package "$PKG" \
  --source "$JJK_SRC" --validate-only

# Four complete sequential windows; no simultaneous full74-frame render.
"$PYTHON" "$PKG/reproduce_D34.py" --repo "$REPO" --package "$PKG" \
  --source "$JJK_SRC" --out "$OUT" \
  --frozen298 "$REPO/collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4"
```

The helper calls the unchanged subsheet/measure/action_window CLI for19,17,19,19frames in sequence; checks all74 reconstructed native pixel hashes; preserves exact native bytes during assembly; stream-copies the four selected shot videos intoD74; and optionally stream-copies frozen298+D74 into372. The largest measured photography child RSS in actual selected/comparison runs was3.54GiB. No full74-frame photography process was run.

Important verification scope: this convenience helper passed syntax and --validate-only checks. Its complete render orchestration was not rerun after packaging. The original execution used the same constituent commands and exact verified core, with actual per-shot runs, actual74-frame assembly and actual372-frame join. final_selection.json records their hashes, timing and memory. The normalized recovery paths and metadata do not claim that the original runs occurred at these new pathnames.

## Rebuild372 directly from the published D74

This does not require rerendering D or any earlier frames:

```sh
cd "$REPO"
mkdir -p "$OUT/join372"
"$PYTHON" anime/join_verify.py "$OUT/join372/redraw_372frames_24fps_once.mp4" \
  collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4 \
  "$PKG/redraw_74frames_24fps_once.mp4"
```

The target video must not already exist. Only the frozen298 original file is eligible; do not use a chat preview and never reencode/rerender it. join_verify uses ffmpeg concat -c copy and writes RGB hash/SPS/PPS/PTS evidence. Expected output372frames,1672×942,24fps,15.5s; expected SHA above in the verified environment.

## Evidence and path normalization

- D34_selected.json: exact selected master sheet.
- manifest_D34_selected.json:34 original art/source hashes, anchors and exposure ranges.
- sources.md:74 exact per-frame source/grade/registration records.
- run.json: normalized assembly provenance and exact selected sheet.
- final_selection.json: all6 executed selected/comparison run hashes, time and peak RSS; chosen4 marked.
- verified_code_manifest.json and environment_and_integrity.json: full upstream code provenance and fresh post-render integrity.
- native_BGR_PIXEL_MD5SUMS/native_SHA256SUMS: all74 native checksums.
- verify_D74_selected.json/verify_join372_selected.json: full decode, exact integer-rational PTS, counts, geometry, immutable prefix/suffix proofs.
- join_D74_check.md/join372_check.md and decoded_rgb_md5_*: stream-copy proofs.
- path_normalization.json: original artifact checksums and normalization scope. Only public copies were normalized; original run/source files remain unchanged.

Actual372 validation confirms every decoded RGB prefix frame matches frozen298 and every suffix frame matches selectedD74; parameter sets match. The independent reviewer additionally confirmed exact encoded H.264 picture-slice payload concatenation and unchanged input bytes. Visual assessment used actual decoded frame sequences, ordered contacts and source comparisons; it is not described as real-time audiovisual playback. Final publication and user delivery belong to the coordinator.

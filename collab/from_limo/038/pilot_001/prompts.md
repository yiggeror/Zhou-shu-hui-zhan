【Limo → Claude】2026-10-05　038 pilot_001 实际调用提示词（逐字记录）

# Actual built-in imagegen prompts

## Call 1 — K1_n1188_v1

Reference: source n1188 PNG only. transparent_background=false.

Use case: identity-preserve, strong-reference anime frame edit.
Asset: K1, exact source zero-based frame n1188, a single full-frame animation anchor in a source-matched Hollow Purple release sequence.
Image 1 is the edit target and absolute authority for pose, composition, camera, occlusion, lighting masses and color. Re-render this exact frame as a consistent finished 2D anime production image. Keep the full source image bounds and aspect ratio; requested native output 1672 by 941, no reframing, no zoom, no crop, no added border or outpainting.
Preserve Satoru Gojo's exact head, face and luminous eyes, spiky hair silhouette cut by the upper edge, tilted expression, dark collar and shoulders. Preserve the very large foreshortened pushing hand and vertical finger-smear shapes at front-left/center, their exact height and occlusion of the body, and the large upright hand silhouette at right. Do not reinterpret the smears as clean extra fingers. Preserve all body poses and relative proportions and the bright flash at lower center.
Preserve purple-magenta emitted light, white-hot light at the emitting hand, the white/pink branching lightning in exactly the source's main paths across face and hands, the horizontal blue-violet lens streak, the nighttime city buildings behind, and the same areas of motion softness and hard ink. These are source-defined effects: white light is intentional here. Do not replace the Purple release with cyan fire, a fight punch, a separate orb in front of the face, or a new pose. Keep source dark/light masses, source purple skin illumination, no extra exposure or globally brighter hair.
Use crisp, restrained ink and hatch detail where visible, cel-like shadows with the existing luminous bloom. Keep blurred portions soft instead of inventing sharp new detail. No text, logo, caption, watermark or source signature. No camera change, no decorative redesign. This is one complete color image, not a contact sheet.

## Call 2 — K2_n1197_v1 (not selected)

Reference: source n1197 PNG only. transparent_background=false.

Use case: style-transfer, strong-reference anime frame edit.
Asset: K2, exact source zero-based frame n1197, full-frame city and Hollow Purple projectile anchor.
Image 1 is the edit target and absolute authority for city geometry, camera, perspective, occlusion, energy footprint, color and directional motion softness. Re-render this exact city frame as a finished 2D anime production background plus integrated effects. Keep the entire source bounds and aspect ratio; requested native output 1672 by 941, no crop, no zoom, no reframing, no border or outpainting.
Match the source's steeply slanted city canyon: the dark indigo tall faceted building filling the left third, the pink lit windowed faces through center, the rounded striped tower behind the light on the right, and the diagonal building planes at far right. Preserve every dominant building silhouette, slope, roof edge, perspective line and relative size. Do not flatten the perspective, replace the city, invent a horizon or create clean architectural lines in motion-blurred areas.
Most important: preserve the large white-core purple energy sphere in the lower middle/right, its exact position, footprint and occlusion of city. The white core and broad pale pink bloom are intentional source content, not an error: retain their source area and light mass, do not shrink it into a crisp small purple orb, do not add a dark center, do not expand it to wash away more buildings. Preserve the strong bright lightning paths toward upper right, lower left and right edge and the surrounding saturated pink-violet light, including soft directional streaking. The brightest connected area is centered approximately x=1463,y=984 in the 2560x1440 source. Keep the same source exposure balance.
Use anime-like ink/cel treatment only where source detail survives, with original speed blur and soft bright emission intact. No characters, text, watermark, signature or caption. No cyan fire, no fight pose, no later fusion imagery. One complete color image, not a sheet.

## Call 3 — K2_n1197_v2 (selected)

References in order: K2_n1197_v1.png; source n1197 PNG. transparent_background=false.

Use case: lighting-weather and motion-softness correction, exact two-image reference edit.
Image 1 is K2_n1197_v1, the edit target. Image 2 is the exact original n1197 reference and is the authority for blur, exposure, camera and energy.
Make ONE correction to Image 1: restore the original source's strong diffuse directional motion blur and pink-violet light wash, as seen in Image 2. The current city in Image 1 is far too sharp and dark; the source has heavily blurred roof/window/vertical edges and very little fine window detail. Match the softness and luminous haze of Image 2 closely across the city instead of improving architectural detail. The existing main geometry of Image 1 is correct; keep exactly the same building silhouettes, camera perspective, framing and relative placement while softening their visible edges to source character.
Keep the white-core sphere's exact size, footprint, center and its occlusion of the city. Preserve the major white lightning paths but make their edge softness and pink glow match Image 2. Keep the bright core white, no dark center, no new radial spokes. Preserve the source's concentrated center/lower-right energy placement, not a new centered orb.
Use full-frame 1672x941 output, no crop, no extra margin, no zoom or camera rotation. No changed buildings, no added sharp lines, no extra objects, no characters, no words or watermark. Do not make an attractive sharp illustration; this must look like the specific fast, strongly blurred anime action frame in Image 2. Do not recreate the source watermark. Only one complete color frame.

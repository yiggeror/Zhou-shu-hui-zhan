【Limo → Claude】2026-10-03　需求 008：红焰 v2 生成提示词

使用内置图像生成编辑。交付 PNG 保留生成器原生尺寸，无后期缩放或像素修改。两个角色 clean 锚点是已经通过的原图，保持不改。

## C01 初次加量

编辑目标：C01_char.png。仅火焰体量与赛璐璐分层参考：B03_char_fx.png。

Use case: precise-object-edit.
Asset type: paired anime animation frame C01 red fire overlay, 16:9 landscape, same native 1672x941 canvas.
Input1 is the ONLY EDIT TARGET: accepted black-haired Sukuna in ivory kimono on solid chroma green. Input2 is only a FIRE VOLUME / CEL SHAPE reference: Gojo cyan fire. NEVER borrow Gojo's face, hair, pose, or clothing.
Change ONLY by adding a large dense mass of crimson red anime fire to the existing foreground punching fist and forearm. Fire intensity must rival the broad cyan fire in reference2; NOT thin tendrils, vines or rings. Broad irregular flame sheets with long pointed tongues, deep-crimson outer shapes, bright saturated red/vermilion middles, pale peach-white cores, three flat cel tones. The fire envelopes the whole fist perimeter; a few translucent red flame sheets cross the lower knuckles/front without hiding the anatomy, the majority is around and behind the fist. Make a strong silhouette of flames on the left and lower sides and along the arm, with long flame tails flowing rearward toward the LOWER RIGHT. The upper knuckle edge can carry short flame tongues but they must STOP below the visible eyes. Preserve a clean open face zone.
STRICT PROTECTED AREA: the upper-right character face, black hair, forehead tattoo, visible red eye and sliver of other eye must stay precisely unchanged and fully readable. Do NOT draw any fire, embers, glow or red haze over the face, eyes or hair. Retain all original fist proportions, knuckle shapes, fingers, nails, arm bands, guard fist, ivory sleeve folds and black circle exactly. Preserve camera, crop, linework, shading, background. Do not move character or enlarge fist. Keep solid vivid green screen; fire only red/orange/pale warm cores, no green or cyan fire. No bloom haze, lighting pass, text or watermark. Return one edited frame only.

## C01 头部保护修整

编辑目标仍为 C01_char.png，第二输入为初次加量结果，参考其火焰。

Use case: precise-object-edit. Produce one paired anime frame on green at the same 1672x941 dimensions.
Image1 is the clean accepted Sukuna C01 EDIT TARGET. Image2 shows the desired big RED FIRE palette, volume and coverage to reproduce, except its flames touch the left ear/temple and therefore need a clean head zone.
Add the same HUGE rich cel red flame mass as image2: broad deep crimson outer sheets, vivid vermilion center, warm pale cores, wrapping sides and bottom of the enormous fist, sparse partly translucent tongues across fist front, and long billowing flame tails along forearm to lower-right corner. This should equal image2 fire mass, not revert to thin red ribbons.
ONLY correction relative to image2's fire design: protect ALL of the character's head, including hair, left ear, temple, eyes and visible cheek. Keep the entire region x=820–1300,y=0–290 clear of ANY red flame, red haze, glow or reflected fire coloring; image1's face/head must stay unmodified. It is okay that this removes fire above part of the top knuckle boundary. Concentrate replacement volume around left/lower fist and lower-right forearm instead. Do not put flames on the other/guard fist at left.
Lock the exact input1 pose, knuckles, fingers, thumbnail, skin tone, facial linework, eye shapes, tattoos, ivory sleeves and bands. No changes to camera or anatomy. Preserve solid bright green background and crop. No text or watermark.

## C09 初次加量

编辑目标：C09_char.png。参考 B03_char_fx.png 的火焰体量与 C01 加量候选的红焰配色。

Use case: identity-preserve / precise-object-edit.
Asset: C09_char_fx_v2, anime compositing animation anchor on green chroma-key background.
EDIT IMAGE 1 ONLY. Image 1 is the accepted Sukuna C09 character drawing and the only composition/identity/pose target. Image 2 is only a supporting reference for the LARGE QUANTITY, broad silhouette, and flat cel-sheet structure of the flame effect; do not borrow its white-haired character, hand, camera, or cyan color.

Change only one thing in image 1: add a substantially LARGE, powerful RED flame mass around its enormous foreground punching fist, visually as weighty and abundant as the cyan fire in image 2. Retain image 1 canvas 1672 x 941, original framing and every character position. This is an effects overlay on the accepted drawing, not a redraw.

Fire design: the entire perimeter of the foreground fist must be wrapped in broad contiguous flame sheets with generous long sharply tapered tongues, not a few small strips. Large outer flame masses extend beyond the knuckles to the upper-left and left of the punching fist, and down around the sides and bottom of the fist; large layered flames continue around the wrist and form long sweeping fire tails streaming along the foreground forearm toward the LOWER RIGHT rear. Make the overall fire volume comparable to the large cyan fire mass of reference 2. A few tongues cross the FRONT of the fist, partially translucent so the finger drawing remains readable. Most flames stay around the fist edges and behind it.
Flat anime cel-shading with three clean shape layers: broad DEEP CRIMSON / dark red outer sheets, vivid VERMILION / bright scarlet red middle, narrow pale warm peach-cream inner cores. Sharp solid-color silhouette shapes; no soft airbrush glow or smoky blur. No vines, thin loops, wire-like spirals, ropes, concentric rings, or miniature decorative flames.

CRITICAL PROTECTED AREAS: preserve the ENTIRE FACE exactly as image 1: exact red eyes, black forehead and cheek markings, skin tones, mischievous arrogant smile, mouth, nose, ears, jaw, and black swept-back spiky hair. Absolutely no flame in front of the face, and no flame glow, red recoloring or light change on the face. Keep all fire below/away from the chin and face. Do not redraw facial expression.
Preserve image 1 anatomy, fist proportions, original fingers and thumb, hand contour, foreshortening, guard hand at the left, sleeve shapes, ivory robe, black concentric-circle sleeve emblem and black wrist/forearm bands. Do not move or alter the pose. Flame overlays may overlap the fist lightly, but must not deform it or replace skin with fire.
Keep the ORIGINAL SOLID VIVID GREEN chroma-key background visible wherever there is neither character nor fire; do not add a scene, shadow, gradient, black background, transparency, captions or text. Output ONE edited full image.


## C09 下巴保护修整

编辑目标为初次加火结果，原始 C09_char.png 用于恢复面部。

Use case: precise-object-edit / identity-preserve.
Make a VERY LOCAL cleanup to image 1. Image 1 is the red-flame C09 almost-final artwork to edit. Image 2 is the original approved no-flame C09 drawing, used ONLY to restore the protected areas.

KEEP ALL THE EXISTING LARGE RED FIRE AROUND THE FOREGROUND FIST AND LOWER-RIGHT FOREARM: same broad deep-crimson / vermilion / warm-cream flame sheets, quantity, vigorous pointed tongues, layers, perimeter and long lower-right tails. Do not reduce the powerful flame mass around the punching fist.

ONLY correct two small encroachments from fire:
1. Restore the ENTIRE original FACE, CHIN AND NECK from image 2, including the small left cheek/chin region under the left side of the smile. Remove the thin red flame reaching up the jaw/cheek and any red flame overlap on skin above the base of the neck. There must be absolutely NO flame, red stripe, glow or red reflection on the face, jaw, chin or neck. The large flame above the fist can remain in front of the shoulder/robe but MUST remain below the neck and curve away from the head. Preserve the exact face and expression: both red eyes, forehead/eye/cheek markings, mouth and smile, black hair, proportions and colors.
2. Restore the whole small raised GUARD FIST at image left and its wrist from image 2 so its knuckles, fingers, thumb, skin contour and black wrist bands are clear. Flames can be behind or to the side of that hand, but not across its surface or hiding its silhouette.

Do not redraw or move anything else. Preserve the large punching fist exactly: same fingers, thumb, perspective, anatomy, front flame tongues and foreshortening. Preserve ivory sleeve, black circle emblem, all body position and the original solid bright GREEN chroma-key background; no black or transparent background. Maintain full original 1672 x 941 composition. Output one full edited frame, no text.


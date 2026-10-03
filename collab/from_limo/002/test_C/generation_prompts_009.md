【Limo → Claude】2026-10-03　测试 C 补全：选用生成提示词

内置图像生成编辑，交付 PNG 保留原生字节。提示词中像素数为编辑目标，不是实际配准保证；实际检查见交付说明。

## Clean 人物

测试 C｜C02–C08 无火人物图：选用提示词

全部选用图为 1672×941 PNG。C01、C09 沿用已通过版本，未修改。
生成方式：以前一张选用无火人物图为编辑目标，顺序完成 C02→C08；C09 仅作终点姿态/五官纹身参考。局部修正均接在对应候选图后。
以下只列构成最终选用图的原始生成/修正提示词，顺序即执行顺序。提示词中的像素值是编辑目标，并非逐像素配准保证。

C02_char.png
选用链：步骤 1 → 步骤 2

步骤 1：生成该帧
编辑目标：C01_char.png
支持参考：C09_char.png
原始提示词：
Use case: identity-preserve. Clean anime animation frame C02.
Image 1 is the ONLY EDIT TARGET, approved C01. Image 2 is a supporting FINAL-pose guide C09, not the current pose. Keep image 1's huge fist perspective.
Make a very small 1/8 in-between towards image 2. The foreground fist must shift LEFT and down, not right. Move the whole foreground fist, including all four knuckles and curled thumb, exactly about 18 pixels to the LEFT and 27 pixels DOWN relative to image 1. Its uppermost central knuckle currently has its peak around (935,143); place that same peak near (917,170). The leftmost fist outline currently around x=509 moves to about x=491. All fist contours move together without enlargement, shrinking or reshaping. Keep the same hand scale as image 1 and connect wrist/forearm naturally. Do not move fist rightward. Do not jump down to the final pose.
The fist still covers the mouth, chin and almost all lower face. Expression remains cold, no smile is visible yet. The red eyes brighten just imperceptibly. Preserve Sukuna's facial identity, tattoos, four eye design, black swept-back spiky hair, ivory kimono, black concentric-circle shoulder emblem and two black forearm bands. Keep camera, head position and angle, body, other raised guarding fist and background unchanged. Only tiny wind changes in outer hair tips and ivory sleeve folds, not their positions.
Preserve clean cel-anime lines, colors, shading, and the solid bright chroma-green background. No green subject, no fire, no FX, no text or watermark, no blur, no added fingers. Single 1672x941 landscape PNG with the same framing.

步骤 2：局部修正
编辑目标：C02 上一步输出
支持参考：C09_char.png
原始提示词：
Use case: precise-object-edit. Clean up ONE local contour artifact in animation frame C02.
Image 1 is the EDIT TARGET and must keep its current fist pose, camera, identity, clothing and background. Image 2 is only a supporting anatomical guide showing what Sukuna's exposed cheek and nose look like.
In image 1 there is a spurious upper ghost arc running approximately from (938,183) through (1045,196) to (1155,232). It cuts across the lower cheek and creates an unnatural doubled skin ribbon above the actual foreground fist. REMOVE ONLY this upper ghost contour and the ribbon shading. Restore the newly exposed skin area above the fist as one continuous cheek/nose plane with the correct cheek tattoo from image 2, without an extra hand edge.
The REAL foreground fist upper silhouette is the LOWER contour, approximately (905,194) through (1030,249) to (1120,257). PRESERVE that lower real fist outline and the entire foreground hand below it in its present position. Do not move the fist at all, do not resize it, do not change its fingers or thumb. Mouth and chin stay occluded by this fist.
Preserve exact head angle, hair, facial features, red eyes, ivory kimono, black sleeve circle, wrist bands, left-side guarding fist, lighting and cel-anime line style. Solid bright green background, no fire, no FX, no text, no extra fingers. Output single 1672x941 landscape image with same framing.


C03_char.png
选用链：步骤 1

步骤 1：生成该帧
编辑目标：C02_char.png
支持参考：C09_char.png
原始提示词：
Edit image 1 (C02) into clean animation C03. Image 2 is the final C09 guide.
MOVE THE BIG FRONT FIST TOWARD THE LEFT EDGE OF THE PICTURE and slightly downward. "Left" means screen-left, toward the small raised guarding fist at the left side of the canvas. It does NOT mean the character's left. Translate the entire huge fist about 30 pixels toward the LEFT CANVAS BORDER and about 24 pixels DOWN. In the result, there must be visibly MORE empty room between the large fist's right edge and the right shoulder circle, and the large fist must overlap a little MORE of the ivory sleeve on the left. The uppermost knuckle must be farther left in the picture than in image 1, never farther right. Keep the exact same huge fist scale and foreshortening; four knuckles and one curled thumb only. Continue wrist naturally.
Erase the whole old fist outline; newly exposed cheek/nose is continuous facial skin and matching tattoos, as in image 2. No extra outline, no ghost arc, no skin ribbon. Mouth/chin still completely covered, expression cold, irises a tiny bit brighter.
Everything else stays anchored: same head position/angle, camera, guarding fist, body, ivory kimono, black shoulder circle and forearm bands, black swept-back spiky hair. Only tiny wind variation at hair tips and sleeve folds. Same green background. No flames, no effects, no text or extra fingers. Single same 1672x941 composition.


C04_char.png
选用链：步骤 1 → 步骤 2

步骤 1：生成该帧
编辑目标：C03_char.png
支持参考：无额外图片；以前一张图为准
原始提示词：
Edit this clean animation frame into the very next frame, with one tiny movement only. The same HUGE foreground fist shifts 15 pixels toward the picture's LEFT border and 30 pixels DOWN on the 1672x941 canvas. This is a small in-between, not a new pose. Keep the front fist exactly the same size, orientation, shape and perspective. Translate all its four knuckles and thumb together. The topmost fist contour now near y=201 should be near y=231. Do not lower it any farther.
Erase the old fist outline and fill the few newly revealed pixels with continuous face skin and its existing cheek tattoo. No duplicate outline or skin ribbon. The mouth remains completely concealed behind the fist. Do not add any fabric near the mouth; leave the collar and kimono exactly where they are.
Keep camera, head, hair, expression, other guarding fist, body, sleeve circle, lighting, and green background identical in placement. Red irises may be a barely perceptible bit brighter. No fire, FX, text, extra fingers, new objects or framing changes. Same clean cel-anime style; single 1672x941 image.

步骤 2：局部修正
编辑目标：C04 上一步输出
支持参考：C09_char.png
原始提示词：
Precise local face repair only. Input image 1 is the EDIT TARGET: C04. Image 2 is the final C09 face/tattoo identity guide.
Do not move or change the fist, hands, body, hair, camera, head angle, clothing, lighting or green background at all.
Repair only the small visible lower-face area above the foreground fist. The prior edit left the exposed lower face blank. Add the visible part of Sukuna's CLOSED NEUTRAL mouth in the anatomically correct position, following the face placement in image 2 but with NO smile and NO teeth. It should be a short calm/unsmiling lip line, running diagonally with the head's tilt and partly occluded by the real foreground fist edge. Do not draw any mouth over the fist. The first mouth corner can just begin to be visible above the fist. No broad expression or open mouth.
Match the visible left-cheek tattoo to image 2's continuous angular cheek marking; remove the invented extra small zigzag segment that appears on the lower cheek in image 1. Preserve the existing real foreground fist silhouette and clean continuous skin above it. No duplicate contour or skin ribbon.
Keep crisp cel-anime styling and exact 1672x941 composition, no fire or other effects.


C05_char.png
选用链：步骤 1

步骤 1：生成该帧
编辑目标：C04_char.png
支持参考：无额外图片；以前一张图为准
原始提示词：
Edit this previous clean animation C04 into the very next frame C05. Small local continuation only.
Move the SAME huge foreground fist 12 pixels toward the LEFT EDGE OF THE PICTURE (toward the small guarding fist) and 22 pixels DOWN. All four knuckles and thumb move together with unchanged size, foreshortening and orientation. The top fist crest near (887,254) should now be near (875,276). This is a small step; do not jump to a new pose. Reconnect forearm naturally and completely erase the previous fist outline, revealing continuous face/neck skin and existing tattoo behind it, with no doubled edge or skin ribbon.
The mouth is now a little more visible. Begin a very restrained confident smirk: lift the mouth corners slightly from the previous closed neutral line, but keep lips CLOSED and show NO teeth yet. This is only the beginning of the smile. Eyes remain narrow and confident; red irises grow slightly brighter. Keep the exact same facial structure, head position and angle, cheek/nose/forehead markings and spiky black swept-back hair.
Camera, body, other guarding fist, shoulder circle and two wrist bands remain anchored. Only minuscule wind variation in a few hair tips and sleeve-fold edges. Do not raise the collar or add fabric near the mouth.
Match all cel-anime linework, palette and lighting. Solid chroma-green background, no green on the character, no fire or effects, no text or extra fingers. Single 1672x941 landscape image.


C06_char.png
选用链：步骤 1

步骤 1：生成该帧
编辑目标：C05_char.png
支持参考：无额外图片；以前一张图为准
原始提示词：
Make the next very subtle animation frame C06 from this image. Edit target is C05.
Maintain almost the SAME pose. The giant foreground fist moves straight DOWN by only a tiny amount, roughly 10 pixels on this 1672x941 image. Keep its horizontal position and size unchanged. Its top contour is still around y300, clearly in front of the lower neck/chin. Do not lower the fist below the chin; do not expose the whole neck. Do not zoom, rotate or move the camera.
Change the mouth just slightly from the current closed-lip smirk: the corners lift a tiny bit and a very NARROW white sliver of teeth begins to appear between the lips, keeping the smile small. Preserve exact face identity, tattoos, head position and angle. Keep all existing contours clean, erasing the previous fist outline with no ghost lines. Keep the left guarding fist EXACTLY in its current position and shape. Same hair, ivory kimono, shoulder circle, wrist bands, green backdrop, cel-anime style and light. Red eyes can be slightly brighter. No other movement, no extra fingers, no fire, FX or text. Single same 1672x941 composition.


C07_char.png
选用链：步骤 1

步骤 1：生成该帧
编辑目标：C06_char.png
支持参考：无额外图片；以前一张图为准
原始提示词：
Edit this C06 image into C07 with an extremely tiny change.
The giant foreground fist stays almost completely fixed: at most 5 pixels lower, with NO horizontal change. Do not lower it enough to reveal any more chin or neck. Keep the uppermost knuckle at essentially the current height, around y316 to y321. All hand contours, size, four fingers, thumb, pose and perspective remain the same. Keep its lower-face occlusion the same. Do not reveal or invent a chin tattoo in this frame.
Change only the smile slightly: widen the existing thin teeth sliver just a little, and raise the corners a little more, midway between a smirk and a confident grin. Keep same lip placement, face shape and head angle. Make red irises subtly brighter, without exterior glow. A couple of outer hair tips can flutter by a few pixels.
Keep head, body, left guarding fist, collar and sleeves, black shoulder emblem, black wrist bands, camera, lighting and green background anchored exactly. No new outlines, ghost arcs, cloth, fingers, fire, effects or text. Same cel-anime style and 1672x941 landscape framing.


C08_char.png
选用链：步骤 1

步骤 1：生成该帧
编辑目标：C07_char.png
支持参考：C09_char.png
原始提示词：
Use case: identity-preserve. Create clean penultimate animation frame C08 by editing INPUT IMAGE 1 (selected C07). INPUT IMAGE 2 is the accepted final C09 ENDPOINT GUIDE, not the edit target.
This is the frame immediately before image 2. Advance image 1 to a NEARLY FINAL pose, about 90–95% of the C09 endpoint. Use image 2's correct foreground fist proportions, narrower width, angle, foreshortening, forearm connection, revealed cheek/chin tattoos and smug grin as the endpoint to approach.
Place the C08 foreground fist very close to image 2, but slightly HIGHER: its uppermost knuckle crest should be around y345 on the 1672x941 canvas, between image 1's y316 and image 2's y359. It must NOT descend below the endpoint fist. Match image 2's near-final horizontal placement (crest around x790) and fist angle/width without overshooting. Four knuckles and one curled thumb; single clean silhouette with no ghost contour.
Face is almost fully revealed, approaching image 2's confident arrogant smile. The grin is just a little less open than the final image 2 grin. Faithfully restore the angular lower-cheek tattoo return and the small black pointed chin tattoo wherever they are physically visible above the fist, exactly consistent with image 2. No invented extra tattoo segments. Eyes approach image 2's bright saturated red irises, with no external halo.
Keep camera, head position/angle, overall face proportions, black swept-back spiky hairstyle, the small raised guarding fist at viewer-left, body and ivory kimono locked to the references. Preserve black concentric-circle shoulder emblem and two black wrist bands. Only minuscule hair-tip and sleeve-fold wind variation. Same crisp cel-anime style and lighting. Solid bright green background, no green on character, fire, FX, text or additional anatomy. Output one clean 1672x941 C08 image.


质检说明
- 已逐张查看选用图；被弃用的明显右移、过度下移、重影弧线、护手位移等候选未交付。
- 选用序列保持同一机位、头部角度、左侧护手与主体身份；无火、无新增手指、无明显重复拳头轮廓。
- 动作是非匀速手绘式过渡：C05 横向推进较多，C06–C07 接近停顿，C08 向 C09 的拳形/角度收拢。
- C05 嘴角开始上扬，C06–C07 露出细窄牙线，C08 接近 C09 的狂妄笑容。
- 头发/衣袖变化较保守；红眼总体趋亮，不能保证每一步所有像素亮度严格单调。
- 亮绿色背景有轻微色相变化，建议采用色度范围抠像，不要只匹配单一 RGB 值。
- 拳形、局部衣褶与线条存在生成式微小变化，不宣称像素级完全一致；建议按各停 2 帧合成后检查节奏。


## 配对红焰

# 测试 C：红焰配对图实际提示词

所有图均使用内置图像生成编辑功能制作，保留绿色背景，输出原生尺寸 1672×941。下列提示词仅记录最终选中结果所需的实际调用文本。

## C02_char_fx.png

首轮编辑目标：C02_char.png。
火焰风格参考输入：C01_char_fx_v2.png。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve.
Asset: C02_char_fx, an anime animation frame paired with its clean drawing. Input image 1 is the ONLY EDIT TARGET: selected C02 clean character. Input image 2 is the approved C01 red-fire STYLE AND VOLUME REFERENCE ONLY. Do not copy its pose or move the character toward its pose.
Change ONLY by adding a huge dense energetic mass of cel-shaded RED FLAME around the full perimeter of the foreground punching fist and along the lower-right forearm. Match image2 broad thick irregular flame sheets and large volume: deep crimson outside, saturated scarlet/vermilion middle, warm pale cream/peach cores, crisp 3-tone anime shapes. Multiple long flame tails flow toward lower right along the forearm. Put some curving fire tongues across the front of the fist, while preserving its readable finger/thumb anatomy. Keep most fire around and behind the fist. This is frame C02: vary the flame silhouette from image2 with a forked broad upper-left plume, a thick curling lower-left wave and three staggered long lower-right tails; it should visibly burn rather than duplicate the same silhouette.
LOCK image1 identity, black spiky hair, all facial markings and linework, red eyes, exact face visibility (mouth remains hidden), head location, fist position and size, four curled fingers and thumb, fingernail, guard fist, skin shading, wrist bands, ivory kimono folds and black circular emblem. No pose changes, no camera or crop changes. All visible face and both eyes must remain fully readable. No flame or haze across eyes, eyebrows, nose or hair; upper flames bend outward away from the head. Preserve the vivid uniform green-screen background, original 1672x941 framing, no black or transparent background. No text, watermark, bloom, blur, particles over the face, new objects or lighting restyle. Output one paired edited frame.
```

## C03_char_fx.png

首轮编辑目标：C03_char.png。
图像输入：仅对应无火人物图；已通过 v2 的体量、配色和画法用文字描述。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve. Asset C03_char_fx paired anime animation frame.
The SINGLE supplied clean C03 is the ONLY EDIT TARGET and sole geometry/identity source. Add fire as an overlay and preserve the exact underlying drawing. In particular keep the foreground thumb and thumbnail exactly where they are in this image: thumb outline approximately x478–766 and y724–868, nail near x612–730 and y760–853. Do not shift the thumb right or up, do not shrink or reshape it. Keep all four punching-finger contours, knuckles, proportions, skin shading and the fist silhouette fixed. Preserve the exact face, red eyes, markings, black hair, raised guard hand, arm bands, ivory clothes, black circle emblem, head/body position, crop, camera and native1672x941 frame. Mouth remains hidden by the existing fist, do not reveal or create a mouth.
Overlay a LARGE DENSE red-fire mass enveloping the entire foreground fist and flowing down the forearm to lower right. Thick layered broad cel flame sheets with irregular sharp tapered split tongues, deep crimson outer shapes, saturated scarlet/vermilion middles and warm pale cream/peach cores. Not thin ribbons, vines or outlines, no soft glow. C03-specific fire silhouette: broad flattened upper-left crescent plumes, a curling pocket outside the left fist edge, a strong wave BELOW the thumb and two long uneven flame sheets sweeping lower-right to the frame edge. Keep most flames around/behind the fist; a few narrow front tongues across the knuckles, but leave the thumb/thumbnail unobscured so its fixed anatomy remains evident.
Protect every visible part of the face, especially BOTH RED EYES and nose. Flames over the fist must curve outward away from the head; no fire across visible cheeks, eyes, eyebrows, hair or nose. Preserve uniform bright chroma GREEN background, no black background or transparency. No relighting, text, watermark, blur, particles across face or other objects. Output one edited paired frame.
```

## C04_char_fx.png

首轮编辑目标：C04_char.png。
火焰风格参考输入：C09_char_fx_v2.png。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve. Add fire as an overlay, not a redraw.
Image1 is the ONLY editable base frame C04. Use ONLY image1 for ALL character geometry and exact coordinates. Image2 is a FIRE PALETTE, SHAPE and VOLUME reference only; ignore every part of its character, pose and smile.
First preserve all existing image1 pixels outside the added fire: exact foreground fist outline and finger contours, thumb at lower-left of the fist (approximately x456–747, y772–916), its thumbnail, all knuckle creases and shadows, arm bands, guard hand, face, neutral partly-visible mouth, red eyes, facial markings, black hair, ivory robe and black circle emblem. Never move the thumb up/right, never change the fist silhouette, never copy image2 anatomy. Keep camera, pose, crop and 1672x941 canvas unchanged.
Overlay a LARGE DENSE mass of broad sharp cel-shaded red fire around the full punching-fist perimeter and along the forearm down to the lower-right edge, matching image2 volume. Deep crimson outer sheets, saturated bright scarlet/vermilion inner sheets, warm pale cream cores. Thick layered flames, not thin ribbons or outlines. A few foreground flame tongues curve across the lower finger surfaces while anatomy stays readable. Most fire surrounds or sits behind the fist. C04's unique flame silhouette: wide leftward flame fan with four uneven pointed prongs, a hooked loop at lower left by the thumb, and a pair of billowing lower-right tails with branching tips. Keep the upper-right/top-of-fist fire very LOW, under the partly-visible neutral mouth; the visible mouth, nose, eyes and cheek must remain wholly clear. Put replacement flame volume at left, bottom and right, away from the face. Preserve pure solid green screen, no transparency or black background. No lighting restyle, red face tint, blur, bloom, text, watermark or added objects. Output one paired frame.
```

### 最终选中结果所需修正

编辑目标：本帧首轮红焰结果。恢复参考：对应无火人物图。

```text
Use case: precise-object-edit / identity-preserve. Strict localized restoration, not new artwork.
Image1 is the C04 fire image to EDIT. Image2 is the approved clean C04 frame. The current image1 wrongly has a toothy smile. Restore the EXACT NEUTRAL CLOSED MOUTH, cheek/chin and facial expression from image2, at the exact same coordinates. Image2 mouth is a short closed downturned-neutral line, no visible teeth, no smile. Copy image2 visible facial area above the fist exactly, including its markings, eyes, skin shading, jaw, brows, ear and hair; do not invent or redraw a new expression. Remove the small red flame tongue immediately against the mouth/chin so the restored neutral mouth is clearly visible. The existing clean image2 forehead, nose and mouth must stay unchanged.
Also preserve image2 exact punching-fist/thumb/thumbnail geometry and coordinates; do not reposition it. Keep ALL other existing image1 huge red fire, broad left fan, lower-left hook, front tongues and lower-right long tails, crimson/red/cream palette and volume. Don't copy fire into face. Keep body, guard hand, clothing, black circle emblem and camera unchanged. Uniform vivid green screen,1672x941 frame, no text, no black background, no transparency. Output one corrected C04 frame.
```

## C05_char_fx.png

首轮编辑目标：C05_char.png。
图像输入：仅对应无火人物图；已通过 v2 的体量、配色和画法用文字描述。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve. Asset C05_char_fx, paired anime animation frame.
The one supplied image is the ONLY edit target and sole source of character geometry. Change only by ADDING CEL-SHADED RED FIRE; absolutely preserve the existing drawing underneath at original coordinates. Keep the exact black-haired tattooed character identity, face, red eyes, subtle CLOSED-LIP SMALL SMIRK (no visible teeth), head, guard hand, enormous foreground fist, each curled finger, knuckle and thumbnail, arm bands, skin shadows, ivory sleeve folds and black circular emblem. Do not move, shrink, enlarge or reshape any hand, finger, thumb or body part. Foreground thumb stays low at x400–687, y813–941; fist upper ridge stays around y294. Keep 1672x941 canvas, perspective and crop.
Add a LARGE DENSE BLAZING MASS wrapping the WHOLE punching-fist perimeter and extending down the lower-right forearm. Approved anime cel fire style: broad layered irregular sheets with sharp long tapered tongues, deep dark crimson outer mass, saturated scarlet/vermilion middle shapes and warm pale cream/peach inner cores; crisp flat tonal boundaries, no blur, no glow-haze. It must be thick and powerful, not thin ribbons, vines or an outline. Most mass surrounds or sits behind the fist; several front fire tongues curl across the lower knuckles without obscuring all anatomy. C05 unique fire phase: a powerful broad left plume splits into two hooked tongues, a curled S-wave runs under the fist and thumb, and three staggered broad long tails sweep down-right along the forearm and out the lower-right edge. Let green pockets separate some tips. Keep the area around all visible FACE, MOUTH, EYES and HAIR CLEAR. No red fire or haze across face; flame on the upper fist must bend sideways away from the jaw, kept below mouth. Keep the smirk readable. Preserve flat vivid uniform green screen, no black background or transparency. No new objects, text, watermark or lighting restyle. Output one edited frame.
```

## C06_char_fx.png

首轮编辑目标：C06_char.png。
图像输入：仅对应无火人物图；已通过 v2 的体量、配色和画法用文字描述。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve. Asset C06_char_fx paired anime frame.
The single supplied clean C06 image is the ONLY EDIT TARGET and sole character reference. Change only by adding red fire as an overlay. Preserve all underlying drawing at exact original coordinates: black hair, red eyes, every face marking, head, face, the small smile with a THIN TINY SLIVER OF TEETH, guard fist, huge foreground fist and its four curled fingers/knuckle contours, thumb and nail, forearm black bands, skin shading, ivory robe folds and black circle emblem. Do not exaggerate the smile. Do not move or reshape any hand/body part, do not shift the thumb up or right. Keep camera, composition, original 1672x941 canvas.
Overlay a LARGE DENSE powerful mass of broad cel-shaded RED FLAME around the WHOLE foreground punching fist, then long fiery tails along the forearm to the lower-right edge. Three principal flat tones: deep dark-crimson outer sheets, saturated bright scarlet/vermilion interiors, pale warm cream/peach cores. Jagged asymmetrical layered broad sheets with fine sharp split tips, strong anime linework, no soft glow. Not thin vines, an outline or a sparse ribbon. Most mass surrounds or is behind the fist; some tapered front tongues sweep across the lower finger surfaces without hiding all anatomy. Unique C06 fire phase: an angular broad crest flares far left into three serrated blades, a large lower-left flame curls back upward, and two thick long lower-right tails braid with a shorter third fork. Keep flame shapes distinct from adjacent frames, consistent total volume. Protect ALL face, hair, both eyes and the tiny-teeth smile completely; no fire, embers, haze or red tint across face. Top-of-fist tongues bend left/right away from jaw and stop below mouth. Preserve the vivid solid green-screen backdrop, no black or transparent background. No new objects, text, watermark, bloom, blur or relighting. Output one edited frame.
```

## C07_char_fx.png

首轮编辑目标：C07_char.png。
图像输入：仅对应无火人物图；已通过 v2 的体量、配色和画法用文字描述。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve. Asset C07_char_fx paired anime animation frame.
The SINGLE supplied clean C07 image is the only editable base and sole geometry/identity source. Preserve its character exactly and add only fire. Lock original coordinates and shapes of enormous foreground fist, four curled fingers, knuckles, visible thumb/nail (low at image bottom), forearm bands, raised guard hand, face, narrow tooth-showing confident smile, bright red eyes, facial markings, black hair, ivory robe and black circular shoulder emblem. Do not move, enlarge or reshape any part; do not invent expression changes. Keep the original crop, perspective, 1672x941 canvas and clean drawing under the added flame.
Add a LARGE DENSE mass of broad irregular red cel-FIRE sheets wrapping the entire foreground punching fist, with long broad tails sweeping along the forearm to lower right. Match powerful 3-tone anime fire: dark deep-crimson outer forms, saturated scarlet/vermilion middle sheets and warm pale cream/peach cores. Thick energetic layering, crisp hard tonal boundaries and many sharp split tips, not thin vines or a sparse ring. Keep most volume beside and behind the fist, with several front tongues across the lower knuckles. Make C07 a visibly new burning phase: a low broad leftward wave with a large central curling hollow, two tall split flame tips farther left behind the guard fist, a sweeping crescent below the thumb, and two asymmetric lower-right tails opening into a wide fork. Different contour from other frames while retaining large volume and palette.
No flame over the face, red eyes, hair or readable smile. Upper-fist fire must bend sideways away from the jaw and stay below the mouth, leaving the entire face clean. Preserve solid uniform vivid GREEN screen outside character/fire, no black background and no transparency. No text, watermark, blur, soft bloom, particles crossing face, relighting or other objects. Output one edited paired frame.
```

## C08_char_fx.png

首轮编辑目标：C08_char.png。
图像输入：仅对应无火人物图；已通过 v2 的体量、配色和画法用文字描述。

### 首轮提示词

```text
Use case: precise-object-edit / identity-preserve. Asset C08_char_fx paired anime animation frame.
The SINGLE supplied clean C08 drawing is the ONLY edit target and the sole source for character geometry. Add fire only as a layer over the existing drawing. Preserve exact original coordinates and contours of foreground fist, four curled fingers, knuckles, bottom-left thumb and nail, forearm black bands, raised guard hand, white/ivory robe folds, black shoulder circle, body pose and perspective. Lock face identity, bright red eyes, black hair, forehead and cheek tattoos including the BENT cheek stripe, dark chin marking and the existing NEAR-FINAL TOOTHY GRIN. Keep the grin exactly its existing size; no changes to head/face/eyes. Do not move, shrink, enlarge or reshape any hand or body part. Native 1672x941 frame and original crop.
Add a HUGE DENSE red-flame mass wrapping the ENTIRE punching-fist perimeter and streaming along its forearm with long tails out toward LOWER RIGHT. Broad layered vigorous anime cel sheets with jagged split pointed tips, deep dark-crimson outside, saturated scarlet/vermilion middles and warm pale cream/peach cores. Large broad fire volume, not vines, thin ribbons or outline. Keep most mass around/behind fist, with a few narrow pointed foreground flames across lower knuckles while clear fingers and thumb stay readable. C08's distinct burning phase: one wide turbulent upper-left plume with three shorter tearing tips, a countercurl just below the guard wrist beside the main fist, a broken crescent of fire below the thumb, and two very long lower-right streams plus shorter flicking side flames. Preserve generous overall volume but let green gaps divide some tips.
Protect ALL FACE and HAIR from fire. Eyes, grin, cheek stripe bend and chin mark must remain clearly visible; the upper fist flames bend sideways away from chin and stop below the chin marking, without red haze/tint across face. Keep original vivid uniform GREEN chroma-key backdrop. No black background, no transparency, no new objects, text, watermark, bloom, blur or relighting. Output one edited paired frame.
```


## C_bg 背景

参考 B_bg.png 的夜街画风与配色，生成反向构图。

Use case: illustration-story.
Asset type: anime animation background plate C_bg, landscape 1672x941 native requested.
Reference image is approved background B_bg: use it for the same Tokyo-like night street, lighting, architecture vocabulary and hand-painted anime art direction. Generate the REVERSE direction down this SAME street, as if the low camera turned 180 degrees for a reverse shot. Do not simply mirror or duplicate the reference skyline.
Composition: very low camera looking upward between tall modern mid-rise and high-rise office blocks, strong converging building verticals, broad deep-blue cloudy sky occupying the central upper half. New arrangement of buildings: tall narrow glass office tower offset toward upper right, a shorter stepped concrete building at left, smaller distant blocks at bottom-center. Keep center readable for a large foreground punching character that will be composited later. No foreground objects through the middle.
Style: crisp drawn architectural contour lines and anime-painted flat/soft brush shading, dark desaturated navy and blue-gray façades, sparse warm amber office windows, a few small warm streetlights near lower corners, deep midnight clouds with restrained hand-painted edges. Match reference exposure/color weight. Not photoreal, no 3D render.
Clean background only, no people or characters, no fists, no fire or aura, no green screen, no text, signs or watermark.


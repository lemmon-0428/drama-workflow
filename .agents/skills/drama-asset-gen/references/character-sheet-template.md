# 角色设计参考表 · 参数化模板（③ drama-asset-gen 用）

> 把单张立绘升级成**多面板角色设计参考表**。`{占位}` 由 `bible.assets[].intent.sheet_spec` 字段填充；
> 同阵营新角色走**编辑模式**（`ref` 传首角色的 sheet）+ 阵营差异化表，保视觉家族一致、又有个体区分。
> 输出画幅 **9:16 竖版**（人物），最高分辨率。生成走 `generate_images.py`（micu→packy→moyu）。

## 为什么是多面板（关键设计）
- **正脸 / 侧脸 / 无脸全身 / 背面** 四格 → 给下游（草图板、视频）多角度锚定，一致性远强于单张。
- **"无脸全身"面板专门不露脸** → 将来换脸编辑时这张不受影响（身材/服装/装备/义肢的纯净参考）。
- 所有面板**同一纯色棚背景 + 同一单边轮廓光** → 像真实造型手册。

## 模板（填好 {占位} 后即 prompt 全文）

```
A character design reference sheet. **Vertical 9:16 aspect ratio. Maximum resolution output.** Pure solid {背景色：neutral light-warm-grey} studio backdrop. {灯光：Single-sided side-rim backlighting from camera-right at 45 degrees behind the subject, no fill light, no front light}—dramatic cinematic studio lookbook lighting.

【Layout】
2x2 grid with unequal panel heights: top row two smaller panels (head/face close-ups, ~1/3 canvas height each); bottom row two larger panels (full body, ~2/3 canvas height each). Thin neutral light-grey dividing lines. All four panels share the same backdrop and lighting.

【4 Panels】
Top-left — FRONT FACE CLOSE-UP: tight close-up of {角色} face (collarbone up), facing camera directly, both eyes visible, {表情/视线}. Face fully visible (headwear pulled down, not covering nose/mouth).
Top-right — SIDE FACE CLOSE-UP (PROFILE): pure side profile (collarbone up), facing camera-right, rim-light silhouettes the profile; {发型/发饰} catch the rim light. Face fully visible.
Bottom-left — FULL BODY FRONT, NO FACE: collarbone-down to feet, facing camera. **Face/head cropped OUT at top of panel** — only neck/shoulders/torso/arms/hips/legs/feet visible (survives future face-replacement edits). Shows body proportions, costume, equipment, weapons, {独特改造/义肢}.
Bottom-right — FULL BODY BACK VIEW: head to feet, facing away from camera (back of head + {背面装备：背挂武器/战利品} visible).

【Subject — same character across all 4 panels】
A {性别} {身份/职业 archetype}, of {阵营/部族/组织}. Overall aura like {核心气质：老练战士/皇家护卫/沙漠猎人…}.

【Character Core】
Age ~{年龄范围}. Physique: {体型：lean wiry athletic / stocky chunky / lean tall …}. NOT {不想要的体型}. Presence: {气质：捕食者般警觉/疲惫老兵/贵族克制…}. Body language reads as "{一句角色印象}".

【ETHNICITY — CRITICAL】
{民族/地域：例 Central Asian Turkic/Sogdian Silk Road 杂胡}. Specific:
- Cheekbones/jaw: {骨相}
- Eyes: {眼型/眼神/眼色，例 deep-set almond, black eyes, NOT round Western double-fold}
- Hair: {发色/发质}
- Skin: {肤色/风化，例 weathered tan-bronze}
- Nose: {鼻梁/侧面轮廓}
- Brows: {眉}
- Skin detail: {年龄纹/日晒纹/伤疤}

【Face Detail】
Face {完全可见/部分遮挡}. Scars/marks/tattoos: {伤疤位置+纹身}. Expression: {表情}. Eye-line: {视线}.

【Hair】 {长度/颜色/质感/发型} + {发饰：编发/饰珠/金属环/布条}.
【Headwear】 {头盔/兜帽/头巾/无} + {材质/磨损/佩戴}; face-visible rule: {脸完全可见/只露眼睛}.
【Upper body】 {上装类型+材质}, state {风化/战损/仪式/干净}, exposes/covers {手臂/躯干}, details {绑带/护甲片/纹身/工具袋}.
【Lower body】 {下装+材质} + {腰带/小袋/枪套/护符}.
【Unique body / mod】 {机械义肢/赛博眼/动物特征/无}: {位置/材质/颜色/构造/磨损}. NOT {不想要风格}, must be {想要风格，例 desert blacksmith salvage, NOT precision cybernetic}.
【Weapons】 Primary {主武器}; secondary {副装备}; ranged {远程}. 都匹配角色文化身份。

【Color Palette】 主色{}；点缀{}；材质色{皮革/青铜/钢/丝/骨}；氛围{低饱和沙漠/冷峻帝国…}；all materials {风化/抛光/覆尘/战损}.

【Pose — same across all 4 panels】 {站立/备战/放松站姿}, body {正面/3-4角度}, hands {靠近武器柄/拿道具/抱臂}. NOT 诱惑/时装模特/过度攻击姿势。

【Critical consistency】 SAME individual in all 4 panels — identical face structure, identical scars, identical hair, identical clothing items in identical positions, identical weapons in identical mounts, identical {义肢}, identical trophies. Same backdrop, same rim-light setup.

【Lighting — critical】 {单边轮廓光 from camera-right 45° behind, NO fill, NO front, NO ambient}. Edge-light catches one side, deep falloff shadow on the other. Cinematic high-end lookbook (Peter Lindbergh / Annie Leibovitz single-rim). Backdrop evenly lit.

【Style】 Hyperrealistic photographic character design rendering — shot like a practical costume in a film production studio for a cinematic lookbook board. NOT illustration, NOT 3D CGI, NOT anime. {族群准确性参考片：例《长安十二时辰》西域狼卫 / Mongol(2007)}. Light Kodak Vision3 35mm film grain.

【Quality】 Maximum resolution, 8K ultra clean, sharp edges. Every {绑带/伤疤/缝线/护甲片/首饰/武器/机械螺栓} clearly defined. Real physical costume photography aesthetic.

【Panel Labels】 small clean monospace black text under each: "FRONT FACE" / "SIDE FACE" / "BODY FRONT (NO FACE)" / "BACK".
Title at top center (small clean black sans-serif): "{角色名} — {形态/版本} CHARACTER SHEET".

【Constraints】
- Ethnicity (CRITICAL): MUST be {目标民族}; NOT {不想要民族/欧美脸/纯汉脸/K-pop/动漫脸/网红脸}.
- Body & costume: {体型约束}; NOT slender model-thin, NOT voluptuous, NOT seductive, NOT teen (must be {年龄}).
- Aesthetic: NOT {不想要风格清单：CGI/卡通/动漫/cosplay/廉价游戏女武神/干净抛光/霓虹赛博…}; weathered patina only; muted {色系} only.
- Layout & lighting: MUST be 9:16; top row smaller / bottom row larger (NOT equal); face cropped OUT in BODY-FRONT panel; face fully visible in face panels (NOT covered); solid {背景色} only; single-side rim backlight only (NO front/fill/even light); NO text other than the 4 panel labels + title.
```

## 由 bible 哪些字段填（②↔③ 契约）
`{占位}` 来自 `bible.assets[].intent.sheet_spec`（②写）。sheet_spec 建议字段：
`ethnicity / physique / aura / face{cheekbones,eyes,hair,skin,nose,brows,skin_detail} / scars / hair / headwear / upper / lower / mod / weapons{primary,secondary,ranged} / palette / pose / lighting / style_ref / anti（反例清单）`。
+ 顶层 `factions[]`（同阵营差异化表）给同阵营角色逐维度区分。

## 同阵营编辑模式（保家族感）
出完阵营首角色（如沙猎钩索手 A）后，新角色（弓箭手 C）走 `generate_images.py` **编辑模式**：
- `ref` 传 A 的 sheet 图；prompt 用本模板填 C 的 spec，**开头加一句**"继承参考图的画风/打光/棚拍格式/阵营美学家族，仅按下文替换为本角色的体型/发须/服装/武器/装备"。
- 用 `factions[]` 差异化表确保 C 与 A/B 在 性别/年龄/体型/发须/服装/signature装备/武器/战利品/气质 上**逐维度可区分**。

## 跑出来重点检查（自检）
族群准确（不跑成欧美/纯汉/动漫脸）；9:16 + 四格不等大 + 最高分辨率；**左下 BODY-FRONT 不露脸**；体型对（不胖不模特瘦）；signature 装备在对应面板可见；同阵营角色逐维度区分到位；单边轮廓光（无正面/补光）；除 4 标签+标题无多余文字。

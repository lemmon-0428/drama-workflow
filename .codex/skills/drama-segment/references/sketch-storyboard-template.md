# 草图分镜板 · 参数化模板（④ drama-segment 用，核心）

> 每个 segment 一张**手绘铅笔分镜板**：N 格 = 段内 N 镜（外加 1 格 Shooting Plan），
> 每格画该镜的构图/机位/动作，红笔标运镜/硬切/whip pan，caption 写 焦段/SFX/台词/动作。
> 这是给 Seedance 的**显式分镜引导**——让它一次生成段内多镜+硬切而不形变。
> 网格 ≈ 镜数：2x2=3镜+plan / 2x3=5镜+plan / 3x3=8镜+plan。画幅 16:9（或 21:9 多镜）。
> 后续会补更多板型（whip-pan 板 / reaction-beat 板 / 单镜大板…），先用此通用版。

## 纸张：用干净白纸，别用做旧牛皮纸（重要）
草图板**只承担构图/调度/硬切引导**，纸张质感是装饰、对引导 SD2 无价值；而**做旧泛黄/牛皮纸色有偏色污染风险**——SD2 可能把它当风格参考、把暖黄复古色带进视频。配色应**只由色卡**决定。所以草图板一律用 **clean pure white storyboard paper**（铅笔灰阶画明暗，纸保持纯白），明暗对比靠 graphite cross-hatch 表现，不靠纸色。

## 全局设置（每张板都带）
```
A hand-drawn pencil sketch storyboard on CLEAN BRIGHT NEUTRAL-WHITE storyboard paper — pure white drawing paper, NO aging, NO yellowing, NO kraft/sepia tone, NO paper texture, NO smudges, NO edge wear. Tonal contrast rendered ONLY in graphite greyscale (cross-hatch for shadow, untouched white paper for highlight); the paper stays pure white — do NOT tint it. In the style of professional film production storyboards. Total image aspect ratio strictly {16:9 或 21:9}.

Layout: {2 columns x 2 rows / 3x2 / 3x3} grid on aged paper. Cells: {Panel 1..N + Shooting Plan in last cell}. Each storyboard panel strictly 16:9 with thick hand-drawn black ink frame border. The Shooting Plan cell is a top-down bird's eye of {场景} with camera positions + 180-degree axis line.

Beneath each panel inner frame: a hand-lettered caption strip (panel#, lens, shot type, brief SFX/action) in serif block letters slightly uneven.

DRAWING TECHNIQUE: loose graphite pencil, confident architectural perspective, clear cinematic composition; gestural but every spatial relation + prop clearly readable. Red colored pencil ONLY for movement arrows, force vectors, camera triangles, key dramatic beats.

LIGHTING (all panels): {本段光：如 late afternoon golden hour, low sun from upper-left 30°}. Dense cross-hatching for shadow base; bright untouched paper for sun-key highlights + rim-lit silhouettes. Strong tonal contrast — NOT evenly lit.

Style refs: Hollywood film storyboards, Mad Max Fury Road action boards, animator pre-vis.
Drawing rules: graphite pencil line + greyscale tonal shading on CLEAN PURE WHITE paper (NO aging/yellow/kraft/texture/smudge); black ink for borders + captions; red pencil ONLY for arrows/emphasis/camera triangles/force vectors/180° axis; cross-hatch shading, untouched white-paper highlights; hand-lettered serif captions slightly uneven.

DIRECTIONAL AXIS RULE: {本段 180°轴：动作轴从 X 到 Y，cameras stay on one consistent side throughout}.

Title at top center, hand-lettered block serif: "{剧名} {集} — {段} — {段标题}"
Subtitle: "{镜数} SHOTS / {硬切数} HARD CUTS{+ whip pan 等} / {场景} / {一句话节拍}"
```

## 每格镜头（逐镜重复，按段内镜序）
```
PANEL {i} ({位置 top-left…}) — SHOT {i}: {机位角度} / {一句话戏}:
Scene composition: {景别} framing. {构图：off-axis/rule-of-thirds/diagonal，主体在画框哪侧，绝不正中对称}.
{出场主体在本镜的局部可见性：谁全身/谁半身/谁只露局部/谁不入画——精确到"江流只在左边缘露躯干+手臂、头不入画"}.
{每个主体：参照角色表的外观特征简画(发须/服装/义肢/武器)，标明姿态动作}.
ACTION: {本镜动作，含末尾的转折/运镜起点，如 "拉出邀请函→举向画外右上的刘回"}.
Background: {背景地标(取连续性锚)+大气(尘/雾)+景深}.
Lighting: {方向光打哪个边缘 rim-light，对侧 cross-hatch 阴影}.
Red pencil annotations: {机位三角(标角度/焦段)+运动箭头(标动作/运镜)+视线虚线(标谁看哪)+情绪节拍标注}.
Caption: "SHOT {i} / PANEL {i} — {景别}{机位} / {一句戏} / {焦段}mm / {机位运动：static+micro-shake / handheld / whip pan ~0.5s} / SFX: {音效} / {角色}: '{台词原文}' / ACTION: {动作}"

{若本镜后是硬切：}**HARD CUT.**
{若是 whip pan 转下镜：红笔在两格间标 "WHIP PAN ~0.5s from {上镜}'s POV"}
```

## Shooting Plan 格（最后一格）
```
SHOOTING PLAN ({位置 bottom-right}) — TOP-DOWN BIRD'S EYE:
Top-down schematic of {场景} floor. Environmental anchors as labeled outlines ({地标}). Each character as a top-down figure-outline + name label ({各角色位置/朝向/姿态；躺着画横向；小动物画小}). {镜数}个红三角标 S1/S2/S3 机位(各镜机位+焦段/景别)。红 curved arrow 标运镜路径(whip pan/dolly)。红 **180-degree axis line**。红 dashed sight-lines 标视线/台词朝向。Hand-lettered labels: "S1/S2/S3 CAMERA POSITIONS"、各角色名、"180° AXIS"、"{运镜} PATH"。
Caption: "SHOOTING PLAN — {镜数} shots on {场景} / {哪些是硬切 哪些是运镜} / 180° axis preserved"
```

## 硬约束（每张板都带）
```
- CLEAN PURE WHITE paper (NO aging/yellow/kraft/texture/smudge — avoid color contamination of the video; color is the color-card's job); graphite pencil line + greyscale tonal shading; black ink borders+captions; red pencil ONLY for arrows/emphasis/camera triangles/force vectors/180° axis/final-frame
- Hand-lettered serif captions slightly uneven, readable not machine-printed
- Each panel strictly 16:9; total image strictly {16:9/21:9}; {网格} grid
- Strong golden-hour high-contrast: dense cross-hatch shadows + bright untouched paper highlights, NOT evenly lit
- NONE of the panels use centered symmetric composition (all off-axis)
- {逐角色一致性约束：取角色表关键特征，如 "刘回: 短刺黑发+额前发绳+右眼眼罩+右臂机械义肢+裸上身部族纹身"}
- {本镜特定约束：如 "江流 panel1: 平躺仰面(face-up supine)、只左边缘露部分躯干、头不入画"}
- 180° axis preserved; {whip pan/硬切标注} in red pencil
- NO digital painting, NO 3D render, NO photographic elements, NO color overlays except red pencil
```

## 怎么填（④ 自己定 + 取上游）
- 网格/镜数：本段 4a 分镜的镜数（+1 plan 格）。
- 每格戏/机位/动作/台词：4a 分镜。
- 每个主体的外观简画 + 一致性约束：取 ③ 角色表的关键特征（发须/服装/义肢/武器）。
- 地标/连续性锚：取 bible 场景 spec。
- 180°轴/硬切/whip pan：4a 的机位设计。

## 自检
网格=镜数(+plan)、每格构图 off-axis 不正中、每个主体局部可见性精确、红笔机位/运镜/硬切/whip pan/180°轴标清、caption 含焦段/SFX/台词原文/动作、逐角色一致性约束取自角色表、纯铅笔+红笔+黑墨、纸张做旧、16:9。

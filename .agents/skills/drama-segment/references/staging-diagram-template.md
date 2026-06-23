# 俯视 Staging 图 · 参数化模板（④ drama-segment 用）

> 每个 segment 一张**俯视(bird's eye)站位图**：手绘铅笔、红笔标机位/运镜/视线/180°轴。
> 它是导演的"调度蓝图"——把"谁站哪、机位在哪、镜头怎么走、轴线在哪"画清楚，
> 供草图分镜板和视频生成对齐空间。画幅 **16:9**。多人/复杂调度的段才需要（单人简单段可省）。

## 模板（填好 {占位} 即 prompt 全文）

```
A hand-drawn top-down bird's eye view blocking diagram on aged off-white paper, in the style of a professional film production staging diagram. Image aspect ratio strictly 16:9 horizontal landscape format.

Layout: top-down schematic floor plan of {场景：如 ship deck / 苏家小院 / 商场} local area, in confident graphite pencil with selective red colored pencil annotations. Aged off-white paper with slight edge wear and faint smudges (heavy production use).

Title at top center, hand-lettered confident block serif: "{剧名} {集} — {段} — STAGING DIAGRAM"
Below title, smaller subtitle: "{场景} BLOCKING / {人数}人 + ENVIRONMENT ANCHORS / {机位运镜一句话}"

DRAWING TECHNIQUE: confident graphite pencil, clear top-down perspective, cross-hatching where appropriate. Red colored pencil ONLY for camera positions, motion vectors, character labels, sight-lines, reveal path. Hand-lettered labels in slightly uneven serif block letters.

THE DIAGRAM:
Main: top-down view of {场景} floor occupying most of the space, subtle {地面纹理：deck planks/泥土院/瓷砖} lines.

Environmental anchors (top-down silhouettes + labels):
{逐条列本段地标：如 "MAIN MAST / 主桅杆" 粗圆柱、"BRONZE SHIP WHEEL / 青铜船舵" 带辐条圆、rope coil、railing… 用 bible 场景里的固定元素，作连续性锚}

Character positions (each a top-down figure-outline silhouette + name label):
{逐条列本段出场角色：位置(前景/中/上右…) + 朝向 + 关键姿态。如 "苏父 (前景, 挑扁担)" / "苏小七 (侧后, 跟随)"。躺着的画成横向轮廓并标 head/feet；体型差异要画出（小动物画小）}

Camera positions + path:
- Red camera triangle at START: {起始机位+朝向+焦段}, label "CAMERA START / {景别} / {焦段}"
- Red camera triangle at END（如有运镜）: {结束机位}, label "CAMERA END / {景别}"
- Red CURVED ARROW from start to end（如有运镜）: smooth curve, annotations along it "{dolly back / pan / tilt / whip pan}", label "{运镜名} PATH"
- {若多镜硬切：每镜一个红三角标 S1/S2/S3 机位}

180° axis + sight-lines:
- Red **180-DEGREE AXIS LINE**: {画出动作轴线，标 cameras stay on one side}
- Red dashed sight-lines: {谁看谁/台词朝向，如 "副手台词→老大 '老大,那小子怎么办?'"}

Final frame note: red dashed rectangle = final master frame, label "FINAL FRAME / off-axis, NOT centered".
Legend (lower-left): "S=start cam / E=end cam / dashed red=sight-lines / curved red=camera path / red line=180° axis".
Production note (bottom margin): "{剧名}/{集}/{段} — {一句话戏} / {运镜风格} / continuity: {接上下段}".

Hard constraints:
- Aged off-white paper, pencil graphite base, black ink title/labels, red pencil ONLY for cameras/path/sight-lines/axis/final-frame
- Hand-lettered serif, slightly uneven, readable; strictly 16:9; TOP-DOWN bird's eye (all figures as silhouettes from directly above)
- {体型差异：小动物/孩子画得比成人小}; 躺着的角色画横向(非站立); 关键地标形状画准(船舵带辐条等)
- camera path = one smooth curved arrow (not multiple); NO digital painting/3D/photo; NO color except red pencil
```

## 怎么填（④ 自己定 + 取 bible）
- 场景/地标：取 bible 场景 spec 里的固定元素（作跨段连续性锚）。
- 角色位置/朝向/姿态：本段 4a 分镜定的站位。
- 机位/运镜/轴线/视线：本段 4a 的机位设计（whip pan / dolly / 硬切各镜机位）。
- 多镜段：每镜一个 S1/S2/S3 机位三角 + 180°轴线，标清各镜在轴的哪一侧（防跳轴）。

## 自检
俯视视角、地标形状准、体型差异画出、躺着画横向、机位/运镜/180°轴/视线红笔标清、16:9、纯铅笔+红笔、连续性锚（地标）在。

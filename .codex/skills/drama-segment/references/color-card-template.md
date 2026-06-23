# 色卡（13色）· 参数化模板（④ drama-segment 用）

> 每个 segment 一张**电影级色卡**（13 色 HEX 调色脚本），锁定该段场景的配色。
> 下游 ⑤ 视频生成时把它当**配色参考**（资产给外观、草图板给构图、色卡给配色）。
> 画幅 **16:9**，纯白底、扁平色块、HEX 精确。色值来自 bible `style_lock` 调性 + 本段场景/资产的材质色。

## 模板（填好 {占位} 即 prompt 全文）

```
A professional 13-color palette design sheet for film production, in the style of a cinematographer's color script reference card. Image aspect ratio strictly 16:9 horizontal landscape format.

Layout: pure clean off-white background. Centered at top: large bold black sans-serif title "{剧名} {集} {段} - {本段一句话} - 13 COLOR PALETTE" in clean industrial typography.

Below the title: 13 vertical color swatch bars in a single horizontal row, evenly spaced, each a tall vertical rectangle of flat solid color, crisp clean edges, no gradient/texture inside. All 13 same size, same baseline.

Below each swatch, two lines: Line 1 color name (clean bold sans-serif uppercase); Line 2 HEX code (monospace).

The 13 colors in left-to-right order with exact HEX values and labels:
1. {色名1} / {#HEX1} ({用途1})
2. {色名2} / {#HEX2} ({用途2})
3. {色名3} / {#HEX3} ({用途3})
4. {色名4} / {#HEX4} ({用途4})
5. {色名5} / {#HEX5} ({用途5})
6. {色名6} / {#HEX6} ({用途6：通常 golden-hour/晨光 direct light tint})
7. {色名7} / {#HEX7} ({用途7：通常 shadow 冷调})
8. {色名8} / {#HEX8} ({用途8})
9. {色名9} / {#HEX9} ({用途9})
10. {色名10} / {#HEX10} ({用途10：通常 dust/haze 大气})
11. {色名11} / {#HEX11} ({用途11：高光})
12. {色名12} / {#HEX12} ({用途12：暗部})
13. {色名13} / {#HEX13} ({用途13：deep black 暗部锚})

Each swatch must render the exact HEX with full fidelity — flat solid, no shading/gradient/texture. Labels perfectly readable.

Hard constraints:
- All 13 swatches exact HEX-accurate flat solid colors
- Strictly 16:9; white/off-white pure background; NO illustrations/photos/sample scenes
- Clean sans-serif labels fully readable; single horizontal row even spacing; each swatch tall vertical rect crisp edges
- No watermarks/decorations; title is largest text
- Feels professional production-grade (Adobe Color / Pantone × film color script)
```

## 13 色怎么定（②↔④ 契约）
按"光 + 主体 + 材质 + 暗部"四类凑 13：
- **光**（2-3）：直射光暖调（黄昏#F0B670/晨光）、阴影冷调（#4A5870）、大气尘霾（#C0B299）
- **场景主色**（2-3）：本段场景的天/地/墙主色（取 bible 场景 spec）
- **主体材质色**（3-5）：本段出场角色/道具的关键材质（皮革/青铜/布料/金属，取角色表 palette）
- **奇幻/特征色**（1-2）：本剧标志色（如步步生金的系统HUD 金#FFD…/青）
- **暗部锚**（1）：deep black #1A1610 类

不够 13 就补材质细分（高光/暗部各一），多了就合并。HEX 尽量复用 bible/角色表里已定的材质色，保跨段一致。

## 自检
13 块、HEX 精确扁平、纯白底无插画、16:9、标签可读、无多余文字；色值与本段场景+出场资产材质对得上、与 STYLE LOCK 调性一致。

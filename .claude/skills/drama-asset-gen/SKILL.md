---
name: drama-asset-gen
description: >
  短剧流水线第④步（拆解→设定→分镜头→资产）。读 bible（设计）+ 分镜头（需求/站位），调用多渠道 gpt-image-2
  生成两类资产：①库资产——人物定妆照 / 场景空镜 / 形象变体，跨集复用、台账追踪；②分镜头站位合成图——把场景板 +
  相关人物参考图用图生图合成每一镜的站位画面。当用户要"生成人物/场景资产、角色定妆照、场景图、
  角色变体/换装图、分镜头站位图 / 合成镜头画面 / 出每个镜头的画面"时触发；即使只说"出几张资产图"也用。
  设计（造型/五官锚/画风）来自 bible，不在本 skill 里重新设计。
---

# Drama Asset Generator（资产生成）

把 `drama-bible` 的设计和 `drama-storyboard` 的镜头需求，渲染成两类图片资产，并跨集统一管理。**设计已在 bible 定好**，本 skill 只负责"按设计出图 + 复用追踪 + 按镜头合成站位"。流水线契约见 `docs/流水线设计.md`。

## 输入
- `docs/scripts/<剧名>/bible/bible.json`——设计源（角色 `identity_anchor`/`outfit_prompt`/looks、场景 looks、全剧 `style`）
- `docs/scripts/<剧名>/<集>/分镜头.json`——需求源（哪些角色/场景/look 出现、每镜站位）。做库资产可只用 bible；做站位图必须有它
- `docs/scripts/<剧名>/assets/`——已有库资产 + 台账

## 输出
```
docs/scripts/<剧名>/assets/
├── characters/  scenes/  props/        4a 库资产： <id>.png · <id>__<look>.png
├── shots/<第N集_集名>/<镜号>.png        4b 站位合成图
├── asset_registry.json                 库资产台账（唯一事实来源）
└── 角色形象卡.md                        派生人读视图
docs/scripts/<剧名>/<集>/资产清单.md     本集复用/新增清单（人读）
```
站位图状态回写到 `分镜头.json` 每镜的 `shot_image`，不进库资产台账。

## 画风
从 `bible.json.style` 读，全剧统一套用。`references/character-prompt-standard.md` 以写实为基准；非写实就替换渲染描述词，保留其余硬标准（全身正面/纯白底/均匀柔光/无文字）。

## 两类资产 + 先后

**4a 库资产**是"一致性锚点"（人物定妆照、场景空镜、形象变体），跨集复用；**4b 站位图**是每镜的合成画面，**用 4a 的图当参考**。所以 **4a 必须先于 4b**。

## 三种模式（库资产，默认 B）

| 触发 | 模式 | 做什么 |
|------|------|--------|
| 默认（"给第N集出资产"） | **B 增量** | 只补本集分镜头用到、但库里还没有的资产 |
| "只盘点/规划全剧资产" | **只读规划** | 出/更新 `资产规划表.md`，不生成 |
| "把整部剧资产都生成" | **A 全量** | 规划 → 展示待生成数量 → 确认后批量（base 先行→锁脸→变体） |

A 即使被显式要求也先出清单+数量、确认再开批。

## 工作流程 4a：库资产

1. **加载**：`bible.json`（设计）+ `assets/asset_registry.json`（已有）。
2. **算需求**：从本集 `分镜头.json` 收集出现的 `(角色id, look)` 和 `(场景id, look)`（A 模式则取全剧）。
3. **去重分类**：每个 (id, look) 比对台账 → 复用 / 新增base / 新增变体。只有新增/变体要出图。
4. **组提示词**：
   - 人物：读 `references/character-prompt-standard.md`。提示词 = bible 的 `identity_anchor`（**逐字复用锁脸**）+ 该 look 的 `outfit_prompt` + 定妆硬标准（9:16 1088x1920、全身正面、纯白底、no text…）。
   - 场景：读 `references/scene-prompt-standard.md`（16:9 1920x1088、默认空镜、剧本写了人/文字才保留）。
   - 变体：走**编辑模式**，`ref` 传 parent look 的图，图生图锁一致性。
5. **确认**：展示本集清单（复用 vs 新增，变体注明 parent+原因），写 `<集>/资产清单.md`；用户已明确要生成就直接继续。
6. **base 先行 → 锁脸检查点 → 再出变体**：先生成新 base，给用户确认五官 OK，再出依赖它的变体。
7. 调脚本（见下），更新台账，重生成 `角色形象卡.md`。

## 工作流程 4b：分镜头站位合成

前提：本集库资产已齐（4a 完成）。对 `分镜头.json` 里每个（或用户指定的）镜头：

1. **取参考图**：`scene.id+look` 的场景板 + 每个 `characters[].id+look` 的人物图（都从 `assets/` 取路径）。
2. **写合成提示词**：用该镜的 `画面 + 景别 + 机位 + 镜头运动 + 每个角色的站位/动作` 组织一句"把这些人物按此站位放进这个场景、此景别构图"的指令（英文），末尾 no text/no watermark。
3. **调脚本编辑模式**：`ref` = [场景板, 人物A, 人物B…]（packy/moyu 的 edits 最多 16 张参考图），输出到 `assets/shots/<集>/<镜号>.png`。
4. **回写** `分镜头.json` 该镜 `shot_image` = 路径 + 成功状态。

站位图默认 16:9 `1920x1088`（成片画幅）。

## 脚本用法（多渠道 + 生成/编辑）

`scripts/generate_images.py` 串行逐张，渠道失败自动回退：默认 `micu → packy → moyu`（`IMAGE2_PROVIDER_ORDER` 可覆盖）。环境变量放 ~/.zshrc，**不进仓库**：`IMAGE2_API_KEY/BASE_URL`、`PACKY_API_KEY/BASE_URL`、`MOYU_API_KEY/BASE_URL`。

```bash
python .claude/skills/drama-asset-gen/scripts/generate_images.py \
  --tasks '<tasks_json>' --output-dir 'docs/scripts/<剧名>/assets' \
  --episode '<集目录名>' --drama '<剧名>' --style '<画风>'
```

task 字段（`ref` 给了就走编辑/图生图；4a 变体和 4b 站位图都用它）：
```json
{ "name": "navigator_k__chest_reveal", "category": "character", "size": "1088x1920",
  "prompt": "<identity_anchor 逐字 + 变化造型 + 硬标准>",
  "char_id": "navigator_k", "look": "chest_reveal", "parent": "default",
  "identity_anchor": "<五官锚>", "display_name": "领航员K", "design": "<摘要>",
  "quality": "medium", "ref": ["characters/navigator_k.png"] }
```
站位图 task：`category` 设为 `"shot"`、`name` 用镜号、`size` 默认 `1920x1088`、`ref` 传 `[场景板, 人物A, 人物B…]`，运行时配合 `--episode <集目录名>`。脚本会把它落到 `shots/<集>/<镜号>.png` 且**不写入库台账**（台账只记库资产）。出图后由本 skill 把路径回写到 `分镜头.json` 对应镜的 `shot_image`。示例：
```json
{ "name": "2-001", "category": "shot", "size": "1920x1088",
  "prompt": "Compose a film still: place the navigator on the right seated on the high platform and the old man entering from the left, medium-wide eye-level shot inside this hall…, no text, no watermark",
  "ref": ["scenes/noah_ark_interior_hall.png", "characters/navigator_k.png", "characters/old_man.png"] }
```
packy/moyu 按 gpt-image-2 约束校验尺寸（≤3840px、16倍数、≤3:1、像素65万~829万）。

脚本合并更新 `asset_registry.json`（记 `provider`/`mode`/`first_episode`/追加 `used_by`，保留手工字段）。

## 台账与人读视图
- `asset_registry.json`：库资产唯一事实来源（扁平 looks 模型：`name/category/char_id/look/parent/identity_anchor/display_name/path/size/provider/mode/status/first_episode/used_by/prompt`）。
- `角色形象卡.md`：从台账派生（每角色：五官锚 + 各 look + 图路径 + 用在哪几集）。
- `<集>/资产清单.md`：本集复用 + 新增。

## 尺寸
| 类型 | 默认 | 说明 |
|------|------|------|
| 人物库资产 | 1088x1920 (9:16, ≈1080p) | 竖版全身定妆照 |
| 场景库资产 | 1920x1088 (16:9, ≈1080p) | 横版空镜 |
| 站位合成图 | 1920x1088 (16:9) | 成片画幅 |
| 道具 | 1024x1024 | 正方形 |

三渠道均支持上述尺寸（packy/moyu 满足约束即可，micu 走固定枚举）。

## 质量自检
- 库资产：本集分镜头用到的 (id,look) 都已"复用或新增"，没有遗漏；变体五官锚逐字复用 + 用 parent 图做 ref。
- 站位图：每个处理的镜头有 `shots/<集>/<镜号>.png`，`分镜头.json` 的 `shot_image` 已回写。
- 4a 先于 4b；图都目检过（全身/纯白底/无文字；空镜该空；站位图人物站位与分镜头一致）。
- 台账、形象卡、资产清单已更新。
- 报告：本集 新增/复用/变体/站位图 数量、失败项、路径。

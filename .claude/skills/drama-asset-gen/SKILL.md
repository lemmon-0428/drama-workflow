---
name: drama-asset-gen
description: >
  短剧流水线的资产生成环节（**前移到分镜之前**）。直接读 `bible.json`（按 `planned_episodes` 含本集的资产算需求），
  调多渠道 gpt-image-2 出三类**库资产**：①**多面板角色参考表**（4格：正脸/侧脸/无脸全身/背面，9:16，按 bible
  `intent.sheet_spec` 填模板；同阵营靠同模板+同lighting+`factions[]` 差异化表保家族一致又可区分，视觉相近阵营可叠编辑模式）；
  ②场景板（16:9）；③道具图（1:1，含需中文 HUD 等特殊项）。跨集复用、台账追踪、单资产重做。
  当用户要"生成人物/场景/道具资产、角色参考表/设计表、角色变体、场景图、道具图、重做某张资产"时触发。
  设计（族群/骨相/造型/打光/画风）来自 bible，本 skill 不重新设计。**不再产站位图、不再产资产绑定.json**（那两件已移交下游分镜环节）。
---

# Drama Asset Generator（资产生成 · 多面板角色参考表）

读 `bible.json`，把全剧设计的"意图层"落成真实图片库：**多面板角色参考表 / 场景板 / 道具图**，跨集复用、台账追踪。本环节**前移到分镜之前**——下游的草图分镜板要画已生成的角色参考表来保长相一致。设计已在 bible 定好，本 skill 只负责"按设计出图 + 复用追踪 + 待补兜底"，不重新设计五官/造型/画风。流水线契约见 `docs/流水线设计.md`。

> **本版变化（相对旧版）**：人物从"竖版单张定妆照"升级为**多面板角色设计参考表**（references/character-sheet-template.md，占位由 bible `intent.sheet_spec` 填）；同阵营靠**同模板+同lighting+`factions[]` 差异化表**保家族一致（视觉相近阵营可叠编辑模式）；需求来源改为**直接读 `bible.json`**（按 planned_episodes 算）；**删除旧站位图合成（旧 `shots/` / `category:shot`）与 `资产绑定.json` 的产出**——这两件由下游分镜环节（草图分镜板 + 资产绑定）接管。

## 输入
- **`docs/scripts/<剧名>/bible/bible.json`——设计与需求的唯一来源**：
  - 扁平 `assets[]`，每条：`ref_token`、`display_name`、`category`(character|scene|prop)、`id`、`look`、`status`、`intent`、`intent.planned_episodes`。
  - 人物 `intent.sheet_spec`——**多面板参考表的结构化字段**（族群/骨相/眼型/服装/signature 装备/武器/打光/反例…，逐字段填进模板 `{占位}`）。**注意 `lighting` 用 bible 该角色定的值**（明亮剧 = 柔和暖光，别照搬模板默认的硬 noir 单边轮廓光）。
  - 场景 / 道具 `intent.spec_prompt`——英文造型/画面描述。
  - 顶层 `factions[]`——**同阵营差异化表**（逐维度区分同阵营角色：性别/年龄/体型/发须/服装/signature/武器/气质）；编辑模式出阵营变体时据此差异化。
  - 顶层 `style_lock`（优先）/ `style`——全剧画风，统一套用。
- **`docs/scripts/<剧名>/assets/`——已有库资产 + 台账 `asset_registry.json`**：判断复用 / 新增。

> **需求口径**：本集需要哪些资产 = `bible.assets[]` 里 `intent.planned_episodes` **含本集**的那些（A 全量模式则取全剧 `assets[]`）。本环节排在分镜之前，需求直接从 bible 算，不依赖任何分镜/提示词产物。

## 输出
```
docs/scripts/<剧名>/assets/                  全剧共享资产库
├── characters/   <id>.png（多面板角色参考表）· <id>__<look>.png（造型/状态变体表）
├── scenes/       <id>.png · <id>__<look>.png（场景板 16:9）
├── props/        <id>.png（道具图 1:1，含需中文标签的 HUD 等）
├── asset_registry.json                      库资产台账（已生成层·唯一事实来源）
└── 角色形象卡.md                            派生人读视图（每角色：sheet_spec 摘要 + 各 look + 图路径 + 用在哪几集）
docs/scripts/<剧名>/<集>/资产清单.md          本集复用 / 新增清单（人读）
```
**不再产** `assets/shots/`（站位合成图）与 `<集>/资产绑定.json`——下游分镜环节产草图分镜板与资产绑定。

## 三类库资产
| 类型 | category | 画幅 | 来源字段 | 出法 |
|------|----------|------|----------|------|
| **多面板角色参考表** | character | 9:16 (1088x1920) | `intent.sheet_spec` 填 character-sheet-template | 全员文生图（同模板+同lighting保家族感）；**仅视觉相近阵营**的后续角色可叠编辑模式 |
| 场景板 | scene | 16:9 (1920x1088) | `intent.spec_prompt` | 文生图，默认空镜 |
| 道具图 | prop | 1:1 (1024x1024) | `intent.spec_prompt` | 文生图；HUD 等含中文标签的特殊项在此出 |

全部为**库资产**（一致性锚点），跨集复用。下游草图分镜板会拿这些图当参考（HUD/道具尤其要先在这里出好，下游才能画一致）。

## 四种模式（默认 B）
| 触发 | 模式 | 做什么 |
|------|------|--------|
| 默认（"给第N集出资产"） | **B 增量** | 只补 `planned_episodes` 含本集、但库里还没有的资产 |
| "只盘点/规划全剧资产" | **只读规划** | 出/更新 `资产规划表.md`，不生成 |
| "把整部剧资产都生成" | **A 全量** | 规划 → 展示待生成数量 → 确认后批量（base 先行→锁脸→变体/阵营变体） |
| "重做/调整 <某资产>" | **重做** | 见「单资产重做」 |

A 即使被显式要求也先出清单 + 数量、确认再开批。

## 工作流程
1. **加载**：`bible.json`（设计 + 需求）+ `asset_registry.json`（已有）。
2. **算需求**：取 `assets[]` 中 `intent.planned_episodes` 含本集的条目（A 模式取全部）→ `(category,id,look)` 集合。
3. **去重分类**：每个 `(id,look)` 比对台账 → 复用 / 新增 base / 新增变体。只有新增 / 变体要出图；复用的进 `--reuse` 追踪 `used_by`。
4. **按 category 组 prompt（设计逐字来自 bible，不自创）**：
   - **人物（参考表）**：读 `references/character-sheet-template.md`，把 `intent.sheet_spec` 各字段填进 `{占位}` → 即 prompt 全文。**`lighting` 用 sheet_spec 里该角色定的值**（如明亮温暖剧填柔和暖光 / 自然光，覆盖模板默认的单边硬轮廓光）；`style` 取 `style_lock`/`style`。校验：缺 `sheet_spec` 的人物 → 走「人物缺 sheet_spec 兜底」（回设定环节补，不自动生成）。
   - **场景**：prompt = `intent.spec_prompt` + `style_lock` 画风 + 硬标准（16:9、默认**空镜**无人无文字、photoreal）。场景无专用模板，直接按 spec_prompt 组。
   - **道具**：prompt = `intent.spec_prompt` + 画风。1:1。HUD 等需中文标签的：prompt 显式写出中文标签文案（如"步数 / 余额"），保证下游草图板能对上。
   - **变体**（同 id 不同 look，有 `parent`）：走**编辑模式**，`ref` 传 parent look 的图，图生图锁一致性。
5. **同阵营一致性 = 共享渲染优先，编辑模式按需（重要）**：阵营的"美学家族感"**主要靠全员走同一 character-sheet-template + 同一 `lighting` + 同一 `style_lock` + 同一棚拍格式**来保证，**不是非得编辑模式**。是否再叠编辑模式，取决于阵营成员长得像不像：
   - **视觉相近的阵营**（同制服/同盔甲/同族同体型，如一队士兵、同族喽啰）→ 后续角色走 `generate_images.py` **编辑模式**（`ref` 传首角色参考表图），prompt 开头加"继承参考图的画风/打光/棚拍格式/阵营美学家族，仅按下文替换本角色的体型/发须/服装/装备/气质"，能更强锁住家族感；`factions[]` 差异化表保证逐维度可区分。
   - **视觉差异大的阵营**（如一个家庭：少女/跛脚老汉/壮实妇人/粗壮农夫——性别·年龄·体型全不同）→ **不要编辑模式**（ref 某成员会把其脸/体型串味到另一个），各自**文生图**走同模板+同 lighting+同 style；家族感来自**共享渲染**，区分来自各自 `sheet_spec` + `factions[]` 差异化表。
   - 一句话判据：成员能不能共用一张脸/一套体型的"底"？能 → 编辑模式；不能（家庭 / 混编组）→ 文生图。
6. **确认**：展示本集清单（复用 vs 新增，变体/阵营变体注明 parent/ref + 原因），写 `<集>/资产清单.md`；用户已明确要生成就直接继续。
7. **base 先行 → 锁脸检查点 → 再出变体/阵营变体**：先生成阵营首角色 base，给用户确认四格参考表的五官/族群 OK，再出依赖它的造型变体与同阵营编辑变体。
8. 调脚本（见下），更新台账，重生成 `角色形象卡.md` 与 `资产清单.md`。

## 角色参考表 task 示例
**阵营首角色（文生图）**：
```json
{ "name": "su_fu", "category": "character", "size": "1088x1920",
  "prompt": "<character-sheet-template.md 用苏父 sheet_spec 填好的全文：4格布局/正脸·侧脸·无脸全身·背面/族群骨相/服装/lighting=柔和暖自然光/style=style_lock/面板标签+标题>",
  "char_id": "su_fu", "look": "default",
  "display_name": "苏父", "design": "<sheet_spec 摘要>",
  "quality": "high" }
```
**同阵营后续角色（编辑模式，ref = 阵营首角色参考表图）**：
```json
{ "name": "su_mu", "category": "character", "size": "1088x1920",
  "prompt": "继承参考图的画风/打光/棚拍格式/家族美学，仅按下文替换为本角色：<character-sheet-template.md 用苏母 sheet_spec 填好的全文 + factions[] 对【苏家】逐维度差异化（性别女/年龄/体型/发型/服装/气质）>",
  "char_id": "su_mu", "look": "default", "parent": "su_fu",
  "display_name": "苏母", "design": "<sheet_spec 摘要 + 与苏父的差异点>",
  "quality": "high", "ref": ["characters/su_fu.png"] }
```
> `ref` 给了就走编辑/图生图模式（保家族一致）；不给走文生图（阵营首角色 / 无阵营的独立角色）。`size` 省略时脚本按 category 自动定（character→1088x1920）。

## 待补资产兜底
读 `assets[]` 中本集需要、但 `intent` 不完整的条目，按 `category` 分流：
- **道具 / 场景**（`category:prop|scene`）：若 bible 缺该条但下游/剧本明确需要，用其 `spec_prompt`（或译自中文 seed 的英文造型核心）兜底生成 + **补登 `bible.assets[]`**（`id` 从 ref_token 解析、`ref_token` 用既有的、`status` 置 `planned`——**bible 恒为规划态，出图成功只记 registry，绝不写回 bible**；`intent.spec_prompt` 写英文造型核心，与其它资产语言一致），并进库台账。不打断。
- **人物缺 `sheet_spec`**（`category:character`）：**不自动生成**，报告"人物〈display_name〉缺 `intent.sheet_spec`（多面板参考表字段），请先回设定环节补 sheet_spec 后再出资产"。族群/骨相/打光必须由设计层锁，本环节不编。

## 单资产重做（重做模式）
触发"重做/调整 <某资产>"，只动目标、不碰其他：
- 在 `asset_registry.json` 定位该资产 → 按用户新要求改 prompt（设计仍以 bible `sheet_spec`/`spec_prompt` 为基，只调可变部分）→ 覆盖重生成（同 name 同 path）→ 更新台账 + 角色形象卡。
- 若有依赖它的变体 / 同阵营编辑变体（`parent`/`ref` 指向它）→ 提示一并重出以保一致。
- 报告：重做了哪些、影响哪些下游资产。

## 回写边界（registry vs bible）
- **已有资产**（bible `status:planned`）生成后 → **只进 `asset_registry.json`**（已生成层），**不改 bible**（bible = 规划层，保持不动）。`ref_token` 把"规划(bible)"与"已生成(registry)"两层连起来。
- **新资产**（待补道具/场景）→ 补登 `bible.assets[]`（见上）；**人物缺 sheet_spec → 回设定环节补**。这是仅有的会写 bible 的情形。

## 画风
从 `bible.json` 的 `style_lock`（优先）或 `style` 读，全剧统一套用，填进 character-sheet-template 的 `{style}`（场景/道具直接拼进 spec_prompt）。模板以写实为基准；非写实就替换渲染描述词，保留其余硬标准（多面板布局 / 棚背景 / 无多余文字 / 空镜该空）。

## 脚本用法（多渠道 + 生成/编辑）
`scripts/generate_images.py` 串行逐张，渠道失败自动回退：默认 `micu → packy → moyu`（`IMAGE2_PROVIDER_ORDER` 可覆盖）。三渠道 API key / moyu URL 放在脚本同目录的 **gitignored `_secrets.py`**（`KEYS` / `MOYU_URL`），脚本自动 import；同名环境变量 `IMAGE2_API_KEY/BASE_URL`、`PACKY_API_KEY/BASE_URL`、`MOYU_API_KEY/BASE_URL` 若设置则**覆盖**。`_secrets.py` 已在 `.gitignore`、**不进 git**；别人 clone 缺它时回退到 env。

```bash
python .claude/skills/drama-asset-gen/scripts/generate_images.py \
  --tasks '<新增/变体/待补 tasks_json>' --output-dir 'docs/scripts/<剧名>/assets' \
  --episode '<集目录名>' --drama '<剧名>' --style '<画风>' \
  --reuse '<复用资产 json，见下>'
```
- `--tasks`：只放本集**要出图**的（新增 base / 变体 / 同阵营编辑变体 / 待补道具场景）。
- `--reuse`：本集**命中复用、不出图**的资产，格式 `[{"category":"character","name":"su_fu"}, …]`——脚本把本集追加进它们的 `used_by`（不重新出图）。**漏传则复用资产的 used_by 不会记上本集**（复用追踪失真）。
- `ref`（task 内）：给了就走编辑/图生图模式（同阵营编辑变体 / 造型变体锁一致）；不给走文生图。

packy/moyu 按 gpt-image-2 约束校验尺寸（≤3840px、16 倍数、≤3:1、像素 65 万~829 万；1088x1920 / 1920x1088 / 1024x1024 都满足）。脚本合并更新 `asset_registry.json`（记 `provider`/`mode`/`first_episode`/追加 `used_by`，保留手工字段；**`size` 出图后读 PNG 回写实际画幅**——渠道枚举导致实际≠请求时另存 `size_requested` 留痕）。

## 台账与人读视图
- `asset_registry.json`：库资产唯一事实来源（扁平 looks 模型：`name/category/char_id/look/parent/display_name/path/size/provider/mode/status/first_episode/used_by/prompt`）。
- `角色形象卡.md`：从台账派生（每角色：sheet_spec 摘要 + 各 look + 图路径 + 用在哪几集）。
- `<集>/资产清单.md`：本集复用 + 新增。

## 尺寸（按 category 分画幅，脚本 `CATEGORY_SIZES` 自动定；task 不传 size 即用默认）
| 类型 | 默认 | 说明 |
|------|------|------|
| 角色参考表（character） | 1088x1920 (9:16) | 竖版四格多面板参考表 |
| 场景板（scene） | 1920x1088 (16:9) | 横版空镜 |
| 道具（prop） | 1024x1024 (1:1) | 正方形（HUD/道具） |

三渠道均支持（packy/moyu 满足约束即可，micu 走固定枚举）。竖屏短剧人物仍 9:16；成片若横屏，场景板跟成片比例。

## 质量自检
- **需求来自 bible**：`planned_episodes` 含本集的资产都已"复用或新增"，无遗漏。
- **角色参考表**：9:16 + 四格不等大（上小下大）+ 最高分辨率；**左下 BODY-FRONT 不露脸**（换脸编辑用）；族群/骨相准确（按 sheet_spec，不跑成欧美/动漫脸）；signature 装备在对应面板可见；**lighting 用 bible 该角色定的值**（明亮剧不应是硬 noir）；除 4 面板标签 + 标题无多余文字。
- **同阵营一致性**：全员同模板+同 lighting+同 style（家族感）、按 `factions[]` 逐维度可区分（不撞脸又同家族）；**视觉相近阵营**才叠编辑模式（`ref` 传首角色图），**视觉差异大的家庭/混编用文生图、不 edit**（防串味）；base 先行锁脸检查点过了再出依赖它的变体。
- **场景 / 道具**：场景该空镜的空；道具 HUD 中文标签正确写出且清晰。
- **待补资产**已处理：道具/场景补登 bible（status 仍 planned）、人物缺 sheet_spec 已回设定环节；已有 planned 资产只进 registry、未改 bible。
- **不产站位图 / 资产绑定.json**：assets/ 下无 shots/、未写 `<集>/资产绑定.json`（确认这两件留给下游）。
- 台账、角色形象卡、资产清单已更新；图都目检过。
- 报告：本集 新增 / 复用 / 变体（含同阵营编辑变体）/ 道具 / 场景 数量、失败项、待补资产去向。

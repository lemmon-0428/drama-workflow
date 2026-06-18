---
name: drama-asset-gen
description: >
  从剧本文件（Word/PDF/TXT）中提取人物小传、场景描述、关键道具，为人物做造型设计，按影视定妆照标准生成
  gpt-image-2 提示词，并调用多渠道 API 生成/编辑资产图片。资产按"整部剧"统一管理、跨集复用：新一集只补差量；
  人物形象随剧情变化（换装/受伤/伪装/反转）用"五官锚 + 图生图"派生变体。当用户提到"剧本资产生成"、
  "从剧本生成人物/场景图"、"短剧资产"、"drama asset"、"角色形象图"、"人物定妆照"、"场景图"、"角色变体/换装图"，
  或上传剧本希望生成配套图片素材时，都应触发。即使只说"帮我从这个剧本里出几张图"也应使用。
---

# Drama Asset Generator

从剧本提取人物/场景/道具，为人物设计造型，按统一标准生成提示词，调用多渠道 gpt-image-2 生成或编辑资产图片。
**资产按整部剧统一管理、跨集复用**，人物形象随剧情演变用变体追踪。

## 目录结构

```
docs/scripts/<剧名>/
├── 00_剧集总览.txt
├── 资产规划表.md                 # 全剧资产盘点：谁/什么场景、各有几个look、用在哪几集、还差哪些（人读）
├── <集目录>/
│   ├── <剧本>.txt
│   └── 资产清单.md               # 本集：复用哪些look + 本集新增/变体哪些（人读）
└── assets/                       # 全剧共享资产库（画一次、各集复用）
    ├── characters/  scenes/  props/   # base: <id>.png；变体: <id>__<look>.png
    ├── 角色形象卡.md             # 由台账自动生成：每角色 五官锚 + 各look + 图路径（人读）
    └── asset_registry.json       # 唯一事实来源（机器）
```

资产放在**剧集级 `assets/`**，不放单集目录。单集剧本就把整部当一集。

## 全剧统一画风

首次处理某剧时定 `style` 写进台账，全剧提示词套用同一风格，避免跨集漂移：写实电影感（真人剧）/ 3D动画电影质感（动漫）/ 2D动漫。按剧本头部标注判断（如"AI真人科幻"→写实、"AI动漫"→3D），必要时与用户确认一次。`references/character-prompt-standard.md` 以写实为基准；非写实就替换渲染描述词，保留其余硬标准（全身正面、纯白底、均匀柔光、无文字）。

## 三种操作模式（默认 B）

| 触发 | 模式 | 做什么 |
|------|------|--------|
| 默认（"给第N集/这一集生成资产"） | **B 增量生成** | 只生成指定集的差量（复用已有、补新增/变体） |
| "只盘点/规划全剧资产，先别生成" | **只读规划** | 通读全剧 → 出/更新 `资产规划表.md`，一张图都不生成 |
| "把整部剧的人物场景资产都生成""一次性全生成" | **A 全量** | 规划 → 展示规划表+待生成数量 → **确认后**批量生成（base先行→锁脸→变体） |

A 即使被显式要求，也先出规划表+数量、等确认再开批（花钱的批量动作不闷头跑）。"生成资产"但没指明哪集（多集剧）→ 取上下文那一集 / 下一个没做的集，拿不准就问。

## 资产台账数据模型

`asset_registry.json` 顶层 `{drama, style, episodes, assets[]}`。每个资产（一张图）一条，扁平存储，关键字段：

- `name` 文件名id（base = `<char_id>`，变体 = `<char_id>__<look>`）｜`category` character/scene/prop
- `char_id` 同一角色/场景的所有 look 共享的分组键｜`look` default / bloodied / night …｜`parent` 由哪个 look 演化（base 为空）
- `identity_anchor` **五官/身份锚**（base 必填，锁不变的脸/体型；变体逐字复用它）
- `display_name` `design`（造型摘要）｜`path` `size` `prompt` `provider`（成功渠道）`mode`（generate/edit）`status`
- `first_episode` 首次出现集｜`used_by` 被哪些集用到（=细化到 look 的复用记录）

"最初base + 最新base + 时间线"都从这里推导：某角色的 base = look==default 那条；最新 look = `used_by` 含最大集号那条。人读的时间线在 `角色形象卡.md`。

## 工作流程（8 步，标 A/B 分叉）

### Step 1 读取剧本 + 加载台账 + 定画风
读剧本（A:全部集 / B:本集）；载入 `assets/asset_registry.json`（已有 look + style）。首次处理该剧：定 `style`，先出 1–2 张画风探针让用户确认再铺开。

### Step 2 提取
A：通读全剧 → 完整 cast + 全部场景 + **每个角色/场景在各集的造型/状态**。
B：提取本集角色（含本集造型/状态）+ 场景。三类提取细则见下方"提取要点"。

### Step 3 比对去重 + 变体检测（核心）
对每个角色建 look 时间线：哪几集同造型(同 look)、哪集变化(新 look)。判定 = 状态比对 ＋ **信号词**（换装/穿上/戴上、血/绷带/淤青、易容/面具/扮成、时间跳跃、身份揭穿）＋ **阈值**（持久且对剧情有定义性才算新 look；单场景脏污/疲惫用 base+后期，不出新图）。
和台账比对，每个 (角色/场景, look) 标：**复用 / 新增base / 新增变体**，变体附 `parent` 和触发原因。
A：产出整张 `资产规划表.md`；B：更新表中本集相关行。

### Step 4 造型设计（仅新增/变体）
新 base：完整造型设计表（角色名｜年龄性别｜身份｜发型发色/妆｜身高体态｜穿搭(上装/下装/鞋/配饰具体到款色质)｜气质）。穿搭须体现身份与经济状况、符合本集处境、不同角色风格鲜明区分。
新变体：`identity_anchor` 逐字复用，只改"变化的造型/状态"，`parent` 默认 = 最新 look（保连续），剧情回退则指定更早 look。

### Step 5 生成提示词
人物先读 `references/character-prompt-standard.md`（9:16 1088x1920、全身正面、纯白底、把造型表译进去、末尾 no text…）。场景先读 `references/scene-prompt-standard.md`（16:9 1920x1088、默认空镜、剧本写了人/文字才保留）。道具用下方模板。全部套用 `style`、英文、以 no text/no watermark 结尾。

### Step 6 确认 + 写本集 `资产清单.md`
展示清单，**复用与新增分列**（变体注明 parent + 触发原因）。A 展示整张规划表，B 展示本集清单。确认后写 `<集目录>/资产清单.md`。用户已明确要生成时展示后直接继续。

### Step 7 调用脚本生成/编辑（按依赖顺序）
**先生成所有新 base → 锁脸检查点（让用户确认五官 OK）→ 再生成变体**（变体走编辑模式：`ref` 传 parent 的图，靠图生图锁脸）。命令见下方"脚本用法"。

### Step 8 收尾
复用项把本集追加进对应资产 `used_by`（脚本对生成项自动做；纯复用项由你补写台账）；从台账重生成 `角色形象卡.md`；报告本集/全剧 新增 / 复用 / 变体 / 失败。

## 提取要点

- **人物**：姓名、年龄性别、身份背景、外貌、**剧情处境**、性格气质。处境决定造型方向。
- **场景**：场景名、日/夜、环境、氛围、重要陈设；合并相似场景。
- **道具**：只取对剧情有推动作用的关键道具。

道具提示词模板：
```
8K hyper-realistic, [prop], [material and texture], [era/style], [details],
centered composition, clean background, product photography, soft studio lighting,
high detail, no text, no words, no watermark
```

## 脚本用法（多渠道 + 生成/编辑）

`scripts/generate_images.py` 串行逐张请求，**渠道失败自动回退**：默认 `micu → packy → moyu`（可用 `IMAGE2_PROVIDER_ORDER` 覆盖）。

环境变量（key/url 放 ~/.zshrc 或 .env，**不进仓库**）：
`IMAGE2_API_KEY`/`IMAGE2_BASE_URL`（micu）、`PACKY_API_KEY`/`PACKY_BASE_URL`、`MOYU_API_KEY`/`MOYU_BASE_URL`。

```bash
python .Codex/skills/drama-asset-gen/scripts/generate_images.py \
  --tasks '<tasks_json>' \
  --output-dir 'docs/scripts/<剧名>/assets' \
  --episode '<集目录名>' --drama '<剧名>' --style '<画风>'
```

task 字段（`ref` 给了就走**编辑/图生图**模式，用于变体锁脸）：
```json
{
  "name": "navigator_k__chest_reveal", "category": "character", "size": "1088x1920",
  "prompt": "<五官锚逐字复用 + 变化的造型/状态 + 硬标准>",
  "char_id": "navigator_k", "look": "chest_reveal", "parent": "default",
  "identity_anchor": "<五官锚>", "display_name": "领航员K", "design": "<造型摘要>",
  "quality": "medium",
  "ref": ["characters/navigator_k.png"]
}
```
脚本把图存进共享库 `characters/scenes/props/`，合并更新 `asset_registry.json`（记 `provider`/`mode`/`first_episode`/追加 `used_by`，保留手工字段）。`ref` 路径相对 `--output-dir` 或绝对。packy/moyu 按 gpt-image-2 通用尺寸约束校验（≤3840px、16的倍数、长短比≤3:1、像素65万~829万），不满足约束的渠道才跳过——常用的 1088x1920 / 1920x1088 等都满足。

## 尺寸参考

| 类型 | 默认 | 说明 |
|------|------|------|
| 人物 | 1088x1920 (9:16, ≈1080p) | 竖版全身定妆照 |
| 场景 | 1920x1088 (16:9, ≈1080p) | 横版空镜 |
| 道具 | 1024x1024 (1:1) | 正方形 |

三渠道均支持上述常用尺寸（packy/moyu 满足 ≤3840 / 16倍数 / ≤3:1 / 像素65万~829万 约束即可；micu 走其固定枚举）。变体编辑建议与 base 同尺寸。

## 注意事项

- 文件名英文小写+下划线；变体加 `__<look>` 后缀（`navigator_k__bloodied`）。
- 提示词避免真实人名/明星名。
- 变体一致性：五官锚一字不改 + 用 parent 图做 `ref` 图生图，是"换装/受伤但仍是同一个人"的关键。
- 剧本较长时优先处理有明确描述的角色和场景。

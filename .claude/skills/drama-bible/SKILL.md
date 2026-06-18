---
name: drama-bible
description: >
  读短剧剧本（通读全剧），产出全剧设计 SoT 的"意图层"：人物/场景/道具的视觉锁定规格（五官锚 / 造型 / look 计划）
  + 全剧 STYLE LOCK，写入 bible.json 的统一 assets[]（status:planned）；叙事（背景 / 性格 / 弧光 / 世界观）写入人读 .md。
  真资产由 ⑤ 按需生成后回写"实现层"。当用户要"生成人物背景 / 人物小传 / 世界观 / 设定集 / 角色设定 /
  character bible / 人物造型设计 / 形象设计 / 确定画风"时触发。这是短剧流水线第②步（拆解→设定→分镜头→提示词→资产→SD2），
  ③④⑤ 都从这里取设计。
---

# Drama Bible（剧本设定 / 人物背景）

像"故事编剧 + 人物造型师"一样工作：通读全剧，把人物、场景、道具、世界观、画风，整理成**全剧统一、可被下游直接消费**的设定集。

**你只产"设计意图（intent）"**——每个视觉资产**应该长什么样、有哪些 look、出现在哪几集**，状态 `planned`。**真资产由 ⑤ `drama-asset-gen` 按需生成后回写"实现（realized）"**，不是你的事。资产 JSON **严格按 `docs/asset-schema.md`**（统一 `assets[]` 契约）。

**叙事 ≠ 资产**：背景 / 性格 / 关系 / 弧光 / 世界观是"角色是谁、怎么变",写进人读 `.md`，**不进 `assets[]`**（出图不需要它）。`assets[]` 只装"长什么样"的视觉锁定规格。

## 输入
- `docs/scripts/<剧名>/第N集_*/…txt`（`drama-script-split` 的产物）。**通读全剧**（不是单集）——人物弧光、换装 / 受伤 / 反转、场景打光变化都是跨集的，look 计划必须看全剧才定得对。
- 也接受用户补充的设定（画风偏好、某角色定位等）。

## 输出
```
docs/scripts/<剧名>/bible/
├── 世界观.md        世界观 / 时代 / 规则 / 基调（人读·叙事）
├── 人物背景.md      每角色：背景·性格·关系·弧光 + 造型设计 + 五官锚 + look 规划（人读·叙事 + 设计）
├── 场景设定.md      每场景：环境·氛围 + look 清单（人读·设计）
└── bible.json       机读：drama meta + style_lock + assets[]（意图层，status:planned）
```
- **分工**：`.md` 是**叙事 + 设计**的人读正本（bio / 弧光 / 世界观只在这里）；`bible.json` 是**机器要消费的视觉规格**（identity_anchor / 造型 / look 计划 / style_lock）。两者**视觉规格部分必须一致**（以 json 为准）；叙事只在 `.md`。
- `bible.json` 严格按 `docs/asset-schema.md`——**本步只填 `intent` + `status:"planned"`，`realized` 留空给 ⑤**。

## 四件核心设计

### 1. 人物 → character 资产（每个 look 一条）
- **背景小传 + 弧光**（→ 写 `人物背景.md`）：定位、身份、性格、关系、关键设定 / 秘密、人物弧光（怎么变）。优先用原文；要推断就标"据剧情推断"，**不凭空编造**。
- **五官锚 `identity_anchor`**（→ `intent.identity_anchor`）：一句**英文**，只描述不变的脸 / 发 / 体型（年龄·五官·肤色·发型·身材），用于全剧锁脸。**同角色各 look 间这句完全一致**（逐条写同一句）。
- **造型设计 `spec_prompt`**（→ `intent.spec_prompt`）：像造型师把模糊描述翻成具体单品（上装 / 下装 / 鞋 / 配饰，到款式颜色材质），体现身份与处境。**只写造型，不含五官**（五官在 identity_anchor）。
- **look 规划**：通读全剧列出形象变体时间线。`default` 为基础；剧情有**持久且有定义性**的变化（换装 / 受伤 / 伪装 / 身份反转）才追加一个 look，标 `parent`（从哪个 look 演化）与 `planned_episodes`。单场景的脏污 / 疲惫不算 look。

### 2. 场景 → scene 资产（每个 look 一条）
每场景一个 `id`，环境 / 氛围写 `intent.spec_prompt`；打光 / 状态 look（如大厅 `dim`/`night`/`flickering`）各一条，标 `parent` 与 `planned_episodes`。

### 3. 道具 → prop 资产
对剧情重要、会被锚定 / 复用的道具（枪、信物、反转道具等），各一条 `prop`，`intent.spec_prompt` 写它长什么样，`planned_episodes` 标用在哪几集。

### 4. 全剧 STYLE LOCK（写进 `style_lock`）
按剧本头部画风定位（"AI真人科幻"→写实电影感；"AI动漫"→动画；等），**写一段完整的 STYLE LOCK 块**作为全剧渲染常量，存进 `bible.json.style_lock`——④ 会**原样照用**、每组复用。**写实剧务必带"反塑料感锚"**（真实胶片颗粒 / 实景光 / 照片级电影定格 / 不是 3D 渲染、不是 CG）。同时保留一句短 `style` 标签备查。拿不准画风时跟用户确认一次。

## 立哪些资产的判据（边界，拿不准时按这个判）
- **场景**：凡分镜头会**给到镜头**的地点就立一个 `scene`——哪怕剧本一句带过，只要会出画（如结局"机器人世界的巴别塔"）；纯提及、不出画的地点不立。
- **look vs prop（身体显形 vs 道具显形）**：角色**自身造型 / 身体**的持久、有定义性的变化 → 给该角色加 `look`（如 K 掀胸露出的机械胸腔，是"他身体本来长这样"的身份揭示）；揭示 / 引入一个**能单独成立的物件** → 立 `prop`（如机器僧胸腔里那颗玻璃盒心脏是独立道具，机器僧身体本身没变）。
- **道具门槛**：会被**多次锚定复用**，**或**虽只一次但属**反转 / 特写级关键物件**（需锁定外观）→ 立 `prop`；纯背景、一次性、不需锁外观的小物件不立（在 `.md` 提一句即可）。

## bible.json 怎么填（意图层，完整字段见 `docs/asset-schema.md`）

```json
{
  "drama": "巴别塔",
  "style": "8K 超写实真人电影感（AI真人科幻 / Dune·Interstellar）",
  "style_lock": "[STYLE LOCK]（全集统一·每组复用）\n8K 超写实真人电影感 / photoreal live-action cinematic；《沙丘》《星际穿越》级质感 + 东方禅意压抑；废土美学 × 心理惊悚 × 赛博科幻。\n质感锚：真实电影胶片颗粒 + 实景光 + 高光轻微光晕 + 大气尘霾 + 可触实体材质；照片级电影定格、透过镜头拍到的真实物理场景——不是 3D 渲染、不是 CG、不是塑料感。",
  "logline": "一句话故事",
  "episodes": ["第1集_开篇", "第2集_乘客", "第3集_抉择", "第4集_倒塌"],
  "assets": [
    { "asset_id": "char.navigator_k.default", "category": "character", "kind": "human",
      "id": "navigator_k", "display_name": "领航员K", "look": "default",
      "ref_token": "@[char:navigator_k|look:default]", "status": "planned",
      "intent": {
        "identity_anchor": "40-yo East Asian man, weathered stoic face, deep-set tired eyes like an extinguished volcano, short cropped black hair flecked with grey, tall lean upright build",
        "spec_prompt": "dark charcoal layered long coat-robe over a high-collar technical tunic, worn leather utility harness, dark trousers tucked into heavy boots, ash-and-earth muted palette, Dune-like survival navigator uniform",
        "parent": null, "planned_episodes": ["第1集_开篇", "第2集_乘客", "第3集_抉择", "第4集_倒塌"] } },

    { "asset_id": "char.navigator_k.chest_reveal", "category": "character", "kind": "human",
      "id": "navigator_k", "display_name": "领航员K", "look": "chest_reveal",
      "ref_token": "@[char:navigator_k|look:chest_reveal]", "status": "planned",
      "intent": {
        "identity_anchor": "40-yo East Asian man, weathered stoic face, deep-set tired eyes like an extinguished volcano, short cropped black hair flecked with grey, tall lean upright build",
        "spec_prompt": "the charcoal coat and shirt torn open at the chest revealing a gunmetal-grey mechanical compartment of tangled wires and circuitry",
        "parent": "default", "planned_episodes": ["第4集_倒塌"] } },

    { "asset_id": "scene.noah_ark_interior_hall.dim", "category": "scene",
      "id": "noah_ark_interior_hall", "display_name": "诺亚方舟内部大厅", "look": "dim",
      "ref_token": "@[scene:noah_ark_interior_hall|look:dim]", "status": "planned",
      "intent": {
        "spec_prompt": "vast empty Noah's Ark spaceship main hall, dim moody, cool light from a huge floor-to-ceiling viewport onto the dead Earth, near-future sci-fi + Eastern Zen minimalism, a raised elevated platform",
        "parent": null, "planned_episodes": ["第1集_开篇", "第2集_乘客"] } },

    { "asset_id": "prop.handgun", "category": "prop",
      "id": "handgun", "display_name": "手枪", "ref_token": "@[prop:handgun]", "status": "planned",
      "intent": { "spec_prompt": "an old worn handgun, K's, the weapon behind the drama's three gunshots",
        "planned_episodes": ["第3集_抉择", "第4集_倒塌"] } }
  ]
}
```

- `id` 用英文小写下划线，全剧稳定不变——③④⑤ 全靠它衔接；`asset_id` = `<category 缩写>.<id>.<look>`（命名见 schema §3）。
- **同角色每个 look 一条独立资产**（`default`/`chest_reveal` 各一条），不再嵌套 `looks[]`；`identity_anchor` 在它们之间写成同一句。
- **`realized` 一律不写、`status` 一律 `planned`**——真图、path、调色板是 ⑤ 的事。
- **`color_card` / `blocking` 本步不产**（它们逐组 / 逐镜、由 ⑤ 按需生成）。

## 人物背景.md 模板（每角色一段；叙事 + 设计的人读正本）
```markdown
## [角色名]  `char_id`
- 其他名字 / 称呼：
- 角色定位 / 身份背景：
- 性格气质：
- 与其他人物关系：
- 关键设定 / 秘密：
- 人物弧光（从…变成…）：
- 五官锚（英文，锁脸；= bible.json 该角色各 look 的 identity_anchor）：
- 造型设计（= 各 look 的 spec_prompt 的人话版）：
- look 规划：default(用在X集) → 变体(parent, 用在X集)
- 来源依据 / 待确认：
```

## 质量自检（写文件前）
- `bible/` 四文件齐全；`bible.json` 能被 `json` 解析，结构**符合 `docs/asset-schema.md`**。
- 每个**资产**都有 `asset_id`/`category`/`id`/`display_name`/`look`(prop 可省)/`ref_token`/`status:"planned"`/`intent`；**没有 `realized`**（那是 ⑤ 的）。
- 每个角色至少有 `default` look 资产；`identity_anchor`（英文）在**同角色各 look 间逐字符完全一致**（用 diff / 脚本核对，别靠肉眼）；造型 `spec_prompt` 具体到单品、且**不含五官**。
- look 规划覆盖全剧的换装 / 受伤 / 伪装 / 反转 / 打光变化，标了 `parent` 与 `planned_episodes`；重要道具都立了 `prop` 资产。
- `style_lock` 是**完整一段**（写实剧含反塑料感锚）；短 `style` 标签也在。
- **bio / 弧光 / 世界观只在 `.md`**，没漏进 `assets[]`；**没产 `color_card` / `blocking`**。
- 没凭空编造；推断内容已标注。

## 交付报告
报告：产出路径；资产清单概览（几个角色 × 各几个 look、几个场景 × 各几个 look、几个道具）；`style_lock` 一句话画风；任何据剧情推断或需用户确认的设计点。

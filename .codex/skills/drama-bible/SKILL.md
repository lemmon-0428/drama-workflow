---
name: drama-bible
description: >
  读短剧剧本（通读全剧），产出全剧设计 SoT 的"意图层"：人物**富 sheet_spec**（多面板角色参考表结构化字段：
  族群/骨相/服装/signature/武器/打光/反例…）+ 同阵营 **factions[]** 差异化表 + 全剧 STYLE LOCK，
  写入 bible.json 的统一 assets[]（status:planned）；叙事（背景 / 性格 / 弧光 / 世界观）写入人读 .md。
  真资产由下游资产环节按需生成后回写"实现层"。当用户要"生成人物背景 / 人物小传 / 世界观 / 设定集 / 角色设定 /
  character bible / 人物造型设计 / 形象设计 / 确定画风"时触发。这是短剧流水线第②步（拆解→设定→资产→分段→视频），
  产出全剧设计的唯一来源，下游出图 / 分镜 / 视频都从这里取设计。
---

# Drama Bible（剧本设定 / 人物背景）

像"故事编剧 + 人物造型师"一样工作：通读全剧，把人物、场景、道具、世界观、画风，整理成**全剧统一、可被下游直接消费**的设定集。

**你只产"设计意图（intent）"**——每个视觉资产**应该长什么样、有哪些 look、出现在哪几集**，状态 `planned`。**真图由下游资产环节按需生成、把"实现（realized）"只记进 registry**，不是你的事（bible 恒为规划态）。资产 JSON **严格按 `docs/asset-schema.md`**（统一 `assets[]` 契约）。

**本版升级（核心）**：人物 `intent` 从"一句锁脸 `identity_anchor` + 一句造型 `spec_prompt`"升级为**结构化 `sheet_spec`**——字段直接对应下游**多面板角色参考表**的渲染槽位（一字段一面板部位，见下「sheet_spec 各字段对应表」）。同时新增顶层 **`factions[]`**（同阵营差异化表），让下游对同阵营新角色走编辑模式时个体可区分。**这么结构化是为了给下游一份"逐字段可直接渲染"的人物规格**，而不是一段笼统描述。场景/道具仍用一句 `spec_prompt`，不变。

**叙事 ≠ 资产**：背景 / 性格 / 关系 / 弧光 / 世界观是"角色是谁、怎么变",写进人读 `.md`，**不进 `assets[]`**（出图不需要它）。`assets[]` 只装"长什么样"的视觉锁定规格。

## 输入
- `docs/scripts/<剧名>/第N集_*/…txt`（上游拆解出的单集剧本）。**通读全剧**（不是单集）——人物弧光、换装 / 受伤 / 反转、场景打光变化都是跨集的，look 计划必须看全剧才定得对。
- 也接受用户补充的设定（画风偏好、某角色定位等）。
- **字段契约**：`sheet_spec` / `factions` / 命名规范全部定义在共享契约 `docs/asset-schema.md`（§1-3）——按它逐字段填，下游据此渲染。

## 输出
```
docs/scripts/<剧名>/bible/
├── 世界观.md        世界观 / 时代 / 规则 / 基调（人读·叙事）
├── 人物背景.md      每角色：背景·性格·关系·弧光 + 造型设计 + sheet_spec 摘要 + look 规划（人读·叙事 + 设计）
├── 场景设定.md      每场景：环境·氛围 + look 清单（人读·设计）
└── bible.json       机读：drama meta + style_lock + factions[] + assets[]（意图层，status:planned）
```
- **分工**：`.md` 是**叙事 + 设计**的人读正本（bio / 弧光 / 世界观只在这里）；`bible.json` 是**机器要消费的视觉规格**（sheet_spec / look 计划 / factions / style_lock）。两者**视觉规格部分必须一致**（以 json 为准）；叙事只在 `.md`。
- `bible.json` 严格按 `docs/asset-schema.md`——**本步只填 `intent` + `status:"planned"`，`realized` 留空**（下游生成真图时才把实现层记进 registry，不回写 bible）。

## 五件核心设计

### 1. 人物 → character 资产（每个 look 一条，intent.sheet_spec 是结构化富字段）
- **背景小传 + 弧光**（→ 写 `人物背景.md`）：定位、身份、性格、关系、关键设定 / 秘密、人物弧光（怎么变）。优先用原文；要推断就标"据剧情推断"，**不凭空编造**。
- **`intent.sheet_spec`**（→ `bible.json`，逐字段渲染到下游多面板角色参考表）：一个结构化对象，字段对应渲染槽位：
  - `identity_anchor`：一句**英文**脸部总锚（年龄·五官·肤色·发型·身材），**同角色各 look 间逐字一致**——作为 sheet_spec 的脸锚。
  - `ethnicity`：民族 / 地域（例 `rural Han Chinese`、`Central Asian Turkic Silk-Road 杂胡`）。
  - `physique`：体型（lean wiry / stocky / petite slender…）。
  - `aura`：核心气质 / 一句角色印象。
  - `face`：子对象 `{cheekbones, eyes, hair, skin, nose, brows, skin_detail}`——逐项骨相级描述（**眼型务必写清，防欧美双眼皮 / K-pop / 网红脸**）。
  - `scars`：伤疤 / 胎记 / 纹身位置（无则 `"none"`）。
  - `hair`：发型 / 发色 / 质感 + 发饰。
  - `headwear`：头盔 / 兜帽 / 头巾 / 帽（无则 `"none"`）+ 露脸规则。
  - `upper`：上装类型 + 材质 + 状态（风化 / 战损 / 仪式 / 干净）。
  - `lower`：下装 + 腰带 / 小袋 / 枪套 / 护符 / 鞋。
  - `mod`：独特改造 / 义肢 / 赛博 / 动物特征（无则 `"none"`）。
  - `weapons`：子对象 `{primary, secondary, ranged}`（无武器剧全填 `"none"`）。
  - `palette`：主色 / 点缀 / 材质色 / 氛围。
  - `pose`：四面板统一站姿 / 手部。
  - `lighting`：**可调参数（按本剧 style_lock 调性定，见下）**。
  - `style_ref`：渲染参考片 / 族群准确性参考（例《长安十二时辰》西域狼卫 / 当代写实青春剧）。
  - `anti`：**反例清单（数组）**——本角色明确不要的族群 / 体型 / 风格（例 `["欧美脸","K-pop偶像","网红整容脸","动漫脸","时装模特身材"]`）。
- **`lighting` 是可调参数（重要）**：模板默认是硬单边轮廓光（noir / 战争 / 黑深剧用）。但**按本剧 style_lock 的调性给每个角色定**：
  - 战争 / 黑深 / 科幻惊悚剧 → `"Single-sided side-rim backlighting from camera-right at 45° behind, no fill, no front, deep falloff shadow"`（硬轮廓）。
  - 明亮温暖 / 青春逆袭 / 生活剧（如步步生金）→ `"soft warm natural studio lighting, gentle fill, even flattering exposure, true-to-life skin, no harsh noir rim"`（柔光暖）。
  - **不要照搬模板默认硬 noir**——明亮剧用硬轮廓光会把人脸打成阴间。
- **look 规划**：通读全剧列出形象变体时间线。`default` 为基础；剧情有**持久且有定义性**的变化（换装 / 受伤 / 伪装 / 身份反转）才追加一个 look，标 `parent`（从哪个 look 演化）与 `planned_episodes`。单场景的脏污 / 疲惫不算 look。**同角色各 look 共享同一 `identity_anchor` 与 `face`，只换 `upper`/`lower`/`mod`/`palette` 等造型字段。**

### 2. 顶层 `factions[]`（同阵营 / 同组角色差异化表）
- **用途**：③ 出完阵营首角色后，同阵营新角色走**编辑模式**（ref 传首角色 sheet 图，继承画风 / 打光 / 棚拍格式 / 阵营美学家族）。`factions[]` 提供**逐维度区分表**，保证同阵营角色家族感一致、个体又可区分。
- **结构**：每个 faction 一条 `{id, display_name, aesthetic_family, members:[char_id…], differentiators:{…}}`。`differentiators` 按维度逐角色区分：`gender / age / physique / hair_beard / costume / signature_gear / weapons / trophies / aura`，每维度写"A=…，B=…，C=…"。
- **无明显阵营的剧**（如纯家庭 / 青春剧，人物各自独立）：`factions` 可为**空数组 `[]`**，或把"同处境同质感的一组"（如同村乡邻、同一豪门一家）列一个 faction，区分维度即可。

### 3. 场景 → scene 资产（每个 look 一条）
每场景一个 `id`，环境 / 氛围写 `intent.spec_prompt`（一句英文）；打光 / 状态 look（如大厅 `dim`/`night`/`flickering`）各一条，标 `parent` 与 `planned_episodes`。**场景不升级 sheet_spec，仍是一句 spec_prompt。**

### 4. 道具 → prop 资产
对剧情重要、会被锚定 / 复用的道具（枪、信物、反转道具、HUD 等），各一条 `prop`，`intent.spec_prompt`（一句英文）写它长什么样，`planned_episodes` 标用在哪几集。**道具不升级 sheet_spec，仍是一句 spec_prompt。**

### 5. 全剧 STYLE LOCK（写进 `style_lock`）
按剧本头部画风定位（"AI真人科幻"→写实电影感；"AI动漫"→动画；等），**写一段完整的 STYLE LOCK 块**作为全剧渲染常量，存进 `bible.json.style_lock`——④ 会**原样照用**、每段复用。**写实剧务必带"反塑料感锚"**（真实胶片颗粒 / 实景光 / 照片级电影定格 / 不是 3D 渲染、不是 CG）。同时保留一句短 `style` 标签备查。**style_lock 的影调（明亮暖 vs 黑深冷）要与各人物 `sheet_spec.lighting` 一致。** 拿不准画风时跟用户确认一次。

## 立哪些资产的判据（边界，拿不准时按这个判）
- **场景**：凡分镜 / 分段会**给到镜头**的地点就立一个 `scene`——哪怕剧本一句带过，只要会出画；纯提及、不出画的地点不立。
- **look vs prop（身体显形 vs 道具显形）**：角色**自身造型 / 身体**的持久、有定义性的变化 → 给该角色加 `look`（如 K 掀胸露出的机械胸腔，是"他身体本来长这样"的身份揭示，写进该 look 的 `sheet_spec.mod`）；揭示 / 引入一个**能单独成立的物件** → 立 `prop`。
- **道具门槛**：会被**多次锚定复用**，**或**虽只一次但属**反转 / 特写级关键物件**（需锁定外观）→ 立 `prop`；纯背景、一次性、不需锁外观的小物件不立（在 `.md` 提一句即可）。

## bible.json 怎么填（意图层，完整字段见 `docs/asset-schema.md`）

```json
{
  "drama": "步步生金",
  "style": "写实真人青春逆袭剧 + 轻奇幻系统HUD（明亮温暖·当代城乡中国）",
  "style_lock": "[STYLE LOCK]（全集统一·每段复用）\n写实真人电影感 / photoreal live-action cinematic；当代中国城乡青春逆袭剧 + 轻奇幻\"进步系统\"流。明亮温暖、积极向上的影调，自然光为主。\n质感锚（反塑料感）：真实电影胶片颗粒 + 实景自然光 + 真实皮肤毛孔/布料/竹篾质感；照片级电影定格——不是 3D 渲染、不是 CG、不是塑料感、不是动画。",
  "logline": "一句话故事",
  "episodes": ["第1集_绝望降临", "第2集_城市谋生", "第3集_全网爆红", "第4集_衣锦还乡"],

  "factions": [
    { "id": "su_family", "display_name": "苏家一家（同村贫寒乡邻）",
      "aesthetic_family": "当代中国农村写实·暖金自然光·朴素磨损布料·真实风化皮肤",
      "members": ["su_xiaoqi", "su_father", "su_mother", "li_shu"],
      "differentiators": {
        "gender":        "苏小七=少女；苏父/李叔=中老年男；苏母=中年女",
        "age":           "苏小七~17；苏母~45；苏父~48；李叔~50",
        "physique":      "苏小七=瘦小纤弱；苏父=精瘦佝偻；苏母=壮实敦厚；李叔=粗壮",
        "hair_beard":    "苏小七=直发齐肩黑框眼镜；苏父=花白短发；苏母=黑发挽髻；李叔=寸头络腮胡茬",
        "costume":       "苏小七=褪色针织+泥小白鞋；苏父=补丁工装挽裤；苏母=碎花罩衫+布围裙；李叔=糙布衫扛锄头",
        "signature_gear":"苏小七=黑框眼镜+泥小白鞋；苏母=布围裙；李叔=肩头锄头",
        "weapons":       "全员 none（生活剧）",
        "trophies":      "无",
        "aura":          "苏小七=倔强清澈；苏父=隐忍老实；苏母=朴实慈和；李叔=粗声爽利"
      } }
  ],

  "assets": [
    { "asset_id": "char.su_xiaoqi.default", "category": "character", "kind": "human",
      "id": "su_xiaoqi", "display_name": "苏小七", "look": "default",
      "ref_token": "@[char:su_xiaoqi|look:default]", "status": "planned",
      "intent": {
        "sheet_spec": {
          "identity_anchor": "17-year-old rural Chinese girl, fresh delicate clear face, fair skin, large bright earnest eyes behind black-framed glasses, straight black shoulder-length hair, slender petite build",
          "ethnicity": "rural Han Chinese, contemporary mainland countryside",
          "physique": "petite slender, slightly underfed, narrow shoulders",
          "aura": "stubborn, clear-eyed, earnest country girl who refuses to give up",
          "face": {
            "cheekbones": "soft rounded youthful cheeks, gentle jaw",
            "eyes": "large bright earnest dark-brown eyes, single/light-fold East Asian eye shape behind black-framed glasses, NOT round Western double-fold",
            "hair": "jet black, straight, healthy but plain",
            "skin": "fair clear young skin, faint natural country flush, real pores",
            "nose": "small soft straight nose bridge",
            "brows": "natural soft dark brows, ungroomed",
            "skin_detail": "no makeup, true-to-life teenage skin, faint sun on cheeks"
          },
          "scars": "none",
          "hair": "shoulder-length straight black hair, simple, sometimes tucked behind ear; no styling product",
          "headwear": "none; face fully visible",
          "upper": "faded modest thin knit top or plain t-shirt, threadbare but clean, humble rural-student wear",
          "lower": "simple loose cheap trousers; worn old little white canvas sneakers caked with mud",
          "mod": "none",
          "weapons": { "primary": "none", "secondary": "none", "ranged": "none" },
          "palette": "muted faded earth tones — washed grey-blue top, dull beige trousers, mud-stained off-white shoes; warm low-saturation country palette",
          "pose": "natural relaxed standing, arms at sides or lightly clasped; NOT fashion-model, NOT seductive",
          "lighting": "soft warm natural studio lighting, gentle fill, even flattering exposure, true-to-life skin, no harsh noir rim",
          "style_ref": "contemporary Chinese realist youth drama; photoreal teenage country girl, NOT idol/glam",
          "anti": ["欧美脸/double-fold Western eyes", "K-pop偶像脸", "网红整容脸", "动漫/cosplay脸", "时装模特纤瘦身材", "浓妆/精致美甲", "硬noir轮廓光"]
        },
        "parent": null,
        "planned_episodes": ["第1集_绝望降临", "第2集_城市谋生", "第3集_全网爆红", "第4集_衣锦还乡"]
      } },

    { "asset_id": "scene.rural_stone_path.dusk", "category": "scene",
      "id": "rural_stone_path", "display_name": "乡间石板路·黄昏", "look": "dusk",
      "ref_token": "@[scene:rural_stone_path|look:dusk]", "status": "planned",
      "intent": {
        "spec_prompt": "a rural countryside stone-slab path covered with rotting leaves, winding through fields at dusk, warm golden backlit sunset, tranquil poor village outskirts",
        "parent": null, "planned_episodes": ["第1集_绝望降临"] } },

    { "asset_id": "prop.white_sneakers", "category": "prop",
      "id": "white_sneakers", "display_name": "旧小白鞋",
      "ref_token": "@[prop:white_sneakers]", "status": "planned",
      "intent": {
        "spec_prompt": "a pair of old worn little white canvas sneakers caked with mud, the signature walk-to-earn shoes, hero close-up prop",
        "parent": null, "planned_episodes": ["第1集_绝望降临"] } }
  ]
}
```

- `id` 用英文小写下划线，全剧稳定不变——下游所有环节全靠它衔接（ref_token 把规划层与已生成层连起来）；`asset_id` = `<category 缩写>.<id>.<look>`（命名见 schema §3）。
- **同角色每个 look 一条独立资产**（`default`/`chest_reveal` 各一条），不嵌套 `looks[]`；`sheet_spec.identity_anchor` 与 `sheet_spec.face` 在它们之间写成同一份，只换造型字段。
- **`realized` 一律不写、`status` 一律 `planned`**——真图、path、调色板是下游资产环节的事。
- **`palette` 色卡 / `board` 草图板本步不产**（它们逐段、由下游分段环节按需生成）。

## sheet_spec 各字段对应"多面板角色参考表"的哪部分（= 为什么这样结构化，供下游逐字段渲染）
| bible `sheet_spec` 字段 | 渲染到角色参考表的哪部分 |
|---|---|
| `identity_anchor` | 四面板共享的脸锚（全程逐字一致） |
| `ethnicity` + `face.*` | 【ETHNICITY — CRITICAL】Cheekbones/Eyes/Hair/Skin/Nose/Brows/Skin detail |
| `physique` | 【Character Core】Physique / NOT |
| `aura` | 【Subject】Overall aura / Body language |
| `scars` | 【Face Detail】Scars/marks/tattoos |
| `hair` | 【Hair】 |
| `headwear` | 【Headwear】 |
| `upper` | 【Upper body】 |
| `lower` | 【Lower body】 |
| `mod` | 【Unique body / mod】 |
| `weapons.{primary,secondary,ranged}` | 【Weapons】 |
| `palette` | 【Color Palette】 |
| `pose` | 【Pose】 |
| `lighting` | 【Lighting — critical】（**本剧调性可调**） |
| `style_ref` | 【Style】族群准确性参考片 |
| `anti[]` | 【Constraints】NOT 清单 |
| 顶层 `factions[].differentiators` | 同阵营编辑模式逐维度区分表 |

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
- 造型设计（= sheet_spec 的 upper/lower/palette 的人话版）：
- sheet_spec 要点（族群 / 体型 / 气质 / signature / 打光基调 / anti 反例）：
- 所属 faction（同阵营差异化表里跟谁区分、怎么区分）：
- look 规划：default(用在X集) → 变体(parent, 用在X集)
- 来源依据 / 待确认：
```

## 质量自检（写文件前）
- `bible/` 四文件齐全；`bible.json` 能被 `json` 解析，结构**符合 `docs/asset-schema.md`**。
- 每个**资产**都有 `asset_id`/`category`/`id`/`display_name`/`look`(prop 可省)/`ref_token`/`status:"planned"`/`intent`；**没有 `realized`**（下游生成时才回写到 registry）。
- **每个人物有完整 `intent.sheet_spec`（结构化富字段，非一句话）**——`ethnicity`/`face.*`/`physique`/`upper`/`lower`/`palette`/`lighting`/`anti[]` 等都填了，不是只剩一句 identity_anchor + 一句 spec_prompt。
- **`identity_anchor` 与 `face` 在同角色各 look 间逐字符完全一致**（用 diff / 脚本核对，别靠肉眼）；只造型字段随 look 变。
- **`lighting` 按本剧 style_lock 调性**：明亮暖剧=柔和自然暖光、黑深 / 战争剧=硬单边轮廓光；没照搬模板默认硬 noir；与 style_lock 影调一致。
- **`factions[]` 差异化表覆盖同阵营 / 同组角色**，逐维度（性别 / 年龄 / 体型 / 发须 / 服装 / signature / 武器 / 战利品 / 气质）可区分；无阵营剧 `factions` 为 `[]` 或按"同处境组"列。
- `anti[]` 列了本角色明确不要的族群 / 体型 / 风格（防欧美 / K-pop / 网红 / 动漫脸）。
- look 规划覆盖全剧的换装 / 受伤 / 伪装 / 反转 / 打光变化，标了 `parent` 与 `planned_episodes`；重要道具都立了 `prop` 资产；场景 / 道具仍是一句 `spec_prompt`。
- `style_lock` 是**完整一段**（写实剧含反塑料感锚）；短 `style` 标签也在。
- **bio / 弧光 / 世界观只在 `.md`**，没漏进 `assets[]`；**没产 `palette` 色卡 / `board` 草图板**。
- 没凭空编造；推断内容已标注。

## 交付报告
报告：产出路径；资产清单概览（几个角色 × 各几个 look、几个场景 × 各几个 look、几个道具）；`factions[]` 有几组、各覆盖谁；全剧 `lighting` 基调（柔暖 / 硬轮廓）与 `style_lock` 一句话画风；任何据剧情推断或需用户确认的设计点。

# 统一资产 Schema（drama-bible / drama-asset-gen / drama-shot-prompt 的共同契约）

> 全流程**所有视觉资产**(人物/场景/道具/色卡/空间站位)用**同一套** `assets[]` 结构登记。
> ② 写"意图层"、⑤ 写"实现层"、④ 按 `ref_token` 引用。这份是唯一事实来源,改格式先改这里。

## 0. 两层 + 两级（核心约定）

- **两层**(同一条资产的两段生命周期)：
  - `intent`（②前置写）：设计计划——叫什么、锁脸文字、look 计划、style。生成**之前**就有。
  - `realized`（⑤生成时回写）：真资产——path、提取的锁定特征/调色板、怎么来的。生成**之后**才有。
  - **冲突以 `realized` 为准**：真图一旦生成，覆盖 `intent` 的预设（吸收"通读全剧的预测 ≠ 实际需要"的漂移）。
- **两级**(同一套 item schema，存两个地方)：
  - **全局** `bible/bible.json` → **去重 SoT**：每个 distinct 资产**只此一条**。新生成的必录；复用的**不新增条目**，只在该条目的 `used_by[]` 追加一次使用。
  - **每集** `<集>/资产清单.json` → **本集清单**：本集用到的**所有**资产（复用 + 新生）各列一条精简引用，让该集对 ⑥SD2 自包含。

## 1. 资产 item schema（全局 bible.json 的 `assets[]` 每条）

**全局 `bible.json` 顶层** = `{ drama, style, style_lock, logline, episodes[], assets[] }`——前 5 个是 drama meta（`style_lock` 是 ④ 原样照用的全剧渲染常量）；`assets[]` 是下面的资产条目数组。叙事（bio / 弧光 / 世界观）不在这里，在人读 `.md`。

每条 `assets[]`：

```json
{
  "asset_id": "char.navigator_k.default",        // 全局唯一键（命名见 §3）
  "category": "character",                        // character|scene|prop|color_card|blocking
  "kind": "human",                                // 仅 character：human|creature|mechanical（可省）
  "id": "navigator_k",                            // 实体稳定键（character/scene/prop 有；色卡/站位用 scope）
  "display_name": "领航员K",
  "look": "default",                              // 变体（character/scene 有；prop 可省）
  "ref_token": "@[char:navigator_k|look:default]",// ④ 提示词里引用它的槽位（命名见 §3）
  "status": "generated",                          // planned（②意图）| generated（⑤已出图）

  "intent": {                                     // ② 写：设计计划（生成前）
    "identity_anchor": "40-yo East Asian man, …", // 仅 character：锁脸/锁形（英文，全 look 复用）
    "spec_prompt": "炭灰长袍领航装 …",             // 锁定设计描述（outfit / scene desc / prop desc）
    "parent": null,                               // look 演化（chest_reveal.parent = "default"）
    "planned_episodes": ["第1集_开篇", "…"]        // ② 预判会出现在哪些集
  },

  "realized": {                                   // ⑤ 写：真资产（status=generated 才有）
    "source": "generate",                         // generate新生 | reuse复用 | edit在源上改
    "derived_from": null,                         // reuse/edit 时指向源 asset_id
    "path": "characters/navigator_k__default.png",// 相对 assets/ 的路径
    "size": "1088x1920",
    "gen_prompt": "8K hyper-realistic …",         // 真正喂出图模型的完整 prompt（存档可复现）
    "locked_features": "…真图实际锁住的五官/配色…", // 回写，覆盖 intent
    "palette": ["#C8581F", "…"],                  // 提取/锁定色（color_card 必有，其它可选）
    "binds": {"#4FC3D9": "机改青电弧眼"},          // 仅 color_card：HEX → 元素
    "composes": ["char.navigator_k.default", "scene.noah_ark_interior_hall.dim"], // 仅 blocking：合成了哪些锚
    "first_episode": "第1集_开篇"                  // 首次生成于哪集
  },

  "used_by": [                                    // 结构化使用记录（跨全剧；复用只在此追加，不新增资产条目）
    {"episode": "第1集_开篇", "group": "第一组", "shot": "1-003"},
    {"episode": "第1集_开篇", "group": "第一组", "shot": "1-004"}
  ]
}
```

- `used_by[]` 每条 = `{episode, group, shot}`：`episode` 用集目录名，`group` 用组名/序，`shot` 用镜号 `<集序>-<三位镜序>`（如 `1-003`）。**这是登记"哪集哪组哪镜用了它"的唯一结构化出口**——复用时只往这里加一条，不复制资产。
- 角色叙事（bio / 弧光 / 世界观）**不进**资产登记，留在 `bible/人物背景.md` 等人读文件（它不被机器步骤消费）。

## 2. 每集清单 `<集>/资产清单.json`（本集自包含视图）

```json
{
  "episode": "第1集_开篇",
  "uses": [
    { "asset_id": "char.navigator_k.default", "category": "character",
      "ref_token": "@[char:navigator_k|look:default]",
      "path": "characters/navigator_k__default.png",
      "source": "reuse",                          // 本集是首次新生(generate) 还是复用(reuse)
      "used_in_shots": ["1-003", "1-004"] }
  ]
}
```

- 全局 `bible.json` 是权威；`资产清单.json` 是 ⑤ 在产该集时一并写出的**派生视图**，供 ⑥ 直接拼这一集。人读版另出 `资产清单.md`。

## 3. 命名约定

| category | `asset_id` | `ref_token`（④ 槽位） | 键 |
|---|---|---|---|
| character | `char.<id>.<look>` | `@[char:<id>\|look:<look>]` | id+look |
| scene | `scene.<id>.<look>` | `@[scene:<id>\|look:<look>]` | id+look |
| prop | `prop.<id>[.<look>]` | `@[prop:<id>]` | id（+look） |
| color_card | `color.<集序>-g<组序>` | `@[color:<集序>-g<组序>]` | 组 scope（如 `1-g1`） |
| blocking | `blk.<镜号>` | `@[blocking:<镜号>]` | 镜号（如 `1-003`） |

## 4. 各 category 用哪些字段

| category | 可复用? | intent 关键字段 | realized 关键字段 |
|---|---|---|---|
| **character**（含生物/机械） | 是（id+look） | identity_anchor, spec_prompt(outfit), parent | path, gen_prompt, locked_features |
| **scene** | 是（id+look） | spec_prompt(desc) | path, gen_prompt, locked_features |
| **prop** | 是（id） | spec_prompt(desc) | path, gen_prompt |
| **color_card** | 可被邻组复用 | palette 计划（可空） | path, **palette[]**, **binds{}** |
| **blocking**（空间站位） | 否（逐镜） | 一般空（按需生） | path, **composes[]** |

- **character 首次生成 = 完整身份锚**（全身/中性/锁脸），不是"只生本镜露出的局部"，否则后续镜复用不了。
- **color_card** 对标万物生"EP-SEG 13色卡"：逐组一张、每个 HEX 绑到具体元素（`binds`）。
- **blocking** 由 `composes` 列出的人物/场景锚**合成**出本镜站位图。

## 5. 谁写谁读

| 阶段 | 对 schema 的动作 |
|---|---|
| **② drama-bible** | 通读全剧，写 `intent` 层 + `status:"planned"`（character/scene/prop 的设计计划；color_card/blocking 一般不预生） |
| **④ drama-shot-prompt** | **只读**：按 `display_name→id→look` 取 `ref_token` 写进提示词槽位；不写资产 |
| **⑤ drama-asset-gen** | 读 ④ 槽位 → 全局有 generated 就 `reuse`、没有就 `generate`、变体 `edit`；回写 `realized` + 翻 `status:"generated"` + 追加 `used_by` + 写每集 `资产清单.json` |
| **⑥ SD2 请求** | **只读**：从 `资产清单.json` 取 path/ref_token 拼 Seedance 请求 |

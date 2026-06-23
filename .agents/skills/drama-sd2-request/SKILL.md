---
name: drama-sd2-request
description: >
  短剧流水线的末端环节：把上游的产物——`资产绑定.json`（`segments[]` 每段一份**有序锚定清单 ref_set** + 顶层 `assets{token→path}`）
  + 段 prose（`*_段提示词.md`）+ 蓝图图（草图板/色卡）——拼成送入 **moyu 平台 Seedance 2.0** 视频生成的请求。
  **一段 segment = 一次 Seedance 生成 = 一条请求**（连续戏剧节拍，含段内硬切，由草图板引导）。每段做：
  ①`text` = 该段 prose 全文（从 `*_段提示词.md` 取）；
  ②`reference_images` = 该段 `ref_set` **按序**解析（`@[board:]` 草图板永远排第1=构图主引导，再 `@[char:]`人物表 / `@[palette:]`色卡 / `@[scene:]`场景 / `@[prop:]`道具）；
  ③每个 `@token` → `资产绑定.json` 的 `assets{}` 查 path → OSS 上传得签名URL → moyu CreateAsset → `asset://<id>` → 填 `metadata.content` 的 image_url。
  产物 `sd2/sd2请求.json` 含「每段：ref_set 解析后的 reference 列表（@token→path→asset://id）+ 拼好的 payload」。
  **全走 reference_image，不用 moyu 互斥的 first_frame，首帧意图写在 prose 里**。当用户要"出 SD2 / Seedance 请求、把分段提示词转成视频生成请求、
  生成送入视频模型的最终 prompt"时触发。**本环节默认只产请求/预览；真正提交 moyu（--submit）是单独动作、需用户确认。**
---

# Drama SD2 Request（SD2 请求构造）

把上游的 `资产绑定.json` + 段 prose + 蓝图图，翻成 **moyu 平台 Seedance 2.0** 的请求。**一段 segment = 一次 Seedance 生成 = 一条请求**，绑定 JSON 的 `segments[]` 天然每段一条。本环节是**确定性的格式翻译 + ref_set 按序解析 + @token→path→asset://id 登记**，不重写剧情、不改 prose。流水线契约见 `docs/流水线设计.md`。

## 单元模型（新：SD2 单元 = segment）
上游已把整集切成 **segment**——连续戏剧节拍，**段内硬切由草图板显式画给模型引导**（不再是"连续机位片段 + 末帧续接 + 拼接"那套）。每段一次 Seedance 生成：
- **单元 = segment**：每段含 3–4 镜、~12s，段内硬切/whip pan/180°轴/站位全画进**草图板（board）**。本环节不拆镜、不续接、不并行串行编排——一段就是一次独立生成。
- **全走 reference_image，不用 first_frame**：moyu 的 `first_frame` 模式与 `reference_image` **互斥**（用 first_frame 只能塞 1 张）。我们要塞草图板 + 人物表 + 色卡 + 场景 + 道具一整套，所以**全部走 `reference_image`**；**首帧意图已由上游写进 prose 里**（各镜"开篇/末帧锚定"），不用 first_frame。
- **草图板永远排第1**：`ref_set` 第一项恒为 `@[board:<seg>]`，作**构图主引导**（机位/硬切/轴线/前中后景）；其后依 `@[char:]`长相 → `@[palette:]`配色 → `@[scene:]`环境 → `@[prop:]`道具。上游已按此序写好 `ref_set`，本环节**严格照 ref_set 顺序**解析。
- **拼接成片（段间硬切在拼接处）**：各段视频生成下载后，`python scripts/concat_clips.py concat --drama X --episode Y` 按 提交记录 顺序 ffmpeg 拼成整集成片（段与段之间的硬切在这里发生）。

## 目标格式：moyu Seedance 2.0 原生请求
直连 moyu 平台生成接口 `POST /v1/video/generations`，请求体：
```json
{
  "model": "doubao-seedance-2-0-260128",
  "prompt": "<该段 prose 全文>",
  "metadata": {
    "content": [
      { "type": "text", "text": "<该段 prose 全文>" },
      { "type": "image_url", "image_url": { "url": "asset://<草图板id>" }, "role": "reference_image" },
      { "type": "image_url", "image_url": { "url": "asset://<人物表id>" }, "role": "reference_image" }
    ],
    "generate_audio": true, "resolution": "720p", "ratio": "16:9", "duration": 12
  }
}
```
- `model` = `doubao-seedance-2-0-260128`（moyu Seedance 2.0）。顶层 `prompt` 是 moyu 要求的非空占位，真实文字在 `metadata.content[0].text`。
- `metadata.content`：第 0 项 `{type:text}` = 段 prose；其后每张参考图一项 `{type:image_url, image_url.url:"asset://<id>", role:"reference_image"}`，**顺序 = ref_set 顺序（草图板第1）**。
- moyu 约束：`duration` 4–15；`resolution` 仅 **480p / 720p**（默认 720p）；`ratio` ∈ {16:9, 9:16, 1:1, 3:4, 4:3, 21:9, adaptive}，**跟成片**（步步生金 = 16:9 横屏）。
- 参考图走 **moyu 素材库 id**（`asset://<id>`，不是本地 path）；`role` 恒为 `reference_image`。

## 为什么产"中间格式"而非可直接发的 payload
我们的图在本地、moyu 参考图要 **moyu 素材库 id**，**中间必须有一步登记换 id**。所以本 skill 只产 **每段：`ref_set 解析后的 reference 列表`（@token → path）+ 拼好的 payload 骨架**；`@token→path` 换成 `asset://<id>`、提交、轮询，由对接脚本 `submit_to_moyu.py` 做（OSS 上传 → moyu CreateAsset → asset://id）。

## 输入（来自上游分段环节）
- **`资产绑定.json`**（上游锚定绑定）：
  - 顶层 `assets{}`：`@token → path` 的全集映射（如 `"@[board:ep1_1B]": "第1集_绝望降临/分段/scenes/SEG-1B_草图板_....png"`）。
  - `segments[]` 每段：`{seg, title, scene, duration_s, ratio, prose_ref, ref_set:[{token, role, why}]}`。**`ref_set` 是有序锚定清单**（草图板第1）。
- **段 prose** `段提示词.md`（上游段提示词）：每段顶部「`## <seg>｜<title>`」起的整段文字 = 该段 `text`。`prose_ref`（如 `分段/段提示词.md#SEG-1B`）指向具体段落锚点。
- **蓝图图**（上游视觉蓝图，路径在 `assets{}` 里）：草图板 `@[board:]` / 色卡 `@[palette:]`（连同人物表/场景板/道具图）都是要传给 moyu 的 reference_image 的本地 png。
- **ref_token 类型**（新增 palette / board）：

  | 类型 | token | 指向 | 在 ref_set 的位置 |
  |---|---|---|---|
  | 草图板 | `@[board:<seg>]` | 草图分镜板（每段一张） | **永远第1（构图主引导）** |
  | 人物 | `@[char:<id>\|look:<look>]` | 多面板角色参考表 | 长相 |
  | 色卡 | `@[palette:<id>]` | 13色色卡（按场景/段复用） | 配色 |
  | 场景 | `@[scene:<id>\|look:<look>]` | 场景板 | 环境 |
  | 道具 | `@[prop:<id>]` | 道具图 | 主体/道具 |

- 也接受指定多集目录（**批量**：每集各出一份 `sd2请求.json`）。
- 兜底：缺 `资产绑定.json` → 提示先跑上游分段环节；某 `@token` 在 `assets{}` 查不到 path（或 path 文件不存在）→ 照常产出但在该段标记缺图，不罢工。

## 每段转换规则
对 `segments[]` 的每段：
1. **取 prose**：从 `prose_ref` 指向的 `*_段提示词.md` 段落，取「`## <seg>｜<title>` … 到下一个 `## ` / `---` 之前」的整段文字（含 STYLE LOCK 引用、本段主体、逐镜 prose、台词、声音、末帧锚定）作 `text`。**一字不改、不翻译台词/VO**。
2. **解析 ref_set（按序，草图板第1）**：遍历 `ref_set`（保持原顺序），每个 `token` → `assets{}` 查 `path`。建该段的 reference 列表，每张 `{label:图片N, token, role, path, asset_type:"Image", role_moyu:"reference_image", moyu_id:null}`。`label` 图片N 按 ref_set 顺序从 1 编号（图片1 = 草图板）。
3. **拼 payload 骨架**：`model` = `doubao-seedance-2-0-260128`；`prompt` / `content[0].text` = 该段 prose；`content[1..]` = 每张 reference（`image_url.url` 暂留 `asset://<待登记>` 占位，由 `submit_to_moyu.py` 回填真 id）；`metadata`：`generate_audio`（默认 true）、`resolution`（默认 720p）、`ratio` = 段 `ratio`（跟成片，缺则默认 16:9）、`duration` = 段 `duration_s`。
4. **数量上限截断**：若该段 reference 数超过 moyu 上限（**实测确定**），按 **ref_set 顺序截断**——保留前 N 张（草图板 / 人物表 / 色卡优先，越靠后越先被砍），并**log 点名被砍的 token**，在该段记 `_truncated:[...]`。

> 画幅跟成片（草图板每格已按成片画幅画，16:9 横屏）；竖屏剧才 9:16。参考图可混画幅（人物表/场景 16:9、色卡任意），Seedance 按成片 ratio 渲染。

## 脚本
```bash
python scripts/build_sd2_requests.py --drama <剧名> --episode <集目录名> \
  [--resolution 720p] [--ratio 16:9] [--no-audio] [--max-refs N]
```
脚本读 `资产绑定.json`（segments[] 有序 ref_set + 顶层 assets{}）+ `段提示词.md`（按 `## SEG-XX` 抽每段 prose），按上面规则逐段转换、写 `<集>/sd2/sd2请求.json`，并逐段打印「参考图N张 / 板第1? / duration / ratio / prose字数 / 缺图token / 被截断token」。`--max-refs` 设 moyu 上限（默认不限，超出按 ref_set 顺序从尾截断）。

## 输出
```
docs/scripts/<剧名>/<集>/sd2/
└── sd2请求.json      每段一条 SD2 请求（ref_set 解析后的 reference 列表 + payload 骨架）
```
`sd2请求.json` schema（每段一条）：
```json
{
  "drama": "步步生金", "episode": "第1集_绝望降临",
  "model_code": "doubao-seedance-2-0-260128", "task_type": "video",
  "segments": [
    {
      "seg": "SEG-1B", "title": "把世界踩在脚下",
      "duration_s": 12, "ratio": "16:9", "resolution": "720p",
      "prose_ref": "分段/段提示词.md#SEG-1B",
      "_ref_set_resolved": [
        { "label": "图片1", "token": "@[board:ep1_1B]",                  "role": "storyboard(构图主引导)", "path": "第1集_绝望降临/分段/scenes/SEG-1B_草图板_把世界踩在脚下_白纸.png", "moyu_id": null },
        { "label": "图片2", "token": "@[char:su_xiaoqi|look:default]",    "role": "character(长相)",        "path": "assets/characters/苏小七.png",                                  "moyu_id": null },
        { "label": "图片3", "token": "@[palette:ep1_s1_dusk]",            "role": "palette(配色)",          "path": "第1集_绝望降临/分段/scenes/场景1色卡_石板路黄昏.png",            "moyu_id": null },
        { "label": "图片4", "token": "@[scene:rural_stone_path|look:dusk]","role": "scene(环境)",           "path": "assets/scenes/乡间石板路·黄昏.png",                              "moyu_id": null },
        { "label": "图片5", "token": "@[prop:white_sneakers]",            "role": "prop(鞋)",               "path": "assets/props/旧小白鞋.png",                                     "moyu_id": null },
        { "label": "图片6", "token": "@[prop:system_hud]",                "role": "prop(HUD中文)",          "path": "assets/props/进步系统面板.png",                                 "moyu_id": null }
      ],
      "payload": {
        "model": "doubao-seedance-2-0-260128",
        "prompt": "<段提示词.md 里 SEG-1B 全文：镜4 急停+系统机械音 / 镜5 拉远揭脸+弦乐 / 镜6 近景眼神转炽热+VO + 出剧名。含 STYLE LOCK + 三段编舞 + 物理相机 + 念白语气 + 声音 + 末帧锚定>",
        "metadata": {
          "content": [
            { "type": "text",      "text": "<同上 prose 全文>" },
            { "type": "image_url", "image_url": { "url": "asset://<待登记_board1B>" },  "role": "reference_image" },
            { "type": "image_url", "image_url": { "url": "asset://<待登记_suxiaoqi>" }, "role": "reference_image" },
            { "type": "image_url", "image_url": { "url": "asset://<待登记_palette>" },  "role": "reference_image" },
            { "type": "image_url", "image_url": { "url": "asset://<待登记_scene>" },    "role": "reference_image" },
            { "type": "image_url", "image_url": { "url": "asset://<待登记_sneakers>" }, "role": "reference_image" },
            { "type": "image_url", "image_url": { "url": "asset://<待登记_hud>" },      "role": "reference_image" }
          ],
          "generate_audio": true, "resolution": "720p", "ratio": "16:9", "duration": 12
        }
      },
      "_truncated": [], "_missing_tokens": []
    }
  ]
}
```
`content` 里 image_url 的顺序 = `_ref_set_resolved` 顺序 = ref_set 顺序（**草图板第1**）；`asset://<待登记_..>` 占位由 `submit_to_moyu.py` 按 path → moyu_id 回填。`_missing_tokens` 非空 = 某 token 在 `assets{}` 缺 path，必回查上游绑定；`_truncated` 非空 = 该段超 moyu 参考图上限被砍的 token。

## 衔接到 moyu（对接脚本 `submit_to_moyu.py`，直连 moyu 平台）
把每段 reference 的 `path` 换成 **moyu 素材库 id**（`asset://<id>`）、组 moyu Seedance 2.0 原生请求、直连 moyu 提交 + 轮询，鉴权用 moyu key。

> **重要：本环节默认只产请求/预览（拼好 `sd2请求.json` + payload 骨架）即可。真正提交 moyu（`--submit`）是单独动作、需用户确认。** 当前阶段常要求"只拼请求、不提交"——除非用户明确说"提交"，否则止步于产出 `sd2请求.json` / `moyu_payload.json`，不要带 `--submit`。

```bash
# 默认（不提交）：OSS 上传换 id + 组 moyu payload 骨架，落 moyu_payload.json，不提交
python scripts/submit_to_moyu.py --drama <剧名> --episode <集目录名> --auto-register

# 用户确认后才提交：换 id → 提交生成 → 轮询取 video_url → 下载 mp4
python scripts/submit_to_moyu.py --drama <剧名> --episode <集目录名> --auto-register --submit --poll
```
- **资产↔moyu id 映射**：剧集级台账 `assets/moyu_asset_map.json`（`ref_path → {display_name, kind, moyu_id}`，**同一张图跨段/跨集共用一个 id**，避免重复上传——草图板/色卡逐段不同，但人物表/场景/道具/HUD 多段复用）。**moyu CreateAsset 只接受公网可下载 url**（base64 / multipart 字节上传实测超时不支持），两条路换 id：
  - **`--auto-register`（推荐，全自动）**：缺 id 的图先 `oss_uploader.py` put 到 OSS 拿 signed url，再 moyu `POST /v1/assets {url,...}` 建素材、轮询到 Active、写台账。OSS 配置走 `_secrets`（`ALIYUN_OSS_*`）。大图上行慢时 `--oss-timeout` 调大。
  - **`--sync-map`（手动备选）**：先 `--init-map` 看要哪些图（带唯一上传名）→ 在 moyu UI 把图传进素材库分组 → `--sync-map` 调 `/v1/assets/list {group_id}` 按文件名自动匹配 id 填台账。
- **回填顺序 = ref_set / 图片N 顺序**：参考图按 `_ref_set_resolved` 顺序拼进 `metadata.content`（**草图板第1**），prose 与构图主引导才对得上。
- **鉴权/地址**：env 或 `scripts/_secrets.py`（gitignored，见 `_secrets.example.py`）——`MOYU_API_KEY` + `MOYU_BASE_URL`（默认 https://47.94.250.161）+ `MOYU_ASSET_GROUP_ID`，与图像生成共用同一 moyu key。
- 产 `<集>/sd2/moyu_payload.json`（每段 moyu 原生请求体）；`--submit` 打 `POST /v1/video/generations` 拿 `task_id`（落 `提交记录.json`），`--poll` 轮询 `GET /v1/video/generations/{task_id}` 取 `video_url`，成功自动下载到 `<集>/sd2/videos/`。
- **拼整集**：各段 mp4 下齐后 `python scripts/concat_clips.py concat --drama <剧名> --episode <集>` 按提交记录顺序 ffmpeg 拼成整集（**段间硬切在拼接处**）；`concat_clips.py extract-last <视频> <末帧.png>` 仅在命门失败时兜底续接用。

## 规则
- **确定性翻译**：段数/段序/seg/title/ratio/duration 照搬 `资产绑定.json`，不合并/拆分/重排；prose 文字**一字不改、不翻译**台词/VO（中文就中文）。
- **草图板永远第1**：`_ref_set_resolved` 与 `content` 的 image_url 第一项恒为 `@[board:]`；其后严格照上游写好的 ref_set 顺序。
- **全走 reference_image，不用 first_frame**：首帧意图已在 prose；不生成站位首帧图、不用 moyu first_frame 模式。
- **全传参考图**：ref_set 里的图都进 reference 列表；超 moyu 上限才按序截断并点名（`_truncated`）。
- **提交需用户确认**：默认不带 `--submit`；只产请求/预览。
- **不臆造**：不新增剧情/参考图；某 token 缺 path 或被截断只如实标记（`_missing_tokens` / `_truncated`），不补图、不改 ref_set。

## 自检（写文件前）
- 每段 `payload.metadata` 五字段齐全；`duration` = 段 `duration_s` ∈ [4,15]；`resolution` ∈ {480p,720p}；`ratio` 合法且跟成片。
- `_ref_set_resolved` 第一项是 `@[board:]`（草图板第1）；图片N 编号连续、顺序 = ref_set 顺序 = `content` 里 image_url 顺序。
- `content[0]` 是 `{type:text}` = 段 prose 全文；其后每张 reference 一个 `{type:image_url, role:reference_image}`，**无 first_frame**。
- 每个 token 都在 `assets{}` 查到 path 且文件存在（缺则进 `_missing_tokens`）；台词/VO 没被翻译；段数/seg/duration/ratio 与绑定 JSON 一致。

## 交付报告
报告：生成了哪些集的 `sd2请求.json`、各几段；每段——参考图数 / ref_set 顺序（确认草图板第1）/ duration / ratio / resolution；任何 `_missing_tokens`（缺 path 的 token，回查上游绑定）或 `_truncated`（超 moyu 上限被砍）的段；批量里被跳过的集。**明确说明本次默认只产请求/预览、未提交 moyu**；并提示下一步——经用户确认后用 `submit_to_moyu.py --auto-register`（换 id、组 payload）→ 再 `--submit --poll`（提交+取视频）→ `concat_clips.py concat` 拼整集。

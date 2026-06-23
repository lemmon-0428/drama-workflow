# 统一资产 Schema（drama-bible / drama-asset-gen / drama-segment / drama-sd2-request 的共同契约）

> 全流程**所有视觉资产**（人物多面板参考表 / 场景 / 道具 / 色卡 / 草图分镜板）用 `ref_token` 串联。
> ② 写 bible 规划层（含人物富 `sheet_spec` + `factions[]`）、③ 出库资产、④ 产色卡/草图板两类新资产并写锚定绑定、⑤ 按绑定拼请求。
> 这份是唯一事实来源，改格式先改这里。

## 0. 两层（核心约定）
- **规划层 `bible.json`（②写）**：每个 character/scene/prop 的设计意图（`intent`）+ `status:"planned"`。bible **恒为规划态**，资产出图这一事实只记 registry，不写回 bible（新资产补登除外）。
- **已生成层 `asset_registry.json`（③④写）**：真图生成日志（path/size/provider/prompt/used_by）。`ref_token` 连接两层。
- **色卡 / 草图板**是 ④ 逐段生成物 → 只进 registry + 绑定，**不进 bible**。

## 1. ref_token 类型（贯穿全流程）
| 类型 | ref_token | 指向 | 谁产 | 资产层 |
|---|---|---|---|---|
| 人物 | `@[char:<id>\|look:<look>]` | 多面板角色参考表（4格：正脸/侧脸/无脸全身/背面，9:16） | ②规划→③出图 | assets/characters/ |
| 场景 | `@[scene:<id>\|look:<look>]` | 场景板（16:9） | ②规划→③出图 | assets/scenes/ |
| 道具 | `@[prop:<id>]` | 道具图（1:1；HUD等可特殊） | ②规划→③出图 | assets/props/ |
| **色卡** | `@[palette:<id>]` | 13色HEX色卡（按场景/段复用，16:9） | ④产 | <集>/分段/scenes/ |
| **草图板** | `@[board:<seg_id>]` | 手绘草图分镜板（每段一张，白纸，16:9） | ④产 | <集>/分段/scenes/ |

- **id**：英文小写下划线，全剧稳定。`look`：造型/状态/打光变体短标签。段 id：`ep<N>_<段序>`（如 `ep1_1A`）。
- **文件名**：base=`<id>.png`、变体=`<id>__<look>.png`；色卡 `色卡_<场景>.png`、草图板 `<段>_草图板.png`。

## 2. bible.json 顶层
`{ drama, style, style_lock, logline, episodes[], factions[], assets[] }`
- `style_lock`：④ 段 prose 原样照用的全剧渲染常量（写实剧含反塑料感锚）。
- **`factions[]`（新）**：同阵营/同处境组的差异化表，供 ③ 同阵营新角色走编辑模式时个体可区分：
```json
{ "id":"su_family", "display_name":"苏家", "aesthetic_family":"当代中国贫困乡村·写实",
  "members":["su_xiaoqi","su_father","su_mother"],
  "differentiators": { "gender":"小七=女 / 父=男 / 母=女", "age":"小七=17 / 父=约48 / 母=约45",
    "physique":"小七=瘦小 / 父=精瘦佝偻跛 / 母=壮实", "hair_beard":"…", "costume":"…",
    "signature_gear":"小七=黑框眼镜+泥小白鞋 / 父=扁担竹篓 / 母=围裙抹布", "weapons":"none(生活剧)",
    "trophies":"none", "aura":"…" } }
```
无明显阵营的剧 `factions:[]`。

## 3. character 资产 item（assets[] 每条，人物）
```json
{
  "asset_id":"char.su_xiaoqi.default", "category":"character", "kind":"human",
  "id":"su_xiaoqi", "display_name":"苏小七", "look":"default",
  "ref_token":"@[char:su_xiaoqi|look:default]", "status":"planned",
  "faction":"su_family",
  "intent": {
    "sheet_spec": {
      "identity_anchor":"17-yo rural Han Chinese girl, …（一句英文锁脸，同角色各 look 逐字一致）",
      "ethnicity":"authentic rural Han Chinese teenager …",
      "physique":"slender petite …", "aura":"humble earnest quietly resilient",
      "face":{ "cheekbones":"…","eyes":"large bright black eyes behind black-framed glasses, NOT Western/K-pop",
               "hair":"straight black shoulder-length","skin":"fair slightly sun-touched, no makeup",
               "nose":"small natural East-Asian","brows":"soft natural black","skin_detail":"fresh young skin" },
      "scars":"none", "hair":"straight black shoulder-length, plain",
      "headwear":"none (black-framed glasses)",
      "upper":"faded modest thin knit top, threadbare neat",
      "lower":"loose worn trousers + worn muddy little white canvas sneakers",
      "mod":"none", "weapons":{ "primary":"none","secondary":"none","ranged":"none" },
      "palette":"muted humble rural tones …",
      "pose":"standing plainly, hand adjusting glasses",
      "lighting":"soft warm natural studio light, gentle side key + soft fill (NOT noir/hard-rim)",
      "style_ref":"authentic contemporary rural China youth drama",
      "anti":["Western face","K-pop idol","网红/整容脸","anime","model-thin glam","harsh noir rim light"]
    },
    "parent":null, "planned_episodes":["第1集_绝望降临","…"]
  }
}
```
- `sheet_spec` 字段 ↔ `drama-asset-gen/references/character-sheet-template.md` 的 `{占位}` 一一对应；③ 据此填模板出多面板参考表。
- **`lighting` 是可调参数**：明亮暖剧=柔和自然暖光；黑深/战争剧=硬单边轮廓光。
- 同角色各 look 一条独立资产，`identity_anchor` 与 `face` 在它们间逐字一致。

## 4. scene / prop 资产 item
```json
{ "asset_id":"scene.rural_stone_path.dusk", "category":"scene", "id":"rural_stone_path",
  "display_name":"乡间石板路·黄昏", "look":"dusk", "ref_token":"@[scene:rural_stone_path|look:dusk]",
  "status":"planned",
  "intent":{ "spec_prompt":"a rural stone-slab path covered with rotting leaves … at dusk, warm golden backlit",
             "parent":null, "planned_episodes":["第1集_绝望降临"] } }
```
道具同理（`@[prop:<id>]`，look 可省）。会被④用来生成草图板的特殊道具（如中文 HUD）也在③出。

## 5. ④ 的绑定 `资产绑定.json`（喂⑤；色卡/草图板在此首次以 ref_token 出现）
```json
{ "drama":"…","episode":"…",
  "assets": { "@[board:ep1_1A]":"<集>/分段/scenes/SEG-1A_草图板.png",
              "@[palette:ep1_s1_dusk]":"<集>/分段/scenes/色卡_石板路黄昏.png",
              "@[char:su_xiaoqi|look:default]":"assets/characters/苏小七.png", "...":"..." },
  "segments": [
    { "seg":"SEG-1A","title":"…","scene":"…","duration_s":12,"ratio":"16:9","prose_ref":"…#SEG-1A",
      "ref_set":[ {"token":"@[board:ep1_1A]","role":"storyboard","why":"构图主引导"},
                  {"token":"@[palette:ep1_s1_dusk]","role":"palette","why":"配色"} ] } ] }
```
- `ref_set` **有序** = 送 SD2 的 reference_image 顺序，`@[board:]` **永远第1**。

## 6. 谁写谁读
| 阶段 | 对 schema 的动作 |
|---|---|
| **② drama-bible** | 通读全剧，写 `intent`（含人物 `sheet_spec`）+ `factions[]` + `status:"planned"` |
| **③ drama-asset-gen** | 只读 bible → 出多面板角色参考表/场景/道具 → 写 `asset_registry.json`（已生成层）；同阵营走编辑模式 |
| **④ drama-segment** | 只读 bible + assets/ → 切段、产色卡(`@[palette:]`)/草图板(`@[board:]`) → 写 `资产绑定.json`（含两类新资产 path + 每段有序 ref_set） |
| **⑤ drama-sd2-request** | 只读 `资产绑定.json` + 段prose + 蓝图 → 每段 text=prose + reference_images=ref_set 解析（板第1）拼 Seedance 请求 |

## 7. registry（已生成层日志，③④ 各一份）
`asset_registry.json`：`{drama,style,updated_at,total,success,failed,assets:[{name,category,char_id,look,path,size,provider,prompt,used_by?}]}`。generate_images.py 自动维护；`size` 出图后读 PNG 回写实际画幅。

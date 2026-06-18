# 场景提示词标准

参照《人物定妆照提示词标准》制定。用途：影视剧场景资产图。所有场景资产图遵守本标准，保证整部剧的场景图风格统一、可直接用作分镜底图和置景参考。

## 核心原则：场景跟着剧本走

场景资产的默认形态是**干净的空镜底图**——无人、无文字。这有两个现实理由：

1. **具名角色单独生成、后期合成**。场景图里若画了人，既会和单独生成的人物资产冲突，又让这张底图无法复用（画面里的人不是剧组定的角色）。
2. **AI 生成的招牌文字往往是乱码错字**，糊在画面上很廉价，会毁掉整张图。

但这是**默认值，不是铁律**。当剧本把"人"或"文字"写成了这个场所之所以成立的一部分时，抹掉它们反而失真——一个空无一人的菜市场、一条没有任何招牌的霓虹街，根本不是剧本要的那个场景。这时候就该保留。下面两节讲清楚怎么判断。

## 人物：默认空镜，群戏场所例外

判断标准——**画面里的人是"环境"还是"角色"？**

- **是角色**（剧中具名人物，哪怕只是"路过的男主"）→ 永远不画进场景图，留给人物资产。
- **是环境**（无名的人海、路人甲、构成场所氛围的群体）→ 当剧本明确以"人多"定义这个场景时，应当保留为**匿名背景群演**。

典型该留人的场景：熙攘的菜市场/夜市、座无虚席的法庭旁听席或会议厅、拥挤的地铁车厢、人声鼎沸的酒吧、围观的人群。这些场景一旦清空，就失去了剧本想要的"挤""闹""围观"的戏剧氛围。

留人时的写法：把人群作为氛围词写进主体描述（如 `bustling with an anonymous crowd`、`crowded with blurred passersby`），并让他们**虚化、背身、无明确面孔**（`faceless background extras, motion-blurred, seen from behind`），避免抢戏或被误当成角色。此时**不要**再写 `no people`。

反过来，私密/安静的场景（房间、办公室、空巷）本就无关人，默认空镜即可。

## 文字：默认抑制，标识性场所例外

判断标准——**文字是这个场所的"视觉灵魂"，还是可有可无的杂项？**

- **是灵魂**（霓虹招牌林立的港式街道、便利店货架、书店、挂牌匾的老宅、贴满标语的厂房、写着站名的地铁站）→ 文字定义了这个场所的身份，应当保留，甚至可以指定招牌大致内容。
- **是杂项**（普通房间墙上的装饰画、办公室里随机的书脊、大厅前台后那面本可空白的背景墙）→ 默认抑制，避免 AI 生成乱码。

保留文字时的写法：把招牌正面写进描述（如 `glowing neon shop signs and billboards lining the street`），末尾负向声明里去掉 `no text / no signage`，只保留 `no watermark, no logo`。

**诚实提醒**：即便如此，gpt-image-2 生成的招牌文字大概率仍是似是而非的乱码/错字。如果某块牌子的**具体文字**对剧情重要（如店名、关键标语），靠提示词很难保证写对，通常需要后期单独处理——提示词阶段只负责把"这里有招牌"的视觉氛围做对。

## 硬性画面标准

| 项目 | 标准 |
|------|------|
| 画幅 | 16:9 横版，默认使用 `1920x1088`（≈1080p；1080 非16倍数故取1088） |
| 取景 | 电影感大全景定场镜头（establishing shot），广角、平视构图，交代空间全貌 |
| 陈设 | 剧本点名的关键陈设必须入镜（如"铺满玫瑰花瓣的大床"），它们往往是剧情戏眼 |
| 布光 | 与剧本标注的日/夜一致；光线写具体（自然光/床头氛围灯/顶光等） |
| 画质 | 8K 超写实、photorealistic film still、材质纹理真实、电影级质感 |
| 人物 | 默认无人空镜；剧本以"人多"定义的群戏场所，保留虚化匿名群演（见上） |
| 文字 | 默认抑制乱码文字；标识性场所保留招牌（见上） |
| 风格红线 | 影视级写实摄影，不是插画、不是概念设定图（概念图风格容易在画面里生成文字标注） |

## 提示词公式（模块化）

中间主体不变，**结尾的人物/文字约束按场景二选一**：

```
8K hyper-realistic photography, [interior/exterior] [scene type],
[day/night] scene, [lighting description], [architecture and spatial description],
[key set pieces from the script], [atmosphere keywords],
cinematic wide-angle establishing shot, eye-level composition,
photorealistic film still, high detail, realistic materials and textures,
<人物子句>, <文字子句>
```

**人物子句**：
- 默认空镜 → `empty unoccupied space, no people, no human figures`
- 群戏场所 → `bustling with an anonymous crowd, faceless background extras, motion-blurred passersby`（删去 no people）

**文字子句**：
- 默认抑制 → `no text, no words, no signage text, no labels, no watermark, no logo`
- 标识性场所 → `[正面描述招牌，如 glowing neon signs lining the street], no watermark, no logo`（删去 no text/no signage）

## 示例

### 示例 A — 默认空镜（含一次判断）

场景提取条目：

> 公司一楼大厅｜日｜现代企业总部大厅，挑高中庭，大理石地面，前台+背景墙，整面落地玻璃，明亮气派（剧本写"人来人往"）

判断：剧本虽写"人来人往"，但这是在描述大厅的繁忙日常氛围，不是要把人群当主体；而且这是男女主反复穿行的背景板，留空更利于后期合成。→ 选空镜，把"明亮气派"用光线和空间体现，而非靠人。

```
8K hyper-realistic photography, modern corporate headquarters lobby interior,
daytime scene, bright natural light flooding through floor-to-ceiling glass curtain walls,
double-height atrium with polished marble floors, sleek reception desk with a clean unmarked feature wall,
bright imposing upscale corporate atmosphere,
cinematic wide-angle establishing shot, eye-level composition,
photorealistic film still, high detail, realistic materials and textures,
empty unoccupied space, no people, no human figures, no text, no signage text, no watermark, no logo
```

### 示例 B — 保留人群 + 招牌（场所灵魂）

场景提取条目：

> 城中村夜市｜夜｜逼仄拥挤的小吃街，两旁大排档烟火气，霓虹招牌和灯箱林立，人挤人，男主在人群中追人

判断：这条街的戏剧性全在"挤"和"乱花迷眼的招牌"。清空人群和招牌就废了。男主是角色、单独生成，但**人海是环境**，保留为匿名群演；招牌是场所灵魂，保留。

```
8K hyper-realistic photography, cramped bustling night market food street exterior,
night scene, lit by warm glowing neon signs, light boxes and food-stall lamps,
narrow alley lined with open-air food stalls, steam and smoke rising, wet reflective pavement,
chaotic vibrant lively street-food atmosphere,
cinematic wide-angle establishing shot, eye-level composition,
photorealistic film still, high detail, realistic materials and textures,
crowded with an anonymous crowd, faceless background extras, motion-blurred passersby,
glowing neon shop signs and light boxes lining the street, no watermark, no logo
```

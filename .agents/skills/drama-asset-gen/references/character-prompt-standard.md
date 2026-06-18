# 人物定妆照提示词标准

来源：《人物资产调用口令》。用途：影视剧选角向 AI 人物定妆图。所有人物资产图必须遵守本标准，保证整部剧的人物图风格统一、可直接用于选角和定妆参考。

## 硬性画面标准（每条提示词都必须包含）

| 项目 | 标准 |
|------|------|
| 画幅 | 9:16 竖版，使用 `1088x1920` |
| 取景 | 全身完整入镜（头到脚），站立正面朝镜头，人体比例标准 |
| 背景 | 纯白无缝摄影棚背景，无杂物、无场景布景、无道具 |
| 布光 | 均匀柔光 / 平光补光，无杂乱硬阴影 |
| 画质 | 8K 超写实、真人肌肤毛发纹理完整、服饰面料纹理细节、电影级质感 |
| 文字 | 画面中严禁出现任何文字、水印、标签、Logo（提示词末尾必须显式声明） |

## 人设锁定要求

提示词必须把造型设计表中的内容完整翻译进去，严格锁定：

- 五官长相、肤色、年龄感
- 发型、发色（女性角色加妆容描述）
- 身高体态（高挑/清瘦/健硕等）
- 穿搭：具体到每件单品的款式、颜色、材质（上装/下装/鞋/配饰）
- 气质关键词（冷艳/单纯/干练/傲慢等）
- 人物种族外貌与剧本设定一致（中文剧本默认中国人外貌）

## 风格红线

- 拒绝网红脸、浮夸整容感、低俗化、丑化
- 画质风格统一为影视级超写实真人（不是插画、不是概念设定图——概念设定图风格容易在画面里生成文字标注）

## 提示词公式

```
8K hyper-realistic photography, full-body standing portrait, [age]-year-old Chinese [gender],
[facial features and skin], [hairstyle], [makeup — 女性角色], [body type],
wearing [specific outfit: top, bottom, shoes, accessories — 来自造型设计表],
[temperament keywords], standing straight facing camera,
complete full body in frame head to toe, standard body proportions,
pure white seamless studio background, even soft diffused studio lighting, no harsh shadows,
realistic skin hair and fabric texture, cinematic film quality,
no text, no words, no labels, no watermark, no logo
```

## 示例

造型设计表条目：

> 苏冷｜24岁女，京圈豪门继承人｜低盘发+银色发簪，红唇精致妆｜高挑大长腿｜黑色高定西装套装+白色真丝衬衫+黑色细高跟｜冷艳沉稳女总裁

生成提示词：

```
8K hyper-realistic photography, full-body standing portrait, 24-year-old Chinese woman,
strikingly beautiful face with fair porcelain skin and sharp elegant features,
long black hair in a sleek low updo fastened with a delicate silver hairpin,
refined makeup with red lips, tall slender figure with long legs,
wearing a perfectly tailored black designer pantsuit with white silk blouse and pointed black stiletto heels,
cold composed power-CEO aura, standing straight facing camera,
complete full body in frame head to toe, standard body proportions,
pure white seamless studio background, even soft diffused studio lighting, no harsh shadows,
realistic skin hair and fabric texture, cinematic film quality,
no text, no words, no labels, no watermark, no logo
```

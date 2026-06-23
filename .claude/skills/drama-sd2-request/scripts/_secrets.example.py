# 复制本文件为同目录 `_secrets.py`（已被 .gitignore 忽略、不进 git）并填写。
# 也可改用同名环境变量（env 优先）。submit_to_moyu.py / oss_uploader.py 自动读取。
# moyu 直连：视频生成 + 素材库用同一套 moyu key（和图像生成共用的那个）。
MOYU_API_KEY = ""                        # moyu 平台 key（sk-...）
MOYU_BASE_URL = "https://47.94.250.161"  # moyu 网关
MOYU_ASSET_GROUP_ID = 0                  # moyu 素材库分组 id（--auto-register / --sync-map 用）

# Aliyun OSS（--auto-register 用：本地图先 put 到 OSS 拿 signed url，再喂 moyu CreateAsset）。
# 取自 ai-drama 的 .env（ALIYUN_OSS_*）。不配则 --auto-register 不可用，改用 UI 传图 + --sync-map。
ALIYUN_OSS_ACCESS_KEY_ID = ""
ALIYUN_OSS_ACCESS_KEY_SECRET = ""
ALIYUN_OSS_BUCKET = ""
ALIYUN_OSS_ENDPOINT = "oss-cn-hangzhou.aliyuncs.com"   # 桶所在区域
ALIYUN_OSS_PUBLIC_HOST = ""                            # 可选 CDN 域名
ALIYUN_OSS_PRESIGN_EXPIRES_SECONDS = "600"             # signed url 有效期（moyu 下载窗口）

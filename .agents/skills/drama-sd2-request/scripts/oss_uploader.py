#!/usr/bin/env python3
"""
Aliyun OSS 上传 helper（移植自 ai-drama backend/app/services/oss_client.py，精简到 skill 自用）。

用途：moyu CreateAsset 只吃公网可下载 url，本地图没有 → 先 put 到 OSS、再 sign_url 出一个
短期 signed url 喂给 moyu，moyu 下载存进它自己的素材库。配置走 env 或同目录 `_secrets.py`：
  ALIYUN_OSS_ACCESS_KEY_ID / ALIYUN_OSS_ACCESS_KEY_SECRET / ALIYUN_OSS_BUCKET /
  ALIYUN_OSS_ENDPOINT / ALIYUN_OSS_PUBLIC_HOST(可选CDN) / ALIYUN_OSS_PRESIGN_EXPIRES_SECONDS
"""
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def _cfg(name, default=""):
    try:
        import _secrets as s
        builtin = getattr(s, name, "")
    except Exception:  # noqa: BLE001
        builtin = ""
    return (os.getenv(name) or "").strip() or str(builtin or default)


def is_enabled() -> bool:
    return bool(_cfg("ALIYUN_OSS_ACCESS_KEY_ID") and _cfg("ALIYUN_OSS_ACCESS_KEY_SECRET")
               and _cfg("ALIYUN_OSS_BUCKET") and _cfg("ALIYUN_OSS_ENDPOINT"))


def _bucket(timeout):
    import oss2
    ak, sk = _cfg("ALIYUN_OSS_ACCESS_KEY_ID"), _cfg("ALIYUN_OSS_ACCESS_KEY_SECRET")
    name, endpoint = _cfg("ALIYUN_OSS_BUCKET"), _cfg("ALIYUN_OSS_ENDPOINT")
    ep = endpoint if endpoint.startswith("http") else "https://" + endpoint
    return oss2.Bucket(oss2.Auth(ak, sk), ep, name, connect_timeout=timeout)


def upload_and_sign(local_path: str, key: str, *, content_type="image/png", timeout=300) -> str:
    """put 本地文件到 OSS key，返回 signed GET url（带 CDN 域名重写若配置了 public_host）。"""
    if not is_enabled():
        raise RuntimeError("OSS 未配置（_secrets ALIYUN_OSS_*）")
    bucket = _bucket(timeout)
    bucket.put_object(key, Path(local_path).read_bytes(), headers={"Content-Type": content_type})
    expires = max(int(_cfg("ALIYUN_OSS_PRESIGN_EXPIRES_SECONDS", "600") or 600), 600)
    url = bucket.sign_url("GET", key, expires, slash_safe=True)
    public_host = _cfg("ALIYUN_OSS_PUBLIC_HOST")
    if public_host:
        from urllib.parse import urlsplit, urlunsplit
        ph = public_host if public_host.startswith("http") else "https://" + public_host
        p, c = urlsplit(url), urlsplit(ph)
        url = urlunsplit((c.scheme, c.netloc, p.path, p.query, p.fragment))
    return url

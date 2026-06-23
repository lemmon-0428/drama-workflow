#!/usr/bin/env python3
"""
Generate / edit gpt-image-2 drama asset images via multiple channels with fallback.

渠道顺序（失败后依次回退）：micu → packy → moyu
每个 task 可带 "ref"（参考图路径列表）→ 走"编辑/图生图"模式（用于角色变体锁脸）；
不带 ref → 走"文生图"模式。

Usage:
    python generate_images.py --tasks '<json_array>' --output-dir <剧名>/assets \
        [--episode <集>] [--drama <剧名>] [--style <画风>]

Task 字段：
    name(必填) prompt(必填) size category(character|scene|prop)
    quality(low|medium|high|auto，默认 medium，仅 packy/moyu 生效)
    ref(参考图路径数组，相对 output-dir 或绝对路径；给了就走编辑模式)
    char_id look parent identity_anchor display_name design   # 写入台账，便于变体/时间线

Environment variables（key/url 不进仓库，放 ~/.zshrc 或 .env）：
    micu :  IMAGE2_API_KEY   IMAGE2_BASE_URL  (默认 https://www.micuapi.ai)
    packy:  PACKY_API_KEY    PACKY_BASE_URL   (默认 https://www.packyapi.com/v1)
    moyu :  MOYU_API_KEY     MOYU_BASE_URL
    IMAGE2_PROVIDER_ORDER    覆盖渠道顺序，逗号分隔，默认 "micu,packy,moyu"
"""

import argparse
import base64
import json
import os
import re
import struct
import sys
import time
from pathlib import Path

import httpx

DEFAULT_ORDER = ["micu", "packy", "moyu"]
DEFAULT_QUALITY = "medium"

# API key / URL 从同目录的 gitignored `_secrets.py` 读（不进 git）。
# env 同名变量优先 → 其次 _secrets 内置 → 都没有则该渠道跳过。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _secrets import KEYS as BUILTIN_KEYS, MOYU_URL as BUILTIN_MOYU_URL
except ImportError:  # 没有 _secrets.py（如别人 clone）→ 全走 env
    BUILTIN_KEYS, BUILTIN_MOYU_URL = {}, ""

CATEGORY_DIRS = {"character": "characters", "scene": "scenes", "prop": "props"}
# 默认画幅（task 没传 size 时按 category 自动定）：人物 9:16 / 场景·站位图 16:9 / 道具 1:1
CATEGORY_SIZES = {"character": "1088x1920", "scene": "1920x1088", "shot": "1920x1088", "prop": "1024x1024"}
MIME_BY_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".webp": "image/webp", ".gif": "image/gif"}
EXT_BY_MIME = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}

def size_meets_constraints(size: str) -> bool:
    """gpt-image-2 通用尺寸约束（packy / moyu 服务端按此校验）：
    最长边 ≤ 3840、两边都是 16 的倍数、长短边比 ≤ 3:1、总像素 ∈ [655360, 8294400]。
    满足即放行该渠道；不满足才跳过，避免白跑一次付费请求。"""
    if size == "auto":
        return True
    m = re.fullmatch(r"(\d+)x(\d+)", size)
    if not m:
        return False
    w, h = int(m.group(1)), int(m.group(2))
    long_e, short_e = max(w, h), min(w, h)
    if long_e > 3840 or w % 16 or h % 16 or short_e == 0:
        return False
    if long_e / short_e > 3.0:
        return False
    return 655_360 <= w * h <= 8_294_400


class ProviderHTTPError(Exception):
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text
        super().__init__(f"HTTP {status_code}: {text[:300]}")


# ----------------------------------------------------------------- HTTP helpers
def _post_json(url: str, api_key: str, body: dict, timeout: float) -> dict:
    with httpx.Client(timeout=timeout, verify=False) as client:
        r = client.post(url, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }, json=body)
    if r.status_code >= 400:
        raise ProviderHTTPError(r.status_code, r.text)
    return r.json()


def _post_multipart(url: str, api_key: str, data: dict, files: list, timeout: float) -> dict:
    with httpx.Client(timeout=timeout, verify=False) as client:
        r = client.post(url, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                        data=data, files=files)
    if r.status_code >= 400:
        raise ProviderHTTPError(r.status_code, r.text)
    return r.json()


def _data_url(raw: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def _size_instruction(size: str) -> str:
    if not size or size == "auto":
        return ""
    return f"Target output size: {size}. Preserve this canvas size and aspect ratio.\n\n"


def _multipart_files(field_namer, refs: list) -> list:
    files = []
    for i, (raw, mime) in enumerate(refs):
        ext = EXT_BY_MIME.get(mime, "png")
        files.append((field_namer(i, len(refs)), (f"reference_{i}.{ext}", raw, mime)))
    return files


# --------------------------------------------------------------- image extract
def extract_image_value(payload: dict):
    """从各渠道响应里取出图片（url / data: / 裸 base64），统一返回字符串或 None。"""
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("result"), str) and item["result"]:
                return item["result"]
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    v = _from_part(part)
                    if v:
                        return v

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                v = item.get("url") or item.get("b64_json")
                if isinstance(v, str) and v:
                    return v

    choices = payload.get("choices")
    if isinstance(choices, list):
        for ch in choices:
            if isinstance(ch, dict):
                v = _from_part(ch.get("message") or ch.get("delta"))
                if v:
                    return v
    return None


def _from_part(part):
    if not isinstance(part, dict):
        return None
    text = part.get("text") or part.get("content")
    if isinstance(text, str):
        m = re.search(r"data:image/[-+.\w]+;base64,[A-Za-z0-9+/=]+", text)
        if m:
            return m.group(0)
        m = re.search(r"!\[[^\]]*]\((https?://[^)\s]+)\)", text)
        if m:
            return m.group(1)
        m = re.search(r"https?://[^\s)]+?\.(?:png|jpe?g|webp)(?:\?[^\s)]*)?", text, re.I)
        if m:
            return m.group(0)
    for key in ("image_url", "url", "b64_json", "image", "src"):
        v = part.get(key)
        if isinstance(v, dict):
            v = v.get("url")
        if isinstance(v, str) and v:
            return v
    content = part.get("content")
    if isinstance(content, list):
        for nested in content:
            v = _from_part(nested)
            if v:
                return v
    return None


def download_image(value: str) -> bytes:
    if value.startswith("data:image/"):
        return base64.b64decode(value.split(",", 1)[1])
    if value.startswith("http"):
        with httpx.Client(timeout=60, verify=False) as client:
            return client.get(value).content
    return base64.b64decode(value)


def read_png_size(path: Path):
    """读 PNG 实际像素尺寸（IHDR），返回 'WxH'；非 PNG / 读失败返回 None。
    渠道（尤其 micu 走固定枚举）实际出图常 ≠ 请求 size，台账要记实际值。"""
    try:
        head = path.read_bytes()[:24]
    except OSError:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
        w, h = struct.unpack(">II", head[16:24])
        return f"{w}x{h}"
    return None


# --------------------------------------------------------------------- micu
def _micu_base() -> str:
    return (os.getenv("IMAGE2_BASE_URL") or "https://www.micuapi.ai").rstrip("/")


def micu_generate(key, prompt, size, quality, timeout):
    body = {"model": "gpt-image-2", "input": prompt, "tools": [{"type": "image_generation", "size": size}]}
    try:
        resp = _post_json(f"{_micu_base()}/v1/responses", key, body, timeout)
    except ProviderHTTPError as e:
        if e.status_code not in {404, 405, 501}:
            raise
        resp = _post_json(f"{_micu_base()}/v1/images/generations", key,
                          {"model": "gpt-image-2", "prompt": prompt, "n": 1, "size": size}, timeout)
    return extract_image_value(resp)


def micu_edit(key, prompt, size, quality, refs, timeout):
    data_urls = [_data_url(raw, mime) for raw, mime in refs]
    instr = _size_instruction(size) + prompt
    content = [{"type": "input_text", "text": instr}]
    content += [{"type": "input_image", "image_url": du} for du in data_urls]
    body = {"model": "gpt-image-2", "input": [{"role": "user", "content": content}],
            "tools": [{"type": "image_generation", "size": size}]}
    try:
        resp = _post_json(f"{_micu_base()}/v1/responses", key, body, timeout)
    except ProviderHTTPError as e:
        if e.status_code not in {404, 405, 501}:
            raise
        cc = [{"type": "text", "text": instr}] + [{"type": "image_url", "image_url": {"url": du}} for du in data_urls]
        resp = _post_json(f"{_micu_base()}/v1/chat/completions", key,
                          {"model": "gpt-image-2", "messages": [{"role": "user", "content": cc}]}, timeout)
    return extract_image_value(resp)


# --------------------------------------------------------------------- packy
def _packy_base() -> str:
    raw = (os.getenv("PACKY_BASE_URL") or "https://www.packyapi.com/v1").rstrip("/")
    return raw if raw.endswith("/v1") else f"{raw}/v1"


def packy_generate(key, prompt, size, quality, timeout):
    body = {"model": "gpt-image-2", "prompt": prompt, "n": 1, "size": size, "quality": quality}
    return extract_image_value(_post_json(f"{_packy_base()}/images/generations", key, body, timeout))


def packy_edit(key, prompt, size, quality, refs, timeout):
    files = _multipart_files(lambda i, n: "image[]", refs)
    data = {"model": "gpt-image-2", "prompt": prompt, "size": size, "n": "1", "quality": quality}
    return extract_image_value(_post_multipart(f"{_packy_base()}/images/edits", key, data, files, timeout))


# --------------------------------------------------------------------- moyu
def _moyu_base() -> str:
    return (os.getenv("MOYU_BASE_URL") or BUILTIN_MOYU_URL).rstrip("/")


def moyu_generate(key, prompt, size, quality, timeout):
    body = {"model": "gpt-image-2", "prompt": prompt, "n": 1, "size": size, "quality": quality}
    return extract_image_value(_post_json(f"{_moyu_base()}/v1/images/generations", key, body, timeout))


def moyu_edit(key, prompt, size, quality, refs, timeout):
    # 单图用 image，多图用 image[]
    files = _multipart_files(lambda i, n: "image" if n == 1 else "image[]", refs)
    data = {"model": "gpt-image-2", "prompt": prompt, "size": size, "n": "1", "quality": quality}
    return extract_image_value(_post_multipart(f"{_moyu_base()}/v1/images/edits", key, data, files, timeout))


PROVIDERS = {
    "micu":  {"key_env": "IMAGE2_API_KEY", "timeout_env": "IMAGE2_TIMEOUT_SECONDS", "timeout": 180,
              "gen": micu_generate, "edit": micu_edit, "size_ok": None},
    "packy": {"key_env": "PACKY_API_KEY", "timeout_env": "PACKY_TIMEOUT_SECONDS", "timeout": 180,
              "gen": packy_generate, "edit": packy_edit, "size_ok": size_meets_constraints},
    "moyu":  {"key_env": "MOYU_API_KEY", "timeout_env": "MOYU_IMAGE_TIMEOUT_SECONDS", "timeout": 300,
              "gen": moyu_generate, "edit": moyu_edit, "size_ok": size_meets_constraints},
}

PASSTHROUGH = ("char_id", "look", "parent", "identity_anchor", "display_name", "design")


def load_refs(ref_spec, output_dir: Path):
    refs = []
    for p in ref_spec:
        path = Path(p)
        if not path.is_absolute():
            path = output_dir / p
        raw = path.read_bytes()
        mime = MIME_BY_EXT.get(path.suffix.lower(), "image/png")
        refs.append((raw, mime))
    return refs


def run_task(task: dict, output_dir: Path, order: list, episode: str = "") -> dict:
    name = task["name"]
    prompt = task["prompt"]
    category = task.get("category", "character")
    size = task.get("size") or CATEGORY_SIZES.get(category, "1024x1024")
    quality = str(task.get("quality") or DEFAULT_QUALITY).lower()
    ref_spec = task.get("ref") or []

    if category == "shot":
        # 4b 分镜头站位合成图：落 shots/<集>/<镜号>.png，不进库台账
        subdir = (output_dir / "shots" / episode) if episode else (output_dir / "shots")
        subdir.mkdir(parents=True, exist_ok=True)
        filepath = subdir / f"{name}.png"
        record = {"name": name, "category": "shot", "episode": episode,
                  "path": str(filepath.relative_to(output_dir)), "size": size, "prompt": prompt}
    else:
        subdir = output_dir / CATEGORY_DIRS.get(category, category)
        subdir.mkdir(parents=True, exist_ok=True)
        filepath = subdir / f"{name}.png"
        record = {"name": name, "category": category, "char_id": task.get("char_id") or name,
                  "look": task.get("look") or "default", "path": str(filepath.relative_to(output_dir)),
                  "size": size, "prompt": prompt}
        for k in PASSTHROUGH:
            if task.get(k):
                record[k] = task[k]

    try:
        refs = load_refs(ref_spec, output_dir)
    except OSError as e:
        return {**record, "status": "failed", "errors": {"_refs": f"参考图读取失败: {e}"}}
    mode = "edit" if refs else "generate"

    errors = {}
    for prov in order:
        cfg = PROVIDERS.get(prov)
        if not cfg:
            continue
        key = os.getenv(cfg["key_env"], "").strip() or BUILTIN_KEYS.get(prov, "")
        if not key:
            errors[prov] = f"缺少 {cfg['key_env']}（且无内置 key）"
            continue
        if cfg.get("size_ok") and not cfg["size_ok"](size):
            errors[prov] = f"尺寸 {size} 不满足渠道约束（≤3840px、16的倍数、长短比≤3:1、像素65万~829万）"
            continue
        timeout = float(os.getenv(cfg["timeout_env"], str(cfg["timeout"])))
        try:
            if mode == "edit":
                value = cfg["edit"](key, prompt, size, quality, refs, timeout)
            else:
                value = cfg["gen"](key, prompt, size, quality, timeout)
            if not value:
                raise RuntimeError("响应中没有图片")
            filepath.write_bytes(download_image(value))
            out = {**record, "status": "success", "mode": mode, "provider": prov}
            actual = read_png_size(filepath)        # B：台账记实际画幅
            if actual:
                if actual != size:
                    out["size_requested"] = size    # 渠道枚举导致实际≠请求时留痕
                out["size"] = actual
            return out
        except Exception as e:
            errors[prov] = str(e)[:300]
            continue

    return {**record, "status": "failed", "mode": mode, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="多渠道生成/编辑 gpt-image-2 短剧资产")
    parser.add_argument("--tasks", required=True, help="JSON array of task objects")
    parser.add_argument("--output-dir", required=True, help="剧集级共享资产库目录，如 docs/scripts/<剧名>/assets")
    parser.add_argument("--episode", default="", help="本次生成所属的集（目录名），记录资产出处与复用")
    parser.add_argument("--drama", default="", help="剧名（写入台账顶层，可选）")
    parser.add_argument("--style", default="", help="全剧统一画风（写入台账顶层，可选）")
    parser.add_argument("--reuse", default="",
                        help="JSON array of 复用资产 {category,name} —— 命中台账即把本集追加进 used_by，不出图")
    args = parser.parse_args()

    order = [p.strip() for p in (os.getenv("IMAGE2_PROVIDER_ORDER") or ",".join(DEFAULT_ORDER)).split(",") if p.strip()]
    available = [p for p in order if os.getenv(PROVIDERS.get(p, {}).get("key_env", ""), "").strip() or BUILTIN_KEYS.get(p)]
    if not available:
        print(f"ERROR: 渠道 {order} 都没有配置 API key（需要 IMAGE2_API_KEY / PACKY_API_KEY / MOYU_API_KEY 之一）", file=sys.stderr)
        sys.exit(1)
    print(f"渠道顺序: {' → '.join(order)}（已配置: {', '.join(available)}）")

    tasks = json.loads(args.tasks)
    reuse_items = json.loads(args.reuse) if args.reuse else []
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, task in enumerate(tasks, 1):
        m = "站位合成" if task.get("category") == "shot" else ("编辑" if task.get("ref") else "生成")
        print(f"[{i}/{len(tasks)}] {m}: {task['name']} ({task.get('category', '?')})...")
        r = run_task(task, output_dir, order, args.episode)
        results.append(r)
        if r["status"] == "success":
            print(f"  ✓ [{r['provider']}] {output_dir / r['path']}")
        else:
            print(f"  ✗ 全部渠道失败: {r.get('errors')}")

    # 库资产合并进台账；站位图(category==shot)不进库台账
    lib_results = [r for r in results if r.get("category") != "shot"]
    if lib_results or reuse_items:
        registry_path = output_dir / "asset_registry.json"
        registry, merged = {}, {}
        if registry_path.exists():
            try:
                registry = json.loads(registry_path.read_text())
                for a in registry.get("assets", []):
                    merged[(a.get("category"), a.get("name"))] = a
            except (json.JSONDecodeError, OSError):
                registry = {}

        for r in lib_results:
            key = (r["category"], r["name"])
            existing = merged.get(key, {})
            first_ep = existing.get("first_episode") or args.episode or None
            used_by = list(dict.fromkeys((existing.get("used_by") or []) + ([args.episode] if args.episode else [])))
            asset = {**existing, **r}
            if first_ep:
                asset["first_episode"] = first_ep
            if used_by:
                asset["used_by"] = used_by
            merged[key] = asset

        # A：复用资产（本集命中、不重新出图）也把本集追加进 used_by
        for ri in reuse_items:
            rkey = (ri.get("category"), ri.get("name") or ri.get("char_id"))
            if rkey in merged and args.episode:
                ex = merged[rkey]
                ex["used_by"] = list(dict.fromkeys((ex.get("used_by") or []) + [args.episode]))
                merged[rkey] = ex
                print(f"  ↺ 复用 {rkey[1]} → used_by {ex['used_by']}")
            elif rkey not in merged:
                print(f"  ⚠ 复用项 {rkey} 不在台账（应先生成过），跳过")

        assets = list(merged.values())
        registry.update({
            "drama": args.drama or registry.get("drama", ""),
            "style": args.style or registry.get("style", ""),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(assets),
            "success": sum(1 for a in assets if a.get("status") == "success"),
            "failed": sum(1 for a in assets if a.get("status") == "failed"),
            "assets": assets,
        })
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
        print(f"\nRegistry updated: {registry_path}")

    shots = [r for r in results if r.get("category") == "shot"]
    if shots:
        sok = sum(1 for r in shots if r["status"] == "success")
        print(f"站位图 {sok}/{len(shots)} 成功 → shots/{args.episode or ''}（不入库台账）")

    ok = sum(1 for r in results if r["status"] == "success")
    print(f"本次 {ok}/{len(results)} 成功" + (f"（集：{args.episode}）" if args.episode else ""))
    if ok < len(results):
        sys.exit(2)


if __name__ == "__main__":
    main()

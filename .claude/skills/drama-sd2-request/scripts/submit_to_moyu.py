#!/usr/bin/env python3
"""
⑥ moyu 直连：把 `sd2请求.json` 的参考图换成 **moyu 素材库 id**（`asset://<id>`），
组 moyu Seedance 2.0 原生请求、直连 moyu 提交生成 + 轮询取 video_url。
**不经 ai-drama 后端**——只用 moyu 平台自己的素材库 + 生成接口。

素材 id 来源（资产 ↔ moyu id 映射）：剧集级台账 `assets/moyu_asset_map.json`
  { ref_path: { display_name, kind, moyu_id } }。同一张图跨集共用一个 id。
两种填法：
  1. 你在 moyu 平台登记素材后，把 id 填进台账（`--init-map` 先生成待填模板）。
  2. `--auto-register`：脚本调 moyu `POST /v1/assets` 自动建素材——需图能被 moyu 公开下载，
     用 `--image-url-base <前缀>` 把 ref_path 拼成公开 URL，并配 group_id。

moyu key/url（env 优先，其次同目录 gitignored `_secrets.py`，见 `_secrets.example.py`）：
  MOYU_API_KEY / MOYU_BASE_URL / MOYU_ASSET_GROUP_ID

Usage:
    python submit_to_moyu.py --drama 巴别塔 --episode 第2集_乘客 --init-map   # 先生成待填 id 模板
    python submit_to_moyu.py --drama 巴别塔 --episode 第2集_乘客               # 组 payload（不提交）
    python submit_to_moyu.py --drama 巴别塔 --episode 第2集_乘客 --submit --poll  # 提交并轮询
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
try:
    from _secrets import MOYU_API_KEY as B_KEY, MOYU_BASE_URL as B_BASE
except Exception:  # noqa: BLE001
    B_KEY, B_BASE = "", ""
try:
    from _secrets import MOYU_ASSET_GROUP_ID as B_GROUP
except Exception:  # noqa: BLE001
    B_GROUP = 0

SUCCESS = {"success", "succeeded"}
FAILED = {"fail", "failed", "failure", "error", "canceled", "cancelled"}


def _cfg(env, builtin):
    return (os.getenv(env) or "").strip() or builtin


def _client(base, key, timeout):
    return httpx.Client(base_url=base, headers={"Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"}, verify=False, timeout=timeout)


# ---- moyu 素材库 ----
def list_assets(cli, group_id):
    """列出 moyu 素材库分组下的素材：[{id, name, url}, ...]。"""
    r = cli.post("/v1/assets/list", json={"group_id": int(group_id)})
    r.raise_for_status()
    return (r.json().get("data") or {}).get("items") or []


def register_asset(cli, *, url, name, group_id, poll_timeout, poll_interval):
    # 建素材 POST：长超时(180s) + 重试——moyu 要现去下载并处理那张图，常 >60s
    aid, last = "", None
    for _ in range(4):
        try:
            r = cli.post("/v1/assets", json={"url": url, "asset_type": "Image",
                                             "name": (name or "Image")[:64], "group_id": int(group_id)}, timeout=180)
            r.raise_for_status()
            aid = str((r.json().get("data") or {}).get("id") or "")
            if aid:
                break
            last = RuntimeError(f"CreateAsset 未返回 id: {r.text[:200]}")
        except Exception as e:  # noqa: BLE001 — 超时/网络抖动 → 重试
            last = e
            time.sleep(3)
    if not aid:
        raise RuntimeError(f"moyu CreateAsset 失败(重试4次): {str(last)[:200]}")
    # 轮询 Active：查询抖动只重试、不抛
    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        try:
            g = cli.post("/v1/assets/get", json={"id": aid}, timeout=60)
            g.raise_for_status()
            status = str((g.json().get("data") or {}).get("status") or "")
        except Exception:  # noqa: BLE001
            time.sleep(poll_interval); continue
        if status.lower() == "active":
            return aid
        if status.lower() in {"failed", "fail", "error"}:
            raise RuntimeError(f"moyu 素材 {aid} 处理失败 status={status}")
        time.sleep(poll_interval)
    raise TimeoutError(f"moyu 素材 {aid} 未在限时内 Active")


# ---- moyu 生成 ----
def build_payload(group):
    p = group["params"]
    content = [{"type": "text", "text": p["prompt"]}]
    for f in group["_files"]:
        content.append({"type": "image_url", "image_url": {"url": f"asset://{f['moyu_id']}"},
                        "role": "reference_image"})
    return {"model": group["model_code"], "prompt": p["prompt"],
            "metadata": {"content": content, "generate_audio": p.get("generate_audio", True),
                         "resolution": p["resolution"], "ratio": p["aspect_ratio"], "duration": p["duration"]}}


def _status(j):
    d = j.get("data")
    n = d.get("data") if isinstance(d, dict) else None
    s = (n or {}).get("status") if isinstance(n, dict) else None
    if s is None and isinstance(d, dict):
        s = d.get("status")
    return str(s or j.get("status") or "").lower()


def _video_url(j):
    import html
    d = j.get("data")
    n = d.get("data") if isinstance(d, dict) else None
    c = n.get("content") if isinstance(n, dict) else None
    u = c.get("video_url") if isinstance(c, dict) else None
    if isinstance(u, str) and u.startswith(("http://", "https://")):
        return html.unescape(u)
    fb = d.get("fail_reason") if isinstance(d, dict) else None
    if isinstance(fb, str) and fb.startswith(("http://", "https://")):
        return html.unescape(fb)
    return None


def _safe_name(s):
    return "".join(ch if (ch.isalnum() or "一" <= ch <= "龥") else "_" for ch in str(s)).strip("_") or "video"


def download_video(url, dest_dir: Path, fname, *, timeout=600, retries=4):
    """把 moyu 返回的 TOS 签名 mp4 下载到本地（签名链接 24h 失效，要趁早下）。返回本地路径。
    原子写(.part→正式)+ 校验 Content-Length + 断流重试——TOS 偶尔中途断连只下到一半，
    不校验就会留个播放不了的残缺 mp4。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{_safe_name(fname)}.mp4"
    tmp = dest.with_name(dest.name + ".part")
    last = None
    for _ in range(retries):
        try:
            with httpx.Client(verify=False, timeout=timeout, follow_redirects=True) as c:
                with c.stream("GET", url) as r:
                    r.raise_for_status()
                    expected = int(r.headers.get("content-length") or 0)
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
            got = tmp.stat().st_size
            if expected and got < expected:          # 不完整 → 重试
                last = RuntimeError(f"不完整 {got}/{expected} 字节")
                time.sleep(2); continue
            tmp.replace(dest)                          # 完整才落正式名
            return dest
        except Exception as e:  # noqa: BLE001 — 断流/超时 → 重试
            last = e
            time.sleep(2)
    if tmp.exists():
        try: tmp.unlink()
        except OSError: pass
    raise RuntimeError(f"下载失败(重试{retries}次): {str(last)[:160]}")


def submit_task(cli, payload):
    """POST 生成请求，立刻返回 (task_id, submit_status)，不轮询——task_id 要第一时间拿到落盘。"""
    r = cli.post("/v1/video/generations", json=payload)
    r.raise_for_status()
    j = r.json()
    task_id = j.get("task_id") or j.get("id") or ((j.get("data") or {}).get("task_id") if isinstance(j.get("data"), dict) else None)
    return task_id, (_status(j) or "submitted")


def poll_task(cli, task_id, *, poll_interval, poll_timeout):
    """轮询 task 到终态，返回 {status, video_url / fail_reason}。
    轮询期网络抖动（SSL/超时）只重试、不抛——task 已提交，绝不能因为查询断一下就当失败。"""
    deadline = time.monotonic() + poll_timeout
    last_err = None
    while time.monotonic() < deadline:
        try:
            g = cli.get(f"/v1/video/generations/{task_id}")
            g.raise_for_status()
            jj = g.json()
        except Exception as e:  # noqa: BLE001 — 查询抖动，等下一轮重试
            last_err = str(e)[:200]
            time.sleep(poll_interval)
            continue
        st = _status(jj)
        if st in SUCCESS:
            return {"status": st, "video_url": _video_url(jj)}
        if st in FAILED:
            return {"status": st, "fail_reason": (jj.get("data") or {}).get("fail_reason"), "raw": jj}
        time.sleep(poll_interval)
    return {"status": "timeout", "last_error": last_err}


def collect_refs(sd2):
    """去重收集本集所有参考图：ref_path -> {display_name, kind}。"""
    seen = {}
    for g in sd2["groups"]:
        for ref in g["references"]:
            seen.setdefault(ref["path"], {
                "display_name": ref.get("display_name") or (f"站位图镜{ref.get('镜号')}" if ref.get("kind") == "站位图" else ref["label"]),
                "kind": ref.get("kind", "库资产")})
    return seen


def main():
    ap = argparse.ArgumentParser(description="moyu 直连：素材id换 asset:// + 组请求 + 可选提交")
    ap.add_argument("--drama", required=True)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--root", default="docs/scripts")
    ap.add_argument("--group", default="", help="只处理指定组：1-based 序号(如 1) 或 组名(如 第一组)")
    ap.add_argument("--init-map", action="store_true", help="生成/更新 moyu_asset_map.json 待填模板后退出")
    ap.add_argument("--sync-map", action="store_true", help="从 moyu 素材库 list 按文件名自动匹配 id 填台账（你在 moyu UI 传图后用）")
    ap.add_argument("--auto-register", action="store_true", help="全自动：缺 id 的图上传 OSS→signed url→moyu 建素材（默认走 _secrets 的 OSS 配置）")
    ap.add_argument("--image-url-base", default="", help="auto-register 备选：图已在某公开 URL 前缀下（不走 OSS）")
    ap.add_argument("--oss-timeout", type=float, default=300.0, help="OSS 上传单张超时秒（大图 / 慢上行调大）")
    ap.add_argument("--group-id", type=int, default=0, help="auto-register 的 moyu 素材库分组 id（覆盖 _secrets）")
    ap.add_argument("--query", default="", help="只续查某个 task_id 的状态/取视频（轮询恢复用），不重新提交")
    ap.add_argument("--query-all", action="store_true", help="统一收割：轮询 提交记录.json 里所有未完成 task + 下载（配合先 --submit 全发）")
    ap.add_argument("--no-download", action="store_true", help="成功后不自动下载 mp4 到本地（默认下载到 <集>/sd2/videos/）")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--poll", action="store_true")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--poll-interval", type=float, default=5.0)
    ap.add_argument("--poll-timeout", type=float, default=900.0)
    args = ap.parse_args()

    drama_dir = Path(args.root) / args.drama
    sd2 = json.loads((drama_dir / args.episode / "sd2" / "sd2请求.json").read_text(encoding="utf-8"))
    # --group：只处理指定组（auto-register 与 submit 都收窄到这一组）
    if args.group:
        gs = sd2["groups"]
        if args.group.isdigit():
            i = int(args.group) - 1
            sel = [gs[i]] if 0 <= i < len(gs) else []
        else:
            sel = [g for g in gs if g.get("group") == args.group or g.get("组名") == args.group]
        if not sel:
            print(f"ERROR: 没找到组 '{args.group}'（共 {len(gs)} 组）", file=sys.stderr)
            sys.exit(1)
        sd2["groups"] = sel
        print(f"只处理组：{sel[0]['group']} {sel[0].get('组名','')}")
    map_path = drama_dir / "assets" / "moyu_asset_map.json"
    amap = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else {}

    refs = collect_refs(sd2)

    # --init-map：写待填模板（保留已填 moyu_id），退出
    if args.init_map:
        for rel, info in refs.items():
            ent = amap.get(rel, {})
            amap[rel] = {"display_name": info["display_name"], "kind": info["kind"],
                         "上传名": rel.replace("assets/", "", 1).replace("/", "_"),
                         "moyu_id": ent.get("moyu_id", "")}
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(amap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        need = [r for r in refs if not amap.get(r, {}).get("moyu_id")]
        print(f"✓ 待填模板 {map_path}（{len(refs)} 张去重资产，缺 id {len(need)} 张）")
        print("  在 moyu UI 把下列图传进素材库分组，建议用『上传名』（唯一、跨集不撞）或保持原文件名：")
        for r in need:
            print(f"   {amap[r]['上传名']:34}← {r}  （{refs[r]['display_name']}）")
        return

    base = (_cfg("MOYU_BASE_URL", B_BASE) or "https://47.94.250.161").rstrip("/")
    key = _cfg("MOYU_API_KEY", B_KEY)
    if not key:
        print("ERROR: 缺 MOYU_API_KEY（env 或 _secrets.py）", file=sys.stderr)
        sys.exit(1)
    cli = _client(base, key, args.timeout)
    group_id = args.group_id or int(_cfg("MOYU_ASSET_GROUP_ID", str(B_GROUP)) or 0)

    # --query：只续查一个已存在的 task_id（轮询恢复 / 查错），不重新提交
    if args.query:
        pr = poll_task(cli, args.query, poll_interval=args.poll_interval, poll_timeout=args.poll_timeout)
        # 回写 提交记录.json 里匹配该 task_id 的条目，保持台账准确
        tp = drama_dir / args.episode / "sd2" / "提交记录.json"
        local = None
        if tp.exists():
            try:
                tl = json.loads(tp.read_text(encoding="utf-8"))
                for s in tl.get("submissions", []):
                    if s.get("task_id") == args.query:
                        # 成功且要下载 → 落本地，文件名用 组_组名
                        if pr.get("video_url") and not args.no_download:
                            d = download_video(pr["video_url"], drama_dir / args.episode / "sd2" / "videos",
                                               f"{s.get('group','')}_{s.get('组名','')}", timeout=args.poll_timeout)
                            local = str(d.relative_to(drama_dir / args.episode / "sd2"))
                        s.update(status=pr.get("status"), video_url=pr.get("video_url"),
                                 fail_reason=pr.get("fail_reason"), last_error=pr.get("last_error"),
                                 local_video=local, queried_at=time.strftime("%Y-%m-%d %H:%M:%S"))
                        s.pop("error", None); s.pop("error_body", None)  # 之前误标的清掉
                tp.write_text(json.dumps(tl, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                print(f"  (回写/下载警告: {str(e)[:120]})")
        print(f"task {args.query}: status={pr.get('status')}")
        if local:
            print("  已下载:", local)
        if pr.get("video_url"):
            print("  video_url:", pr["video_url"])
        if pr.get("fail_reason"):
            print("  fail_reason:", pr["fail_reason"])
        if pr.get("last_error"):
            print("  last_error:", pr["last_error"])
        return

    # --query-all：统一收割 提交记录.json 里所有未完成 task（先 --submit 全发后用）
    if args.query_all:
        tp = drama_dir / args.episode / "sd2" / "提交记录.json"
        vdir = drama_dir / args.episode / "sd2" / "videos"
        tl = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else {"submissions": []}
        for s in tl.get("submissions", []):
            tid = s.get("task_id")
            if not tid:
                continue
            if s.get("status") == "success" and s.get("local_video"):
                print(f"  {s['group']} {s.get('组名','')}：已完成 → {s['local_video']}")
                continue
            pr = poll_task(cli, tid, poll_interval=args.poll_interval, poll_timeout=args.poll_timeout)
            local = None
            if pr.get("video_url") and not args.no_download:
                try:
                    d = download_video(pr["video_url"], vdir, f"{s.get('group','')}_{s.get('组名','')}", timeout=args.poll_timeout)
                    local = str(d.relative_to(drama_dir / args.episode / "sd2"))
                except Exception as e:  # noqa: BLE001
                    print(f"    (下载警告: {str(e)[:120]})")
            s.update(status=pr.get("status"), video_url=pr.get("video_url"), fail_reason=pr.get("fail_reason"),
                     last_error=pr.get("last_error"), local_video=local or s.get("local_video"),
                     queried_at=time.strftime("%Y-%m-%d %H:%M:%S"))
            s.pop("error", None); s.pop("error_body", None)
            tp.write_text(json.dumps(tl, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  {s['group']} {s.get('组名','')}：{pr.get('status')} "
                  f"{('→ '+local) if local else (pr.get('fail_reason') or pr.get('last_error') or '')}", flush=True)
        return

    # --sync-map：从 moyu 素材库按文件名匹配 id，自动填台账
    if args.sync_map:
        if not group_id:
            print("ERROR: --sync-map 需要 group_id（_secrets 的 MOYU_ASSET_GROUP_ID 或 --group-id）", file=sys.stderr)
            sys.exit(1)
        items = list_assets(cli, group_id)
        by_name = {}
        for it in items:                       # 同名取先出现的
            nm = str(it.get("name") or "")
            if nm and nm not in by_name:
                by_name[nm] = it.get("id")
        matched = 0
        for rel, info in refs.items():
            if amap.get(rel, {}).get("moyu_id"):
                continue
            fn, stem = Path(rel).name, Path(rel).stem
            up = rel.replace("assets/", "", 1).replace("/", "_")   # 唯一上传名
            aid = (by_name.get(up) or by_name.get(Path(up).stem)
                   or by_name.get(fn) or by_name.get(stem) or by_name.get(stem + ".png"))
            if aid:
                amap[rel] = {"display_name": info["display_name"], "kind": info["kind"], "moyu_id": aid}
                matched += 1
                print(f"  ✓ {info['display_name']:14} ← {fn} → {aid}")
            else:
                print(f"  ✗ 未匹配 {fn}（{info['display_name']}）——moyu 库 group {group_id} 无同名素材")
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(amap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n同步 {matched}/{len(refs)} 张 → {map_path}")

    # auto-register 缺 id 的图：默认走 OSS 上传拿 signed url，再 moyu CreateAsset
    if args.auto_register:
        import oss_uploader
        use_oss = oss_uploader.is_enabled() and not args.image_url_base
        if not group_id or (not use_oss and not args.image_url_base):
            print("ERROR: --auto-register 需 OSS 配置（_secrets ALIYUN_OSS_*）或 --image-url-base，且需 group_id", file=sys.stderr)
            sys.exit(1)
        MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        for rel, info in refs.items():
            if amap.get(rel, {}).get("moyu_id"):
                continue
            upname = rel.replace("assets/", "", 1).replace("/", "_")
            if use_oss:
                ct = MIME.get(Path(rel).suffix.lower(), "image/png")
                print(f"  上传 OSS: {info['display_name']} ← {rel}")
                url = oss_uploader.upload_and_sign(str(drama_dir / rel), f"drama-workflow/{args.drama}/{upname}",
                                                   content_type=ct, timeout=args.oss_timeout)
            else:
                url = args.image_url_base.rstrip("/") + "/" + rel
            try:
                aid = register_asset(cli, url=url, name=upname, group_id=group_id, poll_timeout=120, poll_interval=2)
            except Exception as e:  # noqa: BLE001 — 单张失败不拖垮整批，已建的已落盘、缺的下次重跑
                print(f"  ✗ 注册失败 {info['display_name']}：{str(e)[:160]}（跳过，可重跑补）", file=sys.stderr, flush=True)
                continue
            amap[rel] = {"display_name": info["display_name"], "kind": info["kind"], "上传名": upname, "moyu_id": aid}
            map_path.write_text(json.dumps(amap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 增量落盘：中断不丢、可见进度
            print(f"  ✓ moyu 素材 {info['display_name']} → {aid}", flush=True)

    # 缺 id 检查
    missing = [r for r in refs if not amap.get(r, {}).get("moyu_id")]
    if missing:
        print("✗ 以下资产缺 moyu_id（先 --init-map 填，或 --auto-register）：", file=sys.stderr)
        for r in missing:
            print(f"   {r}  （{refs[r]['display_name']}）", file=sys.stderr)
        sys.exit(2)

    # 提交记录（task_id 第一时间落盘，便于轮询/查错/重查）
    sd2_dir = drama_dir / args.episode / "sd2"
    tasks_path = sd2_dir / "提交记录.json"
    tasklog = {"episode": args.episode, "drama": args.drama, "base_url": base, "submissions": []}
    if tasks_path.exists():
        try:
            tasklog = json.loads(tasks_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass

    def _log(group, **fields):
        for s in tasklog["submissions"]:
            if s.get("group") == group:
                s.update(fields)
                break
        else:
            tasklog["submissions"].append({"group": group, **fields})
        tasks_path.write_text(json.dumps(tasklog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 组 payload（按 references 顺序回填 moyu_id，prompt 里图片N 才对得上）
    out_groups = []
    for g in sd2["groups"]:
        g["_files"] = [{"moyu_id": amap[ref["path"]]["moyu_id"], "path": ref["path"]} for ref in g["references"]]
        payload = build_payload(g)
        rec = {"group": g["group"], "组名": g.get("组名"), "payload": payload}
        if args.submit:
            try:
                task_id, st = submit_task(cli, payload)
            except Exception as e:  # noqa: BLE001 — 提交本身失败（才是真 error）
                body = getattr(getattr(e, "response", None), "text", "") or ""
                _log(g["group"], 组名=g.get("组名"), status="error", error=str(e)[:500],
                     error_body=body[:800], submitted_at=time.strftime("%Y-%m-%d %H:%M:%S"))
                print(f"  ✗ 提交 {g['group']} 失败：{str(e)[:200]}", file=sys.stderr, flush=True)
                rec["result"] = {"status": "error", "error": str(e)[:500]}
                out_groups.append(rec)
                continue
            # 提交成功 → task_id 第一时间落盘（之后轮询再抖也不会抹掉它）
            _log(g["group"], 组名=g.get("组名"), task_id=task_id, model=payload["model"],
                 duration=payload["metadata"]["duration"], resolution=payload["metadata"]["resolution"],
                 ratio=payload["metadata"]["ratio"], status="submitted",
                 submitted_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                 query_url=f"{base}/v1/video/generations/{task_id}")
            print(f"  ✓ 提交 {g['group']} → task_id={task_id}（已记入 提交记录.json）", flush=True)
            res = {"task_id": task_id, "status": st}
            if args.poll and task_id:
                pr = poll_task(cli, task_id, poll_interval=args.poll_interval, poll_timeout=args.poll_timeout)
                res.update(pr)
                local = None
                if pr.get("video_url") and not args.no_download:
                    try:
                        d = download_video(pr["video_url"], sd2_dir / "videos",
                                           f"{g['group']}_{g.get('组名','')}", timeout=args.poll_timeout)
                        local = str(d.relative_to(sd2_dir))
                        res["local_video"] = local
                    except Exception as e:  # noqa: BLE001
                        print(f"    (下载警告: {str(e)[:120]})", flush=True)
                _log(g["group"], status=pr.get("status"), video_url=pr.get("video_url"),
                     fail_reason=pr.get("fail_reason"), last_error=pr.get("last_error"), local_video=local)
                print(f"    → {pr.get('status')} {('已下载: '+local) if local else (pr.get('video_url') or pr.get('fail_reason') or pr.get('last_error') or '')}", flush=True)
            rec["result"] = res
        out_groups.append(rec)

    out = {"episode": args.episode, "drama": args.drama, "base_url": base, "groups": out_groups}
    (sd2_dir / "moyu_payload.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n✓ moyu payload {sd2_dir/'moyu_payload.json'}（{len(out_groups)} 组）"
          + ("，已提交（task_id 见 提交记录.json）" if args.submit else "，未提交（加 --submit）"))


if __name__ == "__main__":
    main()

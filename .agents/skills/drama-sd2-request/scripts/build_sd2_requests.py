#!/usr/bin/env python3
"""
SD2 请求构造器（segment 模型）：把上游的 `资产绑定.json`（segments[] 有序 ref_set + 顶层 assets{token→path}）
+ `段提示词.md`（每段 prose）翻成 moyu Seedance 2.0 的**中间请求** `sd2请求.json`。

一段 segment = 一次 Seedance 生成 = 一条请求。每段：
  · text  = 段提示词.md 里「## <seg>｜…」起到下一个「## SEG」之前的整段文字（一字不改、不翻译台词）。
  · 解析 ref_set（保持顺序，@[board:] 第1）：每个 token → assets{} 查 path → reference 列表（图片N）。
  · payload 骨架：content[0]=text，其后每张参考图一项 image_url（url 暂留 asset://<PENDING>，由 submit_to_moyu 回填真 id）。
  · duration=段 duration_s；resolution 默认 720p；ratio=段 ratio（跟成片，缺则 16:9）。
  · 超 moyu 参考图上限（--max-refs，默认不限）→ 按 ref_set 顺序截断（越靠后越先砍），记 _truncated。
  · 某 token 在 assets{} 缺 path 或文件不存在 → 记 _missing_tokens，不罢工。

本环节**只产请求/预览，不提交**；换 asset://id、提交、轮询由 submit_to_moyu.py 做。

Usage:
    python build_sd2_requests.py --drama <剧名> --episode <集目录名> \
        [--resolution 720p] [--ratio 16:9] [--no-audio] [--max-refs N]
"""

import argparse
import json
import re
from pathlib import Path

MODEL_CODE = "doubao-seedance-2-0-260128"
SEG_HDR = re.compile(r"^##\s*.*?\b(SEG-\d+[A-Z])\b", re.M)


def extract_prose(md_text: str) -> dict:
    """段提示词.md → {seg_id: 该段整段文字}（从 '## SEG-XX…' 到下一个 '## SEG' 之前）。"""
    blocks = {}
    hits = list(SEG_HDR.finditer(md_text))
    for i, m in enumerate(hits):
        seg = m.group(1)
        start = m.start()
        end = hits[i + 1].start() if i + 1 < len(hits) else len(md_text)
        blocks[seg] = md_text[start:end].rstrip().rstrip("-").rstrip()
    return blocks


def main():
    ap = argparse.ArgumentParser(description="构造本集 SD2 中间请求（segment 模型）")
    ap.add_argument("--drama", required=True)
    ap.add_argument("--episode", required=True, help="集目录名，如 第1集_绝望降临")
    ap.add_argument("--resolution", default="720p", choices=["480p", "720p"])
    ap.add_argument("--ratio", default="", help="覆盖段 ratio（默认跟绑定里每段的 ratio）")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--max-refs", type=int, default=0, help="moyu 参考图上限（0=不限）；超出按 ref_set 顺序截断")
    ap.add_argument("--scripts-root", default="docs/scripts", help="剧集根（默认 docs/scripts）")
    args = ap.parse_args()

    base = Path(args.scripts_root) / args.drama          # 资产路径相对此根
    seg_dir = base / args.episode / "分段"
    binding = json.loads((seg_dir / "资产绑定.json").read_text(encoding="utf-8"))
    prose = extract_prose((seg_dir / "段提示词.md").read_text(encoding="utf-8"))
    assets = binding.get("assets", {})

    out_segments = []
    for s in binding["segments"]:
        seg = s["seg"]
        text = prose.get(seg, "")
        missing, truncated = [], []

        # 解析 ref_set（保持顺序）
        resolved = []
        for ref in s["ref_set"]:
            tok = ref["token"]
            path = assets.get(tok)
            exists = bool(path) and (base / path).exists()
            if not exists:
                missing.append(tok)
            resolved.append({"token": tok, "role": ref.get("role", ""),
                             "path": path, "moyu_id": None})

        # 数量截断（越靠后越先砍；board/人物/色卡在前优先保留）
        if args.max_refs and len(resolved) > args.max_refs:
            truncated = [r["token"] for r in resolved[args.max_refs:]]
            resolved = resolved[:args.max_refs]

        # 编号 图片N
        for n, r in enumerate(resolved, 1):
            r["label"] = f"图片{n}"

        ratio = args.ratio or s.get("ratio") or "16:9"
        content = [{"type": "text", "text": text}]
        for r in resolved:
            content.append({"type": "image_url",
                            "image_url": {"url": f"asset://<PENDING:{r['token']}>"},
                            "role": "reference_image"})

        out_segments.append({
            "seg": seg, "title": s.get("title", ""),
            "duration_s": s.get("duration_s"), "ratio": ratio, "resolution": args.resolution,
            "prose_ref": s.get("prose_ref", ""),
            "_ref_set_resolved": [{"label": r["label"], "token": r["token"], "role": r["role"],
                                   "path": r["path"], "moyu_id": None} for r in resolved],
            "payload": {
                "model": MODEL_CODE,
                "prompt": text,
                "metadata": {
                    "content": content,
                    "generate_audio": not args.no_audio,
                    "resolution": args.resolution,
                    "ratio": ratio,
                    "duration": s.get("duration_s"),
                },
            },
            "_truncated": truncated,
            "_missing_tokens": missing,
        })

    out = {"drama": args.drama, "episode": args.episode,
           "model_code": MODEL_CODE, "task_type": "video", "segments": out_segments}
    out_dir = base / args.episode / "sd2"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sd2请求.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"✓ 写出 {out_dir / 'sd2请求.json'}（{len(out_segments)} 段）")
    for sgo in out_segments:
        n = len(sgo["_ref_set_resolved"])
        first = sgo["_ref_set_resolved"][0]["token"] if n else "—"
        flags = []
        if sgo["_missing_tokens"]:
            flags.append(f"缺图{sgo['_missing_tokens']}")
        if sgo["_truncated"]:
            flags.append(f"截断{sgo['_truncated']}")
        board_ok = "✓板第1" if first.startswith("@[board") else "✗板不在第1"
        print(f"  {sgo['seg']:7} {n}图 {board_ok} {sgo['duration_s']}s {sgo['ratio']} "
              f"prose{len(sgo['payload']['prompt'])}字 {' '.join(flags) or 'OK'}")


if __name__ == "__main__":
    main()

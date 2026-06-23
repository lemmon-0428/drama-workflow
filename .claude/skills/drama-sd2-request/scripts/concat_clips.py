#!/usr/bin/env python3
"""
⑥ 片段后期：把一集的多条 SD2 片段视频按顺序 ffmpeg 拼成成片；并提供"截某条视频末帧"
供 `开场:续接` 的片段当开场图（无缝长镜拆分时用）。

新模型：SD2 单元 = 一条连续机位片段（不是 15s 组），硬切在这里拼。

用法：
    # 截某条片段视频的最后一帧（给续接片段当开场首帧用）
    python concat_clips.py extract-last <视频.mp4> <输出.png>

    # 把一集 videos/ 下的片段按 提交记录.json 的 group 顺序拼成成片
    python concat_clips.py concat --drama 步步生金 --episode 第1集_绝望降临 [--out 成片.mp4]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def _safe(s):
    return "".join(c if (c.isalnum() or "一" <= c <= "龥") else "_" for c in str(s)).strip("_") or "x"


def extract_last(video, out):
    """截视频最后一帧为 png（ffmpeg：seek 到尾、取 1 帧）。续接片段拿它当开场图。"""
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    # -sseof -0.1 定位到末尾前 0.1s，取最后一帧
    r = subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", str(video),
                        "-update", "1", "-q:v", "2", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not Path(out).exists():
        print(r.stderr[-600:], file=sys.stderr)
        raise SystemExit(f"截末帧失败: {video}")
    print(f"✓ 末帧 → {out}")


def concat(drama, episode, root, out):
    base = Path(root) / drama / episode / "sd2"
    vdir = base / "videos"
    rec = json.loads((base / "提交记录.json").read_text(encoding="utf-8"))
    # 按 提交记录 的 submissions 顺序（= 片段/剪辑顺序）找各片段的本地 mp4
    clips = []
    for s in rec.get("submissions", []):
        lv = s.get("local_video")
        p = (base / lv) if lv else (vdir / f"{_safe(s.get('group',''))}_{_safe(s.get('组名',''))}.mp4")
        if Path(p).exists():
            clips.append(Path(p))
        else:
            print(f"⚠ 缺片段视频，跳过：{s.get('group')} {s.get('组名')}", file=sys.stderr)
    if not clips:
        raise SystemExit("没有可拼接的片段视频")
    out = Path(out) if out else (base / f"{_safe(drama)}_{_safe(episode)}_成片.mp4")
    listfile = base / "_concat_list.txt"
    listfile.write_text("".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")
    # 优先无损 concat（要求各片段同编码/分辨率，SD2 同参数输出一般满足）
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                        "-c", "copy", str(out)], capture_output=True, text=True)
    if r.returncode != 0:                      # 退回重编码兜底
        print("（无损 concat 失败，转重编码兜底）", file=sys.stderr)
        r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-800:], file=sys.stderr)
            raise SystemExit("拼接失败")
    listfile.unlink(missing_ok=True)
    print(f"✓ 成片（{len(clips)} 片段）→ {out}")


def main():
    ap = argparse.ArgumentParser(description="片段拼接 / 截末帧")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract-last"); e.add_argument("video"); e.add_argument("out")
    c = sub.add_parser("concat")
    c.add_argument("--drama", required=True); c.add_argument("--episode", required=True)
    c.add_argument("--root", default="docs/scripts"); c.add_argument("--out", default="")
    a = ap.parse_args()
    if a.cmd == "extract-last":
        extract_last(a.video, a.out)
    else:
        concat(a.drama, a.episode, a.root, a.out or None)


if __name__ == "__main__":
    main()

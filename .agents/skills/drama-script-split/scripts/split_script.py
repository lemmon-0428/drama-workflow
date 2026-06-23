#!/usr/bin/env python3
"""
把整本/多集合一的短剧剧本按"集或幕"拆成单集文件。

支持 .docx(python-docx) / .pdf(PyMuPDF) / .txt/.md。
处理：显式分集/分幕标记、无显式首集(首幕)的开篇段落、时间码、front matter(梗概/风格)、
中英对照原样保留、非空段落无丢失校验。

用法：
  # 先 dry-run 看检测到的结构（强烈建议先看一眼再正式拆）
  python split_script.py --src 剧本.docx --drama 剧名 --dry-run
  # 正式拆分，写入 docs/scripts/<剧名>/
  python split_script.py --src 剧本.docx --drama 剧名
"""
import argparse
import re
import sys
from pathlib import Path

CN_NUM = "一二三四五六七八九十百零两"
# 分集/分幕标记：第N集 / 第N幕 / 终集 / 终幕 / ACT / EPISODE / EP n / FINALE（行首，可带【】）
MARK_RE = re.compile(
    rf"^【?\s*(?:第[{CN_NUM}\d]+[集幕]|终[集幕]|序幕|尾声|ACT\b|FINALE\b|EPISODE\b|EP[\s.]?\d+)",
    re.IGNORECASE,
)
SCENE_RE = re.compile(r"^(外景|内景|外|内|EXT|INT)[\.。]", re.IGNORECASE)
TC_RE = re.compile(r"^\[?\d{1,2}:\d{2}")


def read_paragraphs(src: Path) -> list[str]:
    ext = src.suffix.lower()
    if ext == ".docx":
        import docx
        paras = [p.text for p in docx.Document(str(src)).paragraphs]
    elif ext == ".pdf":
        import fitz
        doc = fitz.open(str(src))
        paras = []
        for page in doc:
            paras.extend(page.get_text().splitlines())
    else:  # .txt / .md / 其它纯文本
        paras = src.read_text(encoding="utf-8", errors="replace").splitlines()
    return [p.replace("\xa0", " ").rstrip() for p in paras]


def short_title(mark: str, idx: int) -> str:
    """从标记提取短标题：'【第二幕：乘客】' -> '乘客'；没有就用 第N。"""
    cn = mark.strip().strip("【】").split("/", 1)[0].strip()
    for sep in ("：", ":"):
        if sep in cn:
            return cn.split(sep, 1)[1].strip() or f"第{idx}"
    return f"第{idx}"


def segment(paras: list[str]) -> dict:
    nonempty = [i for i, p in enumerate(paras) if p.strip()]

    def first(pred):
        return next((i for i in nonempty if pred(paras[i])), None)

    idx_summary = first(lambda t: t.strip().startswith("【") and "梗概" in t)
    idx_body = first(lambda t: t.strip().startswith("【") and ("正文" in t or "剧本" in t))
    idx_title = first(lambda t: t.strip().startswith("《"))
    title = paras[idx_title] if idx_title is not None else ""
    idx_subtitle = next((i for i in nonempty if paras[i].strip().startswith("——")), None)
    subtitle = paras[idx_subtitle] if idx_subtitle is not None else ""

    marks = [i for i in nonempty if MARK_RE.match(paras[i].strip())]

    # 梗概块、风格块（front matter）
    summary, style = [], []
    scene0 = None
    if idx_summary is not None:
        end = idx_body if idx_body is not None else (marks[0] if marks else len(paras))
        summary = [paras[i] for i in range(idx_summary + 1, end) if paras[i].strip()]
    if idx_body is not None:
        end = marks[0] if marks else len(paras)
        # 首个场景头（外景/内景）= 风格块结束、正文开始处
        scene0 = next((i for i in range(idx_body + 1, end) if SCENE_RE.match(paras[i].strip())), None)
        style_end = scene0 if scene0 is not None else end
        style = [paras[i] for i in range(idx_body + 1, style_end) if paras[i].strip()]

    # 正文起点：首个场景头在首个分集标记之前 → 隐式首集，从场景头开始；否则从首个标记开始
    if scene0 is not None and (not marks or scene0 < marks[0]):
        body_start = scene0
    elif marks:
        body_start = marks[0]
    elif scene0 is not None:
        body_start = scene0
    else:
        body_start = next((i for i in nonempty if idx_body is None or i > idx_body), nonempty[0] if nonempty else 0)

    # 有些原稿用自由文本写“故事背景 / 人设 / 场景”，没有【梗概】或【剧本正文】标签。
    # 这类正文前内容也必须进入下游自包含头部，不能只出现在 dry-run 的 front matter 差额里。
    consumed_front = {i for i in (idx_title, idx_subtitle, idx_summary, idx_body) if i is not None}
    if idx_summary is not None:
        summary_end = idx_body if idx_body is not None else (marks[0] if marks else body_start)
        consumed_front.update(range(idx_summary, summary_end))
    if idx_body is not None:
        consumed_front.update(range(idx_body, body_start))
    unlabeled_front = [
        paras[i] for i in nonempty
        if i < body_start and i not in consumed_front
    ]
    if unlabeled_front:
        style = [*unlabeled_front, *style]

    # 边界：首集起点 + 各分集标记 + EOF（去重排序）
    bounds = sorted(set([body_start] + marks + [len(paras)]))
    episodes = []
    n = 0
    for a, b in zip(bounds, bounds[1:]):
        if a == len(paras):
            break
        chunk = [i for i in range(a, b) if paras[i].strip()]
        if not chunk:
            continue
        n += 1
        is_mark = bool(MARK_RE.match(paras[a].strip()))
        tc, body_from = "", a
        if is_mark:
            j = a + 1
            while j < b and not paras[j].strip():
                j += 1
            if j < b and TC_RE.match(paras[j].strip()):
                tc = paras[j].strip().strip("[]").strip()
                body_from = j + 1
            else:
                body_from = a + 1
            cn = paras[a].strip().strip("【】").split("/", 1)[0].strip()
            short = short_title(paras[a], n)
            inferred = False
        else:
            cn, short, inferred = f"第{n}（开篇）", "开篇", True
            body_from = a
        body = [paras[i] for i in range(body_from, b) if paras[i].strip()]
        episodes.append(dict(n=n, cn=cn, short=short, tc=tc, inferred=inferred, body=body))

    return dict(title=title, subtitle=subtitle, summary=summary, style=style,
                episodes=episodes, nonempty=len(nonempty))


def main():
    ap = argparse.ArgumentParser(description="按集/幕拆分短剧剧本")
    ap.add_argument("--src", required=True)
    ap.add_argument("--drama", required=True, help="剧名（输出到 docs/scripts/<剧名>/）")
    ap.add_argument("--out-base", default="docs/scripts")
    ap.add_argument("--dry-run", action="store_true", help="只打印检测结构，不写文件")
    args = ap.parse_args()

    paras = read_paragraphs(Path(args.src))
    info = segment(paras)
    eps = info["episodes"]

    display_title = info["title"] or args.drama
    print(f"标题: {display_title} | 副标题: {info['subtitle'] or '(无)'}")
    print(f"梗概 {len(info['summary'])} 行 | 风格设定 {len(info['style'])} 行 | 检测到 {len(eps)} 集/幕")
    body_total = 0
    for ep in eps:
        body_total += len(ep["body"])
        flag = " (开篇·推断)" if ep["inferred"] else (f" [{ep['tc']}]" if ep["tc"] else "")
        print(f"  第{ep['n']}集 {ep['short']:<6}{flag}  正文 {len(ep['body'])} 行")
    front_total = info["nonempty"] - body_total
    print(f"正文合计 {body_total} 行 | front matter {front_total} 行 | 非空总计 {info['nonempty']}")

    if args.dry_run:
        print("\n[dry-run] 未写文件。确认结构无误后去掉 --dry-run 正式拆分。")
        return

    root = Path(args.out_base) / args.drama
    root.mkdir(parents=True, exist_ok=True)
    ov = [display_title, info["subtitle"], "", "【故事梗概】", *info["summary"],
          "", "【创作设定 / Style Notes】", *info["style"], "", "【分集目录 / Episodes】"]
    for ep in eps:
        mark = " (时间码推断)" if ep["inferred"] else ""
        ov.append(f"  第{ep['n']}集  {ep['short']}    [{ep['tc']}]{mark}    -> 第{ep['n']}集_{ep['short']}/{args.drama}_第{ep['n']}集_{ep['short']}.txt")
    (root / "00_剧集总览.txt").write_text("\n".join(ov) + "\n", encoding="utf-8")

    for ep in eps:
        d = root / f"第{ep['n']}集_{ep['short']}"
        d.mkdir(parents=True, exist_ok=True)
        note = "（原文无显式标记，此为开篇段落，时间码为推断）" if ep["inferred"] else ""
        lines = [f"{display_title} 第{ep['n']}集 · {ep['short']}",
                 f"原始结构 / Act：{ep['cn']}{note}",
                 f"时间码 / Timecode：[{ep['tc']}]",
                 "", "──────── 创作设定（全剧通用 / Style Notes）────────",
                 info["subtitle"].strip("—"), *info["style"],
                 "", "──────── 正文 / Script ────────", *ep["body"]]
        (d / f"{args.drama}_第{ep['n']}集_{ep['short']}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n✓ 已写入 {root}（{len(eps)} 集 + 00_剧集总览.txt）")


if __name__ == "__main__":
    main()

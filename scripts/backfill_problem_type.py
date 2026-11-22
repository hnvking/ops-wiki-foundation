# -*- coding: utf-8 -*-
"""一次性回填：给已有 FAQ 文档的 frontmatter 加 problem_type 字段。

数据源：企微表格导出的 JSON（含「卡片编号」「问题类型」）。
原则：
  - 只改 frontmatter，正文一字不动；
  - 已有 problem_type 的文档跳过（可重复运行）；
  - 卡片编号匹配不上 / 问题类型为空 → 写 problem_type: ""（留空，不猜）；
  - 无 source_card_id 的手写文档 → 跳过。
用法：
  python scripts/backfill_problem_type.py --input <表格JSON>
  python scripts/backfill_problem_type.py --input <表格JSON> --apply
"""
import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAQ_DIR = os.path.join(BASE, "docs", "faqs")

VALID = {"用户操作FAQ", "审批流与权限", "配置与报表",
         "缺陷与数据问题", "系统对接与集成"}


def cell_text(v):
    if isinstance(v, list):
        if not v:
            return ""
        first = v[0]
        if isinstance(first, dict):
            return str(first.get("text") or "")
        return str(first)
    return str(v or "")


def load_mapping(path):
    d = json.load(open(path, encoding="utf-8"))
    rows = d["values"][0]["rows"]
    m = {}
    for r in rows:
        card = cell_text(r.get("卡片编号")).strip()
        if not card:
            continue
        pt = cell_text(r.get("问题类型")).strip()
        m[card] = pt if pt in VALID else ""
    return m


def split_fm(text):
    """Return (fm_lines, body, newline_style) or None."""
    nl = "\r\n" if "\r\n" in text else "\n"
    t = text.replace("\r\n", "\n")
    if not t.startswith("---\n"):
        return None
    end = t.find("\n---", 3)
    if end < 0:
        return None
    fm = t[4:end].split("\n")
    body = t[end + 5:]
    return fm, body, nl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    mapping = load_mapping(args.input)
    print("表格映射: %d 张卡片（有分类 %d）" %
          (len(mapping), sum(1 for v in mapping.values() if v)))

    changed = skipped_has = skipped_nocard = nomatch = 0
    preview = []
    for root, dirs, files in os.walk(FAQ_DIR):
        for fn in files:
            if not fn.endswith(".md") or fn == "README.md":
                continue
            p = os.path.join(root, fn)
            text = open(p, encoding="utf-8").read()
            sp = split_fm(text)
            if not sp:
                continue
            fm, body, nl = sp
            if any(line.startswith("problem_type:") for line in fm):
                skipped_has += 1
                continue
            card_line = next((l for l in fm if l.startswith("source_card_id:")), None)
            if not card_line:
                skipped_nocard += 1
                continue
            card = card_line.split(":", 1)[1].strip().strip('"').strip("'")
            pt = mapping.get(card, "")
            if card not in mapping:
                nomatch += 1
            # 分类为空则不写该字段（schema 的 enum 不接受空值），保持可选缺失
            if not pt:
                nomatch += 1  # 计入未分类，便于报告
                continue
            # 在 content_hash 行之前插入 problem_type（若无 content_hash 则追加到末尾）
            insert_at = next((i for i, l in enumerate(fm)
                              if l.startswith("content_hash:")), len(fm))
            fm.insert(insert_at, "problem_type: " + pt)
            new_text = "---\n" + "\n".join(fm) + "\n---\n" + body
            new_text = new_text.replace("\n", nl)
            preview.append((p, new_text, card, pt))
            changed += 1

    print("将回填: %d 篇 | 已有跳过: %d | 无卡片编号跳过: %d | 匹配不到: %d" %
          (changed, skipped_has, skipped_nocard, nomatch))
    from collections import Counter
    print("回填分类分布:", dict(Counter(x[3] or "<空>" for x in preview)))
    if not args.apply:
        print("\n[dry-run] 未写入。加 --apply 执行。")
        for p, _, card, pt in preview[:5]:
            print("  ", os.path.basename(p), "卡" + card, "->", pt or "<空>")
        return

    for p, new_text, _, _ in preview:
        open(p, "w", encoding="utf-8", newline="").write(new_text)
    print("\n[apply] 已回填 %d 篇。" % len(preview))


if __name__ == "__main__":
    main()

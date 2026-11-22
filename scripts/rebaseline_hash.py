# -*- coding: utf-8 -*-
"""一次性迁移：把现有 FAQ 文档的 content_hash 基线对齐到完整字段快照。

背景
----
早期 153 篇文档的 content_hash 是用「残缺的 4 字段快照」计算的
（只有 卡片编号/沉淀类型/状态，其余字段缺失记为 None）。
当「刷新表格数据」按钮拉取完整 19 字段快照后，raw-first 哈希读到的
字段集发生变化，导致 153 篇全部被误判为 updated。

本脚本只做一件事：按完整快照重算每篇文档的 content_hash 并原地更新
frontmatter 中的那一行。它**绝不改动正文**，也**不改动 generated_hash**
（后者对应当前正文，正文没变就应保持原值），因此不会触发任何正文重写。

运行（默认 dry-run，加 --apply 才写入）：
    python scripts/rebaseline_hash.py --input exports/wecom_cards.json
    python scripts/rebaseline_hash.py --input exports/wecom_cards.json --apply
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sync_from_wecom as s  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="完整字段的表格快照 JSON")
    ap.add_argument("--apply", action="store_true", help="写入（默认 dry-run）")
    args = ap.parse_args()

    data = json.load(open(args.input, encoding="utf-8"))
    rows = {}
    for r in s.rows_of(data):
        card = str(r.get("卡片编号") or "").strip()
        if card:
            rows[card] = r

    idx = s.index_existing()
    changed = skipped = missing = 0
    for card, (path, fm, body, ghash) in idx.items():
        r = rows.get(card)
        if not r:
            missing += 1
            continue
        new_chash = s.content_hash_of(r)
        old_chash = s.fm_value(fm, "content_hash")
        if new_chash == old_chash:
            skipped += 1
            continue
        changed += 1
        if not args.apply:
            continue
        # 只替换 frontmatter 中的 content_hash 一行，正文与其余字段原样保留
        with open(path, encoding="utf-8") as fh:
            text = fh.read().replace("\r", "")
        new_text, n = re.subn(
            r"(?m)^content_hash:\s*\S+\s*$",
            "content_hash: " + new_chash,
            text,
            count=1,
        )
        if n != 1:
            print("跳过（未找到 content_hash 行）:", path)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new_text)

    print("需对齐:", changed, "| 已一致:", skipped, "| 快照缺失卡片:", missing)
    if not args.apply:
        print("[DRY-RUN] 未写入。加 --apply 正式执行。")
    else:
        print("[APPLY] 已对齐 %d 篇文档的 content_hash（正文未改动）。" % changed)


if __name__ == "__main__":
    main()

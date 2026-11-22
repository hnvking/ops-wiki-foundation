# -*- coding: utf-8 -*-
"""生成按「问题类型」5 类分组的侧边栏（只替换 5.1 节点，其余节点保留）。

从 docs/faqs 下所有 FAQ 文档 frontmatter 读 problem_type，按 5 类分组；
无 problem_type 的手写文档归入「未分类」。物理目录不动，只重排链接。
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDEBAR = os.path.join(BASE, "_sidebar.md")
FAQ_DIR = os.path.join(BASE, "docs", "faqs")

ORDER = ["用户操作FAQ", "配置与报表", "缺陷与数据问题",
         "审批流与权限", "系统对接与集成"]
LABELS = {
    "用户操作FAQ": "用户操作 FAQ",
    "配置与报表": "配置与报表",
    "缺陷与数据问题": "缺陷与数据问题",
    "审批流与权限": "审批流与权限",
    "系统对接与集成": "系统对接与集成",
    "<未分类>": "其他 / 综合",
}
ORDER_ALL = ORDER + ["<未分类>"]


def fm_value(text, key):
    for line in text.split("\n"):
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def collect():
    groups = {k: [] for k in ORDER_ALL}
    for root, dirs, files in os.walk(FAQ_DIR):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn == "README.md":
                continue
            p = os.path.join(root, fn)
            text = open(p, encoding="utf-8").read().replace("\r", "")
            pt = fm_value(text, "problem_type") or "<未分类>"
            if pt not in groups:
                pt = "<未分类>"
            title = fm_value(text, "title") or fn[:-3]
            rel = os.path.relpath(p, BASE).replace("\\", "/")
            groups[pt].append((title, rel))
    return groups


def build_51():
    groups = collect()
    lines = ["  - [5.1 简道云 PM 系统](docs/faqs/jiandaoyun-pm/README.md)"]
    idx = 1
    for pt in ORDER_ALL:
        items = groups[pt]
        if not items:
            continue
        lines.append("    - [5.1.%d %s（%d篇）](docs/faqs/README.md)" %
                     (idx, LABELS[pt], len(items)))
        for j, (title, rel) in enumerate(items, 1):
            lines.append("      - [5.1.%d.%d %s](%s)" % (idx, j, title, rel))
        idx += 1
    return "\n".join(lines), {k: len(v) for k, v in groups.items()}


def main():
    new51, counts = build_51()
    text = open(SIDEBAR, encoding="utf-8").read().replace("\r\n", "\n")
    lines = text.split("\n")
    # 找 5.1 起始与 5.2 起始
    s = next((i for i, l in enumerate(lines)
              if l.strip().startswith("- [5.1 ")), None)
    e = next((i for i, l in enumerate(lines)
              if l.strip().startswith("- [5.2 ")), None)
    if s is None or e is None or e <= s:
        raise SystemExit("找不到 5.1 / 5.2 边界，未修改")
    out = lines[:s] + new51.split("\n") + lines[e:]
    open(SIDEBAR, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("侧边栏 5.1 已按问题类型分组重写。")
    print("分组统计:", counts)
    print("总FAQ:", sum(counts.values()))


if __name__ == "__main__":
    main()

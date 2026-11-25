#!/usr/bin/env python3
"""生成 FAQ 总索引、系统索引与各表单索引，确保左侧树与页面内容一致。"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAQ_DIR = os.path.join(BASE, "docs", "faqs")
OUTPUT = os.path.join(FAQ_DIR, "README.md")
PM_DIR = os.path.join(FAQ_DIR, "jiandaoyun-pm")

ORDER = ["用户操作FAQ", "配置与报表", "缺陷与数据问题",
         "审批流与权限", "系统对接与集成", "<未分类>"]
LABELS = {
    "用户操作FAQ": "用户操作 FAQ",
    "配置与报表": "配置与报表",
    "缺陷与数据问题": "缺陷与数据问题",
    "审批流与权限": "审批流与权限",
    "系统对接与集成": "系统对接与集成",
    "<未分类>": "其他 / 综合",
}


def fm(text, key):
    for line in text.split("\n"):
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def collect():
    groups = {k: [] for k in ORDER}
    for root, dirs, files in os.walk(FAQ_DIR):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn == "README.md":
                continue
            path = os.path.join(root, fn)
            text = open(path, encoding="utf-8").read().replace("\r", "")
            ptype = fm(text, "problem_type") or "<未分类>"
            if ptype not in groups:
                ptype = "<未分类>"
            rel = os.path.relpath(path, BASE).replace("\\", "/")
            groups[ptype].append({
                "title": fm(text, "title") or fn[:-3],
                "card": fm(text, "source_card_id"),
                "module": fm(text, "module"),
                "system": fm(text, "related_system"),
                "rel": rel,
            })
    return groups


def first_h1(path, fallback):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8").read().split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
    return fallback


def write_if_changed(path, text):
    if os.path.exists(path):
        old = open(path, encoding="utf-8").read()
        if old == text:
            return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"生成索引：{os.path.relpath(path, BASE)}")


def regenerate_system_readme(groups):
    path = os.path.join(PM_DIR, "README.md")
    lines = [
        "# 简道云 PM 系统 FAQ",
        "",
        "本目录收录简道云 PM 系统的运维问题。",
        "",
        "- **物理归档**仍按「系统 → 表单」两级：每个表单一个子目录，问题文件放在对应表单目录下。",
        "- **导航呈现**按「问题类型」分组，与企微表格「问题类型」字段同一口径；侧边栏 5.1 即按此分组展开。",
        "",
        "新增问题时在 frontmatter 填写 `related_system: 简道云 PM 系统`、"
        "`related_form: <表单标识>`（必填）、`problem_type: <问题类型>`（可选），"
        "并保存到 `faqs/jiandaoyun-pm/<表单标识>/<问题>.md`。",
        "",
        "## 问题类型导航",
        "",
    ]
    anchors = {
        "用户操作FAQ": "#用户操作-faq",
        "配置与报表": "#配置与报表",
        "缺陷与数据问题": "#缺陷与数据问题",
        "审批流与权限": "#审批流与权限",
        "<未分类>": "#其他--综合",
    }
    any_items = False
    for key in ORDER:
        count = len(groups[key])
        if not count:
            continue
        any_items = True
        anchor = anchors.get(key, "")
        lines.append(f"- [{LABELS[key]}（{count} 篇）](../README.md{anchor})")
    if not any_items:
        lines.append("当前 0 篇。正式写入后重跑 `python scripts/build_faq_index.py` 自动生成导航。")
    lines += [
        "",
        "完整字段与模板见 [运维问题总览](../README.md)。",
        "",
    ]
    write_if_changed(path, "\n".join(lines))


def regenerate_form_readmes():
    if not os.path.isdir(PM_DIR):
        return
    for form in sorted(os.listdir(PM_DIR)):
        form_dir = os.path.join(PM_DIR, form)
        if not os.path.isdir(form_dir):
            continue
        readme = os.path.join(form_dir, "README.md")
        title = first_h1(readme, form)
        docs = sorted(f for f in os.listdir(form_dir)
                      if f.endswith(".md") and f != "README.md")
        lines = [
            f"# {title}",
            "",
            "所属系统：简道云 PM 系统。本目录只收录与「" + title + "」表单/流程直接相关的 FAQ。",
            "",
            "## 归档规则",
            "",
            f"- 新 FAQ 必须放在本目录：`docs/faqs/jiandaoyun-pm/{form}/<问题>.md`；",
            f"- frontmatter 必须填写 `related_system: 简道云 PM 系统` 和 `related_form: {form}`。",
            "- 一个表单一个目录；跨表单问题按主要触发表单归档，在正文里链接其它表单。",
            "",
            "## FAQ 索引",
            "",
        ]
        if docs:
            for fn in docs:
                text = open(os.path.join(form_dir, fn), encoding="utf-8").read().replace("\r", "")
                doc_title = fm(text, "title") or fn[:-3]
                lines.append(f"- [{doc_title}]({fn.replace(' ', '%20')})")
        else:
            lines.append("当前 0 篇。正式写入后重跑 `python scripts/build_faq_index.py` 自动生成索引。")
        lines += ["", "返回 [简道云 PM 系统 FAQ](../README.md)。", ""]
        write_if_changed(readme, "\n".join(lines))


def main():
    groups = collect()
    total = sum(len(v) for v in groups.values())
    seq = 1
    lines = [
        "# 运维问题 FAQ 总索引",
        "",
        f"共 **{total}** 篇。按「问题类型」分组，序号全局连续且稳定引用请用卡片编号。",
        "",
        "反馈闭环：打开任意 FAQ，点右下角「👍 复用+1」或「⭐ 评分」，数据会写回企微表格。",
        "",
        "## 分组统计",
        "",
        "| 问题类型 | 数量 |",
        "|---|---:|",
    ]
    for key in ORDER:
        if groups[key]:
            lines.append(f"| {LABELS[key]} | {len(groups[key])} |")
    lines += ["", "## 全部条目", ""]

    for key in ORDER:
        items = groups[key]
        if not items:
            continue
        lines += [f"### {LABELS[key]}（{len(items)}篇）", "",
                  "| 序号 | 卡片 | 标题 | 模块 | 所属系统 |",
                  "|---:|---|---|---|---|"]
        for item in sorted(items, key=lambda x: x["rel"]):
            lines.append("| {seq:04d} | {card} | [{title}]({rel}) | {module} | {system} |".format(
                seq=seq,
                card=item["card"] or "-",
                title=item["title"].replace("|", "/"),
                rel=item["rel"].replace(" ", "%20"),
                module=item["module"] or "-",
                system=item["system"] or "-",
            ))
            seq += 1
        lines.append("")

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"生成 FAQ 索引：{OUTPUT}（{total} 篇）")
    regenerate_system_readme(groups)
    regenerate_form_readmes()


if __name__ == "__main__":
    main()

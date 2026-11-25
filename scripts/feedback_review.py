#!/usr/bin/env python3
"""从企微表格生成定期复核提醒报告。

筛选规则（可在常量区调整）：
  - 复用次数 >= 3：高频复用，值得复核内容是否仍然准确。
  - 满意度评分 <= 3：低满意度，优先复核。
  - 已复核且距今天超过 90 天：长期未复核。
"未复核"不单独作为命中条件——大多数卡片从未收到反馈，全部列出只会制造噪音。
命中任一规则即进入报告；按 复用次数降序、满意度升序 排列。

输出：exports/feedback_review.md
"""
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOCID = "s3_AfsAUAYsANQCNg6CtWWh8RnK0zr3K"
SHEET = "PM运维知识卡"
OUTPUT = os.path.join(REPO, "exports", "feedback_review.md")

MIN_REUSE = 3
MAX_RATING = 3
STALE_DAYS = 90

SQL = (
    "SELECT `RECORD_ID`, `卡片编号`, `状态`, `问题类型`, `问题原话`, "
    "`复用次数`, `满意度评分`, `最后复核日期`, `处理日期` "
    f"FROM `{SHEET}` LIMIT 1000"
)


def iso_date(value):
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)) and 20000 < float(value) < 70000:
        return (datetime(1899, 12, 30) + timedelta(days=int(value))).strftime("%Y-%m-%d")
    return str(value)


def fetch_rows():
    cli = shutil.which("wecom-cli") or "wecom-cli"
    proc = subprocess.run(
        [cli, "smartsheet", "records", "query", "--docid", DOCID, "--sql", SQL],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO, timeout=120,
    )
    raw = proc.stdout or ""
    start = raw.find("{")
    if start < 0:
        raise RuntimeError((proc.stderr or raw or "CLI 未返回 JSON")[:300])
    data = json.loads(raw[start:])
    if data.get("errcode") not in (None, 0):
        raise RuntimeError(str(data.get("errmsg") or data.get("errcode")))
    values = data.get("values") or []
    block = values[0] if values else {}
    if isinstance(block, str):
        block = json.loads(block)
    return block.get("rows") or []


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def reasons(row, today):
    out = []
    reuse = to_int(row.get("复用次数"))
    rating = row.get("满意度评分")
    rating_int = to_int(rating) if rating not in (None, "") else None
    reviewed = iso_date(row.get("最后复核日期"))
    if reuse >= MIN_REUSE:
        out.append("高频复用")
    if rating_int is not None and rating_int <= MAX_RATING:
        out.append("低满意度")
    if reviewed:
        try:
            if (today - datetime.strptime(reviewed, "%Y-%m-%d")).days > STALE_DAYS:
                out.append("超90天未复核")
        except ValueError:
            out.append("复核日期异常")
    return out


def main():
    rows = fetch_rows()
    today = datetime.now()
    candidates = []
    for row in rows:
        why = reasons(row, today)
        if why:
            candidates.append((row, why))

    candidates.sort(key=lambda x: (-to_int(x[0].get("复用次数")),
                                   to_int(x[0].get("满意度评分")) or 6,
                                   str(x[0].get("卡片编号"))))

    lines = [
        "# FAQ 定期复核提醒",
        "",
        f"生成时间：{today.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"表格总卡片：{len(rows)}；命中复核规则：{len(candidates)}。",
        "",
        "筛选规则：复用次数 ≥ 3，或满意度 ≤ 3，或已复核但超过 90 天未再复核。",
        "",
        "| 卡片编号 | 问题摘要 | 复用 | 满意度 | 最后复核 | 命中原因 |",
        "|---|---|---:|---:|---|---|",
    ]
    if not candidates:
        lines.append("| - | 暂无需要复核的卡片 | 0 | - | - | - |")
    for row, why in candidates:
        title = str(row.get("问题原话") or "").replace("|", "/").replace("\n", " ")[:60]
        lines.append("| {card} | {title} | {reuse} | {rating} | {reviewed} | {why} |".format(
            card=str(row.get("卡片编号") or ""),
            title=title,
            reuse=to_int(row.get("复用次数")),
            rating=("" if row.get("满意度评分") in (None, "") else to_int(row.get("满意度评分"))),
            reviewed=iso_date(row.get("最后复核日期")),
            why="、".join(why),
        ))
    lines.append("")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"生成复核报告：{OUTPUT}（{len(candidates)} 条）")


if __name__ == "__main__":
    main()

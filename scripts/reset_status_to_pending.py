#!/usr/bin/env python3
"""把企微表格中已沉淀的卡片状态重置为「待审核」。

默认 dry-run；加 --apply 才真正写入。
只重置 已发布 / 已审核 / 已沉淀；不动 不适用 / 废弃 / 已归档 / 待复核。
"""
import argparse
import json
import shutil
import subprocess

DOCID = "s3_AfsAUAYsANQCNg6CtWWh8RnK0zr3K"
SHEET = "PM运维知识卡"
PENDING = {"id": "37htx0", "text": "待审核"}
TARGET_TEXTS = {"已发布", "已审核", "已沉淀"}
QUERY_SQL = (
    "SELECT `RECORD_ID`, `卡片编号`, `状态` "
    f"FROM `{SHEET}` LIMIT 1000"
)


def run_cli(args, timeout=120):
    cli = shutil.which("wecom-cli") or "wecom-cli"
    proc = subprocess.run(
        [cli] + args, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    raw = proc.stdout or ""
    start = raw.find("{")
    if start < 0:
        raise RuntimeError((proc.stderr or raw or "CLI 未返回 JSON")[:300])
    data = json.loads(raw[start:])
    if data.get("errcode") not in (None, 0):
        raise RuntimeError(str(data.get("errmsg") or data.get("errcode")))
    return data


def fetch_rows():
    data = run_cli(["smartsheet", "records", "query", "--docid", DOCID, "--sql", QUERY_SQL])
    values = data.get("values") or []
    block = values[0] if values else {}
    if isinstance(block, str):
        block = json.loads(block)
    rows = block.get("rows") or []
    result = []
    for row in rows:
        status = row.get("状态")
        text = status.get("text") if isinstance(status, dict) else str(status or "")
        if text in TARGET_TEXTS:
            result.append({"record_id": row.get("RECORD_ID"), "card": row.get("卡片编号"), "status": text})
    return result


def status_text(value):
    if isinstance(value, dict):
        return value.get("text", "")
    return str(value or "")


def update_batch(rows):
    payload = {
        "docid": DOCID,
        "sheet_title": SHEET,
        "key_type": "field_title",
        "type": "update",
        "records": [
            {"record_id": row["record_id"], "values": {"状态": PENDING}}
            for row in rows
        ],
    }
    run_cli(["smartsheet", "records", "update", "--json", json.dumps(payload, ensure_ascii=False)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="真正写入表格")
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    rows = fetch_rows()
    print(f"待重置卡片：{len(rows)}")
    if not rows:
        return
    print("样例：", [(r["card"], r["status"]) for r in rows[:5]])
    if not args.apply:
        print("dry-run，未写入。加 --apply 执行。")
        return

    written = 0
    for i in range(0, len(rows), args.batch_size):
        batch = rows[i:i + args.batch_size]
        update_batch(batch)
        written += len(batch)
        print(f"已重置 {written}/{len(rows)}", flush=True)

    data = run_cli(["smartsheet", "records", "query", "--docid", DOCID, "--sql", QUERY_SQL])
    values = data.get("values") or []
    block = values[0] if values else {}
    if isinstance(block, str):
        block = json.loads(block)
    remain = [r for r in block.get("rows", []) if status_text(r.get("状态")) in TARGET_TEXTS]
    print(f"完成。写入 {written} 条，剩余目标状态 {len(remain)} 条。")


if __name__ == "__main__":
    main()

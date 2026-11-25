#!/usr/bin/env python3
"""生成 WeKnora 导入 JSON。

以 docs_export.json 为输入（不存在时提示先运行 export_for_rag.py），
输出 exports/weknora_import.json。文档 ID 优先使用 source_card_id，
保证 RAG 回答能回传溯源编号并做增量删旧导新。
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from lib.frontmatter import find_repo_root, parse_frontmatter_and_body  # noqa: E402

INPUT = os.path.join(REPO, "exports", "docs_export.json")
OUTPUT = os.path.join(REPO, "exports", "weknora_import.json")
UPLOAD_DIR = os.path.join(REPO, "exports", "weknora_upload")


def build_from_docs():
    docs_dir = os.path.join(find_repo_root(), "docs")
    documents = []
    for root, dirs, files in os.walk(docs_dir):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn.upper() == "README.MD":
                continue
            path = os.path.join(root, fn)
            fm, body = parse_frontmatter_and_body(path)
            fm = fm or {}
            rel = os.path.relpath(path, find_repo_root()).replace("\\", "/")
            documents.append({
                "source_path": rel,
                "frontmatter": fm,
                "body": body,
            })
    return documents


def write_upload_files(documents):
    """同时输出可直接上传到 WeKnora 知识库的 Markdown 文件。"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for old in os.listdir(UPLOAD_DIR):
        if old.endswith(".md"):
            os.remove(os.path.join(UPLOAD_DIR, old))

    keys = ["title", "type", "source_card_id", "source_path",
            "related_system", "related_form", "problem_type", "module", "tags"]
    for doc in documents:
        meta = dict(doc["metadata"])
        meta["title"] = doc["title"]
        lines = ["---"]
        for key in keys:
            value = meta.get(key)
            if value in (None, "", []):
                continue
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        lines += ["---", "", doc["content"], ""]
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", doc["title"])[:60]
        filename = f"{doc['id']}_{safe}.md"
        with open(os.path.join(UPLOAD_DIR, filename), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    return len(documents)


def main():
    if os.path.exists(INPUT):
        with open(INPUT, encoding="utf-8") as f:
            source = json.load(f)
        docs = source.get("documents", [])
    else:
        docs = build_from_docs()

    out_docs = []
    seen = set()
    for i, doc in enumerate(docs, 1):
        fm = doc.get("frontmatter") or {}
        card = str(fm.get("source_card_id") or "").strip()
        doc_id = card or f"doc-{i:04d}"
        if doc_id in seen:
            doc_id = f"{doc_id}-{i}"
        seen.add(doc_id)
        out_docs.append({
            "id": doc_id,
            "title": fm.get("title") or doc.get("title") or "Untitled",
            "content": doc.get("body") or "",
            "metadata": {
                "source_path": doc.get("source_path", ""),
                "type": fm.get("type") or doc.get("type") or "unknown",
                "related_system": fm.get("related_system", ""),
                "related_form": fm.get("related_form", ""),
                "problem_type": fm.get("problem_type", ""),
                "module": fm.get("module", ""),
                "tags": fm.get("tags", []),
                "content_hash": fm.get("content_hash", ""),
                "source_card_id": card,
            },
        })

    payload = {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_documents": len(out_docs),
        "documents": out_docs,
    }
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    write_upload_files(out_docs)
    print(f"生成 WeKnora 导入文件：{OUTPUT}（{len(out_docs)} 篇）")
    print(f"可上传 Markdown：{UPLOAD_DIR}")


if __name__ == "__main__":
    main()

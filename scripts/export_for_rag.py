#!/usr/bin/env python3
"""
export_for_rag.py — Export ops-wiki-foundation docs to JSON for RAG pipelines.

Reads all Markdown files in docs/, extracts YAML frontmatter and body content,
and writes a single JSON file to exports/docs_export.json.

The output format is designed to be simple and tool-agnostic so it can be
consumed by any embedding or retrieval system.

Usage:
    python3 scripts/export_for_rag.py

Output:
    exports/docs_export.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the scripts directory to the path so we can import shared lib.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.frontmatter import find_repo_root, parse_frontmatter_and_body


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def main():
    repo_root = find_repo_root()
    docs_dir = repo_root / "docs"
    export_dir = repo_root / "exports"

    if not docs_dir.exists():
        print(f"ERROR: docs/ directory not found at {docs_dir}")
        sys.exit(1)

    # Create exports directory if needed.
    export_dir.mkdir(exist_ok=True)

    # Collect all .md files in docs/ (excluding READMEs).
    md_files = sorted(
        p for p in docs_dir.rglob("*.md")
        if p.name.upper() != "README.MD"
    )

    if not md_files:
        print("No Markdown files found in docs/ (excluding READMEs).")
        sys.exit(0)

    documents = []

    for filepath in md_files:
        rel_path = str(filepath.relative_to(repo_root))
        frontmatter, body = parse_frontmatter_and_body(filepath)

        # Promote 'type' and 'title' to top level for easier RAG filtering.
        fm = frontmatter if frontmatter else {}
        doc = {
            "source_path": rel_path,
            "type": fm.get("type", "unknown"),
            "title": fm.get("title", "Untitled"),
            "frontmatter": fm,
            "body": body,
        }
        documents.append(doc)
        print(f"Exported: {rel_path}")

    # Build the export payload.
    export_data = {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_documents": len(documents),
        "documents": documents,
    }

    # Write the JSON file.
    output_path = export_dir / "docs_export.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nExported {len(documents)} document(s) to {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
validate_docs.py — Validate YAML frontmatter in ops-wiki-foundation docs.

Reads schemas/required-fields.yml and checks every Markdown file in docs/
to ensure it has the required frontmatter fields for its document type.

Checks performed:
    - Required fields are present and non-empty.
    - Field values match allowed enums (if defined in schema field_constraints).
    - Date fields match YYYY-MM-DD format.
    - List fields are non-empty.
    - Files are in the correct directory for their document type.
    - FAQ files follow docs/faqs/<system>/<form>/<page>.md and related_form matches the form directory.

Usage:
    python3 scripts/validate_docs.py

Exit codes:
    0 — All documents pass validation.
    1 — One or more documents have validation errors.
"""

import re
import sys
import yaml
from pathlib import Path

# Add the scripts directory to the path so we can import shared lib.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.frontmatter import find_repo_root, parse_frontmatter


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_schema(repo_root):
    """Load the required-fields schema from schemas/required-fields.yml."""
    schema_path = repo_root / "schemas" / "required-fields.yml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_type_map(schema):
    """
    Build a mapping from frontmatter 'type' value to its full config.

    Returns: { "service": { "required": [...], "directory": "...", ... }, ... }
    """
    type_map = {}
    for doc_type, config in schema.get("document_types", {}).items():
        type_map[doc_type] = config
    return type_map


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_file(filepath, type_map, repo_root):
    """
    Validate a single Markdown file.

    Returns a list of error strings (empty list = valid).
    """
    errors = []

    frontmatter = parse_frontmatter(filepath)
    if frontmatter is None:
        errors.append("No valid YAML frontmatter found.")
        return errors

    # --- Check document type ---
    doc_type = frontmatter.get("type")
    if doc_type is None:
        errors.append("Missing 'type' field in frontmatter.")
        return errors

    config = type_map.get(doc_type)
    if config is None:
        errors.append(
            f"Unknown document type '{doc_type}'. "
            f"Valid types: {', '.join(sorted(type_map.keys()))}"
        )
        return errors

    required_fields = config.get("required", [])
    constraints = config.get("field_constraints", {})

    # --- Check required fields are present and non-empty ---
    for field in required_fields:
        value = frontmatter.get(field)
        if value is None:
            errors.append(f"Missing required field: '{field}'")
        elif isinstance(value, str) and value.strip() == "":
            errors.append(f"Required field '{field}' is empty.")
        elif isinstance(value, list) and len(value) == 0:
            errors.append(f"Required field '{field}' is an empty list.")

    # --- Check field constraints (enums, dates, lists) ---
    for field, constraint in constraints.items():
        value = frontmatter.get(field)
        if value is None:
            # Field not present — only an error if it's required (already caught above).
            continue

        ctype = constraint.get("type")

        if ctype == "enum":
            allowed = constraint.get("values", [])
            if value not in allowed:
                errors.append(
                    f"Field '{field}' has invalid value '{value}'. "
                    f"Allowed: {', '.join(str(v) for v in allowed)}"
                )

        elif ctype == "date":
            str_value = str(value)
            if not DATE_PATTERN.match(str_value):
                errors.append(
                    f"Field '{field}' has invalid date format '{str_value}'. "
                    f"Expected: YYYY-MM-DD"
                )

        elif ctype == "list":
            if not isinstance(value, list):
                errors.append(
                    f"Field '{field}' should be a list, got {type(value).__name__}."
                )
            elif len(value) == 0:
                errors.append(f"Field '{field}' is an empty list.")

    # --- Check file is in the correct directory ---
    rel_path = filepath.relative_to(repo_root)
    expected_dir = config.get("directory")
    if expected_dir:
        expected_prefix = Path(expected_dir)
        if not str(rel_path).startswith(str(expected_prefix)):
            errors.append(
                f"File is in '{rel_path.parent}' but type '{doc_type}' "
                f"should be in '{expected_dir}'."
            )

    # --- FAQ 必须按 系统 → 表单 两级归档 ---
    # 路径固定：docs/faqs/<系统标识>/<表单标识>/<问题>.md
    # related_form 必须与所在表单目录名一致，避免问题散落在错误的表单下。
    if doc_type == "faq":
        parts = rel_path.parts
        if len(parts) != 5 or parts[0] != "docs" or parts[1] != "faqs":
            errors.append(
                "FAQ 必须放在 docs/faqs/<系统标识>/<表单标识>/<问题>.md，"
                f"当前路径为 '{rel_path.as_posix()}'."
            )
        else:
            form_dir = parts[3]
            related_form = frontmatter.get("related_form")
            if related_form is not None and str(related_form).strip() != form_dir:
                errors.append(
                    f"related_form is '{related_form}' but the FAQ is in "
                    f"form directory '{form_dir}'."
                )

    return errors


def main():
    repo_root = find_repo_root()
    schema = load_schema(repo_root)
    type_map = build_type_map(schema)

    docs_dir = repo_root / "docs"
    if not docs_dir.exists():
        print(f"ERROR: docs/ directory not found at {docs_dir}")
        sys.exit(1)

    # Collect all .md files in docs/ (excluding README files).
    md_files = sorted(
        p for p in docs_dir.rglob("*.md")
        if p.name.upper() != "README.MD"
    )

    if not md_files:
        print("No Markdown files found in docs/ (excluding READMEs).")
        sys.exit(0)

    total_files = len(md_files)
    total_errors = 0
    files_with_errors = 0

    print(f"Validating {total_files} document(s) in docs/...\n")

    for filepath in md_files:
        rel_path = filepath.relative_to(repo_root)
        errors = validate_file(filepath, type_map, repo_root)

        if errors:
            files_with_errors += 1
            total_errors += len(errors)
            print(f"FAIL  {rel_path}")
            for err in errors:
                print(f"      - {err}")
        else:
            print(f"OK    {rel_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Files checked:      {total_files}")
    print(f"Files with errors:  {files_with_errors}")
    print(f"Total errors:       {total_errors}")
    print(f"{'='*60}")

    if total_errors > 0:
        print("\nValidation FAILED. Fix the errors above and re-run.")
        sys.exit(1)
    else:
        print("\nAll documents passed validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()

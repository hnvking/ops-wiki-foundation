"""
frontmatter.py — Shared YAML frontmatter parsing and repo-root utilities.

Used by validate_docs.py and export_for_rag.py to avoid duplicating logic.
"""

import yaml
from pathlib import Path


def find_repo_root():
    """
    Find the repository root by looking for schemas/required-fields.yml.

    Starts from this file's parent and walks up to 7 levels. Falls back to cwd.
    """
    current = Path(__file__).resolve().parent
    for _ in range(7):
        if (current / "schemas" / "required-fields.yml").exists():
            return current
        current = current.parent
    return Path.cwd()


def parse_frontmatter(filepath):
    """
    Extract YAML frontmatter from a Markdown file.

    Frontmatter must be delimited by '---' on the first line and a second
    '---' on its own line. This parser finds the first newline-preceded
    '---' after the opening delimiter to avoid matching '---' inside YAML
    values.

    Returns a dict of frontmatter fields, or None if no valid frontmatter found.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None

    # Look for closing '---' that starts on its own line.
    # Skip the opening '---' (first 3 chars + newline).
    search_start = content.index("\n", 3) + 1 if "\n" in content[3:6] else 4
    while True:
        end = content.find("---", search_start)
        if end == -1:
            return None
        # Accept if it's at position 0 of a line (preceded by newline).
        if end == 0 or content[end - 1] == "\n":
            break
        search_start = end + 3

    yaml_text = content[3:end]
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        print(f"  YAML parse error in {filepath}: {exc}")
        return None


def parse_frontmatter_and_body(filepath):
    """
    Extract YAML frontmatter and Markdown body from a file.

    Returns (frontmatter_dict, body_string).
    Returns (None, full_content) if no valid frontmatter found.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None, content

    # Same improved closing-delimiter logic as parse_frontmatter.
    search_start = content.index("\n", 3) + 1 if "\n" in content[3:6] else 4
    while True:
        end = content.find("---", search_start)
        if end == -1:
            return None, content
        if end == 0 or content[end - 1] == "\n":
            break
        search_start = end + 3

    yaml_text = content[3:end]
    body = content[end + 3:].strip()

    try:
        frontmatter = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        frontmatter = None

    return frontmatter, body

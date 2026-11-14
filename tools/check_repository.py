#!/usr/bin/env python3
"""Dependency-free structural checks for this HTMD specification repository.

This is NOT a complete or conforming HTMD parser. It validates example metadata,
selected source patterns, JSON fixtures, link destinations, and package structure.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def report(where: str, problem: str) -> None:
    errors.append(f"{where}: {problem}")


def check_frontmatter(filename: Path, contents: str) -> None:
    if not contents.startswith("---\n"):
        return
    lines = contents.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        report(str(filename), "unclosed frontmatter")
        return
    meta: dict[str, str | list[str]] = {}
    list_key: str | None = None
    for lineno, line in enumerate(lines[1:end], 2):
        if not line or line.startswith("#"):
            continue
        if line.startswith("  - "):
            if list_key is None:
                report(str(filename), f"orphan YAML sequence at line {lineno}")
                continue
            try:
                value = json.loads(line[4:])
                if not isinstance(value, str):
                    raise ValueError("not a quoted string")
            except (ValueError, json.JSONDecodeError):
                report(str(filename), f"invalid quoted sequence item at line {lineno}")
                continue
            assert isinstance(meta[list_key], list)
            meta[list_key].append(value)
            continue
        match = re.fullmatch(r"([a-z][a-z0-9_-]*):(?: (.*))?", line)
        if not match:
            report(str(filename), f"non-subset frontmatter at line {lineno}")
            continue
        key, raw = match.groups()
        if key in meta:
            report(str(filename), f"duplicate key '{key}' at line {lineno}")
            continue
        if raw is None or raw == "":
            meta[key] = []
            list_key = key
            continue
        list_key = None
        try:
            value = json.loads(raw)
            if not isinstance(value, str):
                raise ValueError("not a string")
            meta[key] = value
        except (ValueError, json.JSONDecodeError):
            report(str(filename), f"unquoted/invalid scalar at line {lineno}")
    if meta.get("htmd") != "0.1":
        report(str(filename), "declared HTMD version is missing or not 0.1")
    if meta.get("type") == "fact" and not meta.get("evidence"):
        report(str(filename), "fact must have nonempty evidence")
    if meta.get("type") == "event":
        for key in ("id", "actor", "occurred_at", "recorded_at"):
            if not meta.get(key):
                report(str(filename), f"event missing {key}")


def check_links() -> None:
    md_files = sorted(ROOT.rglob("*.md"))
    # Explicit Markdown inline links. Ignore externals, anchors and image-backed URLs.
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for match in re.finditer(r"(?<!!)\[[^\[\]\n]+\]\(([^)\n]+)\)", text):
            target = match.group(1).split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "data:")):
                continue
            target = target.split(" ", 1)[0]
            resolved = (md.parent / target)
            if not resolved.exists():
                report(str(md.relative_to(ROOT)), f"broken relative Markdown link: {target}")


def check_fixtures() -> None:
    try:
        cases = json.loads((ROOT / "conformance/cases.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas/htmd-ir.schema.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        report("JSON", str(e))
        return
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        report("schema", "expected JSON Schema draft 2020-12")
    if not isinstance(cases, list) or len(cases) < 20:
        report("cases.json", "expected at least 20 conformance cases")
        return
    seen: set[str] = set()
    for case in cases:
        ident = case.get("id", "(unnamed)")
        if ident in seen:
            report("cases.json", f"duplicate case ID {ident}")
        seen.add(ident)
        if case.get("profile") not in {"core", "view"}:
            report(ident, "invalid profile")
        if not isinstance(case.get("source"), str):
            report(ident, "source is not text")
            continue
        lines = case["source"].splitlines()
        if case.get("valid") is True:
            expected = case.get("expected", {})
            for key in ("metadata", "references", "relations"):
                if key not in expected:
                    report(ident, f"missing expected.{key}")
            if expected.get("metadata", {}).get("htmd") != "0.1":
                report(ident, "invalid effective metadata version")
            for ref in expected.get("references", []):
                line = ref.get("line", 0)
                if not isinstance(line, int) or line < 1 or line > len(lines):
                    report(ident, f"reference line out of range: {line}")
                elif ref.get("target", "") not in lines[line-1]:
                    report(ident, f"reference target not found at line {line}")
            for edge in expected.get("relations", []):
                line = edge.get("line", 0)
                if not isinstance(line, int) or line < 1 or line > len(lines):
                    report(ident, f"relation line out of range: {line}")
                elif "<relation" not in lines[line-1]:
                    report(ident, f"relation start not found at line {line}")
        elif case.get("valid") is False:
            if not re.fullmatch(r"E_[A-Z_]+", case.get("error", "")):
                report(ident, "invalid diagnostic code")
        else:
            report(ident, "valid must be a boolean")
    for folder in ("examples/concepts", "examples/knowledge", "examples/ui"):
        for file in (ROOT / folder).glob("*.htmd"):
            check_frontmatter(file.relative_to(ROOT), file.read_text(encoding="utf-8"))


def main() -> int:
    for required in ("README.md", "SPECIFICATION.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md",
                     "docs/quickstart.md", "docs/security.md", "docs/conformance.md",
                     "schemas/htmd-ir.schema.json", "conformance/cases.json"):
        if not (ROOT / required).is_file():
            report("repository", f"missing {required}")
    check_fixtures()
    check_links()
    if errors:
        for issue in errors:
            print(f"ERROR {issue}")
        print(f"{len(errors)} issue(s) detected.")
        return 1
    print("Repository structure, example frontmatter, relative links, and semantic fixtures: OK")
    print("NOTE: Not a complete HTMD grammar or security conformance validator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

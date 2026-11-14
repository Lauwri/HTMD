"""HTMD CLI. All commands are local and non-executing."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from .parser import HTMDError, parse_file
from .render import render_html


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="htmd", description="HTMD 0.1/0.2 semantic parser and safe renderer")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("validate", "parse", "render", "graph"):
        cmd = sub.add_parser(name)
        cmd.add_argument("files", nargs="+", type=Path)
        cmd.add_argument("--profile", choices=("core", "view"), default="core")
        if name == "render":
            cmd.add_argument("--full", action="store_true", help="include full HTML document")
            cmd.add_argument("-o", "--output", type=Path)
    args = p.parse_args(argv)
    docs = []; failed = False
    for path in args.files:
        if path.is_dir():
            files = sorted(path.rglob("*.htmd"))
        else: files = [path]
        for file in files:
            try:
                doc = parse_file(file, profile=args.profile)
                docs.append((str(file), doc))
                if args.command == "validate": print(f"OK {file}")
            except (HTMDError, OSError) as exc:
                print(f"ERROR {file}: {exc}", file=sys.stderr)
                failed = True
    if failed: return 1
    if args.command == "parse":
        payload = {path: doc.to_ir() for path, doc in docs}
        print(json.dumps(payload if len(docs) > 1 else next(iter(payload.values()), {}), indent=2, ensure_ascii=False))
    elif args.command == "graph":
        payload = {"nodes": [{"id": d.metadata["id"], "type": d.metadata["type"],
                               "title": d.metadata.get("title"), "file": path}
                              for path, d in docs if "id" in d.metadata],
                   "edges": [dict(r, document=path) for path, d in docs for r in d.relations]}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.command == "render":
        if len(docs) != 1:
            print("render requires exactly one file", file=sys.stderr); return 2
        rendered = render_html(docs[0][1], full=args.full)
        if args.output:
            try:
                args.output.write_text(rendered, encoding="utf-8")
            except OSError as exc:
                print(f"ERROR {args.output}: {exc}", file=sys.stderr)
                return 1
        else: print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

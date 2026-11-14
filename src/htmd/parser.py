"""HTMD 0.1/0.2 Core and View parser. Never loads resources or invokes capabilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import unicodedata
from typing import Any
from urllib.parse import unquote_to_bytes, urlsplit

from markdown_it import MarkdownIt
from markdown_it.rules_block import paragraph
from markdown_it.rules_inline import StateInline, backtick, html_inline, image
import yaml

TYPES = {"note", "object", "component", "action", "fact", "hypothesis", "thought", "event"}
FIELDS = {"htmd", "id", "type", "title", "actor", "occurred_at", "recorded_at", "evidence", "corrects"}
# Only 0.1 gives workspace/project special (string-only) validation.
METADATA_FIELDS = {"0.1": FIELDS | {"workspace", "project"}, "0.2": FIELDS}
ATTRS = {
    "context": {"ref", "mode", "name"}, "skill": {"ref", "name"},
    "tool": {"ref", "name"}, "resource": {"ref", "src", "name"},
    "relation": {"type", "to", "from", "status", "evidence"}, "view": {"id", "name"},
}
URI = re.compile(r"^(res|mem|skill|tool)://([a-z0-9][a-z0-9.-]*)(/.*)?$")
SEGMENT = re.compile(r"(?:[a-zA-Z0-9_.~-]|%[0-9A-Fa-f]{2})+")
KEY = re.compile(r"^([a-z][a-z0-9_-]*):(?:[ ]*(.*))?$")
ATTR_NAME = re.compile(r"[a-z][a-z0-9-]*")
DIRECTIVE_START = re.compile(r"^[ ]{0,3}<(context|skill|tool|resource|relation)(?=[\s/>]|$)")
VIEW_START = re.compile(r"^[ ]{0,3}<view(?=[\s/>]|$)")
VIEW_END = re.compile(r"^[ ]{0,3}</view>[ \t]*$")
BAD_CLOSING = re.compile(r"^[ ]{0,3}</(context|skill|tool|resource|relation|view)(?=[\s>]|$)")
STAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$")


class HTMDError(ValueError):
    def __init__(self, code: str, line: int, column: int, message: str):
        super().__init__(f"{code} at {line}:{column}: {message}")
        self.code, self.line, self.column, self.message = code, line, column, message

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "line": self.line, "column": self.column, "message": self.message}


@dataclass
class Block:
    kind: str
    line: int
    raw: str
    attributes: dict[str, str] = field(default_factory=dict)
    fragment: str = ""
    html: str = ""


@dataclass
class Document:
    source: str
    metadata: dict[str, Any]
    blocks: list[Block]
    references: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    profile: str = "core"

    def to_ir(self) -> dict[str, Any]:
        return {"htmd": self.metadata["htmd"], "metadata": self.metadata,
                "references": self.references, "relations": self.relations}


def validate_uri(value: str, schemes: set[str] | None = None) -> str:
    m = URI.fullmatch(value)
    if not m or (schemes is not None and m[1] not in schemes):
        raise ValueError("invalid HTMD logical URI or scheme")
    if m[3]:
        for seg in m[3][1:].split("/"):
            if not SEGMENT.fullmatch(seg):
                raise ValueError("invalid URI path segment")
            try:
                decoded = unquote_to_bytes(seg).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("invalid UTF-8 percent escape") from exc
            if decoded in (".", "..") or any(c in "/\\" or unicodedata.category(c) == "Cc" for c in decoded):
                raise ValueError("encoded separator, control, or traversal")
    return value


def canonical_uri(identifier: str) -> str:
    """Canonical lookup key; original identifier stays unchanged in source/IR."""
    validate_uri(identifier)
    # Only unreserved ASCII may be decoded for equality comparisons.
    def normalize(match: re.Match[str]) -> str:
        b = int(match.group()[1:], 16)
        ch = chr(b)
        if ch.isascii() and (ch.isalnum() or ch in "-._~"):
            return ch
        return f"%{b:02X}"
    return re.sub(r"%[0-9A-Fa-f]{2}", normalize, identifier)


def validate_src(src: str) -> str:
    if (not src.startswith("./") or "\\" in src or "%" in src
            or any(unicodedata.category(c) == "Cc" for c in src)
            or any(p in ("", ".", "..") for p in src[2:].split("/"))):
        raise ValueError("src must be an inert, non-traversing local path")
    return src


def _uri(value: str, line: int, kinds: set[str] | None = None) -> str:
    try: return validate_uri(value, kinds)
    except ValueError as exc: raise HTMDError("E_URI", line, 1, str(exc)) from exc


def _quoted(raw: str, line: int) -> str:
    if not raw.startswith('"') or not raw.endswith('"') or "\t" in raw or "\n" in raw:
        raise HTMDError("E_FRONTMATTER", line, 1, "expected YAML double-quoted string")
    try: val = yaml.safe_load(raw)
    except yaml.YAMLError as exc: raise HTMDError("E_FRONTMATTER", line, 1, "invalid YAML double-quoted string") from exc
    if not isinstance(val, str):
        raise HTMDError("E_FRONTMATTER", line, 1, "expected string")
    try: val.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise HTMDError("E_FRONTMATTER", line, 1, "invalid Unicode scalar value") from exc
    return val


def _frontmatter(lines: list[str]) -> tuple[dict[str, Any], int]:
    if not lines or lines[0] != "---":
        return {"htmd": "0.1", "type": "note"}, 0
    try: end = lines.index("---", 1)
    except ValueError as exc: raise HTMDError("E_FRONTMATTER", 1, 1, "unclosed frontmatter") from exc
    if end > 4096: raise HTMDError("E_FRONTMATTER", 1, 1, "frontmatter is too long")
    data: dict[str, Any] = {}
    key_lines: dict[str, int] = {}
    p = 1
    while p < end:
        row = lines[p]
        if not row.strip() or row.startswith("#"):
            p += 1; continue
        if "\t" in row or row[0].isspace():
            raise HTMDError("E_FRONTMATTER", p + 1, 1, "invalid indentation")
        m = KEY.fullmatch(row)
        if not m:
            raise HTMDError("E_FRONTMATTER", p + 1, 1, "expected key: \"value\"")
        key, val = m.groups()
        if key in data:
            raise HTMDError("E_FRONTMATTER", p + 1, 1, "duplicate metadata key")
        key_lines[key] = p + 1
        if val:
            data[key] = _quoted(val, p + 1); p += 1
        else:
            items = []; p += 1
            while p < end and lines[p].startswith("  - "):
                items.append(_quoted(lines[p][4:], p + 1)); p += 1
            if not items: raise HTMDError("E_FRONTMATTER", p + 1, 1, "expected nonempty string array")
            data[key] = items
    version = data.get("htmd")
    if not isinstance(version, str) or version not in METADATA_FIELDS:
        raise HTMDError("E_VERSION", 1, 1, "missing or unsupported htmd version")
    fields = METADATA_FIELDS[version]
    for key, val in data.items():
        if version == "0.1" and key not in fields and not key.startswith("x-"):
            raise HTMDError("E_FRONTMATTER", key_lines[key], 1, "unsupported metadata key")
        if key == "evidence" and not isinstance(val, list):
            raise HTMDError("E_FRONTMATTER", 1, 1, "evidence must be a list")
        if key in fields and key != "evidence" and not isinstance(val, str):
            raise HTMDError("E_FRONTMATTER", 1, 1, "metadata must be a string")
    meta = {"htmd": version, "type": "note", **data}
    typ = meta["type"]
    if typ not in TYPES: raise HTMDError("E_TYPE", 1, 1, "invalid type")
    if "id" in meta: _uri(meta["id"], 1, {"res", "mem"})
    if typ in {"fact", "event", "hypothesis", "thought"} and "id" not in meta:
        raise HTMDError("E_TYPE", 1, 1, "type requires id")
    if typ == "fact" and not meta.get("evidence"):
        raise HTMDError("E_TYPE", 1, 1, "fact requires evidence")
    if "actor" in meta: _uri(meta["actor"], 1, {"res", "mem"})
    if "corrects" in meta: _uri(meta["corrects"], 1, {"mem"})
    for value in meta.get("evidence", []):
        if value.startswith("https://"):
            try: url = urlsplit(value)
            except ValueError as exc:
                raise HTMDError("E_URI", 1, 1, "invalid evidence URL") from exc
            if not url.netloc or any(c.isspace() for c in value):
                raise HTMDError("E_URI", 1, 1, "invalid evidence URL")
        else: _uri(value, 1, {"res", "mem"})
    if typ == "event":
        for key in ("actor", "occurred_at", "recorded_at"):
            if not meta.get(key): raise HTMDError("E_TYPE", 1, 1, "event requires " + key)
    for key in ("occurred_at", "recorded_at"):
        if key in meta:
            if not STAMP.fullmatch(meta[key]):
                raise HTMDError("E_TYPE", 1, 1, "invalid RFC 3339 timestamp")
            try: datetime.fromisoformat(meta[key].replace("Z", "+00:00"))
            except ValueError as exc: raise HTMDError("E_TYPE", 1, 1, "invalid timestamp") from exc
    return meta, end + 1


def _attributes(raw: str, tag: str, line: int) -> dict[str, str]:
    if not raw.startswith("<" + tag) or not raw.rstrip().endswith("/>"):
        raise HTMDError("E_DIRECTIVE", line, 1, "malformed semantic element")
    i, limit, attrs = len(tag) + 1, len(raw.rstrip()) - 2, {}
    while i < limit:
        if not raw[i].isspace():
            raise HTMDError("E_DIRECTIVE", line, i + 1, "expected attribute whitespace")
        while i < limit and raw[i].isspace(): i += 1
        if i == limit: break
        m = ATTR_NAME.match(raw, i)
        if not m: raise HTMDError("E_DIRECTIVE", line, i + 1, "bad attribute name")
        key = m.group(); i = m.end()
        while i < limit and raw[i] in " \t": i += 1
        if i >= limit or raw[i] != "=":
            raise HTMDError("E_DIRECTIVE", line, i + 1, "expected =")
        i += 1
        while i < limit and raw[i] in " \t": i += 1
        if i >= limit or raw[i] != '"':
            raise HTMDError("E_DIRECTIVE", line, i + 1, "expected double quotes")
        i += 1; chars = []
        while i < limit and raw[i] != '"':
            ch = raw[i]
            if ch in "<\r\n\x00": raise HTMDError("E_DIRECTIVE", line, i + 1, "invalid attribute character")
            if ch == "&":
                e = re.match(r"&(?:amp|lt|gt|quot|apos);", raw[i:])
                if not e: raise HTMDError("E_DIRECTIVE", line, i + 1, "invalid XML entity")
                chars.append({"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'"}[e.group()])
                i += len(e.group()); continue
            chars.append(ch); i += 1
        if i >= limit: raise HTMDError("E_DIRECTIVE", line, i + 1, "unclosed attribute")
        i += 1
        if key in attrs or key not in ATTRS[tag]:
            raise HTMDError("E_DIRECTIVE", line, i + 1, "unknown or duplicate attribute")
        attrs[key] = "".join(chars)
    return attrs


def _semantic(tag: str, attrs: dict[str, str], meta: dict[str, Any], line: int,
              refs: list[dict[str, Any]], relations: list[dict[str, Any]]) -> None:
    if tag == "relation":
        if "type" not in attrs or "to" not in attrs:
            raise HTMDError("E_DIRECTIVE", line, 1, "relation requires type and to")
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", attrs["type"]):
            raise HTMDError("E_DIRECTIVE", line, 1, "invalid relation type")
        src = attrs.get("from", meta.get("id"))
        if not src: raise HTMDError("E_RELATION_SOURCE", line, 1, "missing relation source")
        _uri(src, line, {"res", "mem"})
        _uri(attrs["to"], line, {"res", "mem", "skill", "tool"} if attrs["type"] == "uses" else {"res", "mem"})
        if "evidence" in attrs: _uri(attrs["evidence"], line, {"res"})
        status = attrs.get("status", "asserted")
        if status not in {"asserted", "inferred", "hypothetical"}:
            raise HTMDError("E_DIRECTIVE", line, 1, "invalid relation status")
        edge = {"from": src, "type": attrs["type"], "to": attrs["to"], "status": status, "line": line}
        if "evidence" in attrs: edge["evidence"] = attrs["evidence"]
        relations.append(edge)
        return
    if tag == "resource":
        if ("ref" in attrs) == ("src" in attrs):
            raise HTMDError("E_DIRECTIVE", line, 1, "resource requires exactly one of ref/src")
        if "ref" in attrs: target = _uri(attrs["ref"], line, {"res", "mem"})
        else:
            try: target = validate_src(attrs["src"])
            except ValueError as exc: raise HTMDError("E_SOURCE_PATH", line, 1, str(exc)) from exc
    else:
        if "ref" not in attrs: raise HTMDError("E_DIRECTIVE", line, 1, "missing ref")
        target = _uri(attrs["ref"], line, {"context": {"res", "mem"}, "skill": {"skill"}, "tool": {"tool"}}[tag])
    r = {"kind": tag, "target": target, "line": line}
    if "name" in attrs: r["name"] = attrs["name"]
    if tag == "context":
        if attrs.get("mode", "link") not in {"link", "full", "summary"}:
            raise HTMDError("E_DIRECTIVE", line, 1, "invalid context mode")
        if "mode" in attrs: r["mode"] = attrs["mode"]
    refs.append(r)


def _link_rule(state: StateInline, silent: bool) -> bool:
    if not state.src.startswith("[[", state.pos): return False
    start, j = state.pos, state.pos + 2
    line = state.src[:start].count("\n") + 1
    column = start - state.src.rfind("\n", 0, start)
    while j < len(state.src):
        if state.src[j] == "\\" and j + 1 < len(state.src) and state.src[j + 1] in "|]\\":
            j += 2; continue
        if state.src.startswith("]]", j): break
        if state.src[j] in "\n\r":
            raise HTMDError("E_LINK", line, column, "multiline graph link")
        j += 1
    if j >= len(state.src): raise HTMDError("E_LINK", line, column, "unclosed graph link")
    inner = state.src[start+2:j]
    parts = inner.split("|", 1)
    target = parts[0]
    try: validate_uri(target)
    except ValueError as exc: raise HTMDError("E_LINK", line, column, str(exc)) from exc
    label = None
    if len(parts) == 2:
        raw = parts[1]
        chars = []
        i = 0
        while i < len(raw):
            ch = raw[i]
            if ch == "\\" and i + 1 < len(raw) and raw[i + 1] in "|]\\":
                chars.append(raw[i + 1]); i += 2
                continue
            if ch in "\\[]<>|":
                raise HTMDError("E_LINK", line, column, "invalid graph link label")
            chars.append(ch); i += 1
        label = "".join(chars)
        if not label.strip(" "):
            raise HTMDError("E_LINK", line, column, "invalid graph link label")
    if not silent:
        token = state.push("htmd_ref", "", 0)
        token.content = target
        token.meta = {"target": target, "label": label, "offset": start}
    state.pos = j + 2
    return True


def markdown_parser() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True})
    md.inline.ruler.before("link", "htmd_link", _link_rule)

    def positioned_image(state, silent):
        start = state.pos
        matched = image(state, silent)
        if matched and not silent:
            state.tokens[-1].meta["offset"] = start
        return matched

    def positioned_inlines(state):
        for token in state.tokens:
            if token.type != "inline": continue
            if token.children is None: token.children = []
            try:
                state.md.inline.parse(token.content, state.md, state.env, token.children)
            except HTMDError as exc:
                line = exc.line + (token.map[0] if token.map else 0)
                raise HTMDError(exc.code, line, exc.column, exc.message) from exc

    md.inline.ruler.at("image", positioned_image)
    md.core.ruler.at("inline", positioned_inlines)
    return md


def _protected(lines: list[str], md: MarkdownIt) -> set[int]:
    # Keep CommonMark's literal and container rules, but terminate its HTML
    # blocks at HTMD boundaries. In particular, view payload must never affect
    # the Markdown context of the text following the view.
    def track_literal(rule):
        def tracked(state, silent):
            start, count = state.pos, len(state.tokens)
            matched = rule(state, silent)
            if matched and not silent and len(state.tokens) > count:
                token = state.tokens[-1]
                if token.type == "code_inline" or (token.type == "html_inline" and not is_marker(token.content)):
                    token.meta["literal_lines"] = (
                        state.src[:start].count("\n"),
                        state.src[:state.pos].count("\n") + 1,
                    )
            return matched
        return tracked

    md.inline.ruler.at("backticks", track_literal(backtick))
    md.inline.ruler.at("html_inline", track_literal(html_inline))

    def literal_lines(content, base):
        protected = set()
        for token in md.parseInline(content)[0].children or []:
            if "literal_lines" in token.meta:
                first, last = token.meta["literal_lines"]
                protected.update(range(base + first, base + last))
        return protected

    def is_marker(row):
        return DIRECTIVE_START.match(row) or VIEW_START.match(row) or BAD_CLOSING.match(row)

    def boundary(state, start, end, silent):
        if state.level or state.blkIndent or not is_marker(lines[start]):
            return False
        if silent: return True
        stop = start + 1
        if VIEW_START.match(lines[start]):
            while stop < end and not VIEW_END.match(lines[stop]):
                stop += 1
            stop = min(stop + 1, end)
        elif DIRECTIVE_START.match(lines[start]):
            while stop < end and not re.search(r"/>[ \t]*$", lines[stop - 1]):
                stop += 1
        token = state.push("htmd_boundary", "", 0)
        token.map = [start, stop]
        state.line = stop
        return True

    def bounded_paragraph(state, start, end, silent):
        top_level = state.level == 0 and state.blkIndent == 0
        result = paragraph(state, start, end, silent)
        if top_level and not silent:
            inline = state.tokens[-2]
            literals = literal_lines(inline.content, start)
            for row in range(start + 1, state.line):
                if row not in literals and is_marker(lines[row]):
                    state.tokens[-3].map = inline.map = [start, row]
                    inline.content = "\n".join(inline.content.split("\n")[:row - start])
                    state.line = row
                    break
        return result

    md.block.ruler.before("html_block", "htmd_boundary", boundary)
    md.block.ruler.at("paragraph", bounded_paragraph)
    blocked: set[int] = set()
    for tok in md.parse("\n".join(lines) + "\n"):
        if tok.type in ("fence", "code_block", "blockquote_open", "bullet_list_open", "ordered_list_open", "html_block") and tok.map:
            blocked.update(range(*tok.map))
        if tok.type == "inline" and tok.map:
            blocked.update(literal_lines(tok.content, tok.map[0]))
    return blocked


def parse(source: str | bytes, *, profile: str = "core") -> Document:
    return Parser(profile).parse(source)


def parse_file(path: str | Path, *, profile: str = "core") -> Document:
    return parse(Path(path).read_bytes(), profile=profile)


class Parser:
    def __init__(self, profile: str = "core", max_bytes: int = 4_000_000):
        if profile not in {"core", "view"}: raise ValueError("profile must be core or view")
        self.profile, self.max_bytes = profile, max_bytes

    def parse(self, source: str | bytes) -> Document:
        if isinstance(source, bytes):
            try: source = source.decode("utf-8-sig")
            except UnicodeDecodeError as exc: raise HTMDError("E_ENCODING", 1, 1, "invalid UTF-8") from exc
        if source.startswith("\ufeff"): source = source[1:]
        try: size = len(source.encode("utf-8"))
        except UnicodeEncodeError as exc:
            raise HTMDError("E_ENCODING", 1, 1, "invalid Unicode scalar value") from exc
        if size > self.max_bytes:
            raise HTMDError("E_ENCODING", 1, 1, "source size limit exceeded")
        source = source.replace("\r\n", "\n").replace("\r", "\n")
        lines = source.split("\n")
        if lines[-1] == "": lines.pop()
        metadata, start = _frontmatter(lines)
        body = lines[start:]
        md = markdown_parser()
        protected = _protected(body, MarkdownIt("commonmark", {"html": True}))
        blocks: list[Block] = []; refs: list[dict[str, Any]] = []; rels: list[dict[str, Any]] = []
        pending: list[str] = []; pending_start = start + 1

        def flush() -> None:
            nonlocal pending, pending_start
            if not pending: return
            raw = "\n".join(pending) + "\n"
            blocks.append(Block("markdown", pending_start, raw))
            try: toks = md.parse(raw)
            except HTMDError as exc:
                raise HTMDError(exc.code, pending_start + exc.line - 1, exc.column, exc.message) from exc

            def collect(tokens, content, base):
                for c in tokens:
                    if c.type == "image" and c.children:
                        child_line = base + content[:c.meta["offset"] + 2].count("\n")
                        collect(c.children, c.content, child_line)
                    elif c.type == "htmd_ref":
                        line = base + content[:c.meta["offset"]].count("\n")
                        item = {"kind": "link", "target": c.meta["target"], "line": line}
                        if c.meta["label"] is not None: item["label"] = c.meta["label"]
                        refs.append(item)

            for t in toks:
                if t.type != "inline": continue
                collect(t.children or [], t.content, pending_start + (t.map[0] if t.map else 0))
            pending = []

        pos = 0; seen_views: set[str] = set()
        while pos < len(body):
            row, line = body[pos], start + pos + 1
            if pos not in protected and VIEW_START.match(row):
                flush()
                m = re.fullmatch(r"[ ]{0,3}(<view(?:[ \t]+[^<>]*)?>)[ \t]*", row)
                if not m: raise HTMDError("E_VIEW", line, 1, "malformed view opening tag")
                try: attrs = _attributes(m[1][:-1] + "/>", "view", line)
                except HTMDError as exc: raise HTMDError("E_VIEW", line, exc.column, exc.message) from exc
                if "id" in attrs:
                    if attrs["id"] in seen_views: raise HTMDError("E_VIEW", line, 1, "duplicate view id")
                    seen_views.add(attrs["id"])
                end = pos + 1
                while end < len(body) and not VIEW_END.match(body[end]):
                    if VIEW_START.match(body[end]):
                        raise HTMDError("E_VIEW", start + end + 1, 1, "nested view")
                    end += 1
                if end == len(body): raise HTMDError("E_VIEW", line, 1, "unclosed view")
                fragment = "\n".join(body[pos+1:end]); raw = "\n".join(body[pos:end+1]) + "\n"
                block = Block("view", line, raw, attrs, fragment)
                if self.profile == "view":
                    from .render import validate_view
                    block.html = validate_view(fragment, line + 1)
                blocks.append(block); pos = end + 1; pending_start = start + pos + 1; continue
            if pos not in protected and (m := DIRECTIVE_START.match(row)):
                flush(); tag = m[1]; end = pos
                while end < len(body) and not re.search(r"/>[ \t]*$", body[end]):
                    if end > pos and (VIEW_START.match(body[end]) or DIRECTIVE_START.match(body[end])):
                        raise HTMDError("E_DIRECTIVE", line, 1, "missing semantic tag terminator")
                    end += 1
                if end == len(body): raise HTMDError("E_DIRECTIVE", line, 1, "unclosed semantic tag")
                raw = "\n".join(body[pos:end+1])
                attrs = _attributes(raw.strip(), tag, line)
                _semantic(tag, attrs, metadata, line, refs, rels)
                blocks.append(Block(tag, line, raw + "\n", attrs))
                pos = end + 1; pending_start = start + pos + 1; continue
            if pos not in protected and (m := BAD_CLOSING.match(row)):
                code = "E_VIEW" if m[1] == "view" else "E_DIRECTIVE"
                raise HTMDError(code, line, 1, "unmatched semantic closing tag")
            if not pending: pending_start = line
            pending.append(row); pos += 1
        flush()
        return Document(source, metadata, blocks, refs, rels, self.profile)

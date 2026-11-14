"""Safe, static HTML renderer and strict HTMD-View validator.

No JavaScript is generated. Buttons remain inert until a trusted host attaches
an independently authorized navigation handler.
"""
from __future__ import annotations
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit
from markdown_it.renderer import RendererHTML

from .parser import Document, HTMDError, markdown_parser, validate_uri

_TAGS = {"div", "section", "article", "header", "footer", "p", "span", "strong", "em", "small",
         "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "a", "button", "code", "pre", "hr"}
_SHARED = {"class", "title", "aria-label", "role"}


class _Renderer(RendererHTML):
    def renderInlineAsText(self, tokens, options, env):
        # Image alt text must retain labels without emitting HTML into attrs.
        parts = []
        for token in tokens:
            if token.type == "htmd_ref":
                label = token.meta["label"]
                parts.append(label if label is not None else token.meta["target"])
            else:
                parts.append(super().renderInlineAsText([token], options, env))
        return "".join(parts)


def _safe_href(href: str) -> bool:
    if any(c.isspace() or ord(c) < 32 for c in href) or "\\" in href or href.startswith("//"):
        return False
    try:
        u = urlsplit(href)
    except ValueError:
        return False
    if u.scheme:
        return u.scheme == "https" and bool(u.netloc) and not u.username and not u.password
    return not u.netloc and not href.startswith(("#", "?")) and not any(s == ".." for s in u.path.split("/"))


class _ViewParser(HTMLParser):
    def __init__(self, start_line: int):
        super().__init__(convert_charrefs=True)
        self.line_offset = start_line - 1
        self.stack: list[str] = []
        self.output: list[str] = []

    def fail(self, message: str) -> None:
        row, col = self.getpos()
        raise HTMDError("E_VIEW", self.line_offset + row, col + 1, message)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _TAGS: self.fail(f"disallowed HTML element: {tag}")
        seen: set[str] = set(); a: dict[str, str] = {}
        for name, val in attrs:
            if name in seen or val is None: self.fail("duplicate or valueless attribute")
            seen.add(name)
            if not (name in _SHARED or name == "href" and tag == "a" or name in {"data-action", "data-ref"} and tag == "button"):
                self.fail(f"disallowed HTML attribute: {name}")
            a[name] = val
        if "href" in a and not _safe_href(a["href"]): self.fail("unsafe href")
        if tag == "button":
            if ("data-action" in a) != ("data-ref" in a): self.fail("button action needs a ref")
            if "data-action" in a:
                if a["data-action"] != "open": self.fail("unsupported action")
                try: validate_uri(a["data-ref"], {"res", "mem"})
                except ValueError as exc: self.fail(str(exc))
        self.output.append("<" + tag + "".join(f' {name}="{escape(val, quote=True)}"' for name, val in a.items()) + ">")
        if tag != "hr": self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "hr": self.fail("self-closing markup unsupported")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack.pop() != tag:
            self.fail("unbalanced HTML closing tag")
        self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.output.append(escape(data))

    def handle_entityref(self, name: str) -> None:
        self.output.append(escape("&" + name + ";"))

    def handle_charref(self, name: str) -> None:
        self.output.append(escape("&#" + name + ";"))

    def handle_comment(self, data: str) -> None:
        self.fail("HTML comments are not supported in views")

    def handle_decl(self, decl: str) -> None:
        self.fail("HTML declarations are not supported in views")

    def unknown_decl(self, decl: str) -> None:
        self.fail("unknown HTML declaration")

    def handle_pi(self, data: str) -> None:
        self.fail("processing instructions are forbidden")


def validate_view(fragment: str, start_line: int) -> str:
    validator = _ViewParser(start_line)
    validator.feed(fragment)
    validator.close()
    if validator.stack:
        raise HTMDError("E_VIEW", start_line, 1, "unclosed view HTML elements")
    return "".join(validator.output)


def render_html(doc: Document, *, full: bool = False) -> str:
    """Render strictly inert HTML; HTML source in Markdown is escaped, not executed."""
    md = markdown_parser()
    md.renderer = _Renderer()
    # Render raw HTML as escaped text, including scripts in Markdown. Never pass
    # untrusted source HTML through markdown-it's default raw HTML renderer.
    md.add_render_rule("html_block", lambda self, tokens, idx, opts, env: escape(tokens[idx].content))
    md.add_render_rule("html_inline", lambda self, tokens, idx, opts, env: escape(tokens[idx].content))

    def reference(self, tokens, idx, opts, env):
        meta = tokens[idx].meta
        label = meta["label"] if meta["label"] is not None else meta["target"]
        return f'<span class="htmd-link" data-ref="{escape(meta["target"], quote=True)}">{escape(label)}</span>'

    md.add_render_rule("htmd_ref", reference)
    html: list[str] = []
    for block in doc.blocks:
        if block.kind == "markdown":
            html.append(md.render(block.raw))
        elif block.kind == "view":
            if doc.profile != "view":
                html.append('<aside class="htmd-view-placeholder">View requires HTMD-View profile</aside>')
            else:
                html.append(f'<section class="htmd-view">{block.html}</section>')
        elif block.kind == "relation":
            # Provenance is available in to_ir(); rendering has no graph mutation.
            html.append('<div class="htmd-relation">Relation: ' + escape(block.attributes["type"]) + '</div>')
        else:
            ref = block.attributes.get("ref") or block.attributes.get("src", "")
            label = block.attributes.get("name", ref)
            html.append(f'<span class="htmd-{block.kind}" data-ref="{escape(ref, quote=True)}">{escape(label)}</span>')
    body = "\n".join(html)
    if not full: return body
    title = escape(doc.metadata.get("title", "HTMD Document"))
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            f'<title>{title}</title></head><body>{body}</body></html>\n')

# Grammar and lexical boundaries (implementer companion)

This document is explanatory. [SPECIFICATION.md](../SPECIFICATION.md) defines exact required behavior. A complete grammar for Markdown comes from [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/); HTMD does not redefine it.

## Recognition sequence

```text
UTF-8 bytes
  └─ normalize line endings
     └─ optional first-line --- metadata block
        └─ top-level block tokenizer, honoring Markdown literal regions
           ├─ semantic directive (<context ... /> etc.)
           ├─ view block (<view ...> ... </view>)
           └─ CommonMark text
              └─ Markdown AST text nodes: optional [[id|label]] links
```

### Frontmatter selection

Read the restricted mapping before selecting the declared version; `htmd` need not be the first key. Both versions use the same string/string-array syntax and reject duplicates and nested structures. Version 0.2 permits arbitrary well-formed custom keys, while 0.1 retains its legacy key restrictions. No frontmatter still means 0.1. Missing or unsupported declarations produce `E_VERSION`; do not retry malformed 0.1 input under 0.2. The normative details are in [§3.1](../SPECIFICATION.md#31-metadata-grammar-and-constraints).

### Semantic token surface

```text
DIRECTIVE = "<" TAG ATTR* WS? "/>"
TAG       = "context" / "skill" / "tool" / "resource" / "relation"
ATTR      = WS NAME S? "=" S? DQUOTED
NAME      = lowercase-ascii (lowercase-ascii / digit / "-")*
DQUOTED   = '"' (ordinary-unicode / allowed-entity)* '"'
WS        = (ASCII space / tab / LF)+
S         = (ASCII space / tab)*
```

A directive may span lines **between** attributes but cannot have a newline inside a quoted value. Required attributes, values, schemes, and tag-specific restrictions are in §5 of the specification. Unknown tag names remain ordinary CommonMark HTML without HTMD semantics; malformed *known* HTMD tags produce `E_DIRECTIVE`.

### Inline token surface

```text
LINK = "[[" LOGICAL_URI ["|" LABEL] "]]"
```

The label is plain text. `\|`, `\]` and `\\` escape those characters in a label. Source locations and the full raw lexeme should be retained for diagnostics and editor tooling.

## Lexical examples

| Input | Semantic interpretation |
| --- | --- |
| `<resource ref="res://examples/device" />` as a top-level block | Resource reference |
| `` `<resource ref="res://examples/device" />` `` | Literal inline code |
| A fenced code block containing a directive | Literal code |
| `<relation ... />` indented four spaces | Indented code, not a relation |
| `> <relation ... />` | Blockquote content, not a relation |
| `<relation ... />` inside a Markdown list item | List content, not a relation |
| `<view>... <resource ... /> ...</view>` | View HTML content; not a nested semantic resource |
| `[[res://examples/device]]` in Markdown text | Inline graph reference |
| `[[res://examples/device]]` in inline code | Literal text |
| `\[[res://examples/device]]` in prose | Escaped opening bracket, not graph reference |

## Block boundaries and error precedence

- Standalone top-level semantic tags are recognized whether or not adjacent Markdown paragraphs have a blank line. Their lines are removed from the Markdown segment passed to CommonMark.
- Opening `<view>` and closing `</view>` tags must be alone on lines. Everything inside is treated as a view fragment, not Markdown.
- A standalone unknown self-closing XML-like tag is ordinary CommonMark HTML with no HTMD semantics; all ordinary HTML remains subject to final output sanitization.
- If metadata is malformed, `E_FRONTMATTER` takes precedence over downstream semantic diagnostics on that metadata. If a semantic tag has an invalid attribute, report `E_DIRECTIVE` before interpreting its values.
- Core validators may emit multiple diagnostics but cannot silently reinterpret invalid content as privileged commands.

## Practical parser design

A Markdown extension mechanism with source-position tracking is preferable to reimplementing CommonMark. A robust implementation should preserve the token stream or original text and map semantic nodes back to 1-based source positions. The canonical JSON projection intentionally omits enough source details that it must **never** be used as a lossless text serialization.

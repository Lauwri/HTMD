# HTMD 0.2 — Language Specification

**Status:** Public draft · **Version:** 0.2.0-draft · **Date:** 2026-11-14

This document is the **normative** definition of HTMD 0.2, including compatibility rules for HTMD 0.1. Unless explicitly version-specific, the rules apply to both versions. Other material in this repository is explanatory unless expressly identified as normative. HTMD is a proposed language, not an approved international standard or a completed implementation.

## 1. Scope

HTMD (HyperText Markdown) is a UTF-8 text format combining CommonMark, semantic directives, typed links, metadata, and a restricted, declarative HTML view fragment. Its goals are human-readable knowledge, low-authoring overhead, interoperable graph extraction, and safe use in editors, knowledge systems, AI applications, and other document-processing runtimes.

HTMD defines *representation*, not the engine that executes tools or manages databases. No HTMD document can authorize a tool invocation or elevate its own privileges.

A file has the extension `.htmd`; an HTMD renderer **MAY** produce `.html`, native UI, or a machine-readable interchange representation. Renaming a `.htmd` file to `.html` is **NOT** a valid conversion. HTMD has no registered media type; when a transfer needs one, producers SHOULD use `text/plain; charset=utf-8` rather than claiming `text/html` or an unregistered standardized HTMD MIME type.

### 1.1 Normative terms

**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are interpreted as specified in [BCP 14](https://www.rfc-editor.org/rfc/rfc8174) when capitalized. *Parser* means a component that recognizes HTMD syntax. *Resolver* maps identifiers to objects. *Renderer* displays content. *Runtime* enforces access and action permissions. A *store* persists documents, revisions, and event histories. A *profile* is a declared interoperable subset.

### 1.2 Profiles

- **HTMD-Core**: mandatory for an HTMD conforming parser. Frontmatter, Markdown, semantic directives, links, and relation extraction.
- **HTMD-View**: optional. Recognizes `<view>` fragments and their allowed HTML/actions. A Core-only parser MUST preserve unrenderable view content as an opaque block and MUST NOT execute it.
- **HTMD-Resolver**: optional. Resolves logical references, subject to the runtime's policies.

A producer **MUST NOT** assume that a reader supports optional profiles. Profile capability discovery is outside versions 0.1 and 0.2; an application **MAY** report the supported profiles out of band.

## 2. Encoding, input and lexical precedence

1. Files **MUST** be valid UTF-8, without a required BOM. A parser **MAY** accept a UTF-8 BOM and ignore it for syntax; producers **SHOULD NOT** emit one.
2. LF is the canonical line ending; parsers **MUST** accept CRLF. Producers **SHOULD** write LF. Other line endings **MAY** be normalized to LF before parsing.
3. The first line **MAY** begin the frontmatter delimiter `---` (exactly three hyphens, no spaces). If present, the closing delimiter **MUST** be an identical standalone line. A second `---` after frontmatter is an ordinary Markdown thematic break.
4. The parser **MUST** tokenize the frontmatter first, then recognize semantic directives and view blocks at **top level**, then run CommonMark over all remaining Markdown segments. A semantic marker inside an indented/fenced code block, code span, HTML comment, or view fragment is inert and **MUST NOT** create a semantic node.
5. An HTMD directive block starts only at a line with **zero to three leading ASCII spaces**, followed by one of the known semantic tag names (§5) whose complete logical block is self-closing. Other tags remain ordinary CommonMark HTML, without HTMD semantics. A known semantic tag with malformed syntax produces `E_DIRECTIVE`. The tag **MUST** occupy the complete logical block (apart from whitespace). A semantic directive inside a list, blockquote, or Markdown HTML block **MUST NOT** be interpreted as a directive. To place a directive logically adjacent to a list, put it in its own top-level block after the list.
6. A standalone semantic tag **MAY** split its attribute list across multiple lines. The closing `/>` **MUST** be followed only by whitespace to the end of the line. Comments are not allowed within an opening tag.
7. Backslash-escaped `\<` and `\[` are ordinary Markdown escapes; they cannot begin a semantic directive or an HTMD link.
8. Markdown is defined by **CommonMark 0.31.2**. Core does not require GitHub Flavored Markdown extensions. Renderers **MAY** offer a separate `gfm` option, but that option **MUST NOT** alter Core semantic extraction.

These precedence rules intentionally avoid treating the source as ordinary browser HTML or XML. A direct HTML parser cannot correctly implement HTMD.

## 3. Document metadata

A document **MAY** begin with a restricted YAML 1.2-compatible metadata mapping:

```yaml
---
htmd: "0.2"
id: "res://examples/device"
type: "component"
title: "Device assembly"
manufacturer: "Example Electronics"
location: "building-a"
priority: "high"
tags:
  - "hardware"
  - "temperature"
---
```

### 3.1 Metadata grammar and constraints

For Core, the frontmatter is a restricted mapping: ASCII key names matching `[a-z][a-z0-9_-]*`, with **double-quoted string** values or sequences of double-quoted strings (YAML block sequence, one per line). All string values MUST be decoded using YAML 1.2 double-quoted-string rules. Blank lines and `#` full-line comments are permitted. Nested mappings, arbitrary scalar types, anchors, aliases, explicit tags, merge keys, duplicate keys, tabs for indentation, and multiple YAML documents are prohibited. String arrays MUST be nonempty and use a `- ` list at exactly two spaces of indentation after the top-level key; flow arrays such as `["one"]` are prohibited. For interoperability, all metadata values are strings or arrays of strings. In 0.2, any key matching the key grammar is allowed. A parser **MUST** preserve custom keys and their decoded values, including array order, without executing or interpreting them. No `x-` prefix is required; existing `x-*` keys remain valid.

If frontmatter exists, `htmd: "0.1"` or `htmd: "0.2"` **MUST** be present. The declared version selects metadata validation regardless of the position of the `htmd` key. Absent frontmatter means an anonymous HTMD document with an implicit `htmd` value of `"0.1"` and `type` value `"note"`. A declared unsupported major/minor version **MUST** produce `E_VERSION` rather than silently choosing another grammar. Malformed 0.1 documents **MUST NOT** be retried or reinterpreted as 0.2.

The following are the **only reserved metadata fields in 0.2**:

| Field | Type | Rule |
| --- | --- | --- |
| `htmd` | string | Required if frontmatter exists; `"0.1"` or `"0.2"` |
| `id` | URI string | Optional unless required by document type or relation |
| `type` | string | Optional; default `note`; see §3.2 |
| `title` | string | Optional human title |
| `actor` | URI string | Source/author attribution; required for `event` |
| `occurred_at` | string | RFC 3339 timestamp; required for `event` |
| `recorded_at` | string | RFC 3339 timestamp; required for `event` |
| `evidence` | list of URI strings | Required and nonempty for `fact` |
| `corrects` | URI string | References an earlier historical `event`; correction only |

Reserved names always retain their specified types and semantics. A custom field cannot shadow, redefine, or relax a reserved field; an invalid reserved value remains an error. Any repeated key, reserved or custom, is `E_FRONTMATTER`; there is no first/last-value-wins behavior.

`workspace` and `project` are ordinary custom fields in 0.2, with string or string-array values. Neither these names nor any other custom field changes identity, reference resolution, parser options, profiles, permissions, or tool behavior. HTML, script-like text, expressions, paths, and tool URIs inside custom values are inert strings, not markup, expressions to evaluate, or semantic references. Applications may interpret metadata under their own explicit policies but **MUST NOT** derive authorization from document-supplied values.

**0.1 compatibility:** the reserved-field validations above still apply. In addition, 0.1 accepts `workspace` and `project` only as opaque strings, and every other non-reserved key **MUST** start with `x-`. These legacy exceptions do not reserve application-specific names in 0.2. All other metadata grammar and type-specific requirements are unchanged.

Only an explicit specification change may reserve additional names; implementations **MUST NOT** reserve names speculatively or apply future standardized semantics to existing versions.

Timestamps **MUST** include an explicit UTC offset (`Z` or `±HH:MM`). Their lexical interpretation follows [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339). Producers **SHOULD** write UTC (`Z`).

### 3.2 Document types

- `note`: general Markdown knowledge (default).
- `object`: an independently meaningful entity.
- `component`: a part of a larger system.
- `action`: a description of a possible action; **not executable**.
- `fact`: an assertion with source evidence, not a claim of guaranteed truth.
- `hypothesis`: an unverified proposition.
- `thought`: an agent-authored interpretation.
- `event`: a recorded occurrence, protected against mutation by the persistent store.

Unknown `type` values **MUST** produce `E_TYPE` in Core. Future types require an explicit version or extension profile. For `fact`, `event`, `hypothesis`, and `thought`, `id` **MUST** be present. Every `id` MUST be a `res:` or `mem:` logical ID; `corrects` MUST be a `mem:` ID referencing a prior `event`, and `actor` MUST be a `res:` or `mem:` logical ID. `fact` **MUST** declare at least one source in `evidence`; each evidence value MUST be a `res:` or `mem:` logical ID, or an absolute `https:` URI. An `event` **MUST** have `actor`, `occurred_at`, and `recorded_at`. The store **MUST** enforce event immutability; a syntax parser alone cannot.

## 4. Identifiers and references

An HTMD logical identifier is an absolute URI with a scheme from the following set:

| Scheme | Meaning | Example |
| --- | --- | --- |
| `res` | Reusable resource | `res://examples/device` |
| `mem` | Memory record / context | `mem://user/preferences` |
| `skill` | Registered skill descriptor | `skill://research/core` |
| `tool` | Registered runtime capability | `tool://browser/search` |

These are **application-private logical URI conventions**, not claims of IANA scheme registration or global DNS ownership. They use the generic URI shape of RFC 3986; **HTMD additionally requires** lowercase schemes, a nonempty ASCII lowercase authority matching `[a-z0-9][a-z0-9.-]*`, and zero or more slash-separated nonempty path segments formed only from ASCII letters, digits, `_`, `-`, `.`, `~`, and valid percent encodings. Query strings, fragments, ports, credentials, empty segments, `.` and `..` segments are **not** part of logical IDs. Percent-encoded bytes MUST decode to valid UTF-8 and MUST NOT decode to `/`, `\`, NUL, or a control character. Canonical producers SHOULD use uppercase hex in escapes and avoid percent encoding unreserved characters. Equality compares scheme and authority case-insensitively, path case-sensitively, after decoding only percent-encoded unreserved ASCII characters.

The root `res://examples` is valid. `res://examples/device` and `res://examples/Device` are distinct. A workspace name in frontmatter is descriptive; it does not rewrite the identifier namespace. A producer **SHOULD** use stable identifiers; changing the document path **MUST NOT** change its identifier.

Unresolved references are permitted. They **MUST** remain visible as unresolved references in a resolver, never silently resolve to a different record. A forbidden reference **MUST NOT** reveal the existence or content of a restricted resource beyond what policy allows.

### 4.1 Local sources (`src`)

A local `src` value refers to a file within an explicitly configured content root (never a network URL), using a relative POSIX-style path beginning with `./`, for example `./assets/device.svg`. Segments `.` and `..` after the leading `./`, backslashes, empty segments, NULs, and percent escapes are forbidden. The resolver **MUST** prevent traversal through symlinks or other aliases outside the root and **MUST NOT** interpret source paths as executable scripts. A Core parser validates `src` lexically but does not open files.

## 5. Semantic elements

Semantic directives are self-closing, lowercase, XML-like tokens. Attributes are ASCII lowercase names and double-quoted values only. There are no boolean attributes, expression interpolations, comments, entity expansion, or inline scripts. Attribute values decode the five predefined XML entities `&amp;`, `&lt;`, `&gt;`, `&quot;`, and `&apos;`, and only those. Duplicate attributes, unknown attributes on a known HTMD tag, malformed entities, unmatched semantic tags, and mismatched semantic closing markers **MUST** produce a diagnostic. Element and attribute names are case-sensitive.

```ebnf
name          = lowercase, { lowercase | digit | "-" } ;
attribute     = name, "=", '"', { attr-character | entity }, '"' ;
attributes    = { wsp, attribute } ;
self-closing  = "<", ("context" | "skill" | "tool" | "resource" | "relation"),
                attributes, wsp?, "/>" ;
wsp           = " " | "\t" | "\n" ;
entity        = "&amp;" | "&lt;" | "&gt;" | "&quot;" | "&apos;" ;
```

`attr-character` is any valid Unicode scalar value except `&`, `<`, `"`, CR, LF, and NUL. The lexical `attribute` rule is schematic: only one `=`, with optional spaces or tabs on either side, is permitted; literal newlines may appear between attributes, not inside values. This EBNF defines the semantic opening-tag layer, not full Markdown or YAML. See §2 for recognition and precedence.

The *current document* is the source for an implicit relation `from`. Source file location is not a graph identity. Resolvers **MUST NOT** interpret an element as execution.

### 5.1 `<context />`

```htmd
<context ref="mem://user/preferences" mode="summary" name="Preferences" />
```

- Required: `ref` (a `mem:` or `res:` logical ID).
- Optional: `mode` (`link` [default], `summary`, `full`), `name`.
- Purpose: make a context dependency explicit. `summary` and `full` are retrieval *hints* only; the runtime MAY decline because of permission, offline state, or token budget. No hidden content is inserted into the normative parse result.

### 5.2 `<skill />` and `<tool />`

```htmd
<skill ref="skill://research/core" name="Research" />
<tool ref="tool://browser/search" name="Web search" />
```

- Required: `ref`, with matching scheme.
- Optional: `name`.
- Purpose: advertise a dependency on a capability descriptor. **MUST NOT** execute, activate, install, or grant permission to the referenced capability.
- Tool code paths, executable `src` values, shell commands, or argument expressions are **not part of this syntax**.

### 5.3 `<resource />`

```htmd
<resource ref="res://examples/sensor" name="Sensor module" />
<resource src="./assets/device.svg" name="Device diagram" />
```

- Exactly one of `ref` or `src` is required; `name` is optional.
- The `src` form links to inert file content without creating a graph identity. It MUST NOT load remote content.

### 5.4 `<relation />`

```htmd
<relation type="contains" to="res://examples/sensor" status="asserted" />
<relation from="res://examples/sensor" type="reports-to" to="res://examples/controller" />
```

- Required: `type`, `to`.
- Optional: `from`, `status` (`asserted` [default], `inferred`, `hypothetical`), `evidence` (a `res:` logical ID).
- `from` defaults to the current document `id`; if neither exists, reject with `E_RELATION_SOURCE`.
- `from` and `to` must be `res:` or `mem:` logical IDs, except `skill:` or `tool:` MAY be a target for relationships of type `uses` (not execution).
- `type` matches `[a-z][a-z0-9]*(?:-[a-z0-9]+)*`. Standard types are `contains`, `part-of`, `depends-on`, `uses`, `supports`, `contradicts`, `derived-from`, `supplies`, `corrects`, and `supersedes`. Unrecognized well-formed types are allowed as application-specific edges and MUST be preserved unchanged.
- A relation is a *directed assertion*. It does not create an inverse, imply transitivity, or establish a fact as true. The source document's provenance is the origin of the assertion. A resolver SHOULD expose this provenance.

### 5.5 `name` and common behavior

`name` is a presentation label, never an identifier or authorization token. References can name objects that do not yet exist. Resolution errors MUST not change the parsed identifier or silently substitute another entity. All reference directives are inert in untrusted imported text until approved for context assembly by the host.

## 6. Inline resource links

Outside code, comments, and view fragments, Markdown content MAY contain an inline HTMD link:

```htmd
The [[res://examples/device]] contains [[res://examples/sensor|a sensor module]].
```

`[[` starts a link when not backslash-escaped. The first unescaped `]]` ends it. The portion before the first unescaped `|` is a logical identifier (§4); the optional portion after it is a **plain text** label. The label MUST be nonempty after trimming ASCII spaces and MUST NOT include newlines, `[`, `]`, or HTML. The only escapes allowed within a label are `\|`, `\]`, and `\\`; a literal `|` in the label MUST be escaped. Without a label, a renderer SHOULD use an authorized resource title, falling back to the identifier. Unknown or forbidden targets MUST display a safe unresolved/denied representation.

An inline link is a reference, not a relation or capability invocation. A malformed `[[...]]` link is an `E_LINK` error in strict mode. A link inside backtick code is never parsed as HTMD. Links MUST NOT be expanded recursively without explicit resolver controls.

## 7. Declarative views (HTMD-View)

Views are top-level blocks delimited by exact standalone `<view ...>` and `</view>` lines (up to three leading spaces). Nested views are prohibited. The opening tag accepts `id` (unique within the document) and `name` (display label); both are optional and double-quoted. A view is a complete safe-HTML fragment **without** Markdown processing inside it.

```htmd
<view id="device-panel" name="Device panel">
  <section>
    <h2>Device Assembly</h2>
    <button data-action="open" data-ref="res://examples/device">Open resource</button>
  </section>
</view>
```

### 7.1 Allowed markup

A View renderer MUST parse fragment content with a maintained HTML parser and apply an allowlist. Allowed elements in both versions are `div`, `section`, `article`, `header`, `footer`, `p`, `span`, `strong`, `em`, `small`, `h1`–`h6`, `ul`, `ol`, `li`, `a`, `button`, `code`, `pre`, and `hr` (void). Allowed attributes are `class`, `title`, `aria-label`, `role` on those elements, `href` on `a`, and `data-action` + `data-ref` on `button`. `id` is not allowed inside the fragment, to prevent collisions; it is available on the outer `<view>` only. All URLs on `a` MUST use `https:` or a relative local path accepted by the host; `javascript:`, `data:`, `file:`, and protocol-relative URLs are prohibited. `a` is ordinary navigation, not a privileged runtime action.

The only built-in interactive behavior is `<button data-action="open" data-ref="...">`, where `data-ref` is a valid `res:` or `mem:` ID. It asks the host to **navigate**, subject to permissions. All other buttons are inert. Action names other than `open` are invalid under HTMD-View 0.1 and 0.2. Views do not support form submissions, arbitrary JavaScript, CSS properties, expressions, media embeds, SVG/MathML, or network requests.

Disallowed elements or attributes are invalid in the View profile and **MUST NOT** be handed to a browser as active markup. Renderers **MAY** replace invalid views with an inert error placeholder. Views from untrusted sources MUST also be treated as untrusted HTML and sanitized on final rendering; syntax validation does not replace sanitizer maintenance or correct output encoding.

### 7.2 Core-only readers

A Core-only reader MUST keep the original view as an opaque, non-executing block; it MAY display an escaped source preview or a static placeholder. It MUST NOT output unsanitized view contents to an HTML environment. A missing view renderer is not a Core parsing failure.

## 8. Processing model

A conforming implementation MUST process input in this conceptual order:

1. Decode UTF-8 and normalize supported newlines.
2. Parse frontmatter into the restricted metadata map; reject structural metadata errors.
3. Recognize top-level self-closing semantic directives and view blocks while honoring Markdown literal contexts (§2).
4. Parse all remaining text as CommonMark 0.31.2, recognizing inline HTMD links only in Markdown text tokens (not code or raw HTML).
5. Produce semantic references and directed relations without resolving or executing them.
6. Optionally resolve authorized references; preserve unresolved and denied states distinctly.
7. Optionally render sanitized HTML, native UI, or a structured representation.

HTMD is **not** a templating language. No tag, reference, metadata value, or Markdown text triggers automatic filesystem, network, browser, model, or tool access. Context assembly is a separately authorized host operation.

### 8.1 Semantic model

A parsed document exposes:

- effective `version` (`"0.1"` or `"0.2"`), metadata, and ordered content blocks;
- references of kind `context`, `skill`, `tool`, `resource`, and `link`, each retaining its literal identifier and source span;
- relations with literal source, predicate, target, status, and optional evidence;
- optional opaque or validated view blocks;
- diagnostics with stable error codes and source locations.

The **exact parser AST is implementation-defined**. For cross-process interchange, the optional JSON format in [`schemas/htmd-ir.schema.json`](schemas/htmd-ir.schema.json) standardizes the extracted semantic projection, **not** a lossless AST. The projection’s top-level `htmd` **MUST** equal `metadata.htmd`, and its metadata map **MUST** retain every custom key and value. Source bytes remain the authoritative representation. Implementations MUST NOT reconstruct an event record from a lossy projection and overwrite the original.

### 8.2 Error handling

A validator MUST report a code, 1-based line/column where possible, and human-readable detail. A strict-mode parser MUST reject structurally invalid metadata and semantic tags rather than guessing. A renderer MAY display the remaining safe Markdown with an error indicator but MUST NOT execute malformed or unsupported constructs.

| Code | Meaning |
| --- | --- |
| `E_ENCODING` | Invalid UTF-8 |
| `E_VERSION` | Missing/unsupported declared version |
| `E_FRONTMATTER` | Malformed/restricted metadata violation |
| `E_TYPE` | Unsupported document type or type-specific metadata violation |
| `E_URI` | Invalid logical identifier |
| `E_SOURCE_PATH` | Invalid local `src` |
| `E_DIRECTIVE` | Unknown/malformed semantic tag or attributes |
| `E_RELATION_SOURCE` | Missing relation `from` and document `id` |
| `E_LINK` | Malformed inline reference link |
| `E_VIEW` | Malformed or unsafe view (View profile) |

A Core-only reader MAY mark a valid view as unsupported without raising `E_VIEW`.

## 9. Storage, integrity and synchronization

Syntax validation does not guarantee truth or immutability. The persistent HTMD-compatible store **MUST** enforce the following **if it claims event-integrity support**:

1. An `event` record is written once; its original bytes, identity, author attribution, and timestamps MUST remain retrievable.
2. Revisions or corrections to historical statements MUST be separate records, using `corrects` or a `corrects` relation, never destructive edits.
3. The store MUST reject a second event with an existing ID if the bytes differ. Equal-content replays MAY be idempotent.
4. Cross-device merges MUST preserve original events and report conflicting edits to mutable records; automatic merging MUST NOT rewrite immutable history.
5. The store SHOULD store tamper-evident hashes, source provenance, retrieval timestamps, and an audit log. A plain file alone is not a cryptographic guarantee.

For mutable document types (`note`, `object`, `component`, etc.), revision policy is implementation-defined. `htmd` version describes **language syntax**, not document revisions. HTMD does not mandate GraphQL, a particular database, CRDT, synchronization transport, or LLM provider.

## 10. Trust model

HTMD content can be owner-authored, agent-generated, retrieved, or hostile. A compliant runtime:

- MUST treat document instructions as **data**, not system/developer policy;
- MUST enforce permissions outside HTMD and never infer permission from tool/skill elements;
- MUST prevent model-generated/remote content from causing unauthorized actions;
- MUST validate local file containment and all URL destinations;
- MUST encode output and sanitize active HTML in the final target environment;
- MUST label inferred, hypothetical, and evidence-backed information without silently upgrading certainty;
- MUST apply authorization checks to every context retrieval and every graph traversal, not only initial links;
- SHOULD enforce CPU, size, depth, and retrieval budgets against denial of service and runaway context expansion.

See [`docs/security.md`](docs/security.md) for security guidance and examples.

## 11. Conformance

**Core parser**: MUST implement §§2–6, 8 and the Core error semantics. **View renderer**: in addition, MUST implement §7. **Resolver**: MUST respect §§4, 8, and 10. **Event-integrity store**: MUST implement §9.

Conformance cases in [`conformance/cases.json`](conformance/cases.json) are **normative test vectors for semantic extraction and validation**, but do not cover every legal CommonMark input. An implementation claiming Core compliance MUST additionally pass the published CommonMark 0.31.2 tests on Markdown segments without HTMD-reserved constructs (notably a first-line frontmatter delimiter and recognized semantic tags). A renderer MUST NOT claim arbitrary browser-HTML compatibility.

## 12. Extension and versioning policy

Versions 0.1 and 0.2 assign semantic meaning only to the elements and attributes listed here. Other standalone HTML tags retain CommonMark behavior and never gain implicit semantic meaning. Semantic extensions MUST be explicitly opt-in and MUST NOT overload known semantics. Passive custom metadata is allowed as described in §3.1 and does not opt into executable or parser extensions. Breaking syntax/semantics requires a new declared `htmd` version. The supported source version strings are `"0.1"` and `"0.2"`; repository draft revision numbers (e.g., `0.2.0-draft`) are not file grammar versions.

New relation names are allowed without a grammar revision because their meaning is application-defined; a consumer MUST preserve but MUST NOT fabricate semantics for unknown predicates. New document types, elements, and attributes are **not** implicitly forward compatible in Core 0.1 or 0.2.

## 13. External normative references

- [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/)
- [RFC 3986 — URI generic syntax](https://www.rfc-editor.org/rfc/rfc3986)
- [RFC 3339 — timestamps](https://www.rfc-editor.org/rfc/rfc3339)
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) — requirement terminology
- [YAML 1.2.2](https://yaml.org/spec/1.2.2/) — restricted frontmatter string decoding
- [WHATWG HTML Living Standard](https://html.spec.whatwg.org/) — HTML fragment parsing for views
- [RFC 8259 — JSON](https://www.rfc-editor.org/rfc/rfc8259) — semantic interchange format

Security guidance: [OWASP Cross-Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

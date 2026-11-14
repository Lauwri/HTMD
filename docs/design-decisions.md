# Design rationale and recorded decisions

This document is informative. The [specification](../SPECIFICATION.md) governs conformance.

| Decision | Rationale | Trade-off |
| --- | --- | --- |
| `.htmd` source, `.html` export | Avoid pretending hybrid source is browser HTML | Requires a renderer |
| CommonMark 0.31.2 baseline | Reuse a mature, testable Markdown core | GitHub extensions remain opt-in |
| Explicit semantic tags | Readable and familiar for HTML/Markdown users | More verbose than bespoke symbols |
| `[[id|label]]` links | Short, graph-friendly references | Needs a new inline tokenizer |
| Separate `ref` and `src` | Identity is different from filesystem location | Two ways to reference content |
| URI-shaped identifiers | Stable, recognizable namespaces | Private schemes are not registered network protocols |
| No executable syntax | Prevent prompt-injection and scripting via knowledge | Workflows require host runtime APIs |
| Small View allowlist | Reasonable default for safe UI previews | Cannot replace a full application framework |
| Open custom metadata in 0.2 | Keep the language independent of application organization | Applications must agree on their own field meanings |
| Version-specific metadata validation | Preserve 0.1 readers and documents without silent reinterpretation | Producers explicitly opt into 0.2 |
| Strict double-quoted frontmatter | Avoid YAML implicit typing surprises | Less flexible than full YAML |
| Append-only historical events | Preserve truthful records and corrections | Requires a real persistence policy |
| Transport independence | Works offline and across devices | Sync design belongs to the host implementation |

## Why are workspace and project custom fields?

HTMD defines how information is represented, identified, and connected. Applications determine how it is organized and used. Only the universal fields in [§3.1](../SPECIFICATION.md#31-metadata-grammar-and-constraints) are reserved in 0.2; adding a future reserved name requires an explicit specification change. Custom metadata stays passive, including names that resemble permissions or parser settings. Removing the `x-` requirement does not add a YAML object model or an execution mechanism.

## Why not embed a JavaScript/TypeScript execution language?

HTMD documents can come from user-authored files, external websites, synchronized devices, or generated text. Arbitrary code execution inside the document would cross the trust boundary at the parsing stage. Host applications can still use tools and web applications through registered capabilities and runtime grants; those capabilities are intentionally **not** part of HTMD markup.

## Why not build a custom replacement for Markdown?

Structured document systems need semantic references without reinventing every Markdown heading, list, code fence, or emphasis rule. Adding a small semantic layer to CommonMark reduces implementation cost and retains conventional editor support.

## Why not always load `<context>` references?

Context expansion can be private, expensive, cyclic, or simply irrelevant. It belongs to an authorized, budget-aware context assembler. A parser does not fetch content by recognizing a tag.

## Why keep hypotheses and thoughts separate from events?

An event records what someone claims happened at a time. A thought is an agent interpretation and a hypothesis is uncertain. Distinguishing these enables traceable reasoning without turning speculation into historical fact. Evidence-backed `fact` means sourced assertion, not infallibility.

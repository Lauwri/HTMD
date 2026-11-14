# Implementer's guide (informative)

This guide suggests a minimal implementation path without coupling HTMD to any particular AI framework, database, or operating system.

## Parsing stages

1. Decode valid UTF-8 and normalize supported line endings.
2. At offset zero, detect optional `---` metadata and validate the restricted YAML string mapping.
3. Tokenize top-level semantic blocks and opaque View blocks **while respecting CommonMark literal regions**. Do not use a naive global regular-expression replacement: a `<tool />` inside a code fence is not a directive.
4. Parse remaining Markdown with a compliant CommonMark 0.31.2 parser.
5. Find inline `[[...]]` syntax in Markdown text tokens only, not code spans or raw HTML nodes.
6. Validate all references, attributes, types, relationships, and required metadata.
7. Emit a structured document and diagnostics. Graph indexing, fetching, rendering, and tool use are separate subsequent stages.

**Recommended technique:** use a Markdown parser with source position awareness, and add an extension or pre-tokenization pass for top-level HTMD blocks. Do not feed entire HTMD source directly to a browser HTML parser. Test code fences, indentation, comments, and malformed delimiter combinations.

## Semantic projection

The optional [JSON Schema](../schemas/htmd-ir.schema.json) describes an extracted projection:

```json
{
  "htmd": "0.1",
  "metadata": {"htmd": "0.1", "id": "res://examples/device", "type": "component"},
  "references": [
    {"kind": "resource", "target": "res://examples/sensor", "line": 9}
  ],
  "relations": [
    {"from": "res://examples/device", "type": "contains", "to": "res://examples/sensor", "status": "asserted", "line": 10}
  ]
}
```

This interchange format is **lossy**: it excludes the complete Markdown AST and source fidelity. Do not round-trip it to rewrite files.

## Graph indexing

Store directed edges `(source_id, predicate, target_id, status, evidence_ref, source_revision)`. A relation marked `inferred` is not automatically promoted to `asserted` on subsequent sync. Edges that refer to unavailable nodes remain pending rather than redirected.

## Error reporting

Return stable codes defined in §8.2 of the specification, 1-based line/column, and short actionable explanations. Invalid directives should produce explicit diagnostics; do not coerce them to trusted runtime commands. An implementation MAY continue to render safe Markdown around an error.

## Suggested tests

- Valid metadata and metadata failure cases: duplicate keys, invalid types, timestamps, missing required fields.
- Reference grammar, canonical URI comparison and unresolved targets.
- All semantic tags: attribute count, missing required fields, incorrect schemes.
- Directed relations with and without document IDs.
- Inline links in normal text, escaped text, code spans and fences.
- View allowlist, unsafe URLs, unknown actions, event attributes, and nested views.
- Resource roots with `..`, symlinks, and inaccessible paths.
- Event conflicts across two devices; linked corrections retain original bytes.
- Fuzzing with deeply nested Markdown, long attributes, malformed UTF-8 and HTML edge cases.

## Performance considerations

- Cache parse results by a content hash, with invalidation when source changes.
- Build graph indexes incrementally by document revision.
- Resolve context lazily using permissions, relevance and explicit token budget.
- Separate static Markdown rendering from resource resolution to keep offline reads fast.
- Never load all graph neighbors recursively just because a document contains references.

## What this repo provides

This repository is a **specification starter kit** with human examples, machine-readable semantic test vectors, an interchange schema, and static repository checks. It does not ship a complete conforming parser, CommonMark engine, sanitizer, renderer, GraphQL API, or event database. The [roadmap](roadmap.md) lists implementation milestones.

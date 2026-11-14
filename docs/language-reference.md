# Language reference

For normative requirements see [SPECIFICATION.md](../SPECIFICATION.md). This is a short authoring reference.

## Syntax at a glance

| Form | Example | Meaning |
| --- | --- | --- |
| Markdown | `# Heading` | Content, CommonMark 0.31.2 |
| Frontmatter | `htmd: "0.2"` | Document version and metadata |
| Graph link | `[[res://examples/device]]` | Link to an entity |
| Context | `<context ref="mem://user/preferences" />` | Declare context dependency |
| Skill | `<skill ref="skill://research/core" />` | Refer to skill descriptor |
| Tool | `<tool ref="tool://browser/search" />` | Refer to capability descriptor |
| Resource | `<resource ref="res://examples/device" />` | Refer to resource |
| File | `<resource src="./assets/device.svg" />` | Refer to local inert file |
| Relation | `<relation type="contains" to="res://examples/sensor" />` | Assert directed edge |
| View | `<view>...</view>` | Declarative HTML fragment (optional profile) |

**Labeled link syntax:** `[[res://examples/device|Device]]` — an unescaped vertical bar divides target and label. To include a literal vertical bar *within the label*, write `\|`.

## Frontmatter

```yaml
---
htmd: "0.2"
id: "res://examples/device"
type: "component"
title: "Device assembly"
manufacturer: "Example Electronics"
workspace: "example-workspace"
tags:
  - "hardware"
  - "inventory"
---
```

Only double-quoted scalar strings and lists of double-quoted strings are allowed. Duplicate keys, YAML anchors/aliases, implicit numbers/booleans, and nested maps are not. Every declared frontmatter block needs a supported version (`"0.1"` or `"0.2"`). In 0.2, custom keys need no prefix; `workspace` and `project` are custom fields. In 0.1, unknown keys still require `x-`, and `workspace`/`project` remain string-only.

Reserved fields are `htmd`, `id`, `type`, `title`, `actor`, `occurred_at`, `recorded_at`, `evidence`, and `corrects`. Their validation cannot be overridden by custom metadata. See [metadata rules](../SPECIFICATION.md#31-metadata-grammar-and-constraints) for the complete grammar and version rules. Custom values never grant permissions or create semantic references.

## Types and required metadata

| Type | Additional required fields |
| --- | --- |
| `note` | None |
| `object`, `component`, `action` | None; stable `id` recommended |
| `fact` | `id`, nonempty `evidence` list |
| `hypothesis`, `thought` | `id` |
| `event` | `id`, `actor`, `occurred_at`, `recorded_at` |

## Element attributes

| Element | Required | Optional |
| --- | --- | --- |
| `context` | `ref` | `mode`, `name` |
| `skill` | `ref` | `name` |
| `tool` | `ref` | `name` |
| `resource` | one of `ref`, `src` | `name` |
| `relation` | `type`, `to` | `from`, `status`, `evidence` |
| `view` | none | `id`, `name` |

Modes: `link` (default), `summary`, `full`. Relation statuses: `asserted` (default), `inferred`, `hypothetical`. Unknown valid relation predicates are permitted and remain uninterpreted.

## Common errors

- `<tool src="./search.py" />` is invalid; no executable source imports.
- `<relation type="contains" to="res://examples/sensor" />` without a document `id` or explicit `from` is invalid.
- `<context ref="mem://user/preferences" />` is only recognized on its own top-level block line, not embedded inside a list or code fence.
- `<div onclick="run()">` in a view is invalid and dangerous.
- `[[examples/device]]` is invalid: HTMD links require logical URI identifiers.
- `<resource src="../private.txt" />` is invalid: paths must begin with `./` and stay inside the content root.

## Character-level constraints

Semantic attribute names are lowercase; values are double quoted. XML entities are supported only for the five predefined entities. Do not use raw `<` or `&` in attribute values. Use CommonMark escaping outside semantic blocks.

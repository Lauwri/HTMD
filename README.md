# HTMD — HyperText Markdown

**A portable, human-readable format for structured knowledge, relationships, records, and safe interfaces.**

![Status: Public draft](https://img.shields.io/badge/status-public%20draft-orange) ![Language: HTMD 0.1](https://img.shields.io/badge/HTMD-0.1-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

> **Status:** HTMD 0.1 is a proposed language specification (14 November 2026), independent of any particular assistant, application, operating system, or storage engine. The repository contains documentation, examples, normative conformance vectors, and an experimental static checker. It **does not** yet contain a complete reference parser, renderer, or runtime. Do not treat the draft as a stable production standard.

HTMD combines **CommonMark** with typed references, directed relations, metadata, and a safe, optional HTML-like view layer. It is suitable for knowledge bases, technical documentation, inventories, research records, and AI-assisted systems. A `.htmd` file stays legible in a plain text editor while a compatible runtime can index knowledge, connect documents, and render interfaces.

```htmd
---
htmd: "0.1"
id: "res://examples/device"
type: "component"
title: "Device Assembly"
workspace: "example-workspace"
---

# Device Assembly

A modular device containing a [[res://examples/sensor|sensor module]].

<context ref="mem://examples/requirements" mode="summary" />
<resource ref="res://examples/sensor" />
<relation type="contains" to="res://examples/sensor" />
<skill ref="skill://research/core" />
<tool ref="tool://browser/search" />
```

**The references above are declarations, not instructions to retrieve data or execute a tool.**

The `examples` identifiers are illustrative and do not depend on any particular organization, product, or runtime.

## Why HTMD?

| Problem | HTMD approach |
| --- | --- |
| Repeating shared material duplicates content | Reusable stable references; context can be loaded selectively by an authorized runtime |
| Plain Markdown has no standard typed knowledge graph | Semantic links, entity identifiers, and directed edges |
| HTML is verbose and potentially active | Markdown by default; restricted declarative `<view>` blocks |
| Revising records can erase historical context | Append-only event contract and linked correction records |
| Tool references could be mistaken for executable instructions | Skill/tool declarations are inert; runtime controls execution |
| Cross-platform systems need portable content | UTF-8 source with transport- and database-independent semantics |

## Start here

- **[Specification](SPECIFICATION.md)** — normative source of truth, syntax and required behavior.
- [Quick start](docs/quickstart.md) — author your first HTMD files.
- [Language reference](docs/language-reference.md) — compact syntax and element table.
- [Grammar companion](docs/grammar.md) — lexical boundaries and parser notes.
- [Architecture](docs/architecture.md) — AST, resolver, knowledge graph, store and UI.
- [Data model](docs/data-model.md) — facts, hypotheses, events, and corrections.
- [Security](docs/security.md) — untrusted content, permissions and HTML safety.
- [Implementation guide](docs/implementation.md) — parser/renderer engineering plan.
- [Conformance](docs/conformance.md) — how to test implementations.
- [Migration](docs/migration.md) — from Markdown/HTML.
- [Rationale and decisions](docs/design-decisions.md) — trade-offs.
- [Roadmap](docs/roadmap.md) — features explicitly deferred.
- [FAQ](docs/faq.md) — short answers.

## Repository map

```text
htmd-spec/
├── SPECIFICATION.md               # Normative HTMD 0.1 definition
├── README.md                       # Introduction and index
├── docs/                           # Guides, architecture and policies
├── examples/                       # Real .htmd source documents
├── conformance/cases.json          # Normative semantic test vectors
├── schemas/htmd-ir.schema.json     # Semantic projection JSON Schema
├── tools/check_repository.py       # Dependency-free draft checks
├── .github/workflows/validate.yml # CI checks for this repository
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── LICENSE
```

## Basic usage

1. Read the [quick start](docs/quickstart.md) and [specification](SPECIFICATION.md).
2. Create a UTF-8 file with extension `.htmd`.
3. Use CommonMark for content; add frontmatter, semantic links or directives only where useful.
4. Run `python3 tools/check_repository.py` from the repository root to check the **included examples and fixture format**. This checker is not a conformance-certified HTMD parser.
5. For a new parser or renderer, follow the [conformance guide](docs/conformance.md) and use the fixtures.

**Do not open `.htmd` as raw browser HTML.** An HTMD-aware renderer must compile and sanitize the output first.

## Portability and security

HTMD Core uses [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/); GFM is optional. Its `res://`, `mem://`, `skill://`, and `tool://` references are **private logical identifier conventions**, not Internet services or registered public URI schemes. A document cannot grant tool authority by containing `<tool />`.

The event-integrity contract requires a suitable store: the markup alone cannot prevent file edits. The view profile forbids scripts, event-handler attributes, and privileged actions.

## Contributing and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md). The content and repository utilities are offered under the [MIT License](LICENSE). The current copyright notice is a proposed default and can be adjusted by the repository owner before publication.

**Project status:** proposal for discussion and implementation. Not affiliated with the CommonMark, WHATWG, or IANA standards bodies.

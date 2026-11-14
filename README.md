# HTMD — HyperText Markdown

**A portable, human-readable format for structured knowledge, relationships, records, and safe interfaces.**

![Status: Public draft](https://img.shields.io/badge/status-public%20draft-orange) ![Language: HTMD 0.2](https://img.shields.io/badge/HTMD-0.2-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

> **Status:** HTMD 0.2 is a proposed language specification (14 November 2026), independent of any particular assistant, application, operating system, or storage engine. The repository contains documentation, examples, conformance vectors, and an **experimental Python parser, static HTML renderer, and read-only resolver**. The implementation is alpha, not a certified or complete application runtime. Do not treat the draft as a stable production standard.

HTMD combines **CommonMark** with typed references, directed relations, metadata, and a safe, optional HTML-like view layer. It is suitable for knowledge bases, technical documentation, inventories, research records, and AI-assisted systems. A `.htmd` file stays legible in a plain text editor while a compatible runtime can index knowledge, connect documents, and render interfaces.

```htmd
---
htmd: "0.2"
id: "res://examples/device"
type: "component"
title: "Device Assembly"
manufacturer: "Example Electronics"
location: "building-a"
tags:
  - "hardware"
  - "inventory"
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

HTMD 0.2 accepts custom metadata without an `x-` prefix; values stay passive strings or string arrays. The parser also supports 0.1 with its original restrictions, and documents without frontmatter still default to 0.1. See [metadata rules](SPECIFICATION.md#31-metadata-grammar-and-constraints) and [migration](docs/migration.md#htmd-01-to-02).

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
- [Python parser and CLI](docs/python-runtime.md) — install, use, test, and integrate the reference implementation.
- [Migration](docs/migration.md) — from HTMD 0.1 and Markdown/HTML.
- [Rationale and decisions](docs/design-decisions.md) — trade-offs.
- [Roadmap](docs/roadmap.md) — features explicitly deferred.
- [FAQ](docs/faq.md) — short answers.

## Repository map

```text
HTMD/
├── SPECIFICATION.md               # Normative HTMD 0.2 definition
├── README.md                       # Introduction and index
├── docs/                           # Guides, architecture and policies
├── examples/                       # Real .htmd source documents
├── conformance/cases.json          # Normative semantic test vectors
├── schemas/htmd-ir.schema.json     # Semantic projection JSON Schema
├── tools/check_repository.py       # Dependency-free draft checks
├── src/htmd/                       # Experimental parser, renderer, resolver, CLI
├── tests/                          # Conformance, security and CLI regression tests
├── pyproject.toml                   # Python distribution and htmd command
├── .github/workflows/              # Parser and specification validation CI
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── LICENSE
```

## Python implementation (alpha)

The repository includes an installable **HTMD-Core parser**, optional **HTMD-View validator**, static HTML renderer, semantic graph extraction, and an **authorization-gated, read-only in-memory resolver**. Nothing in `.htmd` source executes tools, skills, scripts, or network access.

```bash
python3 -m pip install -e '.[test]'
htmd validate --profile view examples/
htmd parse examples/concepts/device.htmd
htmd graph examples/
htmd render --profile view --full examples/ui/device-panel.htmd -o device.html
python3 -m pytest -q
```

`htmd parse` emits the [JSON semantic projection](schemas/htmd-ir.schema.json), not a lossless AST. `htmd render` outputs static HTML; view buttons require a separately trusted host navigation handler and are inert in standalone HTML. The **event-integrity store**, write-capable runtime, arbitrary HTML support, and external resource fetching are deliberately not provided.

See [implementation details and limitations](docs/python-runtime.md).

## Basic usage

1. Read the [quick start](docs/quickstart.md) and [specification](SPECIFICATION.md).
2. Create a UTF-8 file with extension `.htmd`.
3. Use CommonMark for content; add frontmatter, semantic links or directives only where useful.
4. Use `htmd validate` to parse documents and `python3 tools/check_repository.py` to check repository structure.
5. Run the published [conformance fixtures](docs/conformance.md) via `pytest`. Do not interpret fixture success as complete language or security certification.

**Do not open `.htmd` as raw browser HTML.** An HTMD-aware renderer must compile and sanitize the output first.

## Portability and security

HTMD Core uses [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/); GFM is optional. Its `res://`, `mem://`, `skill://`, and `tool://` references are **private logical identifier conventions**, not Internet services or registered public URI schemes. A document cannot grant tool authority by containing `<tool />`.

The event-integrity contract requires a suitable store: the markup alone cannot prevent file edits. The view profile forbids scripts, event-handler attributes, and privileged actions.

## Contributing and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md). The content and repository utilities are offered under the [MIT License](LICENSE). The current copyright notice is a proposed default and can be adjusted by the repository owner before publication.

**Project status:** proposal for discussion and implementation. Not affiliated with the CommonMark, WHATWG, or IANA standards bodies.

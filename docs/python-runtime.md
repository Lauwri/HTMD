# HTMD Python reference implementation (alpha)

The `htmd-language` Python distribution implements a practical subset of the [HTMD 0.2 specification (including 0.1 compatibility)](../SPECIFICATION.md). It includes an **HTMD-Core parser**, an optional **HTMD-View validator**, **safe static HTML rendering**, **semantic projection**, a **read-only resolver**, and a **CLI**. It is not a production authorization server or an executable workflow engine.

## Installation

Requires Python 3.10 or newer. Uses `markdown-it-py` to parse CommonMark and `PyYAML` to decode strictly constrained double-quoted metadata scalars. Source and tests are in this repository.

```bash
python3 -m pip install -e '.[test]'
python3 -m pytest -q
```

## CLI

```bash
htmd validate examples/                             # Core validation
htmd validate --profile view examples/              # Strict View validation
htmd parse examples/concepts/device.htmd             # JSON semantic projection
htmd graph examples/                                # Local node and edge listing
htmd render --profile view --full examples/ui/device-panel.htmd -o device.html
```

`validate` returns exit status 0 on success and 1 if any document cannot be read or parsed. The `--profile view` option opts into the strict restricted HTML validator; Core-only readers preserve views as **opaque inert blocks**. Files and directories in CLI arguments are explicitly selected local inputs; declarations inside HTMD are never dereferenced.

## Library API

```python
from htmd import parse, render_html, Registry

source = '''---
htmd: "0.2"
id: "res://example/device"
type: "component"
manufacturer: "Example Electronics"
---
# Device
<relation type="contains" to="res://example/sensor" />
'''

record = parse(source, profile="core")
print(record.metadata)
print(record.to_ir())    # HTMD semantic projection (lossy)
print(render_html(record, full=True))

registry = Registry(allowed=lambda identifier: identifier.startswith("res://example/"))
registry.add(record)
print(registry.resolve("res://example/device"))  # resolved
print(registry.resolve("res://private/secret"))   # denied, no metadata leaked
```

`Registry` denies lookups by default; always supply a host-specific authorization policy. The policy receives canonical logical IDs (for example, `res://example/%64evice` is checked as `res://example/device`) for both lookups and graph traversal. Source IDs are preserved in returned results. It performs no network access, file loading, or event writes. `visible_relations()` supplies authorized directed edges with document provenance.

## Parsing and safety

- Frontmatter uses restricted YAML 1.2 double-quoted strings and string arrays. Version 0.2 accepts arbitrary custom keys; 0.1 retains legacy key restrictions. Without frontmatter, the effective version remains 0.1. Custom metadata is preserved in `metadata` and `to_ir()`, with no runtime privileges.
- Top-level semantic directives and View blocks are recognized separately from Markdown literal contexts; tags in code fences, code spans, comments, blockquotes, and lists are inert.
- The parser validates HTMD logical IDs, local `src` path syntax, metadata types, event fields, relations, and inline graph links.
- Markdown uses `markdown-it-py`. Raw HTML in ordinary Markdown is **escaped** on output, rather than executed.
- View fragments use a strict HTML allowlist. Disallowed tags, unsafe navigation URLs, event handlers, and privileged action names are rejected. Standalone view navigation buttons are **inert**; a trusted host must implement permission-checked navigation.
- `<tool>` and `<skill>` are inert declarations. No source file, code, action, or network resource is invoked during parsing, graph extraction, or rendering.
- The parser imposes a default 4 MB input size limit, configurable through `Parser(max_bytes=...)`.

## Non-goals and limitations

1. This implementation is **alpha**. Passing the included vectors does not demonstrate complete CommonMark 0.31.2 conformance or exhaustive protection against malicious input.
2. `Document.to_ir()` is lossy and **must not** be used to rewrite source or immutable event records.
3. URI lookups are policy-gated; the provided registry does not implement synchronized storage or graph databases.
4. Local paths are checked lexically but never opened; symlink containment rules are the responsibility of a future file resolver.
5. Historical event immutability, cryptographic provenance, cross-device conflicts, token-budgeted context retrieval, and runtime tool permissions must be implemented **outside the parser**.
6. Rendering is static HTML; it is not a general-purpose HTML5 or JavaScript application runtime. View validation uses Python's standard-library HTML parser and should be evaluated further before embedding output in sensitive browser contexts.
7. The full upstream CommonMark specification suite, fuzz testing, and independent security assessment remain future work.

## Test evidence

`tests/test_conformance.py` tests all published 0.1/0.2 spec vectors and JSON Schema projections. Additional regression tests cover URI and traversal rejection, inert declarations, HTML escaping, View restrictions, resolver permissions, and CLI execution.

Run both checks before proposing a change:

```bash
python3 -m pytest -q
python3 tools/check_repository.py
```

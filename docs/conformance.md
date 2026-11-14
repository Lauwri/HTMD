# Conformance and test vectors

The [language specification](../SPECIFICATION.md) is normative. [`conformance/cases.json`](../conformance/cases.json) contains normative semantic extraction and validation vectors.

## Profiles

- `HTMD-Core`: required parsing, metadata checks, logical IDs, semantic tags, inline links, relationships, diagnostics.
- `HTMD-View`: optional active-safe view parsing and rendering; invalid view markup must never become active content.
- `HTMD-Resolver`: optional identity resolution under explicit policy.
- `Event-integrity store`: an implementation capability, **not** an intrinsic file property.

## Vector format

Each case provides `id`, `profile`, `description`, `source`, `valid` and either `expected` semantic extraction or `error` diagnostic. Positive `expected` contains `metadata`, `references`, `relations`; an implementation may internally use a different AST, but must expose the equivalent data for comparison. The line numbers in positive cases are 1-based. `metadata` means the *effective* metadata, including defaults (`htmd="0.1"`, `type="note"`). View cases describe validation only; visual rendering is not standardized by exact pixel output.

Failure vectors require the error code but permit implementation-specific wording and additional diagnostics. An invalid input must not be silently treated as an executable tool call. A test suite should also include a broad CommonMark 0.31.2 conformance run.

## How to test an implementation

1. Run the published [CommonMark 0.31.2 conformance suite](https://spec.commonmark.org/0.31.2/) for Markdown content that does not use HTMD-reserved constructs, accounting for first-line `---` being reserved as frontmatter in HTMD.
2. Run all Core positive and negative cases, matching effective metadata, semantic nodes, relation direction/status and error codes.
3. If claiming View support, run View cases and add sanitizer attack tests.
4. Test external URI resolution denied/offline/unresolved states without leaking private metadata.
5. Test persisted event conflicts: same ID with different bytes must be rejected, corrections must be append-only.
6. Check resource consumption and randomized malformed input.

## Repository self-check

`python3 tools/check_repository.py` checks JSON fixture structure, selected declared expectations, source samples, and internal documentation links. It is **not** proof of parser conformance because it does not implement the full HTMD syntax.

## Implementation reporting

An implementation should publish a matrix of supported profiles, passing vectors, CommonMark suite results, security boundaries, limitations, and version. Avoid claiming complete conformance based solely on the repository self-check.

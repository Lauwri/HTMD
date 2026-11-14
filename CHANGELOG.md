# Changelog

All notable specification revisions are recorded here. Dates use ISO 8601.

## [0.2.0-draft] — 2026-11-14

- Generalized metadata: custom lowercase keys no longer require `x-`; `workspace` and `project` are ordinary custom fields.
- Retained only universal reserved fields, with unchanged type, identity, evidence, and event validation.
- Added centralized version-aware metadata validation for 0.1/0.2 and preserved the implicit 0.1 default.
- Preserved custom strings/string arrays and the effective version in JSON projections; updated the version-aware schema.
- Expanded conformance vectors, schema checks, and regression tests for inert metadata, rendering, and authorization.
- Updated examples, metadata documentation, and migration guidance. No new dependencies or executable syntax.

## [Unreleased] — experimental Python parser and renderer

- Added installable `htmd-language` alpha package with Core and View parsers.
- Added safe static HTML renderer, read-only policy-gated resolver and CLI commands.
- Added conformance, negative-case, security, and CLI tests running in GitHub Actions.
- Fixed GitHub Actions workflow placement under `.github/workflows` in the distribution.
- No intended changes to HTMD 0.1 normative syntax.

## [Unreleased] — editorial revision

- Removed implementation-specific branding and references from documentation.
- Replaced domain-specific resource examples with neutral device and sensor examples.
- Updated conformance inputs, expected outputs, quick-start text, and filenames consistently.
- No intended changes to HTMD 0.1 syntax or normative behavior.

## [0.1.0-draft] — 2026-11-14

- Initial HTMD language draft based on CommonMark and declarative semantic elements.
- Defined `context`, `skill`, `tool`, `resource`, `relation` and optional `view`.
- Defined restricted frontmatter, logical URI IDs, inline graph links and directed relationships.
- Separated content representation from authorization and runtime execution.
- Specified event integrity requirements and linked corrections.
- Added draft examples, semantic JSON projection schema and conformance vectors.

No stable release has been published.

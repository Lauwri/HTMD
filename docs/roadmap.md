# Roadmap

Status denotes planning, not completed functionality.

## 0.1 draft — language definition (this repository)

- [x] Core semantics and syntax proposal
- [x] Restricted metadata mapping
- [x] Logical IDs and graph edges
- [x] Tool/context trust separation
- [x] Optional declarative view profile
- [x] Semantic JSON projection schema
- [x] Human examples and test vectors
- [ ] Public review and draft issue resolution

## 0.1 implementation phase (experimental Python implementation)

- [x] Alpha Core parser with CommonMark-aware tokenization (full CommonMark conformance not separately certified)
- [ ] Cross-language parser implementations / SDKs
- [x] Initial View allowlist validator and static HTML renderer (no host UI events)
- [x] Automated conformance tests and CLI regression tests
- [x] Schema-backed semantic projection producer
- [ ] End-to-end fuzz and injection tests
- [ ] Persistent graph index and event-integrity store (basic in-memory resolver exists)
- [ ] Integration examples for independent host implementations

## 0.2 draft — extensible metadata

- [x] Application-independent reserved fields and passive custom metadata
- [x] Version-aware parser and semantic projection schema with 0.1 compatibility
- [x] Metadata conformance vectors, runtime regressions, and migration guidance

## Candidate future features (not specified by 0.1 or 0.2)

- Namespaced extension registry and profile negotiation
- Exact structured query syntax for selective context retrieval
- Signed provenance and portable revision manifests
- Content-addressed immutable snapshot references
- Richer declarative UI state and inputs with capability-based actions
- Registry discovery and cross-workspace identifiers
- Explicit binary asset packaging
- Canonical serialization for interoperable diff/sync
- Compact shorthand for frequently used semantic elements

Propose additions through a GitHub issue or pull request with use case, threat model, compatibility analysis, normative text, and test vectors.

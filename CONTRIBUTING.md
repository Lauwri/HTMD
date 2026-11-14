# Contributing to HTMD

HTMD is an open **draft specification**. Constructive issues and pull requests are welcome.

## Proposing a change

1. State the use case and problem with the current grammar.
2. Provide minimal source examples: valid and invalid.
3. Specify exact normative behavior, error handling and security impact.
4. Explain how existing 0.1 documents and readers would behave.
5. Add positive and negative conformance cases to `conformance/cases.json`.
6. Update the specification first, then the examples and informative documents.

Use clear requirement language (`MUST`, `SHOULD`, `MAY`) only for testable rules. Keep HTMD declarative and avoid adding implicit execution.

## Repository validation

```sh
python3 tools/check_repository.py
```

This command checks the structure of our draft repository, not full standards compliance. Draft tests also run through `.github/workflows/validate.yml`.

## Version policy

- Nonbreaking editorial corrections may update this draft without changing the source syntax version.
- Grammar or semantic changes require revised normative text and regression vectors.
- Breaking changes after 0.1 stabilization require a new `htmd` source version and migration guidance.

## Code and license

By contributing, you agree to license your submitted changes under the repository's MIT license. Do not submit copyrighted external specification text in bulk; link to upstream standards instead.

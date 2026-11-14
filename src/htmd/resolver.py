"""Explicitly authorized, read-only, in-memory document and graph resolution.

Registry does not fetch local, external, or network resources. A denied reference
receives the same generic result whether or not the entity is indexed.
"""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from .parser import Document, canonical_uri


@dataclass(frozen=True)
class Resolution:
    status: str
    identifier: str
    title: str | None = None
    kind: str | None = None


class Registry:
    """Authorization policies receive canonical IDs; results retain source IDs."""
    def __init__(self, allowed: Callable[[str], bool] | None = None):
        self._records: dict[str, Document] = {}
        self._allow = allowed or (lambda _identifier: False)  # deny by default

    def add(self, doc: Document) -> None:
        ident = doc.metadata.get("id")
        if not ident:
            raise ValueError("registry requires an identified document")
        key = canonical_uri(ident)
        if key in self._records:
            raise ValueError("duplicate document identifier")
        self._records[key] = doc

    def resolve(self, identifier: str) -> Resolution:
        key = canonical_uri(identifier)
        if not self._allow(key):
            return Resolution("denied", identifier)
        doc = self._records.get(key)
        if doc is None:
            return Resolution("unresolved", identifier)
        return Resolution("resolved", identifier, doc.metadata.get("title"), doc.metadata.get("type"))

    def visible_relations(self) -> list[dict]:
        edges = []
        for doc in self._records.values():
            if not self._allow(canonical_uri(doc.metadata["id"])): continue
            for edge in doc.relations:
                if self._allow(canonical_uri(edge["from"])) and self._allow(canonical_uri(edge["to"])):
                    edges.append(dict(edge, asserted_by=doc.metadata["id"]))
        return edges

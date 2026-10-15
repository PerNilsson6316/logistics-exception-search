from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import sqrt
from typing import Protocol

from .models import DocumentKind, LogisticsDocument, SearchHit


class Embedder(Protocol):
    embed: Callable[[Sequence[str]], list[list[float]]]


@dataclass(frozen=True)
class IndexedDocument:
    document: LogisticsDocument
    embedding: list[float]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions must match")
    denominator = sqrt(sum(x * x for x in left)) * sqrt(sum(x * x for x in right))
    return sum(x * y for x, y in zip(left, right, strict=True)) / denominator if denominator else 0.0


class ShipmentIndex:
    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._documents: dict[str, IndexedDocument] = {}

    def add(self, documents: list[LogisticsDocument]) -> int:
        embeddings = self._embedder.embed([document.text for document in documents])
        if len(embeddings) != len(documents):
            raise ValueError("The embedding response count must match the document count")
        for document, embedding in zip(documents, embeddings, strict=True):
            self._documents[document.document_id] = IndexedDocument(document, embedding)
        return len(documents)

    def search(self, query: str, limit: int, shipment_id: str | None = None) -> list[SearchHit]:
        query_embedding = self._embedder.embed([query])[0]
        candidates = [
            item for item in self._documents.values()
            if shipment_id is None or item.document.shipment_id == shipment_id
        ]

        hits = [
            SearchHit(
                document=item.document,
                similarity=cosine_similarity(query_embedding, item.embedding),
                exception_priority=(
                    item.document.kind == DocumentKind.EXCEPTION and not item.document.resolved
                ),
            )
            for item in candidates
        ]
        hits.sort(key=lambda hit: (hit.exception_priority, hit.similarity), reverse=True)
        return hits[:limit]

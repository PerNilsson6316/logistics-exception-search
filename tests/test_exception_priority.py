from collections.abc import Sequence

from logistics_search.models import DocumentKind, LogisticsDocument
from logistics_search.shipment_index import ShipmentIndex


class FixedEmbedder:
    vectors = {
        "package status": [1.0, 0.0],
        "Routine carrier scan": [1.0, 0.0],
        "Address needs customer correction": [0.8, 0.6],
        "Another order exception": [0.9, 0.1],
    }

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.vectors[text] for text in texts]


def test_unresolved_exception_leads_relevant_events_for_the_same_shipment() -> None:
    index = ShipmentIndex(FixedEmbedder())
    index.add([
        LogisticsDocument(
            document_id="event-1",
            shipment_id="ORDER-7",
            kind=DocumentKind.SHIPMENT_EVENT,
            text="Routine carrier scan",
            occurred_at="2026-09-05T10:00:00Z",
        ),
        LogisticsDocument(
            document_id="exception-1",
            shipment_id="ORDER-7",
            kind=DocumentKind.EXCEPTION,
            text="Address needs customer correction",
            occurred_at="2026-09-05T11:00:00Z",
        ),
        LogisticsDocument(
            document_id="exception-other",
            shipment_id="ORDER-8",
            kind=DocumentKind.EXCEPTION,
            text="Another order exception",
            occurred_at="2026-09-05T12:00:00Z",
        ),
    ])

    hits = index.search("package status", limit=2, shipment_id="ORDER-7")

    assert [hit.document.document_id for hit in hits] == ["exception-1", "event-1"]
    assert hits[0].exception_priority is True


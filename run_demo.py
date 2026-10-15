from logistics_search.models import DocumentKind, LogisticsDocument
from logistics_search.infrai_embeddings import InfraiEmbeddings
from logistics_search.shipment_index import ShipmentIndex


def main() -> None:
    index = ShipmentIndex(InfraiEmbeddings())
    index.add([
        LogisticsDocument(
            document_id="evt-104",
            shipment_id="ORDER-4821",
            kind=DocumentKind.SHIPMENT_EVENT,
            text="Parcel scanned at the Shanghai sorting center.",
            occurred_at="2026-09-05T09:20:00Z",
        ),
        LogisticsDocument(
            document_id="exc-105",
            shipment_id="ORDER-4821",
            kind=DocumentKind.EXCEPTION,
            text="Delivery address could not be verified; customer action is required.",
            occurred_at="2026-09-05T15:40:00Z",
        ),
        LogisticsDocument(
            document_id="pod-106",
            shipment_id="ORDER-4821",
            kind=DocumentKind.PROOF_OF_DELIVERY,
            text="Signed delivery receipt for the storefront order.",
            occurred_at="2026-09-06T03:10:00Z",
        ),
    ])
    for hit in index.search("Why is this order waiting for delivery?", limit=2):
        print(hit.document.document_id, hit.document.kind.value, round(hit.similarity, 3))


if __name__ == "__main__":
    main()


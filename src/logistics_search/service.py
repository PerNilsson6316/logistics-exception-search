from fastapi import FastAPI

from .infrai_embeddings import InfraiEmbeddings
from .models import IndexRequest, IndexResponse, SearchRequest, SearchResponse
from .shipment_index import ShipmentIndex


def create_service(index: ShipmentIndex | None = None) -> FastAPI:
    search_index = index or ShipmentIndex(InfraiEmbeddings())
    service = FastAPI(title="Logistics document search")

    @service.post("/documents", response_model=IndexResponse)
    def index_documents(request: IndexRequest) -> IndexResponse:
        return IndexResponse(indexed=search_index.add(request.documents))

    @service.post("/search", response_model=SearchResponse)
    def search_documents(request: SearchRequest) -> SearchResponse:
        return SearchResponse(
            hits=search_index.search(request.query, request.limit, request.shipment_id)
        )

    return service


app = create_service()


from enum import Enum

from pydantic import BaseModel, Field


class DocumentKind(str, Enum):
    SHIPMENT_EVENT = "shipment_event"
    PROOF_OF_DELIVERY = "proof_of_delivery"
    EXCEPTION = "exception"


class LogisticsDocument(BaseModel):
    document_id: str
    shipment_id: str
    kind: DocumentKind
    text: str = Field(min_length=1)
    occurred_at: str
    resolved: bool = False


class IndexRequest(BaseModel):
    documents: list[LogisticsDocument] = Field(min_length=1)


class IndexResponse(BaseModel):
    indexed: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    shipment_id: str | None = None


class SearchHit(BaseModel):
    document: LogisticsDocument
    similarity: float
    exception_priority: bool


class SearchResponse(BaseModel):
    hits: list[SearchHit]


"""Read-only endpoints for indexed Taiwanese patent document versions."""

import logging
import re
import unicodedata
from datetime import date, datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.retrieval.embeddings import (
    EmbeddingError,
    LocalEmbeddingModel,
    PIPELINE,
    model_id,
    vector_literal,
)
from services.retrieval.lexical import TOKENIZER_VERSION, tokenize
from services.retrieval.fusion import CANDIDATE_LIMIT, RRF_K, fuse_rankings

logger = logging.getLogger(__name__)
NumberType = Literal["application", "publication", "grant"]
ContentScope = Literal["fulltext", "claims_only", "metadata_and_abstract"]
DocumentStage = Literal["publication", "grant"]
ErrorCode = Literal[
    "INVALID_PATENT_NUMBER",
    "INVALID_REQUEST",
    "PATENT_NOT_FOUND",
    "DATA_SOURCE_UNAVAILABLE",
    "EMBEDDING_UNAVAILABLE",
    "SEMANTIC_INDEX_UNAVAILABLE",
]


class PatentRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request):
            try:
                return await handler(request)
            except RequestValidationError:
                return api_error(
                    422, "INVALID_REQUEST", "請檢查查詢參數或文件版本 ID。"
                )

        return handle


class PatentError(BaseModel):
    code: ErrorCode
    message: str
    request_id: UUID


class PatentErrorEnvelope(BaseModel):
    error: PatentError


router = APIRouter(
    prefix="/api/v1/patents",
    tags=["patents"],
    route_class=PatentRoute,
    responses={
        422: {"model": PatentErrorEnvelope},
        503: {"model": PatentErrorEnvelope},
    },
)


class PatentVersion(BaseModel):
    document_id: UUID
    application_no: str
    publication_no: str
    document_stage: DocumentStage
    kind_code: str | None
    filing_date: date | None
    publication_date: date | None
    title_zh: str | None
    title_en: str | None
    content_scope: ContentScope


class PatentSearchResults(BaseModel):
    items: list[PatentVersion]
    limit: int
    offset: int
    has_more: bool


class LexicalPatentHit(PatentVersion):
    score: float


class LexicalSearchResults(BaseModel):
    items: list[LexicalPatentHit]
    tokenizer_version: str
    limit: int
    offset: int
    has_more: bool


class RankedSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=160)
    ipc: str | None = Field(default=None, max_length=24)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=10000)


class SemanticSearchResults(PatentSearchResults):
    items: list[LexicalPatentHit]
    model_name: str
    model_digest: str
    pipeline: str


class HybridPatentHit(PatentVersion):
    rrf_score: float
    lexical_rank: int | None
    lexical_score: float | None
    semantic_rank: int | None
    semantic_score: float | None


class HybridSearchResults(BaseModel):
    items: list[HybridPatentHit]
    tokenizer_version: str
    model_name: str
    model_digest: str
    pipeline: str
    rrf_k: int
    candidate_limit: int
    limit: int
    offset: int
    has_more: bool


class PartyName(BaseModel):
    zh: str | None = None
    en: str | None = None


class Classification(BaseModel):
    scheme: str
    code: str
    version: str


class SourceArtifact(BaseModel):
    dataset_name: str
    publisher: str
    dataset_url: str | None
    license_url: str | None
    batch_key: str
    ingested_at: datetime
    source_url: str | None
    artifact_sha256: str
    record_locator: str


class SourceLocation(BaseModel):
    xpath: str
    artifact_sha256: str


class PatentSection(BaseModel):
    section_type: str
    ordinal: int
    original_text: str
    source: SourceLocation


class PatentDetail(PatentVersion):
    abstract_zh: str | None
    abstract_en: str | None
    applicants: list[PartyName]
    inventors: list[PartyName]
    classifications: list[Classification]
    document_sha256: str
    parser_version: str
    sources: list[SourceArtifact]
    sections: list[PatentSection]


class PatentClaim(BaseModel):
    claim_number: int
    text: str
    independent: bool | None
    source: SourceLocation


class PatentClaims(BaseModel):
    document_id: UUID
    claims: list[PatentClaim]


SUMMARY_FIELDS = """
    d.id AS document_id, a.application_no, d.publication_no, d.document_stage,
    NULLIF(d.kind_code, '') AS kind_code, a.filing_date, d.publication_date,
    d.title_zh, d.title_en, d.metadata_jsonb->>'content_scope' AS content_scope
"""
DOCUMENTS_FROM = """
    FROM patent_documents d
    JOIN patent_applications a ON a.id = d.application_id
"""
PUBLIC_DOCUMENT_FILTER = """
    WHERE d.jurisdiction = 'TW' AND a.jurisdiction = 'TW'
      AND EXISTS (
        SELECT 1 FROM document_artifacts da
        JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
        JOIN ingestion_batches b ON b.id = ia.batch_id
        JOIN source_datasets s ON s.id = b.dataset_id
        WHERE da.document_id = d.id AND NOT s.is_demo
          AND ia.status IN ('parsed', 'partial') AND b.status IN ('complete', 'partial')
      )
"""
PUBLIC_DOCUMENTS = DOCUMENTS_FROM + PUBLIC_DOCUMENT_FILTER
NUMBER_FILTERS = {
    "application": "a.application_no = %s",
    "publication": "d.publication_no = %s AND d.document_stage = 'publication'",
    "grant": "d.publication_no = %s AND d.document_stage = 'grant'",
}

IPC_FILTER = """
    AND (%s::text IS NULL OR EXISTS (
        SELECT 1 FROM patent_classifications c
        WHERE c.document_id = d.id AND c.scheme = 'IPC'
          AND CASE WHEN length(%s::text) = 4
                   THEN starts_with(replace(upper(c.code), ' ', ''), %s)
                   ELSE replace(upper(c.code), ' ', '') = %s END
    ))
"""

LEXICAL_SEARCH = f"""
    WITH query AS (
        SELECT plainto_tsquery('simple', %s) AS terms
    ), matches AS (
        SELECT t.document_id, max(
            ts_rank(t.terms, q.terms) *
            CASE WHEN t.field IN ('title_zh', 'title_en') THEN 3
                 WHEN t.field IN ('abstract_zh', 'abstract_en') THEN 2 ELSE 1 END
        ) AS score
        FROM patent_lexical_chunks t CROSS JOIN query q
        WHERE t.tokenizer_version = %s AND t.terms @@ q.terms
        GROUP BY t.document_id
    )
    SELECT {SUMMARY_FIELDS}, m.score
    {DOCUMENTS_FROM} JOIN matches m ON m.document_id = d.id
    {PUBLIC_DOCUMENT_FILTER}
    {IPC_FILTER}
    ORDER BY m.score DESC, d.id
    LIMIT %s OFFSET %s
"""

SEMANTIC_SEARCH = f"""
    WITH candidates AS (
        SELECT {SUMMARY_FIELDS}
        {PUBLIC_DOCUMENTS}
        {IPC_FILTER}
    ), matches AS (
        SELECT t.document_id, 1 - min(t.embedding <=> %s::vector) AS score
        FROM patent_dense_chunks t JOIN candidates c ON c.document_id = t.document_id
        WHERE t.model_id = %s
        GROUP BY t.document_id
    )
    SELECT c.*, m.score
    FROM candidates c JOIN matches m ON m.document_id = c.document_id
    ORDER BY m.score DESC, c.document_id
    LIMIT %s OFFSET %s
"""


def normalize_ipc(value: str | None) -> str | None:
    if value is None:
        return None
    ipc = "".join(unicodedata.normalize("NFKC", value).upper().split())
    if not re.fullmatch(r"[A-H][0-9]{2}[A-Z](?:[0-9]{1,4}/[0-9]{1,6})?", ipc):
        raise ValueError("IPC 格式不符，例如 G01R 或 G01R27/02。")
    return ipc


class SemanticIndexUnavailable(Exception):
    pass


def indexed_model_id(model: LocalEmbeddingModel) -> int:
    with engine.connect() as conn:
        identity = model_id(conn, model)
        if (
            identity is None
            or not conn.exec_driver_sql(
                "SELECT EXISTS (SELECT 1 FROM patent_dense_chunks WHERE model_id = %s)",
                (identity,),
            ).scalar_one()
        ):
            raise SemanticIndexUnavailable
    return identity


def lexical_rows(
    conn: Connection, terms: str, ipc: str | None, limit: int, offset: int
):
    return (
        conn.exec_driver_sql(
            LEXICAL_SEARCH, (terms, TOKENIZER_VERSION, *((ipc,) * 4), limit, offset)
        )
        .mappings()
        .all()
    )


def semantic_rows(
    conn: Connection,
    embedding: str,
    identity: int,
    ipc: str | None,
    limit: int,
    offset: int,
):
    return (
        conn.exec_driver_sql(
            SEMANTIC_SEARCH, (*((ipc,) * 4), embedding, identity, limit, offset)
        )
        .mappings()
        .all()
    )


def missing_semantic_index():
    return api_error(503, "SEMANTIC_INDEX_UNAVAILABLE", "指定模型的語意索引尚未建立。")


def normalize_number(number: str, number_type: NumberType) -> str:
    normalized = unicodedata.normalize("NFKC", number).strip().upper()
    pattern = r"I[0-9]{1,12}" if number_type == "grant" else r"[0-9]{9}"
    if not re.fullmatch(pattern, normalized):
        raise ValueError("專利號碼格式與查詢類型不符。")
    return normalized


def api_error(status: int, code: ErrorCode, message: str) -> JSONResponse:
    error = PatentError(code=code, message=message, request_id=uuid4())
    if status == 503:
        logger.warning("Patent lookup unavailable request_id=%s", error.request_id)
    return JSONResponse(
        status_code=status,
        content=PatentErrorEnvelope(error=error).model_dump(mode="json"),
    )


def unavailable() -> JSONResponse:
    return api_error(503, "DATA_SOURCE_UNAVAILABLE", "目前無法查詢專利資料庫。")


def not_found() -> JSONResponse:
    return api_error(404, "PATENT_NOT_FOUND", "找不到此文件版本。")


def source_url(locator: str | None) -> str | None:
    if not locator:
        return None
    try:
        url = urlsplit(locator)
    except ValueError:
        return None
    if url.query or url.fragment:
        return None
    if (url.scheme, url.netloc) in {
        ("https", "data.gov.tw"),
        ("https", "cloud.tipo.gov.tw"),
        ("ftps", "ftp.tipo.gov.tw"),
    }:
        return locator
    return None


def document_sources(conn: Connection, document_id: UUID) -> list[SourceArtifact]:
    rows = conn.exec_driver_sql(
        """SELECT DISTINCT s.name AS dataset_name, s.publisher, s.official_url AS dataset_url,
                  s.license_notes AS license_url, b.batch_key, b.finished_at AS ingested_at,
                  ia.source_locator, ia.checksum AS artifact_sha256, da.record_locator
           FROM document_artifacts da
           JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
           JOIN ingestion_batches b ON b.id = ia.batch_id
           JOIN source_datasets s ON s.id = b.dataset_id
           WHERE da.document_id = %s AND NOT s.is_demo
             AND ia.status IN ('parsed', 'partial') AND b.status IN ('complete', 'partial')
           ORDER BY b.finished_at DESC, ia.checksum, da.record_locator, ia.source_locator,
                    s.name, s.publisher, s.official_url, s.license_notes, b.batch_key""",
        (document_id,),
    ).mappings()
    return [
        SourceArtifact(
            dataset_name=row["dataset_name"],
            publisher=row["publisher"],
            dataset_url=source_url(row["dataset_url"]),
            license_url=source_url(row["license_url"]),
            batch_key=row["batch_key"],
            ingested_at=row["ingested_at"],
            source_url=source_url(row["source_locator"]),
            artifact_sha256=row["artifact_sha256"],
            record_locator=row["record_locator"],
        )
        for row in rows
    ]


@router.get(
    "",
    response_model=PatentSearchResults,
)
def search_patents(
    number: Annotated[str, Query(min_length=1, max_length=32)],
    number_type: NumberType,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    try:
        number = normalize_number(number, number_type)
    except ValueError as error:
        return api_error(422, "INVALID_PATENT_NUMBER", str(error))
    try:
        with engine.connect() as conn:
            rows = (
                conn.exec_driver_sql(
                    f"""SELECT {SUMMARY_FIELDS} {PUBLIC_DOCUMENTS}
                    AND {NUMBER_FILTERS[number_type]}
                    ORDER BY d.document_stage, d.publication_no,
                       CASE d.metadata_jsonb->>'content_scope'
                         WHEN 'fulltext' THEN 0 WHEN 'claims_only' THEN 1 ELSE 2 END,
                       d.id
                    LIMIT %s OFFSET %s""",
                    (number, limit + 1, offset),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    return PatentSearchResults(
        items=[PatentVersion.model_validate(row) for row in rows[:limit]],
        limit=limit,
        offset=offset,
        has_more=len(rows) > limit,
    )


@router.post("/search", response_model=LexicalSearchResults)
def lexical_search(request: RankedSearchRequest):
    terms = " ".join(tokenize(request.query))
    if not terms:
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    try:
        ipc = normalize_ipc(request.ipc)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    try:
        with engine.connect() as conn:
            rows = lexical_rows(conn, terms, ipc, request.limit + 1, request.offset)
    except SQLAlchemyError:
        return unavailable()
    return LexicalSearchResults(
        items=[LexicalPatentHit.model_validate(row) for row in rows[: request.limit]],
        tokenizer_version=TOKENIZER_VERSION,
        limit=request.limit,
        offset=request.offset,
        has_more=len(rows) > request.limit,
    )


@router.post("/search/semantic", response_model=SemanticSearchResults)
def semantic_search(request: RankedSearchRequest):
    query = request.query.strip()
    if not query:
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    try:
        ipc = normalize_ipc(request.ipc)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    try:
        model = LocalEmbeddingModel.from_env()
        identity = indexed_model_id(model)
        embedding = vector_literal(model.embed_query(query))
        with engine.connect() as conn:
            rows = semantic_rows(
                conn, embedding, identity, ipc, request.limit + 1, request.offset
            )
    except SemanticIndexUnavailable:
        return missing_semantic_index()
    except EmbeddingError:
        return api_error(503, "EMBEDDING_UNAVAILABLE", "目前無法使用本機嵌入模型。")
    except SQLAlchemyError:
        return unavailable()
    return SemanticSearchResults(
        items=[LexicalPatentHit.model_validate(row) for row in rows[: request.limit]],
        model_name=model.name,
        model_digest=model.digest,
        pipeline=PIPELINE,
        limit=request.limit,
        offset=request.offset,
        has_more=len(rows) > request.limit,
    )


@router.post("/search/hybrid", response_model=HybridSearchResults)
def hybrid_search(request: RankedSearchRequest):
    query = request.query.strip()
    if not query:
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    try:
        ipc = normalize_ipc(request.ipc)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    try:
        model = LocalEmbeddingModel.from_env()
        identity = indexed_model_id(model)
        embedding = vector_literal(model.embed_query(query))
        terms = " ".join(tokenize(query))
        with engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as conn:
            lexical = (
                lexical_rows(conn, terms, ipc, CANDIDATE_LIMIT, 0) if terms else []
            )
            semantic = semantic_rows(conn, embedding, identity, ipc, CANDIDATE_LIMIT, 0)
    except SemanticIndexUnavailable:
        return missing_semantic_index()
    except EmbeddingError:
        return api_error(503, "EMBEDDING_UNAVAILABLE", "目前無法使用本機嵌入模型。")
    except SQLAlchemyError:
        return unavailable()

    ranked = fuse_rankings(lexical, semantic)
    end = request.offset + request.limit
    return HybridSearchResults(
        items=[
            HybridPatentHit.model_validate(row) for row in ranked[request.offset : end]
        ],
        tokenizer_version=TOKENIZER_VERSION,
        model_name=model.name,
        model_digest=model.digest,
        pipeline=PIPELINE,
        rrf_k=RRF_K,
        candidate_limit=CANDIDATE_LIMIT,
        limit=request.limit,
        offset=request.offset,
        has_more=len(ranked) > end,
    )


@router.get(
    "/{document_id}",
    response_model=PatentDetail,
    responses={404: {"model": PatentErrorEnvelope}},
)
def patent_detail(document_id: UUID):
    try:
        with engine.connect() as conn:
            row = (
                conn.exec_driver_sql(
                    f"""SELECT {SUMMARY_FIELDS}, d.abstract_zh, d.abstract_en,
                        d.metadata_jsonb->'applicants' AS applicants,
                        d.metadata_jsonb->'inventors' AS inventors,
                        d.source_hash AS document_sha256, d.parser_version
                    {PUBLIC_DOCUMENTS} AND d.id = %s""",
                    (document_id,),
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return not_found()
            classifications = (
                conn.exec_driver_sql(
                    """SELECT scheme, code, version FROM patent_classifications
                   WHERE document_id = %s ORDER BY scheme, code, version""",
                    (document_id,),
                )
                .mappings()
                .all()
            )
            sections = (
                conn.exec_driver_sql(
                    """SELECT section_type, ordinal, original_text, source_locator_jsonb AS source
                   FROM patent_sections WHERE document_id = %s ORDER BY section_type, ordinal""",
                    (document_id,),
                )
                .mappings()
                .all()
            )
            sources = document_sources(conn, document_id)
    except SQLAlchemyError:
        return unavailable()
    return PatentDetail.model_validate(
        {
            **row,
            "applicants": row["applicants"] or [],
            "inventors": row["inventors"] or [],
            "classifications": classifications,
            "sections": sections,
            "sources": sources,
        }
    )


@router.get(
    "/{document_id}/claims",
    response_model=PatentClaims,
    responses={404: {"model": PatentErrorEnvelope}},
)
def patent_claims(document_id: UUID):
    try:
        with engine.connect() as conn:
            exists = conn.exec_driver_sql(
                f"SELECT d.id {PUBLIC_DOCUMENTS} AND d.id = %s", (document_id,)
            ).scalar_one_or_none()
            if exists is None:
                return not_found()
            rows = (
                conn.exec_driver_sql(
                    """SELECT claim_number, text, independent_flag_nullable AS independent,
                          source_locator_jsonb AS source
                   FROM patent_claims WHERE document_id = %s ORDER BY claim_number""",
                    (document_id,),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    return PatentClaims(
        document_id=document_id,
        claims=[PatentClaim.model_validate(row) for row in rows],
    )

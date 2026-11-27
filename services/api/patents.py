"""Read-only endpoints for indexed Taiwanese patent document versions."""

import logging
import re
import unicodedata
from datetime import date, datetime
from time import perf_counter
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from services.api.activity import record_activity
from services.api.db import engine
from services.api.identity import IdentityError, IdentityUnavailable
from services.api.model_limits import ModelBusy, model_slot
from services.retrieval.embeddings import (
    EmbeddingError,
    LocalEmbeddingModel,
    PIPELINE,
    model_id,
    vector_literal,
)
from services.retrieval.lexical import TOKENIZER_VERSION, tokenize
from services.retrieval.query_features import (
    MAX_INVENTION_LENGTH,
    QUERY_EXPANSION_VERSION,
    TechnicalFeature,
    expand_query,
)
from services.retrieval.ollama import LocalModelError, LocalOllamaModel
from services.retrieval.rerank import RERANK_LIMIT, RERANK_VERSION, rerank_order
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
    "ANALYSIS_UNAVAILABLE",
    "AUTH_REQUIRED",
    "ADMIN_REQUIRED",
    "ACCOUNT_EXISTS",
    "RUN_NOT_FOUND",
    "PROJECT_NOT_FOUND",
    "PROJECT_NOT_EMPTY",
    "BOOKMARK_NOT_FOUND",
    "SESSION_NOT_FOUND",
    "REPORT_UNAVAILABLE",
    "REPORT_NOT_FOUND",
    "REPORT_NOT_READY",
    "PASSWORD_CONFIRMATION_FAILED",
    "LOGIN_THROTTLED",
    "MODEL_BUSY",
    "SEARCH_JOB_ACTIVE",
    "SEARCH_JOB_NOT_FOUND",
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
            except IdentityError:
                response = api_error(401, "AUTH_REQUIRED", "請登入或確認登入資訊。")
                response.headers["WWW-Authenticate"] = "Bearer"
                return response
            except IdentityUnavailable:
                return unavailable()
            except ModelBusy:
                response = api_error(429, "MODEL_BUSY", "本機模型忙碌中，請稍後重試。")
                response.headers["Retry-After"] = "5"
                response.headers["Cache-Control"] = "no-store"
                return response

        async def track_activity(request):
            started = perf_counter()
            response = await handle(request)
            record_activity(request.method, self.path, response.status_code, started)
            return response

        return track_activity


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
    published_from: date | None = None
    published_to: date | None = None
    document_stage: DocumentStage | None = None
    content_scope: ContentScope | None = None
    applicant: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
        ]
        | None
    ) = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=10000)


class HybridSearchRequest(RankedSearchRequest):
    query: str = Field(min_length=1, max_length=MAX_INVENTION_LENGTH)
    features: list[TechnicalFeature] = Field(default_factory=list, max_length=5)
    rerank: bool = False
    sort_by: Literal["relevance", "date_desc", "date_asc"] = "relevance"


class SemanticSearchResults(PatentSearchResults):
    items: list[LexicalPatentHit]
    model_name: str
    model_digest: str
    pipeline: str


class PartyName(BaseModel):
    zh: str | None = None
    en: str | None = None


class HybridPatentHit(PatentVersion):
    rrf_score: float
    lexical_rank: int | None
    lexical_score: float | None
    semantic_rank: int | None
    semantic_score: float | None
    fusion_rank: int
    rerank_rank: int | None
    abstract_excerpt: str | None = None
    applicants: list[PartyName] = Field(default_factory=list)
    ipc_codes: list[str] = Field(default_factory=list)
    official_source_url: str | None = None


class RerankMetadata(BaseModel):
    model_name: str
    model_digest: str
    version: str
    candidate_count: int


class CorpusCoverage(BaseModel):
    observed_at: datetime
    lexical_versions: int
    semantic_versions: int
    latest_document_date: date | None


class HybridSearchResults(BaseModel):
    items: list[HybridPatentHit]
    tokenizer_version: str
    model_name: str
    model_digest: str
    pipeline: str
    query_expansion_version: str
    rrf_k: int
    candidate_limit: int
    applied_feature_ids: list[str]
    reranker: RerankMetadata | None
    corpus_coverage: CorpusCoverage | None = None
    limit: int
    offset: int
    has_more: bool


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


class PatentLegalEvent(BaseModel):
    kind: Literal["extinguishment", "gazette_correction"]
    certificate_no: str
    effective_on: date | None
    detail: str | None
    source_url: str | None
    dataset_url: str | None
    batch_key: str
    ingested_at: datetime
    artifact_sha256: str
    record_locator: str


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
    legal_events: list[PatentLegalEvent]


class PatentClaim(BaseModel):
    claim_number: int
    text: str
    independent: bool | None
    referenced_claim_numbers: list[int]
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

SEARCH_FILTERS = """
    AND (%s::text IS NULL OR EXISTS (
        SELECT 1 FROM patent_classifications c
        WHERE c.document_id = d.id AND c.scheme = 'IPC'
          AND CASE WHEN length(%s::text) = 4
                   THEN starts_with(replace(upper(c.code), ' ', ''), %s)
                   ELSE replace(upper(c.code), ' ', '') = %s END
    ))
    AND (%s::date IS NULL OR d.publication_date >= %s)
    AND (%s::date IS NULL OR d.publication_date <= %s)
    AND (%s::text IS NULL OR d.document_stage = %s)
    AND (%s::text IS NULL OR d.metadata_jsonb->>'content_scope' = %s)
    AND (%s::text IS NULL OR EXISTS (
        SELECT 1 FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(d.metadata_jsonb->'applicants') = 'array'
                 THEN d.metadata_jsonb->'applicants' ELSE '[]'::jsonb END
        ) AS applicant(entry)
        WHERE strpos(lower(applicant.entry->>'zh'), lower(%s)) > 0
           OR strpos(lower(applicant.entry->>'en'), lower(%s)) > 0
    ))
"""

# Versions of one publication share title and abstract, so their scores can tie.
# The richest version must then rank first; document IDs are random.
SCOPE_ORDER = """CASE {}
        WHEN 'fulltext' THEN 0 WHEN 'claims_only' THEN 1 ELSE 2 END"""

LEXICAL_SEARCH = f"""
    WITH query AS (
        SELECT to_tsquery('simple', %s) AS terms
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
    {SEARCH_FILTERS}
    ORDER BY m.score DESC, {SCOPE_ORDER.format("d.metadata_jsonb->>'content_scope'")}, d.id
    LIMIT %s OFFSET %s
"""

SEMANTIC_CANDIDATES = f"""
    WITH candidates AS (
        SELECT {SUMMARY_FIELDS}
        {PUBLIC_DOCUMENTS}
        {SEARCH_FILTERS}
    )
"""
CORPUS_COVERAGE = (
    SEMANTIC_CANDIDATES
    + """
    , coverage AS (
        SELECT c.publication_date,
            EXISTS (
                SELECT 1 FROM patent_lexical_chunks t
                WHERE t.document_id = c.document_id AND t.tokenizer_version = %s
                  AND t.terms <> ''::tsvector
            ) AS lexical,
            EXISTS (
                SELECT 1 FROM patent_dense_chunks t
                WHERE t.model_id = %s AND t.document_id = c.document_id
            ) AS semantic
        FROM candidates c
    )
    SELECT transaction_timestamp() AS observed_at,
        count(*) FILTER (WHERE lexical) AS lexical_versions,
        count(*) FILTER (WHERE semantic) AS semantic_versions,
        max(publication_date) FILTER (WHERE lexical OR semantic) AS latest_document_date
    FROM coverage
"""
)
SEMANTIC_ORDER = f"""
    ORDER BY m.score DESC, {SCOPE_ORDER.format("c.content_scope")}, c.document_id
    LIMIT %s OFFSET %s
"""
SEMANTIC_SEARCH = (
    SEMANTIC_CANDIDATES
    + """
    , matches AS (
        SELECT t.document_id, 1 - min(t.embedding <=> %s::vector) AS score
        FROM patent_dense_chunks t JOIN candidates c ON c.document_id = t.document_id
        WHERE t.model_id = %s
        GROUP BY t.document_id
    )
    SELECT c.*, m.score
    FROM candidates c JOIN matches m ON m.document_id = c.document_id
"""
    + SEMANTIC_ORDER
)

# For an exact IPC code, look up each candidate's vectors by (model_id, document_id).
SEMANTIC_IPC_SEARCH = (
    SEMANTIC_CANDIDATES
    + """
    SELECT c.*, m.score
    FROM candidates c CROSS JOIN LATERAL (
        SELECT 1 - min(t.embedding <=> %s::vector) AS score
        FROM patent_dense_chunks t
        WHERE t.model_id = %s AND t.document_id = c.document_id
    ) m
    WHERE m.score IS NOT NULL
"""
    + SEMANTIC_ORDER
)


def normalize_ipc(value: str | None) -> str | None:
    if value is None:
        return None
    ipc = "".join(unicodedata.normalize("NFKC", value).upper().split())
    if not re.fullmatch(r"[A-H][0-9]{2}[A-Z](?:[0-9]{1,4}/[0-9]{1,6})?", ipc):
        raise ValueError("IPC 格式不符，例如 G01R 或 G01R27/02。")
    return ipc


def search_filter_params(request: RankedSearchRequest) -> tuple:
    ipc = normalize_ipc(request.ipc)
    if (
        request.published_from
        and request.published_to
        and request.published_from > request.published_to
    ):
        raise ValueError("公開／公告日期起日不得晚於迄日。")
    return (
        *((ipc,) * 4),
        *((request.published_from,) * 2),
        *((request.published_to,) * 2),
        *((request.document_stage,) * 2),
        *((request.content_scope,) * 2),
        *((request.applicant,) * 3),
    )


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


def lexical_statement(terms: str, filters: tuple, limit: int, offset: int):
    return LEXICAL_SEARCH, (terms, TOKENIZER_VERSION, *filters, limit, offset)


def semantic_statement(
    embedding: str, identity: int, filters: tuple, limit: int, offset: int
):
    ipc = filters[0]
    sql = SEMANTIC_IPC_SEARCH if ipc and "/" in ipc else SEMANTIC_SEARCH
    return sql, (*filters, embedding, identity, limit, offset)


def lexical_rows(conn: Connection, terms: str, filters: tuple, limit: int, offset: int):
    return (
        conn.exec_driver_sql(*lexical_statement(terms, filters, limit, offset))
        .mappings()
        .all()
    )


def semantic_rows(
    conn: Connection,
    embedding: str,
    identity: int,
    filters: tuple,
    limit: int,
    offset: int,
):
    return (
        conn.exec_driver_sql(
            *semantic_statement(embedding, identity, filters, limit, offset)
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
    return document_sources_by_id(conn, [document_id]).get(document_id, [])


def document_sources_by_id(
    conn: Connection, document_ids: list[UUID]
) -> dict[UUID, list[SourceArtifact]]:
    if not document_ids:
        return {}
    rows = conn.exec_driver_sql(
        """SELECT DISTINCT da.document_id, s.name AS dataset_name, s.publisher, s.official_url AS dataset_url,
                  s.license_notes AS license_url, b.batch_key, b.finished_at AS ingested_at,
                  ia.source_locator, ia.checksum AS artifact_sha256, da.record_locator
           FROM document_artifacts da
           JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
           JOIN ingestion_batches b ON b.id = ia.batch_id
           JOIN source_datasets s ON s.id = b.dataset_id
           WHERE da.document_id = ANY(%s::uuid[]) AND NOT s.is_demo
             AND ia.status IN ('parsed', 'partial') AND b.status IN ('complete', 'partial')
           ORDER BY b.finished_at DESC, ia.checksum, da.record_locator, ia.source_locator,
                    s.name, s.publisher, s.official_url, s.license_notes, b.batch_key""",
        (document_ids,),
    ).mappings()
    sources: dict[UUID, list[SourceArtifact]] = {}
    for row in rows:
        sources.setdefault(row["document_id"], []).append(
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
        )
    return sources


def add_candidate_previews(conn: Connection, ranked: list[dict]) -> None:
    if not ranked:
        return
    ids = [hit["document_id"] for hit in ranked]
    rows = conn.exec_driver_sql(
        """SELECT d.id, left(coalesce(d.abstract_zh, d.abstract_en), 240) AS abstract_excerpt,
                  d.metadata_jsonb->'applicants' AS applicants,
                  ARRAY(
                    SELECT DISTINCT c.code FROM patent_classifications c
                    WHERE c.document_id = d.id AND c.scheme = 'IPC'
                    ORDER BY c.code LIMIT 4
                  ) AS ipc_codes
           FROM patent_documents d WHERE d.id = ANY(%s::uuid[])""",
        (ids,),
    ).mappings()
    previews = {row["id"]: row for row in rows}
    sources = document_sources_by_id(conn, ids)
    for hit in ranked:
        version = hit["document_id"]
        row = previews[version]
        hit.update(
            abstract_excerpt=row["abstract_excerpt"],
            applicants=row["applicants"] or [],
            ipc_codes=row["ipc_codes"],
            official_source_url=next(
                (
                    artifact.dataset_url
                    for artifact in sources.get(version, [])
                    if artifact.dataset_url is not None
                ),
                None,
            ),
        )


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
    terms = " & ".join(tokenize(request.query))
    if not terms:
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    try:
        filters = search_filter_params(request)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    try:
        with engine.connect() as conn:
            rows = lexical_rows(conn, terms, filters, request.limit + 1, request.offset)
    except SQLAlchemyError:
        return unavailable()
    return LexicalSearchResults(
        items=[LexicalPatentHit.model_validate(row) for row in rows[: request.limit]],
        tokenizer_version=TOKENIZER_VERSION,
        limit=request.limit,
        offset=request.offset,
        has_more=len(rows) > request.limit,
    )


@router.post(
    "/search/semantic",
    response_model=SemanticSearchResults,
    responses={429: {"model": PatentErrorEnvelope}},
)
def semantic_search(request: RankedSearchRequest):
    query = request.query.strip()
    if not query:
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    try:
        filters = search_filter_params(request)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    try:
        model = LocalEmbeddingModel.from_env()
        identity = indexed_model_id(model)
        with model_slot():
            embedding = vector_literal(model.embed_query(query))
        with engine.connect() as conn:
            rows = semantic_rows(
                conn, embedding, identity, filters, request.limit + 1, request.offset
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


@router.post(
    "/search/hybrid",
    response_model=HybridSearchResults,
    responses={429: {"model": PatentErrorEnvelope}},
)
def hybrid_search(request: HybridSearchRequest):
    return run_hybrid(request)


def run_hybrid(request: HybridSearchRequest, *, full_snapshot: bool = False):
    query = request.query.strip()
    if not query:
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    try:
        filters = search_filter_params(request)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    feature_ids = [feature.feature_id for feature in request.features]
    if len(set(feature_ids)) != len(feature_ids):
        return api_error(422, "INVALID_REQUEST", "技術特徵 ID 必須唯一。")
    terms, semantic_query = expand_query(query, request.features)
    try:
        model = LocalEmbeddingModel.from_env()
        identity = indexed_model_id(model)
        with model_slot():
            embedding = vector_literal(model.embed_query(semantic_query))
        with engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as conn:
            lexical = (
                lexical_rows(conn, terms, filters, CANDIDATE_LIMIT, 0) if terms else []
            )
            semantic = semantic_rows(
                conn, embedding, identity, filters, CANDIDATE_LIMIT, 0
            )
            coverage = CorpusCoverage.model_validate(
                conn.exec_driver_sql(
                    CORPUS_COVERAGE, (*filters, TOKENIZER_VERSION, identity)
                )
                .mappings()
                .one()
            )
            ranked = fuse_rankings(lexical, semantic)
            add_candidate_previews(conn, ranked)
    except SemanticIndexUnavailable:
        return missing_semantic_index()
    except EmbeddingError:
        return api_error(503, "EMBEDDING_UNAVAILABLE", "目前無法使用本機嵌入模型。")
    except SQLAlchemyError:
        return unavailable()

    for rank, hit in enumerate(ranked, 1):
        hit.update(fusion_rank=rank, rerank_rank=None)
    reranker = None
    if request.rerank and len(ranked) > 1:
        prefix = ranked[:RERANK_LIMIT]
        candidates = [
            {
                "id": i,
                "title": (hit["title_zh"] or hit["title_en"] or "")[:100],
                "abstract": (hit["abstract_excerpt"] or "")[:180],
            }
            for i, hit in enumerate(prefix, 1)
        ]
        try:
            analyzer = LocalOllamaModel.from_env("ANALYSIS")
            with model_slot():
                order = rerank_order(analyzer, semantic_query, candidates)
        except LocalModelError:
            return api_error(
                503, "ANALYSIS_UNAVAILABLE", "本機模型目前無法重排專利候選。"
            )
        ranked[: len(prefix)] = [prefix[index - 1] for index in order]
        for rank, hit in enumerate(ranked[: len(prefix)], 1):
            hit["rerank_rank"] = rank
        reranker = RerankMetadata(
            model_name=analyzer.name,
            model_digest=analyzer.digest,
            version=RERANK_VERSION,
            candidate_count=len(prefix),
        )
    if request.sort_by != "relevance":
        dated = [hit for hit in ranked if hit["publication_date"] is not None]
        dated.sort(
            key=lambda hit: hit["publication_date"],
            reverse=request.sort_by == "date_desc",
        )
        ranked = dated + [hit for hit in ranked if hit["publication_date"] is None]
    start = 0 if full_snapshot else request.offset
    end = len(ranked) if full_snapshot else start + request.limit
    return HybridSearchResults(
        items=[HybridPatentHit.model_validate(row) for row in ranked[start:end]],
        query_expansion_version=QUERY_EXPANSION_VERSION,
        tokenizer_version=TOKENIZER_VERSION,
        model_name=model.name,
        model_digest=model.digest,
        pipeline=PIPELINE,
        rrf_k=RRF_K,
        candidate_limit=CANDIDATE_LIMIT,
        applied_feature_ids=feature_ids,
        reranker=reranker,
        corpus_coverage=coverage,
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
            events = (
                conn.exec_driver_sql(
                    """SELECT e.kind,e.certificate_no,e.effective_on,e.detail,e.record_locator,
                              ia.source_locator,ia.checksum AS artifact_sha256,b.batch_key,
                              b.finished_at AS ingested_at,s.official_url
                       FROM patent_documents d
                       JOIN patent_legal_events e ON e.application_id = d.application_id
                       JOIN ingestion_artifacts ia ON ia.id = e.artifact_id
                       JOIN ingestion_batches b ON b.id = ia.batch_id
                       JOIN source_datasets s ON s.id = b.dataset_id
                       WHERE d.id=%s AND (d.document_stage='publication' OR d.publication_no=e.certificate_no)
                         AND NOT s.is_demo AND s.dataset_key='TIPO-15974'
                         AND ia.status='parsed' AND b.status='complete'
                       ORDER BY b.batch_key DESC,e.effective_on DESC NULLS LAST,e.id""",
                    (document_id,),
                )
                .mappings()
                .all()
            )
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
            "legal_events": [
                {
                    **event,
                    "source_url": source_url(event["source_locator"]),
                    "dataset_url": source_url(event["official_url"]),
                }
                for event in events
            ],
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
                    """SELECT c.claim_number, c.text, c.independent_flag_nullable AS independent,
                          c.source_locator_jsonb AS source,
                          ARRAY(SELECT d.parent_number FROM claim_dependencies d
                                WHERE d.document_id = c.document_id
                                  AND d.child_number = c.claim_number
                                ORDER BY d.parent_number) AS referenced_claim_numbers
                   FROM patent_claims c WHERE c.document_id = %s ORDER BY c.claim_number""",
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

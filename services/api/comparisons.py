"""Compare reviewed technical features against one public document version."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import (
    PUBLIC_DOCUMENTS,
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    not_found,
    unavailable,
)
from services.retrieval.evidence import (
    COMPARISON_VERSION,
    Passage,
    Verdict,
    judge,
    select_excerpt,
)
from services.retrieval.ollama import LocalModelError, LocalOllamaModel
from services.retrieval.query_features import TechnicalFeature

router = APIRouter(
    prefix="/api/v1/patents",
    tags=["patents"],
    route_class=PatentRoute,
    responses={
        404: {"model": PatentErrorEnvelope},
        422: {"model": PatentErrorEnvelope},
        503: {"model": PatentErrorEnvelope},
    },
)

PASSAGES = """
    WITH body AS (
        SELECT 'claim' AS kind, claim_number AS ordinal, text, source_locator_jsonb AS source
        FROM patent_claims WHERE document_id = %s
        UNION ALL
        SELECT section_type, ordinal, original_text, source_locator_jsonb
        FROM patent_sections WHERE document_id = %s
    )
    SELECT kind, ordinal, text, source->>'xpath' AS xpath,
           source->>'artifact_sha256' AS artifact_sha256
    FROM body
    WHERE nullif(source->>'xpath', '') IS NOT NULL AND EXISTS (
        SELECT 1 FROM document_artifacts da
        JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
        JOIN ingestion_batches b ON b.id = ia.batch_id
        JOIN source_datasets s ON s.id = b.dataset_id
        WHERE da.document_id = %s AND ia.checksum = body.source->>'artifact_sha256'
          AND NOT s.is_demo AND ia.status IN ('parsed', 'partial')
          AND b.status IN ('complete', 'partial')
    )
    ORDER BY (kind <> 'claim'), kind, ordinal
"""


class CompareRequest(BaseModel):
    features: list[TechnicalFeature] = Field(min_length=1, max_length=5)


class EvidenceCitation(BaseModel):
    kind: str
    ordinal: int
    xpath: str
    artifact_sha256: str
    char_start: int
    char_end: int
    quote: str


class FeatureComparison(BaseModel):
    feature_id: str
    verdict: Verdict
    evidence: EvidenceCitation | None
    basis: str


class ComparisonResponse(BaseModel):
    document_id: UUID
    document_sha256: str
    comparison_version: str
    passages_checked: int
    model_name: str | None
    model_digest: str | None
    items: list[FeatureComparison]


@router.post("/{document_id}/compare", response_model=ComparisonResponse)
def compare(document_id: UUID, request: CompareRequest):
    if len({feature.feature_id for feature in request.features}) != len(
        request.features
    ):
        return api_error(422, "INVALID_REQUEST", "技術特徵 ID 必須唯一。")
    try:
        with engine.connect() as conn:
            checksum = conn.exec_driver_sql(
                f"SELECT d.source_hash {PUBLIC_DOCUMENTS} AND d.id = %s", (document_id,)
            ).scalar_one_or_none()
            if checksum is None:
                return not_found()
            passages = [
                Passage(**row)
                for row in conn.exec_driver_sql(PASSAGES, (document_id,) * 3).mappings()
            ]
    except SQLAlchemyError:
        return unavailable()

    excerpts = {
        feature.feature_id: select_excerpt(feature, passages)
        for feature in request.features
    }
    pairs = [
        (feature, excerpts[feature.feature_id])
        for feature in request.features
        if excerpts[feature.feature_id] is not None
    ]
    model = None
    decisions = {}
    if pairs:
        try:
            model = LocalOllamaModel.from_env("ANALYSIS")
            decisions = judge(model, pairs)
        except LocalModelError:
            return api_error(
                503, "ANALYSIS_UNAVAILABLE", "本機模型目前無法完成技術比對。"
            )

    items = []
    for feature in request.features:
        excerpt = excerpts[feature.feature_id]
        verdict = decisions.get(
            feature.feature_id,
            "not_found_in_checked_content" if passages else "uncertain",
        )
        evidence = None
        basis = (
            "在已保存且可追溯的請求項及說明書中未找到指定字詞。"
            if passages
            else "此版本缺少可追溯的請求項或說明書。"
        )
        if excerpt is not None:
            passage = excerpt.passage
            evidence = EvidenceCitation(
                kind=passage.kind,
                ordinal=passage.ordinal,
                xpath=passage.xpath,
                artifact_sha256=passage.artifact_sha256,
                char_start=excerpt.start,
                char_end=excerpt.end,
                quote=excerpt.quote,
            )
            basis = "本機模型根據所附的單一原文片段判定。"
        items.append(
            FeatureComparison(
                feature_id=feature.feature_id,
                verdict=verdict,
                evidence=evidence,
                basis=basis,
            )
        )
    return ComparisonResponse(
        document_id=document_id,
        document_sha256=checksum,
        comparison_version=COMPARISON_VERSION,
        passages_checked=len(passages),
        model_name=model.name if model else None,
        model_digest=model.digest if model else None,
        items=items,
    )

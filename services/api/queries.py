"""Local technical-feature analysis API."""

from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, StringConstraints

from services.api.model_limits import model_slot
from services.api.patents import PatentErrorEnvelope, PatentRoute, api_error
from services.retrieval.ollama import LocalModelError, LocalOllamaModel
from services.retrieval.query_features import (
    ANALYSIS_VERSION,
    TechnicalFeature,
    analyze_features,
)

router = APIRouter(
    prefix="/api/v1/queries",
    tags=["queries"],
    route_class=PatentRoute,
    responses={
        422: {"model": PatentErrorEnvelope},
        429: {"model": PatentErrorEnvelope},
        503: {"model": PatentErrorEnvelope},
    },
)


class AnalyzeRequest(BaseModel):
    query: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
    ]


class AnalyzeResponse(BaseModel):
    features: list[TechnicalFeature]
    model_name: str
    model_digest: str
    analysis_version: str


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    try:
        model = LocalOllamaModel.from_env("ANALYSIS")
        with model_slot():
            features = analyze_features(model, request.query)
    except LocalModelError:
        return api_error(
            503, "ANALYSIS_UNAVAILABLE", "本機模型目前無法產生有效的技術特徵。"
        )
    return AnalyzeResponse(
        features=features,
        model_name=model.name,
        model_digest=model.digest,
        analysis_version=ANALYSIS_VERSION,
    )

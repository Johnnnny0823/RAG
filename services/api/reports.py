"""Build private prior-art PDFs from saved search data."""

from io import BytesIO
from os import getenv
from threading import Lock
from uuid import UUID
from xml.sax.saxutils import escape, quoteattr

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFError
from reportlab.platypus import Paragraph, SimpleDocTemplate
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import (
    PatentErrorEnvelope,
    PatentRoute,
    SourceArtifact,
    api_error,
    document_sources_by_id,
    unavailable,
)
from services.api.search_runs import Owner, RunDetails, read_saved_search

router = APIRouter(
    prefix="/api/v1/search-runs", tags=["research"], route_class=PatentRoute
)
FONT = "PatentScopeCJK"
FONT_LOCK = Lock()
STAGES = {"publication": "公開", "grant": "公告"}
SCOPES = {
    "fulltext": "全文",
    "claims_only": "請求項",
    "metadata_and_abstract": "書目與摘要",
}
VERDICTS = {
    "supported": "有明確證據",
    "partially_supported": "部分符合",
    "not_found_in_checked_content": "未找到證據",
    "uncertain": "不確定",
}


def register_report_font():
    with FONT_LOCK:
        if FONT not in pdfmetrics.getRegisteredFontNames():
            custom_path = getenv("REPORT_FONT_PATH")
            path = custom_path or "/usr/share/fonts/truetype/arphic/uming.ttc"
            default_index = "0" if custom_path else "2"
            pdfmetrics.registerFont(
                TTFont(
                    FONT,
                    path,
                    subfontIndex=int(getenv("REPORT_FONT_INDEX", default_index)),
                )
            )


def build_report(run: RunDetails, sources: dict[UUID, list[SourceArtifact]]) -> bytes:
    register_report_font()
    ink = HexColor("#132432")
    teal = HexColor("#075B56")
    body = ParagraphStyle(
        "Body",
        fontName=FONT,
        fontSize=10.5,
        leading=16,
        spaceAfter=6,
        textColor=ink,
        wordWrap="CJK",
    )
    title = ParagraphStyle(
        "Title",
        parent=body,
        fontSize=25,
        leading=33,
        spaceAfter=12,
        textColor=teal,
        keepWithNext=True,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=body,
        fontSize=16,
        leading=22,
        spaceBefore=14,
        textColor=teal,
        keepWithNext=True,
    )
    subhead = ParagraphStyle(
        "Subhead",
        parent=body,
        fontSize=12,
        leading=18,
        spaceBefore=8,
        keepWithNext=True,
    )
    story = []

    def paragraph(value: str, style=body):
        story.append(Paragraph(escape(value).replace("\n", "<br/>"), style))

    def link(label: str, url: str):
        story.append(
            Paragraph(
                f'<link href={quoteattr(url)} color="#075B56">{escape(label)}</link>',
                body,
            )
        )

    paragraph("先前技術研究報告", title)
    paragraph(
        f"PatentScope AI  /  搜尋建立時間 {run.created_at.isoformat()}  /  紀錄 {run.id}"
    )
    paragraph("研究限制", heading)
    paragraph(
        "供研發前調查使用。結果限於檢索時已索引的 TIPO 樣本與候選範圍。判定只涵蓋已檢查片段，未找到證據不代表技術不存在。相似度與排名不能用來判定侵權、新穎性或可專利性。"
    )
    paragraph("來源批次以匯出時可查證的候選文件來源為準。")
    if coverage := run.settings.get("corpus_coverage"):
        paragraph(
            f"搜尋涵蓋範圍 · 記錄於 {coverage['observed_at']} · "
            f"詞彙索引 {coverage['lexical_versions']} 個文件版本 · "
            f"向量索引 {coverage['semantic_versions']} 個文件版本 · "
            f"最新文件日期 {coverage['latest_document_date'] or '未提供'}"
        )
        paragraph("數量依本次篩選條件計算。同一文件版本可同時出現在兩種索引。")
    else:
        paragraph("這筆搜尋未記錄檢索時的索引涵蓋範圍。")
    paragraph("報告可供核對保存的候選與引用，重建當時的索引仍需原始語料與索引備份。")
    paragraph("構想與檢索策略", heading)
    paragraph(run.request.query)
    filters = [
        ("IPC", run.request.ipc),
        ("日期起日", run.request.published_from),
        ("日期迄日", run.request.published_to),
        ("申請人", run.request.applicant),
        ("文件類型", STAGES.get(run.request.document_stage or "")),
    ]
    paragraph(
        "篩選條件 · "
        + ("、".join(f"{key} {value}" for key, value in filters if value) or "無")
    )
    paragraph(
        f"詞彙與向量檢索經 RRF 融合（k={run.settings.get('rrf_k', '未記錄')}），重排序{'啟用' if run.request.rerank else '停用'}。"
    )
    paragraph(
        f"分詞器 {run.settings.get('tokenizer_version', '未記錄')} · 向量模型 {run.settings.get('model_name', '未記錄')}"
    )
    if digest := run.settings.get("model_digest"):
        paragraph(f"向量模型 SHA-256 · {digest}")
    if reranker := run.settings.get("reranker"):
        paragraph(
            f"重排序模型 {reranker['model_name']} · SHA-256 {reranker['model_digest']}"
        )
    features = {feature.feature_id: feature for feature in run.request.features}
    for feature in features.values():
        paragraph(
            f"{feature.description_zh}（{'必要' if feature.must_have else '選用'}）",
            subhead,
        )
        paragraph(
            "、".join(feature.keywords_zh + feature.keywords_en) or "未保存檢索詞。"
        )
    paragraph("候選文件與證據", heading)
    paragraph(
        f"共保存 {len(run.items)} 個候選文件版本，已比對 {len(run.comparisons)} 份。"
    )
    comparisons = {item.document_id: item for item in run.comparisons}
    for rank, document in enumerate(run.items, 1):
        name = document.title_zh or document.title_en or "未提供標題"
        paragraph(
            f"{rank:02d}  {STAGES[document.document_stage]} {document.publication_no} {document.kind_code or ''}  {name}",
            subhead,
        )
        paragraph(
            f"{SCOPES[document.content_scope]} · 申請號 {document.application_no} · 文件日期 {document.publication_date or '未知'} · 版本 {document.document_id}"
        )
        paragraph(
            f"詞彙順位 {document.lexical_rank or '-'} · 語意順位 {document.semantic_rank or '-'} · 融合順位 {document.fusion_rank} · 重排序位 {document.rerank_rank or '-'}"
        )
        for source in sources.get(document.document_id, []):
            paragraph(
                f"來源 · {source.publisher} · {source.dataset_name} · 批次 {source.batch_key} · 匯入 {source.ingested_at.date()}"
            )
            if source.dataset_url:
                link("官方資料集", source.dataset_url)
            if source.source_url and source.source_url != source.dataset_url:
                link("官方原始檔", source.source_url)
        comparison = comparisons.get(document.document_id)
        if comparison is None:
            paragraph("尚未保存此版本的技術比對。")
            continue
        paragraph(
            f"已檢查 {comparison.passages_checked} 個原文片段 · 比對版本 {comparison.comparison_version}"
        )
        if comparison.model_name:
            paragraph(
                f"比對模型 {comparison.model_name} · SHA-256 {comparison.model_digest or '未知'}"
            )
        for item in comparison.items:
            feature = features.get(item.feature_id)
            paragraph(
                f"{feature.description_zh if feature else item.feature_id} · {VERDICTS[item.verdict]}",
                subhead,
            )
            paragraph(item.basis)
            if evidence := item.evidence:
                paragraph(evidence.quote)
                paragraph(
                    f"原文定位 · {evidence.xpath} · 字元區間 [{evidence.char_start}, {evidence.char_end})"
                )
                paragraph(f"原始檔 SHA-256 · {evidence.artifact_sha256}")

    def footer(canvas, doc):
        canvas.setFillColor(teal)
        canvas.setFont(FONT, 9)
        canvas.drawString(42, 28, "PatentScope AI  /  私人研究紀錄")
        canvas.drawRightString(A4[0] - 42, 28, str(doc.page))

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=48,
        title="PatentScope AI",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


@router.get(
    "/{run_id}/report.pdf",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
        **{code: {"model": PatentErrorEnvelope} for code in (401, 404, 422, 503)},
    },
)
def export_report(run_id: UUID, account: Owner):
    pdf = render_saved_report(run_id, account.id)
    if isinstance(pdf, JSONResponse):
        return pdf
    return pdf_attachment(run_id, pdf)


def render_saved_report(run_id: UUID, user_id: UUID) -> bytes | JSONResponse:
    run = read_saved_search(run_id, user_id)
    if isinstance(run, JSONResponse):
        return run
    try:
        with engine.connect() as conn:
            sources = document_sources_by_id(
                conn, [item.document_id for item in run.items]
            )
    except SQLAlchemyError:
        return unavailable()
    try:
        return build_report(run, sources)
    except (OSError, TTFError, ValueError):
        return api_error(
            503, "REPORT_UNAVAILABLE", "目前無法產生 PDF，請確認報告字型設定。"
        )


def pdf_attachment(run_id: UUID, pdf: bytes) -> Response:
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="patentscope-{run_id}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )

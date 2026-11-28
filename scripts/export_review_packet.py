"""Export public TIPO evidence for a rank-blind review of a pinned pool."""

import argparse
import json
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from scripts.evaluate_search import check_reviewed_version, request, version_details

SCOPES_ZH = {
    "metadata_and_abstract": "書目及摘要",
    "claims_only": "書目及請求項",
    "fulltext": "公開全文",
}
REVIEW_SCRIPT = Path(__file__).with_name("review_packet.js")


def source_link(url):
    if not url:
        return ""
    safe = escape(url)
    if urlsplit(url).scheme in {"https", "ftps"}:
        return f'<a href="{safe}">{safe}</a>'
    return safe


def original_text(text, source):
    return (
        f"<pre>{escape(text)}</pre>"
        f"<small>{escape(source['xpath'])} · "
        f"SHA-256 {escape(source['artifact_sha256'])}</small>"
    )


def render_packet(api, pool):
    parts = [
        '<!doctype html><html lang="zh-Hant"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<link rel="icon" href="data:,">',
        "<title>PatentScope AI 臺灣專利相關性複核</title>",
        "<style>body{max-width:76ch;margin:2rem auto;padding:0 1rem;"
        "font:1rem/1.6 system-ui}article{border-top:1px solid;padding:1rem 0}"
        "pre{white-space:pre-wrap;font:inherit}small,a{overflow-wrap:anywhere}"
        "summary{cursor:pointer}label{display:block}textarea{width:100%;box-sizing:border-box}"
        "button,select,input,textarea{font:inherit}fieldset{margin:1rem 0}</style>",
        "<h1>臺灣專利相關性複核</h1>",
        "<p>請依實際可取得的內容判斷。0 為不相關、1 為部分相關、2 為直接相關。"
        "證據不足時可保留空值。請在每份文件下方填寫分數和理由，並記下可定位的請求項或段落。"
        "可以下載草稿並在下次匯入，資料保存在你的檔案中。</p>",
        f'<label>複核者 <input id="reviewer" maxlength="100" value="{escape(pool.get("reviewer", ""))}"></label>',
        '<label>匯入先前的複核檔 <input id="review-import" type="file" accept="application/json,.json"></label>',
        '<button type="button" id="save-draft">下載草稿</button> '
        '<button type="button" id="finish-review">下載完成複核檔</button>',
        '<p id="review-status" role="status"></p>',
    ]
    for case_index, case in enumerate(pool["cases"]):
        parts.append(
            f"<h2>{escape(case['query'])}</h2>"
            f"<p>查詢識別碼 {escape(case['id'])} · "
            f"IPC {escape(case.get('ipc') or '未限定')}</p>"
        )
        for row_index, row in enumerate(case["judgments"]):
            stage, number = row["stage"], row["number"]
            detail = check_reviewed_version(
                api, row, version_details(api, stage, number)
            )
            document_id = detail["document_id"]
            claims = request(api, f"/patents/{document_id}/claims")
            if claims["document_id"] != document_id:
                raise ValueError(f"Claim version mismatch: {stage}/{number}")
            stage_zh = {"publication": "公開", "grant": "公告"}[stage]
            title = detail["title_zh"] or detail["title_en"] or "標題未提供"
            parts.append(
                f"<article><h3>{stage_zh} {escape(number)} · {escape(title)}</h3>"
                f"<p>{SCOPES_ZH[detail['content_scope']]} · "
                f"{escape(detail['parser_version'])}<br>"
                f"<small>文件 SHA-256 {escape(detail['document_sha256'])}</small></p>"
            )
            parts.append("<h4>摘要</h4>")
            for language in ("zh", "en"):
                if text := detail[f"abstract_{language}"]:
                    parts.append(f"<pre>{escape(text)}</pre>")
            if not (detail["abstract_zh"] or detail["abstract_en"]):
                parts.append("<p>此版本未提供摘要。</p>")
            parts.append(
                f"<details><summary>請求項（{len(claims['claims'])}）</summary>"
            )
            for claim in claims["claims"]:
                parts.append(f"<h4>第 {claim['claim_number']} 項</h4>")
                parts.append(original_text(claim["text"], claim["source"]))
            parts.append("</details>")
            sections = detail["sections"]
            if sections:
                parts.append(
                    f"<details><summary>說明書段落（{len(sections)}）</summary>"
                )
                for section in sections:
                    parts.append(
                        f"<h4>{escape(section['section_type'])} · {section['ordinal']}</h4>"
                    )
                    parts.append(
                        original_text(section["original_text"], section["source"])
                    )
                parts.append("</details>")
            parts.append("<details><summary>官方來源與授權</summary><ul>")
            for source in detail["sources"]:
                parts.append(
                    f"<li>{escape(source['publisher'])} · {escape(source['dataset_name'])}"
                    f" · {escape(source['batch_key'])}<br>"
                    f"{source_link(source['source_url'])}<br>"
                    f"{source_link(source['dataset_url'])}<br>"
                    f"{source_link(source['license_url'])}</li>"
                )
            choices = "".join(
                f'<option value="{grade}"{" selected" if row.get("grade") == grade else ""}>{label}</option>'
                for grade, label in (
                    (0, "0 · 不相關"),
                    (1, "1 · 部分相關"),
                    (2, "2 · 直接相關"),
                )
            )
            parts.append(
                f'</ul></details><fieldset data-case="{case_index}" data-judgment="{row_index}">'
                "<legend>複核判定</legend><label>相關程度 <select data-grade>"
                f'<option value="">尚未判定</option>{choices}</select></label>'
                f'<label>判定依據 <textarea data-basis rows="3">{escape(row.get("basis") or "")}</textarea></label>'
                "</fieldset></article>"
            )
    safe_pool = json.dumps(pool, ensure_ascii=False).replace("<", "\\u003c")
    parts.extend(
        [
            f'<script id="review-pool" type="application/json">{safe_pool}</script>',
            f"<script>{REVIEW_SCRIPT.read_text(encoding='utf-8')}</script>",
            "</html>",
        ]
    )
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pool = json.loads(args.pool.read_text(encoding="utf-8"))
    packet = render_packet(args.api, pool)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(packet)
    print(f"Review packet written to {args.output}")

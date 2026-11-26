"""Parse the TIPO invention publication issue index (dataset 15996)."""

import hashlib
import xml.etree.ElementTree as ET

from services.ingestion.patentpub import (
    ParseIssue,
    PatentPublication,
    collect_records,
    patent_number,
    parse_xml,
)

PARSER_VERSION = "tipo-issue-index-1"
RECORD = "tw-patent-application"


def party_names(node: ET.Element, path: str) -> list[dict[str, str]]:
    parties = []
    for party in node.findall(path):
        names = {}
        for language, tag in (("zh", "chinese-name"), ("en", "english-name")):
            name = party.find(f"addressbook/{tag}")
            if name is None:
                continue
            parts = [
                (name.findtext(part) or "").strip()
                for part in ("last-name", "middle-name", "first-name")
            ]
            value = (" " if language == "en" else "").join(filter(None, parts))
            if value:
                names[language] = value
        if names:
            parties.append(names)
    return parties


def text(node: ET.Element, path: str) -> str | None:
    element = node.find(path)
    if element is None:
        return None
    if paragraphs := element.findall("p"):
        return "\n".join("".join(p.itertext()) for p in paragraphs) or None
    return "".join(element.itertext()).strip() or None


def parse_record(node: ET.Element, locator: str) -> PatentPublication:
    biblio = node.find("tw-bibliographic-data-application")
    if biblio is None:
        raise ValueError("Missing invention publication bibliography")
    publication_no = patent_number(
        biblio, "publication-reference/document-id/doc-number"
    )
    if node.get("publication-number") != publication_no:
        raise ValueError("Publication identifiers in the index disagree")
    node.tail = None
    return PatentPublication(
        locator=locator,
        application_no=patent_number(
            biblio, "application-reference/document-id/doc-number"
        ),
        publication_no=publication_no,
        filing_date=None,
        publication_date=None,
        title_zh=text(biblio, "invention-title/chinese-title"),
        title_en=text(biblio, "invention-title/english-title"),
        applicants=party_names(biblio, "parties/applicants/applicant"),
        inventors=party_names(biblio, "parties/inventors/inventor"),
        ipc=[
            (code, item.get("edition", ""))
            for item in biblio.findall("classification-ipc/*")
            if item.tag in {"main-classification", "further-classification"}
            and (code := (item.text or "").strip())
        ],
        source_hash=hashlib.sha256(ET.tostring(node, encoding="utf-8")).hexdigest(),
        abstract_zh=text(node, "description/isu-abst[@lang='tw']"),
        abstract_en=text(node, "description/isu-abst[@lang='en']"),
    )


def index_records(data: bytes) -> list[ET.Element]:
    root = parse_xml(data)
    records = root.findall(RECORD)
    if (
        root.tag != "tw-patent-applications"
        or len(records) != len(root)
        or root.get("total-count") != str(len(records))
    ):
        raise ValueError("Expected a complete TIPO issue index XML")
    return records


def record_issue(record: ET.Element) -> str:
    prefix = "tw-bibliographic-data-application/"
    volume = record.findtext(prefix + "volno", "").strip()
    issue = record.findtext(prefix + "isuno", "").strip()
    if not all(value.isascii() and value.isdecimal() for value in (volume, issue)):
        raise ValueError("Missing or invalid issue in the TIPO index")
    return volume.zfill(3) + issue.zfill(3)


def discover_issue(data: bytes) -> tuple[str, int]:
    records = index_records(data)
    issues = {record_issue(record) for record in records}
    if len(issues) != 1:
        raise ValueError("TIPO latest index must contain a single nonempty issue")
    [issue] = issues
    if len(issue) != 6:
        raise ValueError("TIPO latest index has an invalid issue format")
    return issue, len(records)


def parse_issue_index(
    data: bytes, limit: int | None = None, expected_issue: str | None = None
) -> tuple[list[PatentPublication], list[ParseIssue]]:
    records = index_records(data)
    selected = records[:limit]
    if expected_issue is not None:
        for record in selected:
            if record_issue(record) != expected_issue:
                raise ValueError("TIPO index does not match the requested issue")
    return collect_records(selected, f"/tw-patent-applications/{RECORD}", parse_record)

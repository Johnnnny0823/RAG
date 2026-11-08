"""Parse the documented TIPO PatentPub XML API response."""

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date

from services.ingestion.artifacts import MAX_XML_BYTES

PARSER_VERSION = "tipopatentpub-1"


@dataclass(frozen=True)
class PatentPublication:
    locator: str
    application_no: str
    publication_no: str
    filing_date: date | None
    publication_date: date | None
    title_zh: str | None
    title_en: str | None
    applicants: list[dict[str, str]]
    inventors: list[dict[str, str]]
    ipc: list[tuple[str, str]]
    source_hash: str
    abstract_zh: str | None = None
    abstract_en: str | None = None


@dataclass(frozen=True)
class ParseIssue:
    locator: str
    message: str


class SafeTreeBuilder(ET.TreeBuilder):
    def doctype(self, name: str, pubid: str | None, system: str | None) -> None:
        raise ValueError("DOCTYPE is forbidden in PatentPub API XML")


def optional_text(node: ET.Element, path: str) -> str | None:
    return (node.findtext(path) or "").strip() or None


def patent_number(node: ET.Element, path: str) -> str:
    value = optional_text(node, path)
    if not value or not re.fullmatch(r"[0-9]{9}", value):
        raise ValueError(f"Invalid or missing {path}")
    return value


def parse_date(node: ET.Element, path: str) -> date | None:
    value = optional_text(node, path)
    if value is None:
        return None
    try:
        return date.fromisoformat(value.replace("/", "-"))
    except ValueError:
        raise ValueError(f"Invalid {path}") from None


def party_names(node: ET.Element, path: str) -> list[dict[str, str]]:
    parties = []
    for party in node.findall(path):
        names = {
            language: name
            for language, tag in (("zh", "chinese-name"), ("en", "english-name"))
            if (name := optional_text(party, tag))
        }
        if names:
            parties.append(names)
    return parties


def parse_record(node: ET.Element, locator: str) -> PatentPublication:
    node.tail = None
    return PatentPublication(
        locator=locator,
        application_no=patent_number(node, "application-reference/appl-no"),
        publication_no=patent_number(node, "publication-reference/notice-no"),
        filing_date=parse_date(node, "application-reference/appl-date"),
        publication_date=parse_date(node, "publication-reference/notice-date"),
        title_zh=optional_text(node, "patent-title/patent-name-chinese"),
        title_en=optional_text(node, "patent-title/patent-name-english"),
        applicants=party_names(node, "parties/applicants/applicant"),
        inventors=party_names(node, "parties/inventors/inventor"),
        ipc=[
            (code, optional_text(ipc, "ipc-version") or "")
            for ipc in node.findall("classification-ipc/ipc")
            if (code := optional_text(ipc, "ipc-full"))
        ],
        source_hash=hashlib.sha256(ET.tostring(node, encoding="utf-8")).hexdigest(),
    )


def parse_patentpub(data: bytes) -> tuple[list[PatentPublication], list[ParseIssue]]:
    root = parse_xml(data)
    container = root.find("tw-patent-pub")
    if root.tag != "API" or optional_text(root, "status") != "ok" or container is None:
        raise ValueError("Expected a successful TIPO PatentPub XML response")
    records = container.findall("patentcontent")
    if len(records) != len(container) or container.get("page-count") != str(
        len(records)
    ):
        raise ValueError("PatentPub record count or element structure does not match")
    return collect_records(records, "/API/tw-patent-pub/patentcontent", parse_record)


def parse_xml(data: bytes) -> ET.Element:
    if len(data) > MAX_XML_BYTES:
        raise ValueError("XML artifact exceeds the size limit")
    return ET.fromstring(data, parser=ET.XMLParser(target=SafeTreeBuilder()))


def collect_records(
    records, path, parser
) -> tuple[list[PatentPublication], list[ParseIssue]]:
    publications = []
    issues = []
    for position, record in enumerate(records, 1):
        locator = f"{path}[{position}]"
        try:
            publications.append(parser(record, locator))
        except ValueError as error:
            issues.append(ParseIssue(locator, str(error)))
    return publications, issues

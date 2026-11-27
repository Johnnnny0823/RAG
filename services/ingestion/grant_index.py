"""Parse selected grants from the verified TIPO S01 issue index."""

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import date

from services.ingestion.artifacts import MAX_GAZETTE_XML_BYTES
from services.ingestion.issue_index import party_names, text
from services.ingestion.patentpub import (
    PatentPublication,
    PriorityClaim,
    optional_text,
    parse_xml,
    patent_number,
)
from services.ingestion.specification import Claim

GRANT_APPLICATION_TYPES = {"I": "invention", "M": "model", "D": "design"}


def parse_grant(data: bytes, issue: str, certificate: str):
    [grant] = parse_selected_grants(data, issue, [certificate])
    return grant


def grant_records(data: bytes) -> ET.Element:
    root = parse_xml(data, size_limit=MAX_GAZETTE_XML_BYTES)
    if root.tag != "tw-patent-grants" or root.get("total-count") != str(len(root)):
        raise ValueError("Expected a complete TIPO grant issue index")
    return root


def discover_grant_issue(
    data: bytes, grant_type: str = "invention"
) -> tuple[str, list[str]]:
    certificates = []
    issues = set()
    for item in grant_records(data):
        if item.tag != "tw-patent-grant":
            raise ValueError("Unexpected element in the TIPO grant issue index")
        certificate = item.get("certificate-number", "")
        if (
            not re.fullmatch(r"[IMD][0-9]+", certificate)
            or GRANT_APPLICATION_TYPES[certificate[0]] != grant_type
        ):
            continue
        biblio = item.find("tw-bibliographic-data-grant")
        if biblio is None:
            raise ValueError("Missing grant bibliography")
        issues.add(grant_issue(biblio))
        certificates.append(certificate)
    if len(issues) != 1 or len(set(certificates)) != len(certificates):
        raise ValueError(
            "Expected a single nonempty grant issue with distinct certificates"
        )
    [issue] = issues
    return issue, certificates


def parse_selected_grants(
    data: bytes, issue: str, certificates: list[str]
) -> list[tuple[PatentPublication, list[Claim]]]:
    selected = set(certificates)
    if (
        not selected
        or len(selected) != len(certificates)
        or any(
            not re.fullmatch(r"[IMD][0-9]{1,12}", certificate)
            for certificate in selected
        )
    ):
        raise ValueError("Expected distinct grant numbers")
    matches = {}
    for position, item in enumerate(grant_records(data), 1):
        certificate = item.get("certificate-number")
        if item.tag != "tw-patent-grant" or certificate not in selected:
            continue
        if certificate in matches:
            raise ValueError(f"Multiple matching grants: {certificate}")
        matches[certificate] = _parse_grant(item, position, issue, certificate)
    if missing := selected - matches.keys():
        raise ValueError(f"Missing selected grants: {', '.join(sorted(missing))}")
    return [matches[certificate] for certificate in certificates]


def grant_issue(biblio: ET.Element) -> str:
    volume = biblio.findtext("volno", "").strip()
    issue_number = biblio.findtext("isuno", "").strip()
    if (
        not volume.isascii()
        or not volume.isdecimal()
        or not issue_number.isascii()
        or not issue_number.isdecimal()
        or len(volume) > 3
        or len(issue_number) > 3
    ):
        raise ValueError("Invalid grant issue")
    return volume.zfill(3) + issue_number.zfill(3)


def parse_priorities(biblio: ET.Element) -> tuple[PriorityClaim, ...]:
    priorities = []
    for ordinal, item in enumerate(biblio.findall("priority-claims/priority-claim"), 1):
        country = optional_text(item, "country")
        number = optional_text(item, "doc-number")
        day = optional_text(item, "date")
        if not country or not number or not day or not re.fullmatch(r"[0-9]{8}", day):
            raise ValueError("Incomplete or invalid TIPO priority claim")
        try:
            priority_date = date.fromisoformat(day)
        except ValueError:
            raise ValueError("Invalid TIPO priority date") from None
        priorities.append(PriorityClaim(ordinal, country, number, priority_date))
    return tuple(priorities)


def _parse_grant(item: ET.Element, position: int, issue: str, certificate: str):
    biblio = item.find("tw-bibliographic-data-grant")
    if biblio is None:
        raise ValueError("Missing grant bibliography")
    if grant_issue(biblio) != issue:
        raise ValueError("TIPO grant index does not match the requested issue")
    application_type = GRANT_APPLICATION_TYPES[certificate[0]]
    if (
        biblio.findtext("publication-reference/document-id/doc-number") != certificate
        or biblio.findtext("certificate-number/document-id/doc-number") != certificate
        or biblio.find(f"./application-reference[@appl-type='{application_type}']")
        is None
    ):
        raise ValueError("Grant identifiers or application type disagree")

    locator = f"/tw-patent-grants/tw-patent-grant[{position}]"
    claims = []
    numbers = set()
    for index, claim in enumerate(item.findall("claims/claim"), 1):
        raw_number = claim.get("num", "")
        if (
            not re.fullmatch(r"[1-9][0-9]{0,8}", raw_number)
            or int(raw_number) in numbers
        ):
            raise ValueError("Missing or duplicate grant claim number")
        number = int(raw_number)
        original = "\n".join("".join(p.itertext()) for p in claim.findall("p"))
        if not original.strip():
            raise ValueError("Empty grant claim")
        numbers.add(number)
        claims.append(Claim(number, original, None, f"{locator}/claims/claim[{index}]"))
    if application_type == "design" and claims:
        raise ValueError("Unexpected claims in selected design grant")
    if application_type != "design" and not claims:
        raise ValueError("No claims in selected invention or utility model grant")

    item.tail = None
    return PatentPublication(
        locator=locator,
        application_no=patent_number(
            biblio,
            "application-reference/document-id/doc-number",
            design=application_type == "design",
        ),
        publication_no=certificate,
        filing_date=None,
        publication_date=None,
        title_zh=text(biblio, "invention-title/chinese-title"),
        title_en=text(biblio, "invention-title/english-title"),
        applicants=party_names(biblio, "parties/applicants/applicant"),
        inventors=party_names(biblio, "parties/inventors/inventor"),
        ipc=[
            (code, part.get("edition", ""))
            for part in biblio.findall("classification-ipc/*")
            if part.tag in {"main-classification", "further-classification"}
            and (code := (part.text or "").strip())
        ],
        source_hash=hashlib.sha256(ET.tostring(item, encoding="utf-8")).hexdigest(),
        priorities=parse_priorities(biblio),
    ), claims

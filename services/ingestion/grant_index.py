"""Parse a selected invention grant from the verified TIPO S01 issue index."""

import hashlib
import re
import xml.etree.ElementTree as ET

from services.ingestion.issue_index import party_names, text
from services.ingestion.patentpub import PatentPublication, parse_xml, patent_number
from services.ingestion.specification import Claim


def parse_grant(data: bytes, issue: str, certificate: str):
    root = parse_xml(data)
    if root.tag != "tw-patent-grants" or root.get("total-count") != str(len(root)):
        raise ValueError("Expected a complete TIPO grant issue index")
    candidates = [
        (position, item)
        for position, item in enumerate(root, 1)
        if item.tag == "tw-patent-grant"
        and item.get("certificate-number") == certificate
    ]
    if len(candidates) != 1 or not re.fullmatch(r"I[0-9]+", certificate):
        raise ValueError("Expected exactly one matching invention grant")
    position, item = candidates[0]
    biblio = item.find("tw-bibliographic-data-grant")
    if biblio is None:
        raise ValueError("Missing grant bibliography")
    volume = biblio.findtext("volno", "").strip()
    issue_number = biblio.findtext("isuno", "").strip()
    if (
        not volume.isascii()
        or not volume.isdecimal()
        or not issue_number.isascii()
        or not issue_number.isdecimal()
    ):
        raise ValueError("Invalid grant issue")
    if volume.zfill(3) + issue_number.zfill(3) != issue:
        raise ValueError("TIPO grant index does not match the requested issue")
    if (
        biblio.findtext("publication-reference/document-id/doc-number") != certificate
        or biblio.findtext("certificate-number/document-id/doc-number") != certificate
        or biblio.find("./application-reference[@appl-type='invention']") is None
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
    if not claims:
        raise ValueError("No claims in selected invention grant")

    item.tail = None
    return PatentPublication(
        locator=locator,
        application_no=patent_number(
            biblio, "application-reference/document-id/doc-number"
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
    ), claims

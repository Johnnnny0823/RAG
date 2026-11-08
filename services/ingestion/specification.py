"""Parse the verified TIPO invention-specification A103.1.0 format."""

import re
from dataclasses import dataclass

from services.ingestion.patentpub import parse_xml

DOCTYPE = b'<!DOCTYPE invention-specification SYSTEM "../invention-specification.dtd">'
DTD_VERSION = "A103.1.0"


@dataclass(frozen=True)
class Section:
    kind: str
    ordinal: int
    text: str
    locator: str


@dataclass(frozen=True)
class Claim:
    number: int
    text: str
    independent: bool | None
    locator: str


def parse_specification(
    data: bytes, application_no: str
) -> tuple[list[Section], list[Claim]]:
    # The publisher's known external DTD is inert. All other declarations fail in parse_xml.
    root = parse_xml(data.replace(DOCTYPE, b"", 1))
    if (
        root.tag != "invention-specification"
        or root.get("dtd-version") != DTD_VERSION
        or root.get("application-num") != application_no
    ):
        raise ValueError("Unexpected specification format or application number")

    sections = []
    for group in root.findall("description/*"):
        if not re.fullmatch(r"[a-z-]+", group.tag):
            raise ValueError("Unexpected description section name")
        for index, paragraph in enumerate(group.findall("p"), 1):
            text = "".join(paragraph.itertext())
            if text.strip():
                sections.append(
                    Section(
                        group.tag,
                        index,
                        text,
                        f"/invention-specification/description/{group.tag}/p[{index}]",
                    )
                )

    claims = []
    numbers = set()
    for index, item in enumerate(root.findall("claims/claim"), 1):
        value = item.get("num", "")
        if not re.fullmatch(r"[1-9][0-9]{0,8}", value) or int(value) in numbers:
            raise ValueError("Invalid or duplicate specification claim number")
        number = int(value)
        numbers.add(number)
        text = "\n".join(
            "".join(part.itertext()) for part in item.findall("claim-text")
        )
        if not text.strip():
            raise ValueError("Empty specification claim text")
        independent = {
            "independent-claim": True,
            "dependent-claim": False,
        }.get(item.get("dependency"))
        claims.append(
            Claim(
                number,
                text,
                independent,
                f"/invention-specification/claims/claim[{index}]",
            )
        )
    if not sections or not claims:
        raise ValueError("Specification is missing description paragraphs or claims")
    return sections, claims

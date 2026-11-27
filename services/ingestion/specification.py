"""Parse verified TIPO specification XML formats by patent type."""

import re
from dataclasses import dataclass

from services.ingestion.patentpub import parse_xml

DOCTYPE = b'<!DOCTYPE invention-specification SYSTEM "../invention-specification.dtd">'
GRANT_DOCTYPE = b'<!DOCTYPE specification SYSTEM "../specification.dtd">'
DTD_VERSION = "A103.1.0"
GRANT_DTD_VERSIONS = {"I": DTD_VERSION, "M": "1.0.0", "D": "2.0.1"}


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
    data: bytes, application_no: str, *, grant_number: str | None = None
) -> tuple[list[Section], list[Claim]]:
    # The publisher's known external DTD is inert. All other declarations fail in parse_xml.
    grant = grant_number is not None
    grant_prefix = grant_number[:1] if grant_number is not None else None
    expected_version = (
        GRANT_DTD_VERSIONS.get(grant_prefix)
        if grant_prefix is not None
        else DTD_VERSION
    )
    root_name = "specification" if grant else "invention-specification"
    root = parse_xml(data.replace(GRANT_DOCTYPE if grant else DOCTYPE, b"", 1))
    if (
        expected_version is None
        or root.tag != root_name
        or root.get("dtd-version") != expected_version
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
                        f"/{root_name}/description/{group.tag}/p[{index}]",
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
                f"/{root_name}/claims/claim[{index}]",
            )
        )
    if not sections:
        raise ValueError("Specification is missing description paragraphs")
    if grant_prefix == "D" and root.find("claims") is not None:
        raise ValueError("Unexpected claims in design specification")
    if grant_prefix != "D" and not claims:
        raise ValueError("Specification is missing claims")
    return sections, claims

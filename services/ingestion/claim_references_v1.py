"""Conservative explicit claim references used by revision 0011."""

import re
from collections.abc import Iterable

NUMBER = r"[0-9]{1,9}"
TERM = rf"{NUMBER}(?:\s*[至到～~－-]\s*{NUMBER})?"
SEPARATOR = r"[、，,或及和與]"
REFERENCE = re.compile(
    rf"請求項\s*(?P<terms>{TERM}(?:\s*{SEPARATOR}\s*{TERM})*)"
    r"\s*(?:(?:中|之)?任(?:一|何一)項\s*)?(?:所述|所記載|記載)"
)
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def reference_pairs(claims: Iterable[tuple[int, str]]) -> list[tuple[int, int]]:
    """Return (citing claim, cited claim) from verifiable earlier claims."""
    text_by_number = dict(claims)
    pairs = []
    for child, original in text_by_number.items():
        earlier = {number for number in text_by_number if number < child}
        parents = set()
        for match in REFERENCE.finditer(original.translate(FULLWIDTH_DIGITS)):
            group = set()
            for term in re.split(SEPARATOR, match["terms"]):
                first, *last = map(int, re.findall(NUMBER, term))
                end = last[0] if last else first
                present = {number for number in earlier if first <= number <= end}
                if not present or len(present) != end - first + 1:
                    break
                group.update(present)
            else:
                parents.update(group)
        pairs.extend((child, parent) for parent in sorted(parents))
    return pairs


INSERT_REFERENCES = """
    INSERT INTO claim_dependencies (document_id, child_number, parent_number)
    VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
"""

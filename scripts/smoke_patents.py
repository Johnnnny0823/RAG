"""Exercise M2 endpoints against the documented official M1 sample corpus."""

import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import UUID

INDEX_SHA256 = "7befed78be2cc6067266f13afd4a34f6feca4730b9a717f3f99890d551da9b69"
INDEX_URL = (
    "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml"
)
SPEC_SHA256 = "0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a"


def smoke(base_url: str, *, official_e2e: bool = False) -> None:
    def read(path, expected_status=200):
        try:
            with urlopen(base_url + path, timeout=10) as response:
                status = response.status
                body = json.load(response)
        except HTTPError as error:
            status = error.code
            body = json.load(error)
        if status != expected_status:
            raise RuntimeError(f"{path} returned {status}: {body}")
        return body

    def lookup(number, number_type, **paging):
        query = urlencode({"number": number, "number_type": number_type, **paging})
        return read(f"/api/v1/patents?{query}")

    page = lookup("114106690", "application", limit=1)
    assert page["has_more"] and len(page["items"]) == 1
    next_page = lookup("114106690", "application", limit=1, offset=1)
    assert page["items"][0]["document_id"] != next_page["items"][0]["document_id"]
    versions = lookup("114106690", "application")["items"]
    assert {row["document_stage"] for row in versions} == {"publication", "grant"}
    assert not lookup("000000000", "publication")["items"]

    publications = lookup("２０２６４０１６２", "publication")["items"]
    assert [row["content_scope"] for row in publications] == [
        "fulltext",
        "metadata_and_abstract",
    ]
    [grant] = lookup("i941082", "grant")["items"]
    assert (
        grant["document_stage"] == "grant" and grant["content_scope"] == "claims_only"
    )
    publication = publications[0]
    assert grant["document_id"] != publication["document_id"]
    for row, expected_sections in [(publication, 41), (grant, 0)]:
        document_id = row["document_id"]
        assert UUID(document_id)
        path = f"/api/v1/patents/{document_id}"
        detail = read(path)
        assert detail["application_no"] == "114106690"
        assert detail["document_id"] == document_id
        assert detail["classifications"] and detail["title_zh"]
        assert len(detail["sections"]) == expected_sections
        claim_set = read(f"{path}/claims")
        assert claim_set["document_id"] == document_id
        claims = claim_set["claims"]
        assert [claim["claim_number"] for claim in claims] == list(range(1, 14))
        hashes = {source["artifact_sha256"] for source in detail["sources"]}
        assert all(claim["source"]["artifact_sha256"] in hashes for claim in claims)
        assert all(
            section["source"]["artifact_sha256"] in hashes
            for section in detail["sections"]
        )
    assert (
        read(f"/api/v1/patents/{publications[1]['document_id']}/claims")["claims"] == []
    )

    if official_e2e:
        [sample] = lookup("202639611", "publication")["items"]
        path = f"/api/v1/patents/{sample['document_id']}"
        detail = read(path)
        assert detail["application_no"] == "113133932"
        assert detail["content_scope"] == "fulltext"
        assert any(
            source["source_url"] == INDEX_URL
            and source["artifact_sha256"] == INDEX_SHA256
            for source in detail["sources"]
        )
        claims = read(f"{path}/claims")["claims"]
        assert [claim["claim_number"] for claim in claims] == list(range(1, 20))
        assert len(detail["sections"]) == 122
        assert all(
            entry["source"]["artifact_sha256"] == SPEC_SHA256
            for entry in (*claims, *detail["sections"])
        )
    else:
        [second_issue] = lookup("202637274", "publication")["items"]
        detail = read(f"/api/v1/patents/{second_issue['document_id']}")
        assert detail["sources"][0]["source_url"].endswith(
            "/InventionPubXML_024018/index.xml"
        )
    missing = read("/api/v1/patents/00000000-0000-0000-0000-000000000000", 404)
    assert missing["error"]["code"] == "PATENT_NOT_FOUND"
    assert UUID(missing["error"]["request_id"])
    print(
        "Patent API smoke passed: exact identifiers, version isolation, pagination and source hashes"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18003")
    parser.add_argument("--official-e2e", action="store_true")
    args = parser.parse_args()
    smoke(args.api, official_e2e=args.official_e2e)

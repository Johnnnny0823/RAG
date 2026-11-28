"""Verify known-item semantic retrieval against the real M1 corpus."""

import argparse
import json
from urllib.request import Request, urlopen


def smoke(
    base_url: str, *, official_e2e: bool = False, issue_024020: bool = False
) -> None:
    def search(query, ipc, limit=10, offset=0, *, mode="semantic"):
        request = Request(
            f"{base_url}/api/v1/patents/search/{mode}",
            data=json.dumps(
                dict(query=query, ipc=ipc, limit=limit, offset=offset)
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=100) as response:
            return json.load(response)

    cases = [("功率元件切換導通時如何測量電阻", "G01R27/02", "202640162")]
    if issue_024020:
        cases = [
            ("使用雷達和光學訊號控制移動物體的鏡頭焦距", "G01S13/86", "202642194"),
            (
                "在可攜式電子設備內使用具有上方罩蓋的平面式天線部件",
                "H01Q1/22",
                "202642585",
            ),
        ]
    elif official_e2e:
        cases.append(
            ("Resin formulation that hardens upon light exposure", "C08F", "202639611")
        )
    else:
        cases.append(
            ("A heat barrier sheet made with a porous gel", "B01J", "202637274")
        )
    scope_order = {"fulltext": 0, "claims_only": 1}
    for query, ipc, expected in cases:
        result = search(query, ipc)
        assert result["pipeline"] == "patent-dense-v1"
        assert len(result["model_digest"]) == 64
        items = result["items"]
        identifiers = [item["publication_no"] for item in items]
        assert expected in identifiers, (expected, identifiers)
        assert all(-1.001 <= item["score"] <= 1.001 for item in items)
        assert items == sorted(
            items,
            key=lambda item: (
                -item["score"],
                scope_order.get(item["content_scope"], 2),
                item["document_id"],
            ),
        )
        print(f"{expected}: rank {identifiers.index(expected) + 1}")
        if issue_024020:
            same_versions = {
                item["document_id"]
                for item in items
                if item["publication_no"] == expected
            }
            assert any(
                item["content_scope"] == "fulltext"
                for item in items
                if item["publication_no"] == expected
            )
            hybrid = search(query, ipc, mode="hybrid")
            [hit] = [
                item for item in hybrid["items"] if item["publication_no"] == expected
            ]
            assert hit["document_id"] in same_versions
            assert hit["semantic_rank"] is not None
    first = search(cases[0][0], cases[0][1], limit=1)
    next_page = search(cases[0][0], cases[0][1], limit=1, offset=1)
    assert first["has_more"]
    assert first["items"][0]["document_id"] != next_page["items"][0]["document_id"]
    print(
        "Semantic smoke passed: real Ollama embeddings, IPC, model identity and pagination"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18005")
    suite = parser.add_mutually_exclusive_group()
    suite.add_argument("--official-e2e", action="store_true")
    suite.add_argument("--issue-024020", action="store_true")
    args = parser.parse_args()
    smoke(args.api, official_e2e=args.official_e2e, issue_024020=args.issue_024020)

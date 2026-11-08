"""Check bilingual known-item retrieval against the M1 official sample corpus."""

import argparse
import json
from urllib.request import Request, urlopen


def smoke(base_url: str) -> None:
    def search(query, **filters):
        payload = json.dumps({"query": query, **filters}).encode()
        request = Request(
            f"{base_url}/api/v1/patents/search",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=10) as response:
            return json.load(response)

    cases = [
        ("動態導通電阻", "G01R", "202640162"),
        ("動態導通電阻", "Ｇ０１Ｒ ２７／０２", "202640162"),
        ("氣凝膠隔熱片", "B01J", "202637274"),
        ("aerogel thermal insulation sheet", "B01J", "202637274"),
    ]
    for query, ipc, expected in cases:
        result = search(query, ipc=ipc, limit=10)
        assert result["tokenizer_version"] == "han-bigram-v1"
        numbers = [row["publication_no"] for row in result["items"]]
        assert expected in numbers, (query, ipc, numbers)
        print(f"{query} ({ipc}): {expected} at rank {numbers.index(expected) + 1}")
    assert not search("動態導通電阻", ipc="B01J")["items"]
    assert not search("動態導通電阻", ipc="G01R27/021")["items"]
    first = search("動態導通電阻", limit=1)
    second = search("動態導通電阻", limit=1, offset=1)
    assert (
        first["has_more"]
        and first["items"][0]["document_id"] != second["items"][0]["document_id"]
    )
    print(
        "Lexical smoke passed: known-item queries, IPC filtering and stable pagination"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18004")
    smoke(parser.parse_args().api)

"""Check listwise reranking with the local model and real TIPO candidates."""

import argparse
import json
from urllib.request import Request, urlopen


def smoke(url):
    def search(rerank):
        request = Request(
            url + "/api/v1/patents/search/hybrid",
            data=json.dumps(
                {"query": "動態導通電阻量測", "ipc": "G01R27/02", "rerank": rerank}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=300) as response:
            return json.load(response)

    base = search(False)
    result = search(True)
    assert base["reranker"] is None
    count = result["reranker"]["candidate_count"]
    assert count >= 2
    original = {hit["document_id"]: hit for hit in base["items"]}
    assert original.keys() == {hit["document_id"] for hit in result["items"]}
    for rank, hit in enumerate(result["items"], 1):
        prior = original[hit["document_id"]]
        assert hit["fusion_rank"] == prior["fusion_rank"]
        assert hit["rrf_score"] == prior["rrf_score"]
        assert hit["rerank_rank"] == (rank if rank <= count else None)
    print(
        f"Reranking smoke passed for {count} real candidates; fusion ranks: "
        + str([hit["fusion_rank"] for hit in result["items"][:count]])
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18009")
    smoke(parser.parse_args().api)

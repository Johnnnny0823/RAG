from services.retrieval.evidence import Passage, select_excerpt
from services.retrieval.query_features import TechnicalFeature


def test_excerpt_uses_original_text_and_offsets():
    original = "甲" * 80 + "Ａ；導通電阻量測" + "乙" * 80
    passage = Passage("claim", 1, original, "/claim[1]", "a" * 64)
    feature = TechnicalFeature(
        feature_id="f1",
        description_zh="量測",
        keywords_zh=["導通電阻"],
        keywords_en=[],
        must_have=True,
        confidence="high",
        ipc_candidates=[],
    )
    excerpt = select_excerpt(feature, [passage])
    assert excerpt is not None
    assert excerpt.quote == original[excerpt.start : excerpt.end]
    assert "Ａ；導通電阻量測" in excerpt.quote
    assert select_excerpt(feature, []) is None

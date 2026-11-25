from services.ingestion.claim_references_v1 import reference_pairs


def test_explicit_references_include_known_single_multiple_and_range_targets():
    assert reference_pairs(
        [
            (1, "起始裝置"),
            (2, "如請求項１所述的裝置"),
            (3, "如請求項1或2所述的裝置"),
            (4, "包含請求項1至3中任一項所述的裝置及請求項2所述的組件"),
        ]
    ) == [(2, 1), (3, 1), (3, 2), (4, 1), (4, 2), (4, 3)]


def test_absent_forward_self_and_ambiguous_references_are_not_inferred():
    assert reference_pairs(
        [
            (1, "如請求項5所述的裝置"),
            (3, "如請求項1至2所述的裝置"),
            (4, "圖中的請求項1號元件；如請求項4所述的裝置"),
            (5, "如請求項1或9所述的裝置，另含請求項1所記載的元件"),
        ]
    ) == [(5, 1)]

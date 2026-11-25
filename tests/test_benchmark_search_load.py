from pytest import raises

from scripts import benchmark_search_load


def test_load_summary_keeps_rejections_out_of_success_latency():
    report = benchmark_search_load.summarize(
        [("200_known_item", 30), ("429_model_busy", 1), ("200_known_item", 70)],
        wall_seconds=0.2,
    )
    assert report["outcomes"] == {"200_known_item": 2, "429_model_busy": 1}
    assert report["success_per_second"] == 10
    assert report["successful_p50_ms"] == 50
    assert report["successful_p95_ms"] == 70


def test_load_rejects_non_loopback_api():
    with raises(ValueError, match="loopback"):
        benchmark_search_load.benchmark("https://example.invalid", 8)

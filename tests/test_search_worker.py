from services.api import search_worker


def test_worker_finishes_current_search_without_claiming_report(monkeypatch):
    stopping = False
    finished = []

    def search():
        nonlocal stopping
        stopping = True
        finished.append("search")
        return True

    def report():
        raise AssertionError("Worker claimed a report after receiving shutdown")

    monkeypatch.setattr(search_worker, "process_one", search)
    monkeypatch.setattr(search_worker, "process_one_report", report)
    search_worker.run_worker(lambda: stopping)

    assert finished == ["search"]

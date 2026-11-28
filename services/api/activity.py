"""Record API outcomes without copying any user-supplied values."""

import json
import logging
from time import perf_counter

logger = logging.getLogger("uvicorn.error")
PRIVATE_DOWNLOADS = {
    "/api/v1/me/export",
    "/api/v1/search-runs/{run_id}/report.pdf",
    "/api/v1/search-runs/{run_id}/reports/{report_id}/pdf",
}


def write_activity(event: str, started: float, **fields) -> None:
    logger.info(
        "%s",
        json.dumps(
            {
                "event": event,
                **fields,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
            separators=(",", ":"),
        ),
    )


def record_activity(
    method: str, route_template: str, status: int, started: float
) -> None:
    if method in {"POST", "PATCH", "PUT", "DELETE"} or (
        method == "GET" and route_template in PRIVATE_DOWNLOADS
    ):
        write_activity(
            "api_activity", started, method=method, route=route_template, status=status
        )

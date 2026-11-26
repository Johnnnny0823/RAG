"""Resume bounded archive imports using PostgreSQL completion checkpoints."""

import hashlib
import json
import logging
from collections.abc import Callable
from os import getenv

from services.api.db import engine
from services.ingestion.download import list_archive_issues
from services.ingestion.import_issue import PARSER_VERSION
from services.ingestion.latest_publication import main as import_one
from services.ingestion.legal_events import PARSER_VERSION as LEGAL_PARSER_VERSION
from services.ingestion.legal_refresh import main as import_legal_issue

logger = logging.getLogger(__name__)


def refresh_archive(
    stage: str,
    year: str,
    first_issue: str,
    options: list[str],
    max_issues: int,
    should_stop: Callable[[], bool],
) -> bool:
    """Return whether more work or a retry is needed."""
    available = set(list_archive_issues(stage, year))
    end = max(
        (issue for issue in available if issue[:3] == first_issue[:3]), default=""
    )
    if not end or first_issue > end:
        logger.warning("%s archive has not reached %s", stage, first_issue)
        return True

    identity = [LEGAL_PARSER_VERSION if stage == "legal" else PARSER_VERSION, *options]
    if "hybrid" in options:
        identity.extend(
            getenv(name, "") for name in ("EMBEDDING_MODEL", "EMBEDDING_DIGEST")
        )
    configuration = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
    key = (stage, year, configuration)
    with engine.connect() as conn:
        completed = set(
            conn.exec_driver_sql(
                """SELECT issue FROM archive_refresh_checkpoints
               WHERE stage=%s AND archive_year=%s AND configuration_hash=%s""",
                key,
            ).scalars()
        )

    import_issue = import_legal_issue if stage == "legal" else import_one
    year_option = "--year" if stage == "legal" else "--issue-year"
    imported = 0
    for number in range(int(first_issue), int(end) + 1):
        issue = f"{number:06d}"
        if issue in completed:
            continue
        if issue not in available:
            logger.warning("%s archive is missing issue %s", stage, issue)
            return True
        if should_stop() or imported == max_issues:
            return True
        if import_issue([*options, year_option, year, "--archive-issue", issue]):
            return True
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """INSERT INTO archive_refresh_checkpoints
                       (stage, archive_year, configuration_hash, issue)
                   VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (*key, issue),
            )
        imported += 1
        logger.info("%s archive completed issue %s", stage, issue)
    logger.info("%s archive checked through %s, imported %s", stage, end, imported)
    return False

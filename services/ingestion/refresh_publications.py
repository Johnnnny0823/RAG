"""Periodically refresh the official publication index within the deployment."""

import argparse
import logging
import re
import signal
from collections.abc import Callable
from ftplib import all_errors
from os import getenv
from time import monotonic, sleep

from sqlalchemy.exc import SQLAlchemyError

from services.ingestion.archive_refresh import refresh_archive
from services.ingestion.latest_publication import main as refresh_once
from services.ingestion.legal_events import main as replay_legal
from services.ingestion.legal_refresh import main as refresh_legal

logger = logging.getLogger(__name__)


def serve(
    options: list[str],
    interval: int,
    retry_interval: int,
    should_stop: Callable[[], bool],
    *,
    include_grants: bool = False,
    catch_up_year: str | None = None,
    publication_from: str | None = None,
    grant_from: str | None = None,
    catch_up_max_issues: int = 2,
    legal_year: str | None = None,
    legal_from: str | None = None,
) -> None:
    batches = [("publication", options, publication_from)]
    if include_grants:
        batches.append(("grant", [*options, "--grants"], grant_from))
    if legal_year:
        batches.append(("legal-replay", ["--replay-stored"], None))
        if legal_from:
            batches.append(("legal", ["--apply"], legal_from))
        batches.append(("legal-latest", ["--year", legal_year, "--apply"], None))
    while not should_stop():
        needs_retry = False
        for stage, arguments, first_issue in batches:
            if should_stop():
                return
            try:
                archive_year = legal_year if stage == "legal" else catch_up_year
                if stage == "legal-replay":
                    replay_legal(arguments)
                elif stage == "legal-latest":
                    refresh_legal(arguments)
                elif archive_year and first_issue:
                    needs_retry |= refresh_archive(
                        stage,
                        archive_year,
                        first_issue,
                        arguments,
                        catch_up_max_issues,
                        should_stop,
                    )
                else:
                    needs_retry |= bool(refresh_once(arguments))
            except SystemExit as error:
                needs_retry |= bool(error.code)
                logger.warning("%s refresh did not complete: %s", stage, error.code)
            except (*all_errors, ValueError, SQLAlchemyError) as error:
                needs_retry = True
                logger.warning(
                    "%s refresh unavailable: %s", stage, type(error).__name__
                )
        delay = retry_interval if needs_retry else interval
        logger.info("TIPO refresh finished; next attempt in %s seconds", delay)
        deadline = monotonic() + delay
        while not should_stop() and (remaining := deadline - monotonic()) > 0:
            sleep(min(1, remaining))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=86400)
    parser.add_argument("--retry-interval", type=int, default=900)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--archive-year")
    parser.add_argument("--gazette-year")
    parser.add_argument("--include-grants", choices=("yes", "no"), default="no")
    parser.add_argument("--catch-up-year")
    parser.add_argument("--publication-from")
    parser.add_argument("--grant-from")
    parser.add_argument("--catch-up-max-issues", type=int, default=2)
    parser.add_argument("--legal-year")
    parser.add_argument("--legal-from")
    parser.add_argument(
        "--index-mode", choices=("none", "lexical", "hybrid"), default="lexical"
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 500 or not 60 <= args.retry_interval <= args.interval:
        parser.error("Expected a limit of 1..500 and 60 <= retry interval <= interval")
    if not getenv("PATENT_OBJECTS_DIR"):
        parser.error("Set PATENT_OBJECTS_DIR to a persistent object directory")
    if args.legal_year and not re.fullmatch(r"[0-9]{3}", args.legal_year):
        parser.error("--legal-year must be a three-digit ROC archive year")
    if args.legal_from and (
        not args.legal_year or not re.fullmatch(r"[0-9]{6}", args.legal_from)
    ):
        parser.error(
            "--legal-from requires --legal-year and a six-digit starting issue"
        )
    starts = [issue for issue in (args.publication_from, args.grant_from) if issue]
    if (
        bool(args.catch_up_year) != bool(starts)
        or (args.catch_up_year and not re.fullmatch(r"[0-9]{3}", args.catch_up_year))
        or any(not re.fullmatch(r"[0-9]{6}", issue) for issue in starts)
        or (args.grant_from and args.include_grants != "yes")
        or not 1 <= args.catch_up_max_issues <= 20
    ):
        parser.error(
            "Set a three-digit catch-up year, valid starting issues for enabled stages, and a maximum of 1..20 issues"
        )

    options = ["--apply", "--limit", str(args.limit), "--index-mode", args.index_mode]
    for option, year in (
        ("--archive-year", args.archive_year),
        ("--gazette-year", args.gazette_year),
    ):
        if year:
            if not re.fullmatch(r"[0-9]{3}", year):
                parser.error(f"{option} must be a three-digit ROC year")
            if args.catch_up_year and year != args.catch_up_year:
                parser.error(f"{option} must match --catch-up-year")
            options.extend([option, year])

    logging.basicConfig(level=logging.INFO)
    stopping = False

    def request_shutdown(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    serve(
        options,
        args.interval,
        args.retry_interval,
        lambda: stopping,
        include_grants=args.include_grants == "yes",
        catch_up_year=args.catch_up_year,
        publication_from=args.publication_from,
        grant_from=args.grant_from,
        catch_up_max_issues=args.catch_up_max_issues,
        legal_year=args.legal_year,
        legal_from=args.legal_from,
    )


if __name__ == "__main__":
    main()

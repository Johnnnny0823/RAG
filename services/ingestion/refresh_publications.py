"""Periodically refresh the official publication index within the deployment."""

import argparse
import logging
import re
import signal
from collections.abc import Callable
from os import getenv
from time import monotonic, sleep

from sqlalchemy.exc import SQLAlchemyError

from services.ingestion.latest_publication import main as refresh_once

logger = logging.getLogger(__name__)


def serve(
    options: list[str],
    interval: int,
    retry_interval: int,
    should_stop: Callable[[], bool],
    *,
    include_grants: bool = False,
) -> None:
    batches = [("Publication", options)]
    if include_grants:
        batches.append(("Grant", [*options, "--grants"]))
    while not should_stop():
        failed = False
        for stage, arguments in batches:
            if should_stop():
                return
            try:
                failed |= bool(refresh_once(arguments))
            except SystemExit as error:
                failed |= bool(error.code)
                logger.warning("%s refresh did not complete: %s", stage, error.code)
            except (OSError, SQLAlchemyError) as error:
                failed = True
                logger.warning(
                    "%s refresh unavailable: %s", stage, type(error).__name__
                )
        delay = retry_interval if failed else interval
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
    parser.add_argument(
        "--index-mode", choices=("none", "lexical", "hybrid"), default="lexical"
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 500 or not 60 <= args.retry_interval <= args.interval:
        parser.error("Expected a limit of 1..500 and 60 <= retry interval <= interval")
    if not getenv("PATENT_OBJECTS_DIR"):
        parser.error("Set PATENT_OBJECTS_DIR to a persistent object directory")

    options = ["--apply", "--limit", str(args.limit), "--index-mode", args.index_mode]
    for option, year in (
        ("--archive-year", args.archive_year),
        ("--gazette-year", args.gazette_year),
    ):
        if year:
            if not re.fullmatch(r"[0-9]{3}", year):
                parser.error(f"{option} must be a three-digit ROC year")
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
    )


if __name__ == "__main__":
    main()

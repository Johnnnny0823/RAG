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
) -> None:
    while not should_stop():
        try:
            status = refresh_once(options)
        except SystemExit as error:
            status = error.code
            logger.warning("Publication refresh did not complete: %s", status)
        except (OSError, SQLAlchemyError) as error:
            status = 1
            logger.warning("Publication refresh unavailable: %s", type(error).__name__)
        delay = retry_interval if status else interval
        logger.info("Publication refresh finished; next attempt in %s seconds", delay)
        deadline = monotonic() + delay
        while not should_stop() and (remaining := deadline - monotonic()) > 0:
            sleep(min(1, remaining))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=86400)
    parser.add_argument("--retry-interval", type=int, default=900)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--archive-year")
    parser.add_argument(
        "--index-mode", choices=("none", "lexical", "hybrid"), default="lexical"
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 500 or not 60 <= args.retry_interval <= args.interval:
        parser.error("Expected a limit of 1..500 and 60 <= retry interval <= interval")
    if args.archive_year and not re.fullmatch(r"[0-9]{3}", args.archive_year):
        parser.error("--archive-year must be a three-digit ROC year")
    if not getenv("PATENT_OBJECTS_DIR"):
        parser.error("Set PATENT_OBJECTS_DIR to a persistent object directory")

    options = ["--apply", "--limit", str(args.limit), "--index-mode", args.index_mode]
    if args.archive_year:
        options.extend(["--archive-year", args.archive_year])

    logging.basicConfig(level=logging.INFO)
    stopping = False

    def request_shutdown(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    serve(options, args.interval, args.retry_interval, lambda: stopping)


if __name__ == "__main__":
    main()

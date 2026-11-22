"""CLI: `python -m app.ingestion reference` | `python -m app.ingestion import <bundle.json>`.

Exit codes: 0 succeeded, 2 partial (some records rejected or conflicting), 1 failed.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from app.config import get_settings
from app.db import _sessionmaker
from app.ingestion.connectors import InputError, read_local_file
from app.ingestion.importer import import_bundle
from app.ingestion.reference import seed_reference
from app.models import IngestionRun, IngestionStatus

_EXIT = {IngestionStatus.SUCCEEDED: 0, IngestionStatus.PARTIAL: 2, IngestionStatus.FAILED: 1}


def _summary(run: IngestionRun) -> dict[str, object]:
    return {
        "run_id": str(run.id),
        "job": run.job_name,
        "status": run.status.value,
        "counts": run.counts,
        "issues": run.issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingestion")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("reference", help="seed exchanges and the sector taxonomy (idempotent)")
    imp = sub.add_parser("import", help="import a company/financials bundle (idempotent)")
    imp.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=get_settings().log_level.upper())

    with _sessionmaker()() as session:
        if args.command == "reference":
            runs = seed_reference(session)
        else:
            try:
                raw = read_local_file(args.path)
            except InputError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            runs = [import_bundle(session, raw)]
        # Commit data and run records together; a failed run still records what went wrong.
        session.commit()

    print(json.dumps([_summary(r) for r in runs], indent=2, ensure_ascii=False, default=str))
    statuses = {r.status for r in runs}
    for status in (IngestionStatus.FAILED, IngestionStatus.PARTIAL):  # worst outcome wins
        if status in statuses:
            return _EXIT[status]
    return 0


if __name__ == "__main__":
    sys.exit(main())

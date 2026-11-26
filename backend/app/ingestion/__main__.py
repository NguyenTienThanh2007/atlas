"""CLI:
  python -m app.ingestion reference
  python -m app.ingestion import <bundle.json>
  python -m app.ingestion review <evidence-id> --from S --decision D --curator C --reviewer R
                                 --checked-against "document, page" [--notes N]
  python -m app.ingestion reviews <evidence-id>
  python -m app.ingestion classify <company-id> --kind K --evidence E --basis "document, page"
                                   --curator C --reviewer R [--supersedes ID]

Exit codes: 0 succeeded, 2 partial (some records rejected or conflicting), 1 failed or refused.
"""

import argparse
import json
import logging
import sys
import uuid
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.db import _sessionmaker
from app.ingestion.connectors import InputError, read_local_file
from app.ingestion.importer import import_bundle
from app.ingestion.reference import seed_reference
from app.ingestion.review import history, record_classification, record_review
from app.models import (
    CompanyKind,
    IngestionRun,
    IngestionStatus,
    ReviewDecision,
    VerificationReview,
    VerificationStatus,
)

_EXIT = {IngestionStatus.SUCCEEDED: 0, IngestionStatus.PARTIAL: 2, IngestionStatus.FAILED: 1}


def _summary(run: IngestionRun) -> dict[str, object]:
    return {
        "run_id": str(run.id),
        "job": run.job_name,
        "status": run.status.value,
        "counts": run.counts,
        "issues": run.issues,
    }


def _review_summary(r: VerificationReview) -> dict[str, object]:
    return {
        "review_id": str(r.id),
        "evidence_id": str(r.evidence_id),
        "from_status": r.from_status.value,
        "decision": r.decision.value,
        "curator": r.curator,
        "reviewer": r.reviewer,
        "checked_against": r.checked_against,
        "notes": r.notes,
        "reviewed_at": r.reviewed_at.isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingestion")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("reference", help="seed exchanges and the sector taxonomy (idempotent)")
    imp = sub.add_parser("import", help="import a company/financials bundle (idempotent)")
    imp.add_argument("path", type=Path)
    rev = sub.add_parser("review", help="record a two-person verification decision")
    rev.add_argument("evidence_id", type=uuid.UUID)
    rev.add_argument("--from", dest="from_status", required=True, type=VerificationStatus)
    rev.add_argument("--decision", required=True, type=ReviewDecision)
    rev.add_argument("--curator", required=True, help="person who prepared the record")
    rev.add_argument("--reviewer", required=True, help="independent person who checked it")
    rev.add_argument("--checked-against", required=True, help="document and page(s) checked")
    rev.add_argument("--notes")
    hist = sub.add_parser("reviews", help="show the review history of one evidence record")
    hist.add_argument("evidence_id", type=uuid.UUID)
    cls = sub.add_parser("classify", help="record a two-person company classification (WS4-4)")
    cls.add_argument("company_id", type=uuid.UUID)
    cls.add_argument("--kind", required=True, type=CompanyKind)
    cls.add_argument("--evidence", required=True, type=uuid.UUID, help="evidence about the company")
    cls.add_argument("--basis", required=True, help="what the document says, and where")
    cls.add_argument("--curator", required=True)
    cls.add_argument("--reviewer", required=True)
    cls.add_argument("--supersedes", type=uuid.UUID, help="the classification this corrects")
    args = parser.parse_args(argv)
    logging.basicConfig(level=get_settings().log_level.upper())

    with _sessionmaker()() as session:
        if args.command == "reviews":
            print(
                json.dumps(
                    [_review_summary(r) for r in history(session, args.evidence_id)],
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.command in ("review", "classify"):
            try:
                with session.begin_nested():  # a refusal undoes only this record
                    if args.command == "review":
                        summary = _review_summary(
                            record_review(
                                session,
                                evidence_id=args.evidence_id,
                                from_status=args.from_status,
                                decision=args.decision,
                                curator=args.curator,
                                reviewer=args.reviewer,
                                checked_against=args.checked_against,
                                notes=args.notes,
                            )
                        )
                    else:
                        c = record_classification(
                            session,
                            company_id=args.company_id,
                            kind=args.kind,
                            evidence_id=args.evidence,
                            basis=args.basis,
                            curator=args.curator,
                            reviewer=args.reviewer,
                            supersedes_id=args.supersedes,
                        )
                        summary = {
                            "classification_id": str(c.id),
                            "company_id": str(c.company_id),
                            "kind": c.kind.value,
                            "evidence_id": str(c.evidence_id),
                            "supersedes_id": str(c.supersedes_id) if c.supersedes_id else None,
                            "decided_at": c.decided_at.isoformat(),
                        }
            except IntegrityError as exc:
                detail = getattr(getattr(exc.orig, "diag", None), "message_primary", None)
                constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                print(f"refused: {constraint or detail or 'database constraint'}", file=sys.stderr)
                return 1
            session.commit()
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return 0
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

import logging
from collections import Counter
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.ingestion.connectors import RawInput
from app.models import IngestionRun, IngestionStatus

logger = logging.getLogger("app.ingestion")

IssueKind = Literal["invalid", "duplicate", "conflict", "missing_reference", "fatal"]


class RunRecorder:
    """Persists one IngestionRun with counts and actionable issues."""

    def __init__(self, session: Session, job_name: str, raw: RawInput) -> None:
        self.run = IngestionRun(
            job_name=job_name,
            input_ref=raw.ref,
            input_sha256=raw.sha256,
            status=IngestionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        session.add(self.run)
        session.flush()
        self.counts: Counter[str] = Counter()
        self.issues: list[dict[str, object]] = []

    def issue(self, kind: IssueKind, record: str, message: str, key: str | None = None) -> None:
        self.issues.append({"kind": kind, "record": record, "key": key, "message": message})
        self.counts[f"issues.{kind}"] += 1
        logger.warning("ingestion %s %s [%s] %s: %s", self.run.job_name, kind, record, key, message)

    def finish(self) -> IngestionRun:
        if any(i["kind"] == "fatal" for i in self.issues):
            status = IngestionStatus.FAILED
        elif self.issues:
            status = IngestionStatus.PARTIAL
        else:
            status = IngestionStatus.SUCCEEDED
        self.run.status = status
        self.run.counts = dict(sorted(self.counts.items()))
        self.run.issues = self.issues
        self.run.finished_at = datetime.now(UTC)
        logger.info("ingestion %s finished: %s %s", self.run.job_name, status, self.run.counts)
        return self.run

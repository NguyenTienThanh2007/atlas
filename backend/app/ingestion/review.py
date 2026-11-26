"""Two-person verification reviews (local CLI only; there is no API for this).

The database does the enforcing (migration 31b1317163eb): curator != reviewer, the reviewer is
not the system, allowed transitions only, append-only history, and `from_status` must match the
evidence's current state. This module only records the request and reports the outcome.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Company,
    CompanyClassification,
    CompanyKind,
    EntityType,
    Evidence,
    ReviewDecision,
    Security,
    VerificationReview,
    VerificationStatus,
)


def record_review(
    session: Session,
    *,
    evidence_id: uuid.UUID,
    from_status: VerificationStatus,
    decision: ReviewDecision,
    curator: str,
    reviewer: str,
    checked_against: str,
    notes: str | None = None,
) -> VerificationReview:
    """Insert one review. Raises sqlalchemy IntegrityError when the database refuses it."""
    review = VerificationReview(
        evidence_id=evidence_id,
        from_status=from_status,
        decision=decision,
        curator=curator,
        reviewer=reviewer,
        checked_against=checked_against,
        notes=notes,
    )
    session.add(review)
    session.flush()
    session.refresh(review)
    if decision is ReviewDecision.VERIFIED:
        _stamp_last_verified(session, evidence_id, review.reviewed_at)
    return review


def _stamp_last_verified(session: Session, evidence_id: uuid.UUID, at: datetime) -> None:
    """Company/security `last_verified_at` = time of the latest review that verified their
    evidence. It is a display convenience; the reviews table is the record."""
    entity_type, entity_id = session.execute(
        select(Evidence.entity_type, Evidence.entity_id).where(Evidence.id == evidence_id)
    ).one()
    row: Company | Security | None = None
    if entity_type is EntityType.COMPANY:
        row = session.get(Company, entity_id)
    elif entity_type is EntityType.SECURITY:
        row = session.get(Security, entity_id)
    if row is not None:
        if row.last_verified_at is None or at > row.last_verified_at:
            row.last_verified_at = at
            session.flush()


def history(session: Session, evidence_id: uuid.UUID) -> list[VerificationReview]:
    return list(
        session.scalars(
            select(VerificationReview)
            .where(VerificationReview.evidence_id == evidence_id)
            .order_by(VerificationReview.reviewed_at, VerificationReview.id)
        )
    )


def record_classification(
    session: Session,
    *,
    company_id: uuid.UUID,
    kind: CompanyKind,
    evidence_id: uuid.UUID,
    basis: str,
    curator: str,
    reviewer: str,
    supersedes_id: uuid.UUID | None = None,
) -> CompanyClassification:
    """Record one reviewed company classification (WS4-4-D1, D7). The database enforces the
    two-person rule, the evidence rules and the single chain per company (migration
    5c1f0a2b7e44); it raises IntegrityError when it refuses."""
    record = CompanyClassification(
        company_id=company_id,
        kind=kind,
        evidence_id=evidence_id,
        basis=basis,
        curator=curator,
        reviewer=reviewer,
        supersedes_id=supersedes_id,
    )
    session.add(record)
    session.flush()
    session.refresh(record)
    return record

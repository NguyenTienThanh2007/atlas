"""WS4-4 Phase A: a company's current classification and what the dictionary says about each
metric for it (decisions WS4-4-D1 to D4, D7). Read-only; nothing derived here is stored.

`not_applicable` needs a reviewed classification **and** a dictionary `not_applicable`; anything
else (no classification, `other_financial`, a dictionary `unclassified`) is `unknown`, which is
never read as "not applicable" (WS4-D10 G-2)."""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.ingestion.reference import MetricDef
from app.models import CompanyClassification, CompanyKind, VerificationStatus

Effective = Literal["applicable", "not_applicable", "unknown"]

# WS4-4-D7: a classification stops counting while its evidence is under dispute or rejected.
_WITHDRAWN = (VerificationStatus.DISPUTED, VerificationStatus.REJECTED)


@dataclass(frozen=True)
class Current:
    record: CompanyClassification  # the last row of the company's chain, evidence loaded

    @property
    def kind(self) -> CompanyKind | None:
        """The kind that counts, or None (unclassified)."""
        return None if self.record.evidence.verification_status in _WITHDRAWN else self.record.kind


def current_classifications(
    db: Session, company_ids: Iterable[uuid.UUID]
) -> dict[uuid.UUID, Current]:
    """The last classification of each company that has one, in one query."""
    ids = list(company_ids)
    if not ids:
        return {}
    newer = aliased(CompanyClassification)
    rows = db.scalars(
        select(CompanyClassification)
        .where(
            CompanyClassification.company_id.in_(ids),
            ~exists().where(newer.supersedes_id == CompanyClassification.id),
        )
        .options(joinedload(CompanyClassification.evidence))
    )
    return {r.company_id: Current(r) for r in rows}


def company_kind(db: Session, company_id: uuid.UUID) -> CompanyKind | None:
    current = current_classifications(db, [company_id]).get(company_id)
    return current.kind if current else None


def effective(kind: CompanyKind | None, metric: MetricDef) -> Effective:
    """Plan §3.1: what the dictionary says about `metric` for a company of this kind."""
    if kind is CompanyKind.BANK:
        value = metric.applicability.bank
    elif kind is CompanyKind.NON_BANK:
        value = metric.applicability.non_bank
    else:
        return "unknown"  # unclassified, or other_financial (no dictionary column yet)
    return "unknown" if value == "unclassified" else value


def basis(kind: CompanyKind | None) -> Literal["dictionary_bank", "dictionary_non_bank"] | None:
    """Which dictionary column a `not_applicable` came from."""
    if kind is CompanyKind.BANK:
        return "dictionary_bank"
    if kind is CompanyKind.NON_BANK:
        return "dictionary_non_bank"
    return None

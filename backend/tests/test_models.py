"""Database-level guarantees, tested against real PostgreSQL."""

import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AccessMethod,
    Company,
    DataSource,
    EntityType,
    Evidence,
    Exchange,
    FinancialMetric,
    FinancialStatement,
    ListingStatus,
    Sector,
    Security,
    SecurityType,
    SourceType,
    StatementScope,
    StatementType,
    VerificationStatus,
)


def fails(db: Session, action: Callable[[], object]) -> None:
    """The action must be rejected by the database; the test session stays usable."""
    with pytest.raises(IntegrityError), db.begin_nested():
        action()
        db.flush()


def sector(db: Session, code: str = "TECHNOLOGY") -> Sector:
    return db.scalars(select(Sector).where(Sector.code == code)).one()


def exchange(db: Session, code: str = "HOSE") -> Exchange:
    return db.scalars(select(Exchange).where(Exchange.code == code)).one()


def new_company(db: Session, **kw: object) -> Company:
    fields: dict[str, object] = {"legal_name": "Test Co JSC", "short_name": "Test Co"}
    fields.update(kw)
    c = Company(sector_id=sector(db).id, **fields)
    db.add(c)
    db.flush()
    return c


def new_security(db: Session, company: Company, ticker: str = "TST", **kw: object) -> Security:
    fields: dict[str, object] = {
        "security_type": SecurityType.COMMON_STOCK,
        "currency": "VND",
        "listing_status": ListingStatus.LISTED,
        "exchange_id": exchange(db).id,
    }
    fields.update(kw)
    s = Security(company_id=company.id, ticker=ticker, **fields)
    db.add(s)
    db.flush()
    return s


def new_statement(db: Session, company: Company, **kw: object) -> FinancialStatement:
    src = DataSource(
        name=f"src-{uuid.uuid4()}",
        source_type=SourceType.COMPANY_DISCLOSURE,
        description="test",
        access_method=AccessMethod.FILE_IMPORT,
    )
    db.add(src)
    db.flush()
    sid = uuid.uuid4()
    ev = Evidence(
        data_source_id=src.id,
        entity_type=EntityType.FINANCIAL_STATEMENT,
        entity_id=sid,
        source_url="https://example.test/fs.pdf",
        retrieved_at=datetime.now(UTC),
        verification_status=VerificationStatus.UNVERIFIED,
    )
    db.add(ev)
    db.flush()
    fields: dict[str, object] = {
        "reporting_period_start": date(2025, 1, 1),
        "reporting_period_end": date(2025, 12, 31),
        "fiscal_year": 2025,
        "statement_type": StatementType.INCOME_STATEMENT,
        "scope": StatementScope.CONSOLIDATED,
        "currency": "VND",
    }
    fields.update(kw)
    st = FinancialStatement(id=sid, company_id=company.id, source_evidence_id=ev.id, **fields)
    db.add(st)
    db.flush()
    return st


def test_reference_data_is_seeded(ref: Session) -> None:
    assert sorted(ref.scalars(select(Exchange.code))) == ["HNX", "HOSE", "UPCOM"]
    assert ref.scalar(select(text("count(*)")).select_from(Sector)) == 7


def test_exchange_code_is_unique(ref: Session) -> None:
    fails(ref, lambda: ref.add(Exchange(code="HOSE", name="dup", country_code="VN")))


def test_company_can_have_several_securities(ref: Session) -> None:
    c = new_company(ref)
    new_security(ref, c, "TSTA")
    new_security(
        ref,
        c,
        "TSTB",
        exchange_id=exchange(ref, "UPCOM").id,
        security_type=SecurityType.PREFERRED_STOCK,
    )
    loaded = ref.scalars(
        select(Company).where(Company.id == c.id).options(selectinload(Company.securities))
    ).one()
    assert [s.ticker for s in loaded.securities] == ["TSTA", "TSTB"]


def test_active_ticker_unique_per_exchange_but_reusable_after_delisting(ref: Session) -> None:
    a, b = new_company(ref), new_company(ref, legal_name="Other JSC")
    old = new_security(ref, a, "TKR")
    fails(ref, lambda: new_security(ref, b, "TKR"))  # two active listings of one ticker
    # Same ticker on another exchange is a different listing.
    new_security(ref, b, "TKR", exchange_id=exchange(ref, "HNX").id)
    # Delist the old listing: its row stays as history and the ticker can be reused.
    old.listing_status = ListingStatus.DELISTED
    old.delisted_at = date(2025, 6, 30)
    ref.flush()
    new_security(ref, b, "TKR")
    assert (
        ref.scalar(select(text("count(*)")).select_from(Security).where(Security.ticker == "TKR"))
        == 3
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ticker", "bad ticker"),
        ("isin", "NOTANISIN"),
        ("currency", "vnd"),
        ("listing_status_without_date", ListingStatus.DELISTED),
    ],
)
def test_security_constraints(ref: Session, field: str, value: object) -> None:
    c = new_company(ref)
    if field == "listing_status_without_date":
        fails(ref, lambda: new_security(ref, c, listing_status=value))
    elif field == "ticker":
        fails(ref, lambda: new_security(ref, c, ticker=str(value)))
    else:
        extra: dict[str, Any] = {field: value}
        fails(ref, lambda: new_security(ref, c, **extra))


def test_delisted_before_listed_is_rejected(ref: Session) -> None:
    c = new_company(ref)
    fails(
        ref,
        lambda: new_security(
            ref,
            c,
            listing_status=ListingStatus.DELISTED,
            listed_at=date(2025, 1, 1),
            delisted_at=date(2024, 1, 1),
        ),
    )


def test_company_constraints(ref: Session) -> None:
    fails(ref, lambda: new_company(ref, tax_code="12AB"))
    fails(ref, lambda: new_company(ref, website="javascript:alert(1)"))
    new_company(ref, tax_code="0100000000")
    fails(ref, lambda: new_company(ref, tax_code="0100000000"))  # unique


def test_deletes_never_cascade(ref: Session) -> None:
    c = new_company(ref)
    new_security(ref, c)
    fails(ref, lambda: ref.execute(delete(Company).where(Company.id == c.id)))
    fails(ref, lambda: ref.execute(delete(Sector).where(Sector.id == c.sector_id)))


def test_timestamps_are_timezone_aware(ref: Session) -> None:
    c = new_company(ref)
    ref.refresh(c)
    assert c.created_at.tzinfo is not None
    assert c.updated_at.tzinfo is not None


@pytest.mark.parametrize(
    "value",
    [
        Decimal("12345678901234567890123456789012.123456"),  # 38 significant digits
        Decimal("-0.000001"),
        Decimal("0.1") + Decimal("0.2"),  # exactly 0.3, unlike floats
        Decimal("1000000000000000"),  # 1 quadrillion VND
    ],
)
def test_metric_values_round_trip_exactly(ref: Session, value: Decimal) -> None:
    st = new_statement(ref, new_company(ref))
    m = FinancialMetric(
        financial_statement_id=st.id,
        metric_code="net_revenue",
        metric_name="Net revenue",
        value=value,
        unit="VND",
    )
    ref.add(m)
    ref.flush()
    stored = ref.execute(
        text("SELECT value FROM financial_metrics WHERE id = :id"), {"id": m.id}
    ).scalar_one()
    assert isinstance(stored, Decimal)
    assert stored == value
    assert (
        ref.execute(
            text("SELECT pg_typeof(value)::text FROM financial_metrics WHERE id=:id"), {"id": m.id}
        ).scalar_one()
        == "numeric"
    )


def test_financial_history_is_append_only(ref: Session) -> None:
    st = new_statement(ref, new_company(ref))
    ref.add(
        FinancialMetric(
            financial_statement_id=st.id,
            metric_code="net_revenue",
            metric_name="Net revenue",
            value=Decimal("1"),
            unit="VND",
        )
    )
    ref.flush()
    fails(ref, lambda: ref.execute(update(FinancialMetric).values(value=Decimal("2"))))
    fails(ref, lambda: ref.execute(delete(FinancialMetric)))
    fails(ref, lambda: ref.execute(update(FinancialStatement).values(currency="USD")))
    fails(
        ref, lambda: ref.execute(delete(FinancialStatement).where(FinancialStatement.id == st.id))
    )
    assert ref.scalar(select(FinancialMetric.value)) == Decimal("1")


def test_statement_identity_and_revision_rules(ref: Session) -> None:
    c = new_company(ref)
    first = new_statement(ref, c)
    # Same identity (NULL quarter included) cannot be stored twice.
    fails(ref, lambda: new_statement(ref, c))
    # A restatement is a new revision pointing at the one it supersedes.
    new_statement(ref, c, revision=2, supersedes_id=first.id)
    fails(ref, lambda: new_statement(ref, c, revision=3))  # revision > 1 needs supersedes
    fails(ref, lambda: new_statement(ref, c, fiscal_quarter=5))
    fails(ref, lambda: new_statement(ref, c, reporting_period_end=date(2024, 1, 1)))

"""ATLAS domain model.

Key decisions (details in docs/ARCHITECTURE.md):
- A Company (legal entity) is distinct from a Security (a tradable instrument on one exchange).
- Financial statements belong to the Company: one legal entity files one set of statements,
  however many securities it has listed.
- History is append-only: financial statements and metrics cannot be UPDATEd or DELETEd
  (enforced by database triggers); restatements are new revisions that point at the row
  they supersede.
- Foreign keys never cascade deletes.
- Verification is a two-person decision recorded in append-only `verification_reviews`; only a
  review may change `evidence.verification_status` (enforced by database triggers, see
  docs/VERIFICATION_WORKFLOW.md).
"""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Large enough for VND amounts (quadrillions) with exact sub-unit ratios; never use floats.
MONEY = Numeric(precision=38, scale=6, asdecimal=True)


def _enum(cls: type[enum.Enum], name: str) -> Enum:
    # VARCHAR + CHECK instead of native PG enums: simpler, fully reversible migrations.
    return Enum(
        cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _updated() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def _fk(target: str, *, nullable: bool = False, index: bool = True) -> Mapped[uuid.UUID]:
    return mapped_column(
        Uuid, ForeignKey(target, ondelete="RESTRICT"), nullable=nullable, index=index
    )


class SecurityType(enum.StrEnum):
    COMMON_STOCK = "common_stock"
    PREFERRED_STOCK = "preferred_stock"
    FUND_CERTIFICATE = "fund_certificate"
    BOND = "bond"
    COVERED_WARRANT = "covered_warrant"
    OTHER = "other"


class ListingStatus(enum.StrEnum):
    PENDING = "pending"
    LISTED = "listed"
    SUSPENDED = "suspended"
    DELISTED = "delisted"


class SourceType(enum.StrEnum):
    OFFICIAL_REGULATOR = "official_regulator"
    EXCHANGE = "exchange"
    COMPANY_DISCLOSURE = "company_disclosure"
    LICENSED_PROVIDER = "licensed_provider"
    INTERNAL = "internal"
    SAMPLE_FIXTURE = "sample_fixture"


class AccessMethod(enum.StrEnum):
    MANUAL = "manual"
    FILE_IMPORT = "file_import"
    API = "api"
    WEB_PAGE = "web_page"


class CommercialUsageStatus(enum.StrEnum):
    # Public accessibility is NOT redistribution permission: default to UNKNOWN.
    UNKNOWN = "unknown"
    PERSONAL_ONLY = "personal_only"
    LICENSED = "licensed"
    PUBLIC_OFFICIAL = "public_official"
    RESTRICTED = "restricted"


class EntityType(enum.StrEnum):
    SECTOR = "sector"
    COMPANY = "company"
    SECURITY = "security"
    FINANCIAL_STATEMENT = "financial_statement"


class VerificationStatus(enum.StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    SAMPLE = "sample"  # fictional fixture data; never real


class ReviewDecision(enum.StrEnum):
    """Target state of a review. `sample` is never a decision: sample data is never reviewed."""

    VERIFIED = "verified"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    UNVERIFIED = "unverified"  # reopen a rejected or disputed record
    SUPERSEDED = "superseded"


# Scale a document's amounts are printed in; the stored `value` is always in full units.
AMOUNT_SCALES = (1, 1_000, 1_000_000)


class StatementType(enum.StrEnum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"


class StatementScope(enum.StrEnum):
    SEPARATE = "separate"
    CONSOLIDATED = "consolidated"


class IngestionStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"  # finished, but some records were rejected or conflicted
    FAILED = "failed"


CURRENCY_CHECK = "~ '^[A-Z]{3}$'"


class Sector(Base):
    __tablename__ = "sectors"
    __table_args__ = (
        CheckConstraint("code ~ '^[A-Z][A-Z0-9_]{1,31}$'", name="code_format"),
        CheckConstraint("parent_sector_id <> id", name="not_own_parent"),
    )

    id: Mapped[uuid.UUID] = _pk()
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_vi: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_sector_id: Mapped[uuid.UUID | None] = _fk("sectors.id", nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Exchange(Base):
    __tablename__ = "exchanges"
    __table_args__ = (
        CheckConstraint("code ~ '^[A-Z]{2,16}$'", name="code_format"),
        CheckConstraint("country_code ~ '^[A-Z]{2}$'", name="country_code_format"),
    )

    id: Mapped[uuid.UUID] = _pk()
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = _created()


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("tax_code ~ '^[0-9]{10}(-[0-9]{3})?$'", name="tax_code_format"),
        CheckConstraint("website ~ '^https?://'", name="website_scheme"),
        Index("ix_companies_short_name_id", "short_name", "id"),  # stable list ordering
        Index("ix_companies_legal_name_lower", text("lower(legal_name)")),
    )

    id: Mapped[uuid.UUID] = _pk()
    legal_name: Mapped[str] = mapped_column(String(300), nullable=False)
    short_name: Mapped[str] = mapped_column(String(120), nullable=False)
    english_name: Mapped[str | None] = mapped_column(String(300))
    tax_code: Mapped[str | None] = mapped_column(String(14), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(300))
    sector_id: Mapped[uuid.UUID] = _fk("sectors.id")
    is_sample: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()

    sector: Mapped[Sector] = relationship(lazy="raise")
    securities: Mapped[list["Security"]] = relationship(
        back_populates="company", lazy="raise", order_by="Security.ticker"
    )


class Security(Base):
    __tablename__ = "securities"
    __table_args__ = (
        CheckConstraint("ticker ~ '^[A-Z0-9]{2,12}$'", name="ticker_format"),
        CheckConstraint("isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$'", name="isin_format"),
        CheckConstraint(f"currency {CURRENCY_CHECK}", name="currency_format"),
        CheckConstraint(
            "delisted_at IS NULL OR listed_at IS NULL OR delisted_at >= listed_at",
            name="delisted_after_listed",
        ),
        CheckConstraint(
            "(listing_status = 'delisted') = (delisted_at IS NOT NULL)",
            name="delisted_status_has_date",
        ),
        # A ticker is unique per exchange among non-delisted securities; delisted rows keep history
        # and the ticker can later be reused or the company can re-list elsewhere.
        Index(
            "uq_securities_active_exchange_ticker",
            "exchange_id",
            "ticker",
            unique=True,
            postgresql_where=text("listing_status <> 'delisted'"),
        ),
        Index("ix_securities_ticker", "ticker"),
    )

    id: Mapped[uuid.UUID] = _pk()
    company_id: Mapped[uuid.UUID] = _fk("companies.id")
    exchange_id: Mapped[uuid.UUID] = _fk("exchanges.id")
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    security_type: Mapped[SecurityType] = mapped_column(
        _enum(SecurityType, "security_type"), nullable=False
    )
    isin: Mapped[str | None] = mapped_column(String(12), unique=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    listing_status: Mapped[ListingStatus] = mapped_column(
        _enum(ListingStatus, "listing_status"), nullable=False
    )
    listed_at: Mapped[date | None] = mapped_column(Date)
    delisted_at: Mapped[date | None] = mapped_column(Date)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()

    company: Mapped[Company] = relationship(back_populates="securities", lazy="raise")
    exchange: Mapped[Exchange] = relationship(lazy="raise")


class DataSource(Base):
    __tablename__ = "data_sources"
    __table_args__ = (
        CheckConstraint("base_url ~ '^https?://'", name="base_url_scheme"),
        CheckConstraint("terms_url ~ '^https?://'", name="terms_url_scheme"),
    )

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        _enum(SourceType, "source_type"), nullable=False
    )
    base_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    access_method: Mapped[AccessMethod] = mapped_column(
        _enum(AccessMethod, "access_method"), nullable=False
    )
    commercial_usage_status: Mapped[CommercialUsageStatus] = mapped_column(
        _enum(CommercialUsageStatus, "commercial_usage_status"),
        nullable=False,
        server_default=CommercialUsageStatus.UNKNOWN.value,
    )
    terms_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Evidence(Base):
    """Where a fact came from. Polymorphic (entity_type, entity_id): no FK on entity_id."""

    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint("source_url ~ '^(https?|file|fixture)://'", name="source_url_scheme"),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from",
            name="effective_range",
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash_sha256"),
        UniqueConstraint(
            "data_source_id",
            "entity_type",
            "entity_id",
            "source_url",
            "retrieved_at",
            name="uq_evidence_identity",
        ),
        Index("ix_evidence_entity", "entity_type", "entity_id"),
    )

    id: Mapped[uuid.UUID] = _pk()
    data_source_id: Mapped[uuid.UUID] = _fk("data_sources.id")
    entity_type: Mapped[EntityType] = mapped_column(
        _enum(EntityType, "entity_type"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    document_title: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "verification_status"), nullable=False
    )
    content_hash: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()

    data_source: Mapped[DataSource] = relationship(lazy="raise")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        CheckConstraint("reporting_period_end >= reporting_period_start", name="period_order"),
        CheckConstraint("fiscal_year BETWEEN 1990 AND 2200", name="fiscal_year_range"),
        CheckConstraint("fiscal_quarter BETWEEN 1 AND 4", name="fiscal_quarter_range"),
        CheckConstraint(f"currency {CURRENCY_CHECK}", name="currency_format"),
        CheckConstraint("revision >= 1", name="revision_positive"),
        CheckConstraint("(revision = 1) = (supersedes_id IS NULL)", name="revision_chain"),
        UniqueConstraint(
            "company_id",
            "statement_type",
            "scope",
            "fiscal_year",
            "fiscal_quarter",
            "reporting_period_end",
            "revision",
            name="uq_statement_identity",
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_statements_company_period", "company_id", "reporting_period_end"),
    )

    id: Mapped[uuid.UUID] = _pk()
    company_id: Mapped[uuid.UUID] = _fk("companies.id", index=False)
    reporting_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    reporting_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fiscal_quarter: Mapped[int | None] = mapped_column(SmallInteger)
    statement_type: Mapped[StatementType] = mapped_column(
        _enum(StatementType, "statement_type"), nullable=False
    )
    scope: Mapped[StatementScope] = mapped_column(
        _enum(StatementScope, "statement_scope"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    supersedes_id: Mapped[uuid.UUID | None] = _fk("financial_statements.id", nullable=True)
    source_evidence_id: Mapped[uuid.UUID] = _fk("evidence.id")
    created_at: Mapped[datetime] = _created()

    metrics: Mapped[list["FinancialMetric"]] = relationship(
        lazy="raise", order_by="FinancialMetric.metric_code"
    )
    source_evidence: Mapped[Evidence] = relationship(lazy="raise")


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"
    __table_args__ = (
        CheckConstraint("metric_code ~ '^[a-z][a-z0-9_]{1,63}$'", name="metric_code_format"),
        UniqueConstraint("financial_statement_id", "metric_code", name="uq_metric_per_statement"),
        CheckConstraint("source_page >= 1", name="source_page_positive"),
        CheckConstraint("reported_scale IN (1, 1000, 1000000)", name="reported_scale_allowed"),
        # Conversion provenance: both present or both absent (rows from before WS1), and the
        # stored value is exactly the reported value times the declared scale.
        CheckConstraint(
            "(reported_value IS NULL) = (reported_scale IS NULL)", name="reported_pair"
        ),
        CheckConstraint(
            "reported_value IS NULL OR value = reported_value * reported_scale",
            name="value_is_reported_times_scale",
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    financial_statement_id: Mapped[uuid.UUID] = _fk("financial_statements.id", index=False)
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    # Page of the source document (the statement's evidence) the figure is printed on.
    # Required for real figures (trigger); optional for the fictional sample fixture.
    source_page: Mapped[int | None] = mapped_column(Integer)
    reported_value: Mapped[Decimal | None] = mapped_column(MONEY)
    reported_scale: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _created()


class VerificationReview(Base):
    """One review decision on one evidence row. Append-only (trigger); a changed decision is a
    new row whose `from_status` is the state it moves away from."""

    __tablename__ = "verification_reviews"
    __table_args__ = (
        CheckConstraint("btrim(curator) <> '' AND btrim(reviewer) <> ''", name="names_present"),
        # The two-person rule: the reviewer is never the curator.
        CheckConstraint(
            "lower(btrim(curator)) <> lower(btrim(reviewer))", name="curator_is_not_reviewer"
        ),
        # A reviewer is a person: names the system uses for itself are refused.
        CheckConstraint(
            "lower(btrim(reviewer)) !~ '^(system|atlas|auto|automated|automatic|bot|import|"
            "importer|ingestion|claude|ai)$'",
            name="reviewer_is_a_person",
        ),
        CheckConstraint("btrim(checked_against) <> ''", name="checked_against_present"),
        Index("ix_verification_reviews_evidence", "evidence_id", "reviewed_at"),
    )

    id: Mapped[uuid.UUID] = _pk()
    evidence_id: Mapped[uuid.UUID] = _fk("evidence.id", index=False)
    from_status: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "review_from_status"), nullable=False
    )
    decision: Mapped[ReviewDecision] = mapped_column(
        _enum(ReviewDecision, "review_decision"), nullable=False
    )
    curator: Mapped[str] = mapped_column(String(120), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(120), nullable=False)
    checked_against: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (CheckConstraint("input_sha256 ~ '^[0-9a-f]{64}$'", name="input_sha256"),)

    id: Mapped[uuid.UUID] = _pk()
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_ref: Mapped[str] = mapped_column(String(1000), nullable=False)
    input_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data_source_id: Mapped[uuid.UUID | None] = _fk("data_sources.id", nullable=True)
    status: Mapped[IngestionStatus] = mapped_column(
        _enum(IngestionStatus, "ingestion_status"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    counts: Mapped[dict[str, int]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    issues: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

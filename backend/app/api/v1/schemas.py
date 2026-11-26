"""Public response models. Only fields meant for clients; money is serialised as a decimal
string (Pydantic's JSON mode), never as a float."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, computed_field

from app.calculations.comparisons import ComparisonType, Direction, Side, Status
from app.calculations.comparisons import ReasonCode as ComparisonReason
from app.calculations.ratios import InputVerification, ReasonCode, Role
from app.ingestion.reference import metric_dictionary
from app.models import (
    CommercialUsageStatus,
    EntityType,
    Evidence,
    ListingStatus,
    SecurityType,
    SourceType,
    StatementScope,
    StatementType,
    VerificationStatus,
)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class ExchangeOut(_Out):
    id: uuid.UUID
    code: str
    name: str
    country_code: str


class SectorRef(_Out):
    id: uuid.UUID
    code: str
    name: str
    name_vi: str


class SectorOut(SectorRef):
    description: str
    taxonomy_version: str
    parent_sector_id: uuid.UUID | None
    company_count: int


class ExchangeRef(_Out):
    code: str
    name: str


class SecurityBrief(_Out):
    id: uuid.UUID
    ticker: str
    exchange: ExchangeRef
    listing_status: ListingStatus


class SecurityOut(SecurityBrief):
    security_type: SecurityType
    isin: str | None
    currency: str
    listed_at: date | None
    delisted_at: date | None
    last_verified_at: datetime | None


class CompanyRef(_Out):
    id: uuid.UUID
    short_name: str
    legal_name: str
    is_sample: bool


class SecurityDetailOut(SecurityOut):
    company: CompanyRef


class CompanyListItem(CompanyRef):
    english_name: str | None
    sector: SectorRef
    securities: list[SecurityBrief]
    # WS4-4: set by the endpoint from the reviewed classification; unclassified unless one counts.
    classification: "ClassificationOut" = Field(default_factory=lambda: ClassificationOut())


class CompanyOut(CompanyListItem):
    tax_code: str | None
    description: str | None
    website: str | None
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    securities: list[SecurityOut]  # type: ignore[assignment]


class DataSourceRef(_Out):
    name: str
    source_type: SourceType
    commercial_usage_status: CommercialUsageStatus
    terms_url: str | None


class EvidenceOut(_Out):
    id: uuid.UUID
    entity_type: EntityType
    entity_id: uuid.UUID
    source_url: str
    document_title: str | None
    published_at: datetime | None
    retrieved_at: datetime
    effective_from: date | None
    effective_to: date | None
    verification_status: VerificationStatus
    content_hash: str | None
    notes: str | None
    data_source: DataSourceRef


def linkable_url(url: str) -> str | None:
    """The URL if it is safe to render as a link: absolute http(s) with a host, no credentials,
    no whitespace or control characters. Anything else (fixture://, file://, javascript:, ...)
    is not a link. Never fetched."""
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        return None
    try:
        parts = urlsplit(url)
        host = parts.hostname
        has_credentials = parts.username is not None or parts.password is not None
    except ValueError:
        return None
    if parts.scheme.lower() not in {"http", "https"} or not host or has_credentials:
        return None
    return url


class MetricSourceOut(BaseModel):
    """Where one figure comes from (WS3). The document is the figure's statement's evidence (one
    per statement, enforced by the schema); the page is the figure's own `source_page`."""

    evidence_id: uuid.UUID
    document_title: str | None
    document_url: str | None  # only when linkable
    link_status: Literal["linkable", "not_linkable"]
    page: int | None  # None = unknown (sample fixture or rows from before WS1); never 0
    verification_status: VerificationStatus

    @classmethod
    def for_figure(cls, evidence: Evidence, page: int | None) -> "MetricSourceOut":
        url = linkable_url(evidence.source_url)
        return cls(
            evidence_id=evidence.id,
            document_title=evidence.document_title,
            document_url=url,
            link_status="linkable" if url else "not_linkable",
            page=page,
            verification_status=evidence.verification_status,
        )


class ClassificationOut(BaseModel):
    """A company's current reviewed classification (WS4-4-D1, D2, D7). `unclassified` when there
    is none, or while its evidence is disputed or rejected. Never derived from sector or name."""

    kind: Literal["bank", "non_bank", "other_financial", "unclassified"] = "unclassified"
    decided_at: datetime | None = None
    basis: str | None = None  # what the cited document says, and where
    source: MetricSourceOut | None = None  # the cited company evidence (no page column)


class AbsentMetricOut(BaseModel):
    """A dictionary metric of this statement's type with no figure (WS4-D6 Phase A). Absence is
    never a zero and never "not reported": ATLAS can't prove anyone checked the document."""

    metric_code: str
    metric_name_vi: str
    metric_name_en: str
    state: Literal["not_yet_collected", "not_applicable"]
    applicability_basis: Literal["dictionary_bank", "dictionary_non_bank"] | None


class MetricOut(_Out):
    metric_code: str
    metric_name: str
    value: Decimal  # full units, exact
    unit: str
    reported_value: Decimal | None  # as printed in the document; None for rows from before WS1
    reported_scale: int | None  # 1, 1000 or 1000000; None for rows from before WS1
    source: MetricSourceOut
    # WS4-4-D4: a figure stored for a metric the dictionary says does not apply to this company's
    # reviewed kind (entered before the classification). Shown, flagged, never hidden.
    applicability_conflict: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metric_name_vi(self) -> str | None:
        """Vietnamese label from the versioned metric dictionary (read-only; never stored)."""
        definition = metric_dictionary().get(self.metric_code)
        return definition.name_vi if definition else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metric_name_en(self) -> str | None:
        """English label from the current metric dictionary (read-only; never stored).
        `metric_name` stays the name stored at import time, which may be an older label."""
        definition = metric_dictionary().get(self.metric_code)
        return definition.name if definition else None


class FinancialStatementOut(_Out):
    id: uuid.UUID
    reporting_period_start: date
    reporting_period_end: date
    fiscal_year: int
    fiscal_quarter: int | None
    statement_type: StatementType
    scope: StatementScope
    currency: str
    publication_date: date | None
    revision: int
    supersedes_id: uuid.UUID | None
    is_superseded: bool
    source_evidence: EvidenceOut
    metrics: list[MetricOut]
    absent_metrics: list[AbsentMetricOut] = []


class ErrorOut(BaseModel):
    detail: str


# Calculated values: fixed-point strings ("0.0000000001", never "1E-10" or "-0").
FixedDecimal = Annotated[Decimal, PlainSerializer(lambda d: format(d, "f"), return_type=str)]


class CalculationInputOut(BaseModel):
    """One reported figure used by a calculation, with its WS3 provenance."""

    role: Role
    metric_code: str
    metric_name_vi: str | None
    metric_name_en: str | None
    statement_id: uuid.UUID
    revision: int
    period_end: date
    value: Decimal
    unit: str
    reported_value: Decimal | None
    reported_scale: int | None
    source: MetricSourceOut


class CalculationIssueOut(BaseModel):
    code: ReasonCode
    role: Role
    metric_code: str
    metric_name_vi: str | None
    metric_name_en: str | None
    period_end: date


class CalculatedMetricOut(BaseModel):
    """A ratio computed at read time (WS4-2). Never stored and never verified itself:
    `input_verification` describes its inputs only."""

    code: Literal["roe", "roa"]
    kind: Literal["calculated"] = "calculated"
    formula_id: str
    formula_version: int
    name_vi: str
    name_en: str
    formula_text_vi: str
    formula_text_en: str
    fiscal_year: int
    scope: StatementScope
    period_start: date
    period_end: date
    status: Literal["computed", "not_computable"]
    reason: ReasonCode | None
    value: FixedDecimal | None  # ratio, 10 decimals, half-even
    percent: FixedDecimal | None  # 2 decimals, half-up (WS4-D8)
    denominator_average: FixedDecimal | None  # exact, 7 decimals
    inputs: list[CalculationInputOut]
    issues: list[CalculationIssueOut]
    input_verification: InputVerification | None


class ComparisonSideOut(BaseModel):
    """One period of a comparison: its latest-revision statement and, if reported, the figure."""

    statement_id: uuid.UUID
    fiscal_year: int
    fiscal_quarter: int | None
    period_start: date
    period_end: date
    revision: int
    value: FixedDecimal | None  # None = this statement does not report the metric
    reported_value: FixedDecimal | None
    reported_scale: int | None
    source: MetricSourceOut | None


class ComparisonIssueOut(BaseModel):
    code: ComparisonReason
    side: Side
    metric_code: str
    period_end: date | None  # end of the statement concerned; None when no statement matched


class PeriodComparisonOut(BaseModel):
    """A change between two periods computed at read time (WS4-3). Never stored and never
    verified itself: `input_verification` describes its inputs only."""

    kind: Literal["comparison"] = "comparison"
    type: ComparisonType
    formula_id: str
    formula_version: int
    formula_text_vi: str
    formula_text_en: str
    metric_code: str
    metric_name_vi: str
    metric_name_en: str
    statement_type: StatementType
    scope: StatementScope
    unit: str
    current: ComparisonSideOut
    previous: ComparisonSideOut | None
    status: Status
    reason: ComparisonReason | None
    issues: list[ComparisonIssueOut]
    absolute_change: FixedDecimal | None  # exact, 6 decimals
    growth_value: FixedDecimal | None  # 10 decimals, half-even (W3-D4)
    growth_percent: FixedDecimal | None  # 2 decimals, half-up (W3-D4)
    direction: Direction | None
    input_verification: InputVerification | None


CompanyListItem.model_rebuild()
CompanyOut.model_rebuild()

"""Public response models. Only fields meant for clients; money is serialised as a decimal
string (Pydantic's JSON mode), never as a float."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, computed_field

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


class MetricOut(_Out):
    metric_code: str
    metric_name: str
    value: Decimal  # full units, exact
    unit: str
    reported_value: Decimal | None  # as printed in the document; None for rows from before WS1
    reported_scale: int | None  # 1, 1000 or 1000000; None for rows from before WS1
    source: MetricSourceOut

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metric_name_vi(self) -> str | None:
        """Vietnamese label from the versioned metric dictionary (read-only; never stored)."""
        definition = metric_dictionary().get(self.metric_code)
        return definition.name_vi if definition else None


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


class ErrorOut(BaseModel):
    detail: str

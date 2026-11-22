"""Public response models. Only fields meant for clients; money is serialised as a decimal
string (Pydantic's JSON mode), never as a float."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import (
    CommercialUsageStatus,
    EntityType,
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


class MetricOut(_Out):
    metric_code: str
    metric_name: str
    value: Decimal
    unit: str


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

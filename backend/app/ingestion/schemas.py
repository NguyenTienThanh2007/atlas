"""Input schemas for import bundles. Every field is validated and normalised before any
business rule runs; unknown fields are rejected so typos never pass silently."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from app.ingestion import normalize
from app.models import (
    AccessMethod,
    CommercialUsageStatus,
    ListingStatus,
    SecurityType,
    SourceType,
    StatementScope,
    StatementType,
    VerificationStatus,
)

_Norm = BeforeValidator(normalize.text)
_Code = BeforeValidator(normalize.code)

Text120 = Annotated[str, _Norm, StringConstraints(min_length=1, max_length=120)]
Text200 = Annotated[str, _Norm, StringConstraints(min_length=1, max_length=200)]
Text300 = Annotated[str, _Norm, StringConstraints(min_length=1, max_length=300)]
Text500 = Annotated[str, _Norm, StringConstraints(min_length=1, max_length=500)]
LongText = Annotated[str, _Norm, StringConstraints(min_length=1, max_length=5000)]


Url = Annotated[
    str,
    BeforeValidator(normalize.text),
    StringConstraints(pattern=r"^https?://\S+$", max_length=500),
]
EvidenceUrl = Annotated[
    str,
    BeforeValidator(normalize.text),
    StringConstraints(pattern=r"^(https?|file|fixture)://\S+$", max_length=1000),
]
Ticker = Annotated[str, _Code, StringConstraints(pattern=r"^[A-Z0-9]{2,12}$")]
ExchangeCode = Annotated[str, _Code, StringConstraints(pattern=r"^[A-Z]{2,16}$")]
Currency = Annotated[str, _Code, StringConstraints(pattern=r"^[A-Z]{3}$")]
SectorCode = Annotated[str, _Code, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]{1,31}$")]
TaxCode = Annotated[
    str, BeforeValidator(normalize.tax_code), StringConstraints(pattern=r"^[0-9]{10}(-[0-9]{3})?$")
]
Isin = Annotated[str, _Code, StringConstraints(pattern=r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataSourceIn(_In):
    name: Text200
    source_type: SourceType
    base_url: Url | None = None
    description: LongText
    access_method: AccessMethod
    commercial_usage_status: CommercialUsageStatus
    terms_url: Url | None = None


class EvidenceIn(_In):
    source_url: EvidenceUrl
    document_title: Text500 | None = None
    published_at: AwareDatetime | None = None
    retrieved_at: AwareDatetime
    effective_from: date | None = None
    effective_to: date | None = None
    verification_status: VerificationStatus
    content_hash: Sha256 | None = None
    notes: LongText | None = None

    @model_validator(mode="after")
    def _ranges(self) -> "EvidenceIn":
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to is before effective_from")
        if self.published_at and self.published_at > self.retrieved_at:
            raise ValueError("published_at is after retrieved_at")
        return self


class SecurityIn(_In):
    ticker: Ticker
    exchange_code: ExchangeCode
    security_type: SecurityType
    isin: Isin | None = None
    currency: Currency
    listing_status: ListingStatus
    listed_at: date | None = None
    delisted_at: date | None = None

    @model_validator(mode="after")
    def _dates(self) -> "SecurityIn":
        if (self.listing_status is ListingStatus.DELISTED) != (self.delisted_at is not None):
            raise ValueError("delisted_at must be set exactly when listing_status is 'delisted'")
        if self.listed_at and self.delisted_at and self.delisted_at < self.listed_at:
            raise ValueError("delisted_at is before listed_at")
        return self

    @property
    def key(self) -> str:
        return f"{self.exchange_code}:{self.ticker}"


class CompanyIn(_In):
    legal_name: Text300
    short_name: Text120
    english_name: Text300 | None = None
    tax_code: TaxCode | None = None
    description: LongText | None = None
    website: Url | None = None
    sector_code: SectorCode
    securities: list[SecurityIn] = Field(min_length=1)
    evidence: list[EvidenceIn] = Field(min_length=1)  # no evidence, no record

    @model_validator(mode="after")
    def _unique_securities(self) -> "CompanyIn":
        keys = [s.key for s in self.securities]
        if len(keys) != len(set(keys)):
            raise ValueError("a security is listed twice in this company record")
        return self

    @property
    def key(self) -> str:
        return f"tax:{self.tax_code}" if self.tax_code else self.securities[0].key


class MetricIn(_In):
    code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,63}$")]
    # The value exactly as printed in the document, in the statement's declared amount_scale.
    # Strings or JSON numbers parsed as Decimal by the connector; floats/NaN/Infinity rejected.
    value: Annotated[Decimal, Field(allow_inf_nan=False, max_digits=38, decimal_places=6)]
    # Page of the statement's source document; required for real figures (importer + DB).
    source_page: Annotated[int, Field(ge=1, le=100_000)] | None = None


# Statement currencies ATLAS can import today. Extending this list needs scale names for the
# new currency too, so nothing is ever guessed.
STATEMENT_CURRENCIES = frozenset({"VND"})
# How a document prints its amounts. The names are exact; anything else is rejected.
AMOUNT_SCALES: dict[str, int] = {"dong": 1, "nghin_dong": 1_000, "trieu_dong": 1_000_000}
QUARTER_DAYS = (80, 100)  # inclusive length of a quarterly flow period
ANNUAL_DAYS = (360, 371)  # inclusive length of an annual flow period


class CompanyRef(_In):
    exchange_code: ExchangeCode
    ticker: Ticker


class FinancialStatementIn(_In):
    company: CompanyRef
    reporting_period_start: date
    reporting_period_end: date
    fiscal_year: Annotated[int, Field(ge=1990, le=2200)]
    fiscal_quarter: Annotated[int, Field(ge=1, le=4)] | None = None
    statement_type: StatementType
    scope: StatementScope
    currency: Currency
    # Required: the scale the document prints currency amounts in (no default, no guessing).
    amount_scale: Literal["dong", "nghin_dong", "trieu_dong"]
    publication_date: date | None = None
    revision: Annotated[int, Field(ge=1)] = 1
    evidence: EvidenceIn
    metrics: list[MetricIn] = Field(min_length=1)

    @model_validator(mode="after")
    def _checks(self) -> "FinancialStatementIn":
        start, end = self.reporting_period_start, self.reporting_period_end
        if end < start:
            raise ValueError("reporting_period_end is before reporting_period_start")
        if self.currency not in STATEMENT_CURRENCIES:
            raise ValueError(f"currency {self.currency} is not supported for statements")
        codes = [m.code for m in self.metrics]
        if len(codes) != len(set(codes)):
            raise ValueError("a metric code appears twice in this statement")
        _check_period(self.statement_type, self.fiscal_year, self.fiscal_quarter, start, end)
        return self

    @property
    def key(self) -> str:
        q = f"Q{self.fiscal_quarter}" if self.fiscal_quarter else "FY"
        return (
            f"{self.company.exchange_code}:{self.company.ticker}:{self.statement_type}:"
            f"{self.scope}:{self.fiscal_year}{q}:{self.reporting_period_end}:r{self.revision}"
        )


def _check_period(
    statement_type: StatementType, fiscal_year: int, quarter: int | None, start: date, end: date
) -> None:
    """Period rules (docs/VERIFICATION_WORKFLOW.md, "Reporting periods").

    The fiscal year is named after the calendar year it ends in, so non-calendar years work:
    an annual period ends in `fiscal_year`; a quarter ends in `fiscal_year` or the year before.
    A balance sheet is a position at one date; income and cash-flow statements cover a span.
    """
    if quarter is None and end.year != fiscal_year:
        raise ValueError(f"an annual period ending {end} belongs to fiscal year {end.year}")
    if quarter is not None and end.year not in (fiscal_year - 1, fiscal_year):
        raise ValueError(f"a quarter ending {end} cannot belong to fiscal year {fiscal_year}")
    if statement_type is StatementType.BALANCE_SHEET:
        if start != end:
            raise ValueError(
                "a balance sheet is at one date: reporting_period_start must equal end"
            )
        return
    days = (end - start + timedelta(days=1)).days
    low, high = ANNUAL_DAYS if quarter is None else QUARTER_DAYS
    if not low <= days <= high:
        kind = "an annual" if quarter is None else "a quarterly"
        raise ValueError(f"{kind} period must span {low}-{high} days, not {days}")


class BundleIn(_In):
    """Top level only: records stay raw dicts so one bad record never rejects the bundle."""

    schema_version: Literal["1"]
    data_source: DataSourceIn
    companies: list[dict[str, Any]] = []
    financial_statements: list[dict[str, Any]] = []


def describe_error(exc: Exception) -> str:
    """One-line, actionable description of a parse or validation failure."""
    if isinstance(exc, ValidationError):
        parts = [
            f"{'.'.join(str(p) for p in e['loc']) or '(root)'}: {e['msg']}" for e in exc.errors()
        ]
        return "; ".join(parts)[:2000]
    return str(exc)[:2000]

"""Import job for company / security / evidence / financial-statement bundles.

Rules:
- Every record is validated on its own; a bad record is reported, the rest still import.
- Each record is applied in a SAVEPOINT: it lands completely or not at all.
- Existing data is never overwritten. A record that disagrees with stored data is a conflict.
  Restated financials must arrive as revision N+1 of an existing revision N.
- Re-running the same bundle changes nothing (idempotent).
- Sample-fixture data and real data never mix.
- Imports never verify anything: real evidence arrives `unverified`, fixture evidence `sample`.
  Only a two-person review (`python -m app.ingestion review`) changes that.
- Figures are stored in full units: value = reported value x the statement's amount_scale,
  exactly; the as-reported value, scale and source page are kept with each figure.
"""

import uuid
from dataclasses import dataclass
from decimal import Context, Decimal, Inexact
from typing import Any

from pydantic import ValidationError
from sqlalchemy import and_, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.calculations.applicability import company_kind, effective
from app.ingestion.connectors import InputError, RawInput, parse_json
from app.ingestion.reference import metric_dictionary
from app.ingestion.runs import RunRecorder
from app.ingestion.schemas import (
    AMOUNT_SCALES,
    BundleIn,
    CompanyIn,
    DataSourceIn,
    EvidenceIn,
    FinancialStatementIn,
    describe_error,
)
from app.models import (
    Company,
    DataSource,
    EntityType,
    Evidence,
    Exchange,
    FinancialMetric,
    FinancialStatement,
    IngestionRun,
    Sector,
    Security,
    SourceType,
    VerificationStatus,
)

JOB_NAME = "import_bundle"


class _Rejected(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass
class _Ctx:
    session: Session
    rec: RunRecorder
    source: DataSource
    exchanges: dict[str, Exchange]
    sectors: dict[str, Sector]

    @property
    def is_sample(self) -> bool:
        return self.source.source_type is SourceType.SAMPLE_FIXTURE


def import_bundle(session: Session, raw: RawInput) -> IngestionRun:
    """Apply one bundle. The caller owns the transaction (commit/rollback)."""
    rec = RunRecorder(session, JOB_NAME, raw)
    try:
        bundle = BundleIn.model_validate(parse_json(raw))
    except (InputError, ValidationError) as exc:
        rec.issue("fatal", "bundle", describe_error(exc))
        return rec.finish()

    source = _resolve_source(session, bundle.data_source, rec)
    if source is None:
        return rec.finish()
    rec.run.data_source_id = source.id

    ctx = _Ctx(
        session=session,
        rec=rec,
        source=source,
        exchanges={e.code: e for e in session.scalars(select(Exchange))},
        sectors={s.code: s for s in session.scalars(select(Sector))},
    )
    _each(ctx, "companies", bundle.companies, CompanyIn, _apply_company)
    _each(
        ctx,
        "financial_statements",
        bundle.financial_statements,
        FinancialStatementIn,
        _apply_statement,
    )
    return rec.finish()


def _each(ctx: _Ctx, section: str, records: list[dict[str, Any]], model: Any, apply: Any) -> None:
    seen: set[str] = set()
    for i, raw_record in enumerate(records):
        label = f"{section}[{i}]"
        ctx.rec.counts[f"{section}.seen"] += 1
        try:
            record = model.model_validate(raw_record)
        except ValidationError as exc:
            ctx.rec.issue("invalid", label, describe_error(exc))
            continue
        if record.key in seen:
            ctx.rec.issue(
                "duplicate", label, "same record appears earlier in this bundle", record.key
            )
            continue
        seen.add(record.key)
        savepoint = ctx.session.begin_nested()
        try:
            outcome = apply(ctx, record)
        except _Rejected as exc:
            savepoint.rollback()
            ctx.rec.issue(exc.kind, label, str(exc), record.key)  # type: ignore[arg-type]
            continue
        except IntegrityError as exc:
            # A constraint the validators did not foresee (or a concurrent import): reject
            # this record only, naming the constraint, never the raw SQL or parameters.
            savepoint.rollback()
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            ctx.rec.issue("conflict", label, f"database rejected record ({constraint})", record.key)
            continue
        savepoint.commit()
        ctx.rec.counts[f"{section}.{outcome}"] += 1


def _resolve_source(session: Session, src: DataSourceIn, rec: RunRecorder) -> DataSource | None:
    row = session.scalar(select(DataSource).where(DataSource.name == src.name))
    if row is None:
        row = DataSource(**src.model_dump())
        session.add(row)
        session.flush()
        rec.counts["data_sources.created"] += 1
        return row
    stored = {k: getattr(row, k) for k in DataSourceIn.model_fields}
    if stored != src.model_dump():
        # Licensing/usage terms must never change silently through an import.
        rec.issue(
            "fatal",
            "data_source",
            "differs from the stored data source; update it deliberately, not through an import",
            src.name,
        )
        return None
    return row


# ---------------------------------------------------------------- evidence


def _check_evidence(ctx: _Ctx, items: list[EvidenceIn]) -> None:
    expected = VerificationStatus.SAMPLE if ctx.is_sample else VerificationStatus.UNVERIFIED
    for ev in items:
        if ev.verification_status is not expected:
            raise _Rejected(
                "invalid",
                f"imported evidence must be '{expected}' (sample-fixture sources use 'sample', "
                "real sources 'unverified'); verification happens only through a review",
            )


def _add_evidence(
    ctx: _Ctx, ev: EvidenceIn, entity_type: EntityType, entity_id: uuid.UUID
) -> Evidence | None:
    """Insert unless the same evidence (source, entity, URL, retrieval time) already exists."""
    exists = ctx.session.scalar(
        select(Evidence.id).where(
            Evidence.data_source_id == ctx.source.id,
            Evidence.entity_type == entity_type,
            Evidence.entity_id == entity_id,
            Evidence.source_url == ev.source_url,
            Evidence.retrieved_at == ev.retrieved_at,
        )
    )
    if exists:
        return None
    row = Evidence(
        data_source_id=ctx.source.id,
        entity_type=entity_type,
        entity_id=entity_id,
        **ev.model_dump(),
    )
    ctx.session.add(row)
    ctx.rec.counts["evidence.created"] += 1
    return row


# ---------------------------------------------------------------- companies

_COMPANY_FIELDS = ("legal_name", "short_name", "english_name", "tax_code", "description", "website")
_SECURITY_FIELDS = (
    "security_type",
    "isin",
    "currency",
    "listing_status",
    "listed_at",
    "delisted_at",
)


def _diff(row: object, incoming: dict[str, Any]) -> list[str]:
    return [
        f"{k}: stored={getattr(row, k)!r} incoming={v!r}"
        for k, v in incoming.items()
        if getattr(row, k) != v
    ]


def _apply_company(ctx: _Ctx, c: CompanyIn) -> str:
    _check_evidence(ctx, c.evidence)
    sector = ctx.sectors.get(c.sector_code)
    if sector is None:
        raise _Rejected("missing_reference", f"unknown sector_code {c.sector_code}")
    for s in c.securities:
        if s.exchange_code not in ctx.exchanges:
            raise _Rejected("missing_reference", f"unknown exchange_code {s.exchange_code}")

    # Identify the company by tax code and by every (exchange, ticker) it lists.
    sec_filters = [
        (Security.exchange_id == ctx.exchanges[s.exchange_code].id) & (Security.ticker == s.ticker)
        for s in c.securities
    ]
    existing_secs = list(ctx.session.scalars(select(Security).where(or_(*sec_filters))))
    candidate_ids = {s.company_id for s in existing_secs}
    if c.tax_code:
        by_tax = ctx.session.scalar(select(Company.id).where(Company.tax_code == c.tax_code))
        if by_tax:
            candidate_ids.add(by_tax)
    if len(candidate_ids) > 1:
        raise _Rejected("conflict", "tax code and tickers match different stored companies")

    company_fields = {k: getattr(c, k) for k in _COMPANY_FIELDS}

    if not candidate_ids:
        company = Company(
            sector_id=sector.id,
            is_sample=ctx.is_sample,
            **company_fields,
        )
        ctx.session.add(company)
        ctx.session.flush()
        outcome = "created"
    else:
        company = ctx.session.get_one(Company, candidate_ids.pop())
        problems = _diff(company, company_fields)
        if company.sector_id != sector.id:
            problems.append(f"sector: incoming={c.sector_code}")
        if company.is_sample != ctx.is_sample:
            problems.append("sample and real data cannot be merged")
        if problems:
            raise _Rejected("conflict", "; ".join(problems))
        outcome = "unchanged"

    for s in c.securities:
        sec_fields = {k: getattr(s, k) for k in _SECURITY_FIELDS}
        exchange = ctx.exchanges[s.exchange_code]
        match = [x for x in existing_secs if x.exchange_id == exchange.id and x.ticker == s.ticker]
        if not match:
            ctx.session.add(
                Security(
                    company_id=company.id,
                    exchange_id=exchange.id,
                    ticker=s.ticker,
                    **sec_fields,
                )
            )
            ctx.rec.counts["securities.created"] += 1
            continue
        # Several historical rows may share a ticker; it must equal one of them exactly.
        if not any(not _diff(x, sec_fields) for x in match):
            raise _Rejected("conflict", f"{s.key}: " + "; ".join(_diff(match[0], sec_fields)))

    for ev in c.evidence:
        _add_evidence(ctx, ev, EntityType.COMPANY, company.id)
    ctx.session.flush()
    return outcome


# ---------------------------------------------------------------- financial statements

# NUMERIC(38,6) holds at most 32 integer digits.
_MAX_ABS_VALUE = Decimal(10) ** 32
# Python's default decimal context keeps 28 digits and would round; this one is wide enough
# for 38-digit values times 10^6 and raises instead of rounding.
_EXACT = Context(prec=60, traps=[Inexact])


@dataclass(frozen=True)
class _Figure:
    code: str
    value: Decimal  # full units
    reported_value: Decimal
    reported_scale: int
    source_page: int | None


def _figures(ctx: _Ctx, s: FinancialStatementIn) -> list[_Figure]:
    """Validate metrics and convert to full units. Only currency amounts are scaled: per-share
    figures and share counts are printed in units in Vietnamese statements."""
    dictionary = metric_dictionary()
    scale = AMOUNT_SCALES[s.amount_scale]
    out = []
    for m in s.metrics:
        definition = dictionary.get(m.code)
        if definition is None:
            raise _Rejected("invalid", f"metric {m.code} is not in the metric dictionary")
        if definition.statement_type is not s.statement_type:
            raise _Rejected("invalid", f"metric {m.code} belongs to {definition.statement_type}")
        if m.source_page is None and not ctx.is_sample:
            raise _Rejected("invalid", f"metric {m.code}: real figures need a source_page")
        figure_scale = scale if definition.unit == "currency" else 1
        value = _EXACT.multiply(m.value, figure_scale)
        if value.copy_abs() >= _MAX_ABS_VALUE:  # abs() would round to 28 digits
            raise _Rejected("invalid", f"metric {m.code}: {value} is too large to store exactly")
        out.append(_Figure(m.code, value, m.value, figure_scale, m.source_page))
    return out


def _overlapping(ctx: _Ctx, company_id: uuid.UUID, s: FinancialStatementIn) -> str | None:
    """A different statement of the same company, type, scope and granularity (annual vs
    quarterly) whose period overlaps this one. Revisions of the same statement don't count, and
    annual and quarterly statements may cover the same months."""
    granularity = (
        FinancialStatement.fiscal_quarter.is_(None)
        if s.fiscal_quarter is None
        else FinancialStatement.fiscal_quarter.is_not(None)
    )
    same_statement = and_(
        FinancialStatement.fiscal_year == s.fiscal_year,
        FinancialStatement.fiscal_quarter.is_not_distinct_from(s.fiscal_quarter),
        FinancialStatement.reporting_period_end == s.reporting_period_end,
    )
    other = ctx.session.scalar(
        select(FinancialStatement).where(
            FinancialStatement.company_id == company_id,
            FinancialStatement.statement_type == s.statement_type,
            FinancialStatement.scope == s.scope,
            granularity,
            FinancialStatement.reporting_period_start <= s.reporting_period_end,
            FinancialStatement.reporting_period_end >= s.reporting_period_start,
            not_(same_statement),
        )
    )
    if other is None:
        return None
    q = f"Q{other.fiscal_quarter}" if other.fiscal_quarter else "FY"
    return (
        f"period {s.reporting_period_start}..{s.reporting_period_end} overlaps the stored "
        f"{other.fiscal_year}{q} statement {other.reporting_period_start}.."
        f"{other.reporting_period_end}"
    )


def _apply_statement(ctx: _Ctx, s: FinancialStatementIn) -> str:
    _check_evidence(ctx, [s.evidence])
    figures = _figures(ctx, s)
    dictionary = metric_dictionary()

    exchange = ctx.exchanges.get(s.company.exchange_code)
    company = None
    if exchange is not None:
        company = ctx.session.scalar(
            select(Company)
            .join(Security, Security.company_id == Company.id)
            .where(Security.exchange_id == exchange.id, Security.ticker == s.company.ticker)
            .order_by(Security.listing_status == "delisted")  # prefer the active listing
            .limit(1)
        )
    if company is None:
        raise _Rejected(
            "missing_reference",
            f"no company listed as {s.company.exchange_code}:"
            f"{s.company.ticker}; import the company first",
        )
    if company.is_sample != ctx.is_sample:
        raise _Rejected("invalid", "sample and real data cannot be mixed")

    def identity(revision: int) -> Any:
        return select(FinancialStatement).where(
            FinancialStatement.company_id == company.id,
            FinancialStatement.statement_type == s.statement_type,
            FinancialStatement.scope == s.scope,
            FinancialStatement.fiscal_year == s.fiscal_year,
            FinancialStatement.fiscal_quarter.is_not_distinct_from(s.fiscal_quarter),
            FinancialStatement.reporting_period_end == s.reporting_period_end,
            FinancialStatement.revision == revision,
        )

    existing = ctx.session.scalar(
        identity(s.revision).options(selectinload(FinancialStatement.metrics))
    )
    incoming_values = {
        f.code: (f.value, f.reported_value, f.reported_scale, f.source_page) for f in figures
    }
    if existing is not None:
        stored_values = {
            m.metric_code: (m.value, m.reported_value, m.reported_scale, m.source_page)
            for m in existing.metrics
        }
        same = (
            stored_values == incoming_values
            and existing.reporting_period_start == s.reporting_period_start
            and existing.currency == s.currency
            and existing.publication_date == s.publication_date
        )
        if not same:
            raise _Rejected(
                "conflict",
                f"revision {s.revision} already stored with different "
                f"values; submit a restatement as revision {s.revision + 1}",
            )
        return "unchanged"

    overlap = _overlapping(ctx, company.id, s)
    if overlap:
        raise _Rejected("conflict", overlap)
    # WS4-4-D4: no new figure for a metric the dictionary says does not apply to the company's
    # reviewed kind. Statements stored before the classification are kept (append-only).
    kind = company_kind(ctx.session, company.id)
    not_applicable = [
        f.code for f in figures if effective(kind, dictionary[f.code]) == "not_applicable"
    ]
    if not_applicable:
        raise _Rejected(
            "invalid",
            f"metric {', '.join(not_applicable)} does not apply to a company classified "
            f"{kind.value if kind else 'unclassified'} (metric dictionary applicability)",
        )

    previous = None
    if s.revision > 1:
        previous = ctx.session.scalar(identity(s.revision - 1))
        if previous is None:
            raise _Rejected(
                "missing_reference",
                f"revision {s.revision} needs revision {s.revision - 1} stored first",
            )

    statement_id = uuid.uuid4()
    evidence = _add_evidence(ctx, s.evidence, EntityType.FINANCIAL_STATEMENT, statement_id)
    if evidence is None:  # impossible: a brand-new statement id cannot have evidence yet
        raise RuntimeError("evidence for a new statement unexpectedly exists")
    ctx.session.flush()
    ctx.session.add(
        FinancialStatement(
            id=statement_id,
            company_id=company.id,
            reporting_period_start=s.reporting_period_start,
            reporting_period_end=s.reporting_period_end,
            fiscal_year=s.fiscal_year,
            fiscal_quarter=s.fiscal_quarter,
            statement_type=s.statement_type,
            scope=s.scope,
            currency=s.currency,
            publication_date=s.publication_date,
            revision=s.revision,
            supersedes_id=previous.id if previous else None,
            source_evidence_id=evidence.id,
        )
    )
    ctx.session.flush()
    units = {
        "currency": s.currency,
        "currency_per_share": f"{s.currency}/share",
        "shares": "shares",
    }
    ctx.session.add_all(
        FinancialMetric(
            financial_statement_id=statement_id,
            metric_code=f.code,
            metric_name=dictionary[f.code].name,
            value=f.value,
            unit=units[dictionary[f.code].unit],
            source_page=f.source_page,
            reported_value=f.reported_value,
            reported_scale=f.reported_scale,
        )
        for f in figures
    )
    ctx.session.flush()
    return "created"

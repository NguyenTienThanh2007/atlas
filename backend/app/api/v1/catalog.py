"""Read-only catalogue API: sectors, exchanges, companies, securities, evidence, financials.

Every list is paginated with a deterministic order (ties broken by id). Related rows are
eager-loaded in a fixed number of queries per request (no N+1)."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload, selectinload

from app.api.v1.schemas import (
    CompanyListItem,
    CompanyOut,
    ErrorOut,
    EvidenceOut,
    ExchangeOut,
    FinancialStatementOut,
    MetricOut,
    MetricSourceOut,
    Page,
    SectorOut,
    SecurityDetailOut,
)
from app.db import get_session
from app.ingestion.reference import MetricDictionary, metric_dictionary_document
from app.models import (
    Company,
    EntityType,
    Evidence,
    Exchange,
    FinancialStatement,
    ListingStatus,
    Sector,
    Security,
    StatementScope,
    StatementType,
)

router = APIRouter()
DB = Annotated[Session, Depends(get_session)]
Limit = Annotated[int, Query(ge=1, le=100, description="Page size")]
Offset = Annotated[int, Query(ge=0, le=100_000, description="Rows to skip")]
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut, "description": "Not found"}}


def _page[T](db: Session, stmt: Select[Any], limit: int, offset: int, out: type[T]) -> Page[T]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).unique().all()
    return Page[out](  # type: ignore[valid-type]
        items=[out.model_validate(r) for r in rows],  # type: ignore[attr-defined]
        total=total,
        limit=limit,
        offset=offset,
    )


def _like(term: str) -> str:
    """Treat user input literally inside ILIKE: escape the wildcard characters."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _company_or_404(db: Session, company_id: uuid.UUID) -> None:
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")


# ---------------------------------------------------------------- exchanges & sectors


@router.get("/metric-dictionary", response_model=MetricDictionary, tags=["reference"])
def get_metric_dictionary() -> MetricDictionary:
    """The versioned metric dictionary: names, definitions (vi/en), statement type, unit and
    bank / non-bank applicability. A small fixed reference document, so not paginated."""
    return metric_dictionary_document()


@router.get("/exchanges", response_model=Page[ExchangeOut], tags=["reference"])
def list_exchanges(db: DB, limit: Limit = 50, offset: Offset = 0) -> Page[ExchangeOut]:
    return _page(
        db, select(Exchange).order_by(Exchange.code, Exchange.id), limit, offset, ExchangeOut
    )


_company_count = (
    select(func.count(Company.id)).where(Company.sector_id == Sector.id).scalar_subquery()
)


@router.get("/sectors", response_model=Page[SectorOut], tags=["reference"])
def list_sectors(db: DB, limit: Limit = 50, offset: Offset = 0) -> Page[SectorOut]:
    total = db.scalar(select(func.count()).select_from(Sector)) or 0
    rows = db.execute(
        select(Sector, _company_count).order_by(Sector.code, Sector.id).limit(limit).offset(offset)
    ).all()
    return Page[SectorOut](
        items=[_sector(s, n) for s, n in rows], total=total, limit=limit, offset=offset
    )


@router.get(
    "/sectors/{sector_id}", response_model=SectorOut, responses=NOT_FOUND, tags=["reference"]
)
def get_sector(sector_id: uuid.UUID, db: DB) -> SectorOut:
    row = db.execute(select(Sector, _company_count).where(Sector.id == sector_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Sector not found")
    return _sector(*row)


def _sector(sector: Sector, count: int) -> SectorOut:
    return SectorOut(
        id=sector.id,
        code=sector.code,
        name=sector.name,
        name_vi=sector.name_vi,
        description=sector.description,
        taxonomy_version=sector.taxonomy_version,
        parent_sector_id=sector.parent_sector_id,
        company_count=count,
    )


# ---------------------------------------------------------------- companies & securities

_SECURITIES = selectinload(Company.securities).joinedload(Security.exchange)


@router.get("/companies", response_model=Page[CompanyListItem], tags=["companies"])
def list_companies(
    db: DB,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=100, description="Ticker or company name (substring)"),
    ] = None,
    sector: Annotated[
        str | None, Query(pattern=r"^[A-Z][A-Z0-9_]{1,31}$", description="Sector code")
    ] = None,
    exchange: Annotated[
        str | None,
        Query(pattern=r"^[A-Z]{2,16}$", description="Exchange code (active listings only)"),
    ] = None,
    limit: Limit = 20,
    offset: Offset = 0,
) -> Page[CompanyListItem]:
    stmt = (
        select(Company)
        .options(joinedload(Company.sector), _SECURITIES)
        .order_by(Company.short_name, Company.id)
    )
    if q and q.strip():
        term = _like(q.strip())
        ticker_match = exists().where(
            Security.company_id == Company.id, Security.ticker.ilike(term, escape="\\")
        )
        stmt = stmt.where(
            or_(
                Company.short_name.ilike(term, escape="\\"),
                Company.legal_name.ilike(term, escape="\\"),
                Company.english_name.ilike(term, escape="\\"),
                ticker_match,
            )
        )
    if sector:
        stmt = stmt.where(Company.sector.has(Sector.code == sector))
    if exchange:
        listing = aliased(Security)
        stmt = stmt.where(
            exists().where(
                listing.company_id == Company.id,
                listing.listing_status != ListingStatus.DELISTED,
                listing.exchange.has(Exchange.code == exchange),
            )
        )
    return _page(db, stmt, limit, offset, CompanyListItem)


@router.get(
    "/companies/{company_id}", response_model=CompanyOut, responses=NOT_FOUND, tags=["companies"]
)
def get_company(company_id: uuid.UUID, db: DB) -> CompanyOut:
    company = db.scalars(
        select(Company)
        .where(Company.id == company_id)
        .options(joinedload(Company.sector), _SECURITIES)
    ).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(company)


@router.get(
    "/securities/{security_id}",
    response_model=SecurityDetailOut,
    responses=NOT_FOUND,
    tags=["companies"],
)
def get_security(security_id: uuid.UUID, db: DB) -> SecurityDetailOut:
    security = db.scalars(
        select(Security)
        .where(Security.id == security_id)
        .options(joinedload(Security.exchange), joinedload(Security.company))
    ).first()
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found")
    return SecurityDetailOut.model_validate(security)


@router.get(
    "/companies/{company_id}/evidence",
    response_model=Page[EvidenceOut],
    responses=NOT_FOUND,
    tags=["companies"],
)
def list_company_evidence(
    company_id: uuid.UUID, db: DB, limit: Limit = 50, offset: Offset = 0
) -> Page[EvidenceOut]:
    """Evidence for the company record and for each of its securities, newest first."""
    _company_or_404(db, company_id)
    security_ids = select(Security.id).where(Security.company_id == company_id)
    stmt = (
        select(Evidence)
        .where(
            or_(
                and_(Evidence.entity_type == EntityType.COMPANY, Evidence.entity_id == company_id),
                and_(
                    Evidence.entity_type == EntityType.SECURITY,
                    Evidence.entity_id.in_(security_ids),
                ),
            )
        )
        .options(joinedload(Evidence.data_source))
        .order_by(Evidence.retrieved_at.desc(), Evidence.id)
    )
    return _page(db, stmt, limit, offset, EvidenceOut)


@router.get(
    "/companies/{company_id}/financial-statements",
    response_model=Page[FinancialStatementOut],
    responses=NOT_FOUND,
    tags=["companies"],
)
def list_financial_statements(
    company_id: uuid.UUID,
    db: DB,
    fiscal_year: Annotated[int | None, Query(ge=1990, le=2200)] = None,
    statement_type: StatementType | None = None,
    scope: StatementScope | None = None,
    include_superseded: Annotated[
        bool, Query(description="Include revisions replaced by a restatement")
    ] = False,
    limit: Limit = 20,
    offset: Offset = 0,
) -> Page[FinancialStatementOut]:
    _company_or_404(db, company_id)
    newer = aliased(FinancialStatement)
    superseded = exists().where(newer.supersedes_id == FinancialStatement.id)
    stmt = select(FinancialStatement, superseded.label("is_superseded")).where(
        FinancialStatement.company_id == company_id
    )
    if not include_superseded:
        stmt = stmt.where(~superseded)
    if fiscal_year is not None:
        stmt = stmt.where(FinancialStatement.fiscal_year == fiscal_year)
    if statement_type is not None:
        stmt = stmt.where(FinancialStatement.statement_type == statement_type)
    if scope is not None:
        stmt = stmt.where(FinancialStatement.scope == scope)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.options(
            selectinload(FinancialStatement.metrics),
            joinedload(FinancialStatement.source_evidence).joinedload(Evidence.data_source),
        )
        .order_by(
            FinancialStatement.reporting_period_end.desc(),
            FinancialStatement.statement_type,
            FinancialStatement.scope,
            FinancialStatement.fiscal_quarter.asc().nulls_first(),  # full year before quarters
            FinancialStatement.revision.desc(),
            FinancialStatement.id,
        )
        .limit(limit)
        .offset(offset)
    ).all()
    items = [
        FinancialStatementOut(
            id=s.id,
            reporting_period_start=s.reporting_period_start,
            reporting_period_end=s.reporting_period_end,
            fiscal_year=s.fiscal_year,
            fiscal_quarter=s.fiscal_quarter,
            statement_type=s.statement_type,
            scope=s.scope,
            currency=s.currency,
            publication_date=s.publication_date,
            revision=s.revision,
            supersedes_id=s.supersedes_id,
            is_superseded=flag,
            source_evidence=EvidenceOut.model_validate(s.source_evidence),
            metrics=[
                MetricOut(
                    metric_code=m.metric_code,
                    metric_name=m.metric_name,
                    value=m.value,
                    unit=m.unit,
                    reported_value=m.reported_value,
                    reported_scale=m.reported_scale,
                    source=MetricSourceOut.for_figure(s.source_evidence, m.source_page),
                )
                for m in s.metrics
            ],
        )
        for s, flag in rows
    ]
    return Page[FinancialStatementOut](items=items, total=total, limit=limit, offset=offset)

"""WS4-3: pair each latest statement with its previous period and compare every reported metric.
Read-only; never writes or caches. Design: docs/WS4_3_IMPLEMENTATION_PLAN.md §12.3."""

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.calculations.comparisons import (
    ComparisonType,
    Issue,
    Outcome,
    Period,
    Value,
    compare,
    match,
)
from app.calculations.service import company_mixed, latest_statements
from app.ingestion.reference import metric_dictionary
from app.models import (
    Company,
    FinancialMetric,
    FinancialStatement,
    StatementScope,
    StatementType,
)

TYPE_ORDER = {
    StatementType.INCOME_STATEMENT: 0,
    StatementType.BALANCE_SHEET: 1,
    StatementType.CASH_FLOW: 2,
}
SCOPE_ORDER = {StatementScope.CONSOLIDATED: 0, StatementScope.SEPARATE: 1}


@dataclass(frozen=True)
class Row:
    metric_code: str
    unit: str  # of the reported figure(s)
    current: FinancialStatement
    current_metric: FinancialMetric | None
    previous: FinancialStatement | None  # shown also for period_mismatch, never used then
    previous_metric: FinancialMetric | None
    outcome: Outcome


def period(s: FinancialStatement) -> Period:
    return Period(
        s.fiscal_year,
        s.fiscal_quarter,
        s.reporting_period_start,
        s.reporting_period_end,
        s.statement_type is StatementType.BALANCE_SHEET,
    )


def _value(s: FinancialStatement, m: FinancialMetric | None) -> Value | None:
    if m is None:
        return None
    return Value(
        m.value, m.unit, s.currency, s.source_evidence.verification_status, s.reporting_period_end
    )


def comparisons(
    db: Session,
    company_id: uuid.UUID,
    kind: ComparisonType,
    scope: StatementScope | None = None,
    metric: str | None = None,
    fiscal_year: int | None = None,
) -> list[Row]:
    """Every comparison row of one company and type, newest period first.

    shortcut: builds all rows of the company in memory before the caller pages them; fine for
    one company's statements (hundreds at most), revisit if a request ever spans companies."""
    company = db.get(Company, company_id)
    if company is None:
        return []
    mixed = company_mixed(db, company_id, company.is_sample)
    dictionary = metric_dictionary()
    order = {code: i for i, code in enumerate(dictionary)}
    groups: dict[tuple[StatementType, StatementScope], list[FinancialStatement]] = defaultdict(list)
    for s in latest_statements(db, company_id, quarterly=kind != "annual_yoy"):
        groups[(s.statement_type, s.scope)].append(s)

    currents = sorted(
        (
            s
            for group in groups.values()
            for s in group
            if (scope is None or s.scope is scope)
            and (fiscal_year is None or s.fiscal_year == fiscal_year)
        ),
        key=lambda s: (
            -s.reporting_period_end.toordinal(),
            TYPE_ORDER[s.statement_type],
            SCOPE_ORDER[s.scope],
        ),
    )
    rows: list[Row] = []
    for current in currents:
        pool = [s for s in groups[(current.statement_type, current.scope)] if s is not current]
        matched = match(kind, period(current), pool, period)
        previous, problem = matched
        used = previous if problem is None else None
        now = {m.metric_code: m for m in current.metrics}
        before = {m.metric_code: m for m in used.metrics} if used else {}
        codes = sorted((set(now) | set(before)) & set(order), key=order.__getitem__)
        for code in codes if metric is None else [c for c in codes if c == metric]:
            cm, pm = now.get(code), before.get(code)
            figure = cm or pm
            if figure is None:  # impossible: the code comes from one of the two statements
                continue
            issues: list[Issue] = []
            if cm is None:
                issues.append(
                    Issue("missing_current_value", "current", code, current.reporting_period_end)
                )
            if problem is not None:
                end = previous.reporting_period_end if previous else None
                issues.append(Issue(problem, "previous", code, end))
            elif used is not None and pm is None:
                issues.append(
                    Issue("missing_previous_value", "previous", code, used.reporting_period_end)
                )
            outcome = compare(
                code,
                _value(current, cm),
                _value(used, pm) if used else None,
                issues,
                currency_metric=dictionary[code].unit == "currency",
                company_is_sample=company.is_sample,
                company_mixed=mixed,
            )
            rows.append(Row(code, figure.unit, current, cm, previous, pm, outcome))
    return rows

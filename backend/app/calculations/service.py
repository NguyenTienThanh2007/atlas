"""WS4-2: select the inputs of ROE and ROA for one company. Read-only; never writes or caches.

Matching rules: docs/WS4_2_IMPLEMENTATION_PLAN.md §4 (owner-approved design, 2026-11-25)."""

import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, aliased, joinedload, selectinload

from app.calculations.ratios import Figure, Formula, Issue, Outcome, Role, compute, formulas_for
from app.models import (
    Company,
    Evidence,
    FinancialMetric,
    FinancialStatement,
    StatementScope,
    StatementType,
    VerificationStatus,
)

OPENING_WINDOW = timedelta(days=7)  # approved period-end alignment rule (WS4 plan §4.3)


@dataclass(frozen=True)
class Input:
    role: Role
    statement: FinancialStatement
    metric: FinancialMetric


@dataclass(frozen=True)
class Result:
    formula: Formula
    income_statement: FinancialStatement
    inputs: tuple[Input, ...]
    outcome: Outcome


def latest_statements(
    db: Session, company_id: uuid.UUID, *, quarterly: bool
) -> list[FinancialStatement]:
    """Latest revisions of one granularity's statements (every type), with figures and evidence.
    A revision replaced by a newer one is never returned, whatever the newer one's status."""
    newer = aliased(FinancialStatement)
    superseded = exists().where(newer.supersedes_id == FinancialStatement.id)
    quarter = FinancialStatement.fiscal_quarter
    return list(
        db.scalars(
            select(FinancialStatement)
            .where(
                FinancialStatement.company_id == company_id,
                quarter.is_not(None) if quarterly else quarter.is_(None),
                ~superseded,
            )
            .options(
                selectinload(FinancialStatement.metrics),
                joinedload(FinancialStatement.source_evidence),
            )
        ).unique()
    )


def _metric(statement: FinancialStatement, code: str) -> FinancialMetric | None:
    return next((m for m in statement.metrics if m.metric_code == code), None)


def company_mixed(db: Session, company_id: uuid.UUID, is_sample: bool) -> bool:
    """True when any statement of the company (any type, granularity or revision) has evidence of
    the other classification. The database refuses such rows since migration 8de09b58f4c2; this
    is the independent check of the calculation engine (audit AU-3)."""
    other = (
        Evidence.verification_status != VerificationStatus.SAMPLE
        if is_sample
        else Evidence.verification_status == VerificationStatus.SAMPLE
    )
    return bool(
        db.scalar(
            select(
                exists()
                .where(FinancialStatement.company_id == company_id)
                .where(Evidence.id == FinancialStatement.source_evidence_id)
                .where(other)
            )
        )
    )


def _result(
    formula: Formula,
    income: FinancialStatement,
    balance_sheets: list[FinancialStatement],
    company_is_sample: bool,
    company_mixed: bool,
) -> Result:
    inputs: list[Input] = []
    issues: list[Issue] = []

    numerator = _metric(income, formula.numerator)
    if numerator is None:
        issues.append(
            Issue("missing_input", "numerator", formula.numerator, income.reporting_period_end)
        )
    else:
        inputs.append(Input("numerator", income, numerator))

    same_scope = [b for b in balance_sheets if b.scope is formula.scope]
    closing = next(
        (
            b
            for b in same_scope
            if b.fiscal_year == income.fiscal_year
            and b.reporting_period_end == income.reporting_period_end
        ),
        None,
    )
    closing_metric = _metric(closing, formula.denominator) if closing else None
    if closing is None or closing_metric is None:
        issues.append(
            Issue(
                "missing_input",
                "denominator_closing",
                formula.denominator,
                income.reporting_period_end,
            )
        )
    else:
        inputs.append(Input("denominator_closing", closing, closing_metric))

    expected = income.reporting_period_start - timedelta(days=1)
    candidates = [
        b
        for b in same_scope
        if b.fiscal_year == income.fiscal_year - 1
        and abs(b.reporting_period_end - expected) <= OPENING_WINDOW
    ]
    if len(candidates) > 1:
        issues.append(
            Issue("ambiguous_opening_balance", "denominator_opening", formula.denominator, expected)
        )
    elif not candidates:
        issues.append(
            Issue("missing_opening_balance", "denominator_opening", formula.denominator, expected)
        )
    else:
        opening = candidates[0]
        opening_metric = _metric(opening, formula.denominator)
        if opening_metric is None:
            issues.append(
                Issue(
                    "missing_opening_balance",
                    "denominator_opening",
                    formula.denominator,
                    opening.reporting_period_end,
                )
            )
        else:
            inputs.append(Input("denominator_opening", opening, opening_metric))

    figures = [
        Figure(
            role=i.role,
            metric_code=i.metric.metric_code,
            period_end=i.statement.reporting_period_end,
            value=i.metric.value,
            unit=i.metric.unit,
            currency=i.statement.currency,
            status=i.statement.source_evidence.verification_status,
        )
        for i in inputs
    ]
    outcome = compute(
        formula,
        figures,
        issues,
        company_is_sample=company_is_sample,
        company_mixed=company_mixed,
    )
    return Result(formula, income, tuple(inputs), outcome)


def calculated_metrics(
    db: Session,
    company_id: uuid.UUID,
    fiscal_year: int | None = None,
    scope: StatementScope | None = None,
) -> list[Result]:
    """One result per formula for each latest annual income statement, newest year first."""
    company = db.get(Company, company_id)
    if company is None:
        return []
    mixed = company_mixed(db, company_id, company.is_sample)
    statements = latest_statements(db, company_id, quarterly=False)
    incomes = sorted(
        (
            s
            for s in statements
            if s.statement_type is StatementType.INCOME_STATEMENT
            and (fiscal_year is None or s.fiscal_year == fiscal_year)
            and (scope is None or s.scope is scope)
        ),
        key=lambda s: (-s.fiscal_year, s.scope.value),
    )
    balance_sheets = [s for s in statements if s.statement_type is StatementType.BALANCE_SHEET]
    return [
        _result(formula, income, balance_sheets, company.is_sample, mixed)
        for income in incomes
        for formula in sorted(formulas_for(income.scope), key=lambda f: f.code)
    ]

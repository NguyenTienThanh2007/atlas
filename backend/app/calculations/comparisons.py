"""WS4-3: period comparisons. Pure functions, no database.

Rules: WS4-D9 (docs/WS4_FINANCIAL_INTELLIGENCE_PLAN.md §8) and W3-D1 to W3-D11
(docs/PRODUCT_DECISIONS.md §2e); design in docs/WS4_3_IMPLEMENTATION_PLAN.md §12. Changing the
formula needs a new formula_version and a new owner decision. Exact Decimal only; nothing stored."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from app.calculations.ratios import (
    _EXACT,
    PERCENT_PLACES,
    VALUE_PLACES,
    InputVerification,
    rounded_quotient,
    verification_label,
)
from app.models import VerificationStatus

ComparisonType = Literal["annual_yoy", "quarterly_qoq", "quarterly_yoy"]
Side = Literal["current", "previous"]
Status = Literal["computed", "change_only", "not_comparable"]
Direction = Literal["up", "down", "unchanged"]
ReasonCode = Literal[
    "mixed_sample_and_real",
    "missing_current_value",
    "missing_previous_period",
    "ambiguous_previous_period",
    "period_mismatch",
    "missing_previous_value",
    "input_disputed_or_rejected",
    "input_superseded",
    "unit_or_currency_mismatch",
    "metric_not_applicable",
    "prior_zero",
    "sign_change",
]

# Plan §12.4 (W3-D10, W3-D11): lower rank first; within a rank, current before previous.
# WS4-4-D4 adds `metric_not_applicable` before the change-only codes; earlier order unchanged.
RANK: dict[str, int] = {
    "mixed_sample_and_real": 0,
    "missing_current_value": 1,
    "missing_previous_period": 2,
    "ambiguous_previous_period": 3,
    "period_mismatch": 4,
    "missing_previous_value": 5,
    "input_disputed_or_rejected": 6,
    "input_superseded": 7,
    "unit_or_currency_mismatch": 8,
    "metric_not_applicable": 9,
    "prior_zero": 10,
    "sign_change": 10,
}
SIDE_ORDER: dict[str, int] = {"current": 0, "previous": 1}

FORMULA_ID = "growth_abs_prior"  # WS4-D9: (current - prior) / |prior|
FORMULA_VERSION = 1
FORMULA_TEXT_VI = "(Kỳ này \u2212 kỳ trước) ÷ |kỳ trước|"  # U+2212: typographic minus
FORMULA_TEXT_EN = "(current \u2212 previous) ÷ |previous|"

WINDOW = timedelta(days=7)  # W3-D9: period ends align within 7 days
QOQ_BALANCE_DAYS = (80, 100)  # W3-D9: previous quarter-end balance sheet, inclusive
CHANGE_QUANTUM = Decimal("0.000001")  # inputs have 6 decimals, so the change is exact


@dataclass(frozen=True)
class Period:
    fiscal_year: int
    fiscal_quarter: int | None
    start: date
    end: date
    balance_sheet: bool  # a position at one date; otherwise a flow over start..end


def previous_year(d: date) -> date:
    """The same day one year earlier; 29 February becomes 28 February."""
    return (
        d.replace(year=d.year - 1, day=28)
        if (d.month, d.day) == (2, 29)
        else d.replace(year=d.year - 1)
    )


def _within(a: date, b: date) -> bool:
    return abs(a - b) <= WINDOW


def _candidate(kind: ComparisonType, c: Period, p: Period) -> bool:
    if (p.fiscal_quarter is None) != (c.fiscal_quarter is None) or p.end >= c.end:
        return False  # never annual against quarter, never the same or a later period
    if kind == "quarterly_qoq":
        if c.balance_sheet:
            low, high = QOQ_BALANCE_DAYS
            return low <= (c.end - p.end).days <= high
        return _within(p.end, c.start - timedelta(days=1))
    same_day = _within(p.end, previous_year(c.end))
    if kind == "annual_yoy" and not c.balance_sheet:
        return same_day and _within(p.end, c.start - timedelta(days=1))
    return same_day


def expected_label(kind: ComparisonType, c: Period) -> tuple[int, int | None]:
    if kind == "annual_yoy":
        return (c.fiscal_year - 1, None)
    quarter = c.fiscal_quarter or 0
    if kind == "quarterly_yoy":
        return (c.fiscal_year - 1, quarter)
    return (c.fiscal_year, quarter - 1) if quarter > 1 else (c.fiscal_year - 1, 4)


def match[T](
    kind: ComparisonType, current: Period, pool: Sequence[T], period: Callable[[T], Period]
) -> tuple[T | None, ReasonCode | None]:
    """The previous statement for `current` among `pool` (same company, type, scope and
    granularity). Never picks between candidates; a label that disagrees with the dates is
    returned with `period_mismatch` so it can be shown, never used."""
    candidates = [s for s in pool if _candidate(kind, current, period(s))]
    if not candidates:
        return None, "missing_previous_period"
    if len(candidates) > 1:
        return None, "ambiguous_previous_period"
    found = period(candidates[0])
    if (found.fiscal_year, found.fiscal_quarter) != expected_label(kind, current):
        return candidates[0], "period_mismatch"
    return candidates[0], None


@dataclass(frozen=True)
class Value:
    """One side's reported figure (latest revision) and its evidence status."""

    value: Decimal
    unit: str
    currency: str
    status: VerificationStatus
    period_end: date


@dataclass(frozen=True)
class Issue:
    code: ReasonCode
    side: Side
    metric_code: str
    period_end: date | None  # end of the statement concerned; None when there is none


@dataclass(frozen=True)
class Outcome:
    status: Status
    absolute_change: Decimal | None
    growth_value: Decimal | None
    growth_percent: Decimal | None
    direction: Direction | None
    issues: tuple[Issue, ...]
    input_verification: InputVerification | None

    @property
    def reason(self) -> ReasonCode | None:
        return self.issues[0].code if self.issues else None


def _ordered(issues: list[Issue]) -> tuple[Issue, ...]:
    return tuple(sorted(issues, key=lambda i: (RANK[i.code], SIDE_ORDER[i.side])))


def compare(
    metric_code: str,
    current: Value | None,
    previous: Value | None,
    issues: list[Issue],
    *,
    currency_metric: bool,
    company_is_sample: bool,
    company_mixed: bool,
) -> Outcome:
    """`issues` are the missing or unmatched sides (from the caller, which knows the periods).
    Isolation, status and unit checks happen here, then the change (WS4-D9, W3-D2, W3-D4)."""
    found = list(issues)
    sides: list[tuple[Side, Value]] = []
    if current is not None:
        sides.append(("current", current))
    if previous is not None:
        sides.append(("previous", previous))
    for side, v in sides:
        if company_mixed or (v.status is VerificationStatus.SAMPLE) != company_is_sample:
            found.append(Issue("mixed_sample_and_real", side, metric_code, v.period_end))
        if v.status in (VerificationStatus.DISPUTED, VerificationStatus.REJECTED):
            found.append(Issue("input_disputed_or_rejected", side, metric_code, v.period_end))
        elif v.status is VerificationStatus.SUPERSEDED:
            found.append(Issue("input_superseded", side, metric_code, v.period_end))
        if (currency_metric and v.unit != v.currency) or (
            side == "previous" and current is not None
            and (v.unit, v.currency) != (current.unit, current.currency)
        ):  # fmt: skip
            found.append(Issue("unit_or_currency_mismatch", side, metric_code, v.period_end))
    mixed = any(i.code == "mixed_sample_and_real" for i in found)
    verification = None if mixed else verification_label([v.status for _, v in sides])
    if found or current is None or previous is None:
        return Outcome("not_comparable", None, None, None, None, _ordered(found), verification)

    change = _EXACT.subtract(current.value, previous.value)  # never the 28-digit default context
    change = _EXACT.quantize(change.copy_abs() if change == 0 else change, CHANGE_QUANTUM)
    direction: Direction = "up" if change > 0 else "down" if change < 0 else "unchanged"
    prior, now = previous.value, current.value
    if prior == 0:
        why = Issue("prior_zero", "previous", metric_code, previous.period_end)
    elif (now < 0 < prior) or (prior < 0 < now):  # zero has no sign (W3-D2)
        why = Issue("sign_change", "current", metric_code, current.period_end)
    else:
        base = prior.copy_abs()
        return Outcome(
            status="computed",
            absolute_change=change,
            growth_value=rounded_quotient(change, base, VALUE_PLACES, "even"),
            growth_percent=rounded_quotient(
                _EXACT.multiply(change, 100), base, PERCENT_PLACES, "up"
            ),
            direction=direction,
            issues=(),
            input_verification=verification,
        )
    return Outcome("change_only", change, None, None, direction, (why,), verification)

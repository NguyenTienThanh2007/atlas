"""WS4-2: ROE and ROA. Pure functions, no database.

Formulas are owner-approved (docs/PRODUCT_DECISIONS.md §2d, WS4-D1 to D3, D7, D8, D12) and the
design is in docs/WS4_2_IMPLEMENTATION_PLAN.md. Changing a formula needs a new formula_version
and a new owner decision. Arithmetic is exact Decimal only; nothing here is ever stored."""

from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal, Inexact
from typing import Literal

from app.models import StatementScope, VerificationStatus

Role = Literal["numerator", "denominator_closing", "denominator_opening"]
ReasonCode = Literal[
    "missing_input",
    "missing_opening_balance",
    "ambiguous_opening_balance",
    "input_disputed_or_rejected",
    "input_superseded",
    "unit_mismatch",
    "equity_not_positive",
    "assets_not_positive",
]
InputVerification = Literal["all_verified", "some_unverified", "sample"]

# Plan §8: lower rank first; within a rank, by role.
RANK: dict[str, int] = {
    "missing_input": 1,
    "missing_opening_balance": 2,
    "ambiguous_opening_balance": 3,
    "input_disputed_or_rejected": 4,
    "input_superseded": 5,
    "unit_mismatch": 6,
    "equity_not_positive": 7,
    "assets_not_positive": 7,
}
ROLE_ORDER: dict[str, int] = {"numerator": 0, "denominator_closing": 1, "denominator_opening": 2}

VALUE_PLACES = 10  # ratio, half-even (WS4 plan §4.3)
PERCENT_PLACES = 2  # display percentage, half-up (WS4-D8)
AVERAGE_PLACES = 7  # exact: 6-decimal inputs halved

# Exact: raises instead of rounding. Inputs are below 10^32 with 6 decimals, so 100 digits is ample.
_EXACT = Context(prec=100, traps=[Inexact])


@dataclass(frozen=True)
class Formula:
    code: Literal["roe", "roa"]
    formula_id: str
    version: int
    scope: StatementScope
    numerator: str  # metric code on the FY t income statement
    denominator: str  # metric code on the FY t-1 and FY t balance sheets; no fallback exists
    not_positive: ReasonCode
    name_vi: str
    name_en: str
    text_vi: str
    text_en: str


_ROE_VI = "Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE)"
_ROE_EN = "Return on equity (ROE)"
_ROA_VI = "Tỷ suất lợi nhuận trên tổng tài sản (ROA)"
_ROA_EN = "Return on assets (ROA)"
_ROA_TEXT_VI = "Lợi nhuận sau thuế ÷ bình quân tổng tài sản đầu kỳ và cuối kỳ"
_ROA_TEXT_EN = "Net profit after tax ÷ average of opening and closing total assets"

REGISTRY: tuple[Formula, ...] = (
    Formula(
        code="roe",
        formula_id="roe_parent_avg_equity",
        version=1,
        scope=StatementScope.CONSOLIDATED,
        numerator="net_profit_parent",
        denominator="equity_parent",  # WS4-D12: never total_equity
        not_positive="equity_not_positive",
        name_vi=_ROE_VI,
        name_en=_ROE_EN,
        text_vi="Lợi nhuận sau thuế của cổ đông công ty mẹ ÷ bình quân vốn chủ sở hữu của cổ đông "
        "công ty mẹ đầu kỳ và cuối kỳ",
        text_en="Net profit attributable to parent ÷ average of opening and closing equity "
        "attributable to owners of the parent",
    ),
    Formula(
        code="roa",
        formula_id="roa_avg_assets",
        version=1,
        scope=StatementScope.CONSOLIDATED,
        numerator="net_profit",
        denominator="total_assets",
        not_positive="assets_not_positive",
        name_vi=_ROA_VI,
        name_en=_ROA_EN,
        text_vi=_ROA_TEXT_VI,
        text_en=_ROA_TEXT_EN,
    ),
    Formula(
        code="roe",
        formula_id="roe_separate_avg_equity",
        version=1,
        scope=StatementScope.SEPARATE,
        numerator="net_profit",
        denominator="total_equity",
        not_positive="equity_not_positive",
        name_vi=_ROE_VI,
        name_en=_ROE_EN,
        text_vi="Lợi nhuận sau thuế ÷ bình quân vốn chủ sở hữu đầu kỳ và cuối kỳ",
        text_en="Net profit after tax ÷ average of opening and closing total equity",
    ),
    Formula(
        code="roa",
        formula_id="roa_avg_assets",
        version=1,
        scope=StatementScope.SEPARATE,
        numerator="net_profit",
        denominator="total_assets",
        not_positive="assets_not_positive",
        name_vi=_ROA_VI,
        name_en=_ROA_EN,
        text_vi=_ROA_TEXT_VI,
        text_en=_ROA_TEXT_EN,
    ),
)


def formulas_for(scope: StatementScope) -> list[Formula]:
    return [f for f in REGISTRY if f.scope is scope]


@dataclass(frozen=True)
class Figure:
    """One selected input: the latest revision's figure and its evidence status."""

    role: Role
    metric_code: str
    period_end: date
    value: Decimal
    unit: str
    currency: str
    status: VerificationStatus


@dataclass(frozen=True)
class Issue:
    code: ReasonCode
    role: Role
    metric_code: str
    period_end: date


@dataclass(frozen=True)
class Outcome:
    value: Decimal | None
    percent: Decimal | None
    average: Decimal | None
    issues: tuple[Issue, ...]
    input_verification: InputVerification | None

    @property
    def reason(self) -> ReasonCode | None:
        return self.issues[0].code if self.issues else None


def _ordered(issues: list[Issue]) -> tuple[Issue, ...]:
    return tuple(sorted(issues, key=lambda i: (RANK[i.code], ROLE_ORDER[i.role])))


def _verification(figures: list[Figure]) -> InputVerification | None:
    if not figures:
        return None
    if any(f.status is VerificationStatus.SAMPLE for f in figures):
        return "sample"
    if all(f.status is VerificationStatus.VERIFIED for f in figures):
        return "all_verified"
    return "some_unverified"


def _integer(d: Decimal, places: int) -> Decimal:
    """d x 10^places as an integer-valued Decimal; raises if that would lose a digit."""
    scaled = _EXACT.scaleb(d, places)
    return _EXACT.quantize(scaled, Decimal(1))


def rounded_quotient(numerator: Decimal, denominator: Decimal, places: int, half: str) -> Decimal:
    """numerator / denominator rounded once to `places` decimals from the exact quotient.

    half="even": ties to even; half="up": ties away from zero (symmetric for negatives).
    The denominator must be positive (callers check this first)."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    n = _integer(numerator.copy_abs(), AVERAGE_PLACES + places)
    d = _integer(denominator, AVERAGE_PLACES)
    q, r = _EXACT.divmod(n, d)
    twice = _EXACT.multiply(r, 2)
    if twice > d or (twice == d and (half == "up" or _EXACT.remainder(q, 2) == 1)):
        q = _EXACT.add(q, 1)
    if q == 0:
        return Decimal(0).scaleb(-places)  # never negative zero
    signed = q if numerator >= 0 else _EXACT.minus(q)
    return _EXACT.scaleb(signed, -places)


def compute(formula: Formula, figures: list[Figure], issues: list[Issue]) -> Outcome:
    """`figures` are the inputs that were found; `issues` the missing or ambiguous ones (from the
    caller, which knows the dates). Status, unit and sign checks happen here."""
    found = list(issues)
    for f in figures:
        if f.status in (VerificationStatus.DISPUTED, VerificationStatus.REJECTED):
            found.append(Issue("input_disputed_or_rejected", f.role, f.metric_code, f.period_end))
        elif f.status is VerificationStatus.SUPERSEDED:
            found.append(Issue("input_superseded", f.role, f.metric_code, f.period_end))
        if f.unit != f.currency:
            found.append(Issue("unit_mismatch", f.role, f.metric_code, f.period_end))
    verification = _verification(figures)
    if found:
        return Outcome(None, None, None, _ordered(found), verification)

    by_role = {f.role: f for f in figures}
    numerator = by_role["numerator"].value
    opening = by_role["denominator_opening"]
    closing = by_role["denominator_closing"]
    not_positive = [
        Issue(formula.not_positive, f.role, f.metric_code, f.period_end)
        for f in (closing, opening)
        if f.value <= 0
    ]
    if not_positive:  # the average of two positive values is positive, so this is complete
        return Outcome(None, None, None, _ordered(not_positive), verification)

    average = _EXACT.divide(_EXACT.add(opening.value, closing.value), 2)  # exact, never rounded
    return Outcome(
        value=rounded_quotient(numerator, average, VALUE_PLACES, "even"),
        percent=rounded_quotient(_EXACT.multiply(numerator, 100), average, PERCENT_PLACES, "up"),
        average=_EXACT.quantize(average, Decimal(1).scaleb(-AVERAGE_PLACES)),
        issues=(),
        input_verification=verification,
    )

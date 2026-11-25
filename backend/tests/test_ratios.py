"""WS4-2: pure ROE/ROA computation (no database). Expected values are checked against an exact
rational oracle (fractions.Fraction), never against floats."""

from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from app.calculations import ratios
from app.calculations.ratios import (
    REGISTRY,
    Figure,
    Issue,
    Outcome,
    Role,
    compute,
    formulas_for,
    rounded_quotient,
)
from app.models import StatementScope, VerificationStatus

D = Decimal
U = VerificationStatus.UNVERIFIED
END, OPEN = date(2025, 12, 31), date(2024, 12, 31)
ROE_C = next(f for f in REGISTRY if f.formula_id == "roe_parent_avg_equity")
ROA_C = next(f for f in REGISTRY if f.formula_id == "roa_avg_assets")


def fig(role: Role, value: str, status: VerificationStatus = U, unit: str = "VND") -> Figure:
    code = {"numerator": "net_profit_parent"}.get(role, "equity_parent")
    return Figure(
        role, code, END if role != "denominator_opening" else OPEN, D(value), unit, "VND", status
    )


def calc(formula: Any, figures: list[Figure], issues: list[Issue], sample: bool = False) -> Outcome:
    """compute() for a real (or, with sample=True, a sample) company whose data isn't mixed."""
    return compute(formula, figures, issues, company_is_sample=sample, company_mixed=False)


def three(num: str, opening: str, closing: str, status: VerificationStatus = U) -> list[Figure]:
    return [
        fig("numerator", num, status),
        fig("denominator_opening", opening, status),
        fig("denominator_closing", closing, status),
    ]


def oracle(n: Fraction, places: int, half: str) -> str:
    """Round a rational once; returns the fixed-point string."""
    scaled = abs(n) * 10**places
    q, r = divmod(scaled.numerator, scaled.denominator)
    twice = 2 * r
    if twice > scaled.denominator or (twice == scaled.denominator and (half == "up" or q % 2 == 1)):
        q += 1
    sign = "-" if n < 0 and q else ""
    digits = str(q).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


# ---------------------------------------------------------------- registry


def test_registry_is_exactly_the_approved_formulas() -> None:
    got = {(f.code, f.formula_id, f.version, f.scope, f.numerator, f.denominator) for f in REGISTRY}
    assert got == {
        (
            "roe",
            "roe_parent_avg_equity",
            1,
            StatementScope.CONSOLIDATED,
            "net_profit_parent",
            "equity_parent",
        ),
        ("roa", "roa_avg_assets", 1, StatementScope.CONSOLIDATED, "net_profit", "total_assets"),
        (
            "roe",
            "roe_separate_avg_equity",
            1,
            StatementScope.SEPARATE,
            "net_profit",
            "total_equity",
        ),
        ("roa", "roa_avg_assets", 1, StatementScope.SEPARATE, "net_profit", "total_assets"),
    }
    # WS4-D12: consolidated ROE has exactly one denominator, and it is equity_parent.
    consolidated_roe = [f for f in formulas_for(StatementScope.CONSOLIDATED) if f.code == "roe"]
    assert [f.denominator for f in consolidated_roe] == ["equity_parent"]


# ---------------------------------------------------------------- exact rounding


@pytest.mark.parametrize(
    ("num", "den"),
    [
        ("1", "3"),
        ("2", "3"),
        ("1", "7"),
        ("30", "200"),
        ("40", "950"),
        ("1", "2048"),  # 0.00048828125: tie at the 11th decimal, even neighbour
        ("3", "2048"),  # 0.00146484375: tie, odd neighbour
        ("1", "32"),  # 3.125 %: tie at the 3rd percent decimal
        ("-1", "32"),  # same tie on a loss
        ("-2", "3"),
        ("999999999999", "32000000000000"),  # value ties up, percent must not (double rounding)
        ("99999999999999999999999999999999.999999", "0.0000005"),  # huge exact ratio
        ("0.000001", "99999999999999999999999999999999.9999995"),  # tiny ratio
        ("0", "5"),
        ("-0.000001", "10000000000"),  # rounds to zero: no negative zero
    ],
)
def test_one_rounding_from_the_exact_quotient(num: str, den: str) -> None:
    exact = Fraction(D(num)) / Fraction(D(den))
    value = rounded_quotient(D(num), D(den), 10, "even")
    percent = rounded_quotient(ratios._EXACT.multiply(D(num), 100), D(den), 2, "up")
    assert format(value, "f") == oracle(exact, 10, "even")
    assert format(percent, "f") == oracle(exact * 100, 2, "up")
    assert not format(value, "f").startswith("-0.0000000000")
    assert "E" not in format(value, "f") + format(percent, "f")


def test_percent_is_not_derived_from_the_rounded_value() -> None:
    value = rounded_quotient(D("999999999999"), D("32000000000000"), 10, "even")
    percent = rounded_quotient(D("99999999999900"), D("32000000000000"), 2, "up")
    assert format(value, "f") == "0.0312500000"  # rounding this to a percent would give 3.13
    assert format(percent, "f") == "3.12"  # exact 3.12499999999...


def test_ties_follow_their_rounding_rule() -> None:
    assert format(rounded_quotient(D("1"), D("2048"), 10, "even"), "f") == "0.0004882812"
    assert format(rounded_quotient(D("3"), D("2048"), 10, "even"), "f") == "0.0014648438"
    assert format(rounded_quotient(D("100"), D("32"), 2, "up"), "f") == "3.13"
    assert format(rounded_quotient(D("-100"), D("32"), 2, "up"), "f") == "-3.13"


def test_a_non_positive_denominator_is_never_divided() -> None:
    for den in ("0", "-1"):
        with pytest.raises(ValueError):
            rounded_quotient(D("1"), D(den), 10, "even")


# ---------------------------------------------------------------- compute()


def test_computed_ratio_average_and_percent() -> None:
    out = calc(ROE_C, three("30", "180", "220"), [])
    assert out.issues == () and out.reason is None
    assert (format(out.value, "f"), format(out.percent, "f"), format(out.average, "f")) == (
        "0.1500000000",
        "15.00",
        "200.0000000",
    )


def test_average_is_exact_never_rounded() -> None:
    out = calc(ROE_C, three("1", "0.000001", "0.000002"), [])
    assert format(out.average, "f") == "0.0000015"
    big = "99999999999999999999999999999999.999999"
    out = calc(ROE_C, three("1", big, "99999999999999999999999999999999.999998"), [])
    assert format(out.average, "f") == "99999999999999999999999999999999.9999985"


def test_loss_gives_a_negative_ratio() -> None:
    out = calc(ROE_C, three("-30", "180", "220"), [])
    assert (format(out.value, "f"), format(out.percent, "f")) == ("-0.1500000000", "-15.00")


@pytest.mark.parametrize(
    ("opening", "closing", "roles"),
    [
        ("-10", "4", ["denominator_opening"]),
        ("10", "0", ["denominator_closing"]),
        ("0", "0", ["denominator_closing", "denominator_opening"]),
        ("-5", "-5", ["denominator_closing", "denominator_opening"]),
    ],
)
def test_non_positive_equity_is_not_meaningful(
    opening: str, closing: str, roles: list[str]
) -> None:
    out = calc(ROE_C, three("30", opening, closing), [])
    assert out.value is None and out.percent is None and out.average is None
    assert [(i.code, i.role) for i in out.issues] == [("equity_not_positive", r) for r in roles]


def test_non_positive_assets_use_their_own_reason() -> None:
    out = calc(ROA_C, three("30", "0", "100"), [])
    assert out.reason == "assets_not_positive"


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (VerificationStatus.DISPUTED, "input_disputed_or_rejected"),
        (VerificationStatus.REJECTED, "input_disputed_or_rejected"),
        (VerificationStatus.SUPERSEDED, "input_superseded"),
    ],
)
def test_refused_evidence_states(status: VerificationStatus, code: str) -> None:
    figures = three("30", "180", "220")
    figures[2] = fig("denominator_closing", "220", status)
    out = calc(ROE_C, figures, [])
    assert out.value is None and out.reason == code
    assert [(i.code, i.role) for i in out.issues] == [(code, "denominator_closing")]


def test_unit_mismatch_is_refused() -> None:
    figures = three("30", "180", "220")
    figures[0] = fig("numerator", "30", unit="VND/share")
    assert calc(ROE_C, figures, []).reason == "unit_mismatch"


def test_simultaneous_issues_are_all_listed_in_precedence_order() -> None:
    figures = [
        fig("denominator_closing", "220", VerificationStatus.SUPERSEDED),
        fig("denominator_opening", "-1", VerificationStatus.REJECTED),
    ]
    missing = [Issue("missing_input", "numerator", "net_profit_parent", END)]
    out = calc(ROE_C, figures, missing)
    assert [(i.code, i.role) for i in out.issues] == [
        ("missing_input", "numerator"),
        ("input_disputed_or_rejected", "denominator_opening"),
        ("input_superseded", "denominator_closing"),
    ]  # value checks (the negative opening) only run once nothing else is wrong
    assert out.reason == "missing_input"


def test_issue_ties_are_ordered_by_role() -> None:
    issues = [
        Issue("missing_opening_balance", "denominator_opening", "equity_parent", OPEN),
        Issue("missing_input", "denominator_closing", "equity_parent", END),
        Issue("missing_input", "numerator", "net_profit_parent", END),
    ]
    out = calc(ROE_C, [], issues)
    assert [(i.code, i.role) for i in out.issues] == [
        ("missing_input", "numerator"),
        ("missing_input", "denominator_closing"),
        ("missing_opening_balance", "denominator_opening"),
    ]
    assert out.input_verification is None  # no input found


@pytest.mark.parametrize(
    ("statuses", "label"),
    [
        ([VerificationStatus.VERIFIED] * 3, "all_verified"),
        ([VerificationStatus.VERIFIED, U, VerificationStatus.VERIFIED], "some_unverified"),
        ([VerificationStatus.SAMPLE] * 3, "sample"),
    ],
)
def test_input_verification_label(statuses: list[VerificationStatus], label: str) -> None:
    figures = three("30", "180", "220")
    figures = [fig(f.role, str(f.value), s) for f, s in zip(figures, statuses, strict=True)]
    out = calc(ROE_C, figures, [], sample=label == "sample")
    assert out.input_verification == label and out.value is not None


def test_calculation_modules_never_use_float() -> None:
    package = Path(ratios.__file__).parent
    for path in package.glob("*.py"):
        assert "float" not in path.read_text(encoding="utf-8"), path.name


# ---------------------------------------------------------------- sample/real isolation (AU-3)


@pytest.mark.parametrize(
    ("company_is_sample", "statuses", "mixed_roles"),
    [
        # real company, one sample input
        (False, [U, VerificationStatus.SAMPLE, U], ["denominator_opening"]),
        # sample company, one real input
        (True, [VerificationStatus.SAMPLE, VerificationStatus.SAMPLE, U], ["denominator_closing"]),
        # real company, all inputs sample: every one is refused
        (
            False,
            [VerificationStatus.SAMPLE] * 3,
            ["numerator", "denominator_closing", "denominator_opening"],
        ),
    ],
)
def test_mixed_sample_and_real_inputs_are_refused(
    company_is_sample: bool, statuses: list[VerificationStatus], mixed_roles: list[str]
) -> None:
    figures = [
        fig(f.role, str(f.value), st)
        for f, st in zip(three("30", "180", "220"), statuses, strict=True)
    ]
    out = compute(ROE_C, figures, [], company_is_sample=company_is_sample, company_mixed=False)
    assert (out.value, out.percent, out.average) == (None, None, None)
    assert out.reason == "mixed_sample_and_real"
    assert [i.role for i in out.issues] == mixed_roles
    assert out.input_verification is None  # no "sample" or "unverified" label hides the mix


def test_company_level_mix_refuses_even_consistent_inputs() -> None:
    out = compute(ROE_C, three("30", "180", "220"), [], company_is_sample=False, company_mixed=True)
    assert out.reason == "mixed_sample_and_real" and out.value is None
    assert len(out.issues) == 3 and out.input_verification is None


def test_mixed_data_outranks_every_other_reason() -> None:
    figures = [
        fig("denominator_closing", "-1", VerificationStatus.REJECTED),
        fig("denominator_opening", "180", VerificationStatus.SAMPLE),
    ]
    missing = [Issue("missing_input", "numerator", "net_profit_parent", END)]
    out = compute(ROE_C, figures, missing, company_is_sample=False, company_mixed=False)
    assert [(i.code, i.role) for i in out.issues] == [
        ("mixed_sample_and_real", "denominator_opening"),
        ("missing_input", "numerator"),
        ("input_disputed_or_rejected", "denominator_closing"),
    ]

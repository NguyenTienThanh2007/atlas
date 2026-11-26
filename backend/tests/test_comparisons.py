"""WS4-3 pure comparison engine: matching on dates (W3-D9), the WS4-D9 formula with W3-D2/D4,
reason precedence (W3-D10, W3-D11). Expected values: docs/WS4_3_IMPLEMENTATION_PLAN.md §12.9,
checked against an independent Fraction oracle. All values fictional."""

import random
import re
from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from app.calculations.comparisons import (
    Issue,
    Period,
    Value,
    compare,
    match,
    previous_year,
)
from app.models import VerificationStatus

U = VerificationStatus.UNVERIFIED
END = date(2025, 12, 31)
PRIOR_END = date(2024, 12, 31)


def val(v: str, status: VerificationStatus = U, unit: str = "VND", end: date = END) -> Value:
    return Value(Decimal(v), unit, "VND", status, end)


def run(prior: str, current: str) -> tuple[object, ...]:
    out = compare(
        "net_profit",
        val(current),
        val(prior, end=PRIOR_END),
        [],
        currency_metric=True,
        company_is_sample=False,
        company_mixed=False,
    )
    fmt = [
        None if d is None else format(d, "f")
        for d in (out.absolute_change, out.growth_value, out.growth_percent)
    ]
    return (out.status, out.reason, *fmt)


def oracle(x: Fraction, places: int, half: str) -> str:
    v = abs(x) * 10**places
    q, r = divmod(v.numerator, v.denominator)
    if 2 * r > v.denominator or (2 * r == v.denominator and (half == "up" or q % 2 == 1)):
        q += 1
    digits = str(q).rjust(places + 1, "0")
    return f"{'-' if x < 0 and q else ''}{digits[:-places]}.{digits[-places:]}"


# ---------------------------------------------------------------- arithmetic fixtures F1-F16

BIG = "99999999999999999999999999999999.999999"
FIXTURES = [
    ("F1", "100", "120", "computed", None, "20.000000", "0.2000000000", "20.00"),
    ("F2", "100", "80", "computed", None, "-20.000000", "-0.2000000000", "-20.00"),
    ("F3", "-100", "-150", "computed", None, "-50.000000", "-0.5000000000", "-50.00"),
    ("F4", "-100", "-50", "computed", None, "50.000000", "0.5000000000", "50.00"),
    ("F5", "0", "30", "change_only", "prior_zero", "30.000000", None, None),
    ("F6", "50", "0", "computed", None, "-50.000000", "-1.0000000000", "-100.00"),
    ("F7", "-50", "0", "computed", None, "50.000000", "1.0000000000", "100.00"),
    ("F8", "-40", "60", "change_only", "sign_change", "100.000000", None, None),
    ("F9", "60", "-40", "change_only", "sign_change", "-100.000000", None, None),
    ("F10", "0", "0", "change_only", "prior_zero", "0.000000", None, None),
    ("F11", "0.000001", "1", "computed", None, "0.999999", "999999.0000000000", "99999900.00"),
    ("F12a", "200", "200.01", "computed", None, "0.010000", "0.0000500000", "0.01"),
    ("F12b", "200", "199.99", "computed", None, "-0.010000", "-0.0000500000", "-0.01"),
    ("F12c", "20000", "20000.000005", "computed", None, "0.000005", "0.0000000002", "0.00"),
    ("F12d", "20000", "20000.000003", "computed", None, "0.000003", "0.0000000002", "0.00"),
    (
        "F13",
        "90000000000000000000000000000000",
        "10000000000000000000000000000000",
        "computed",
        None,
        "-80000000000000000000000000000000.000000",
        "-0.8888888889",
        "-88.89",
    ),
    ("F14", "3", "4", "computed", None, "1.000000", "0.3333333333", "33.33"),
    ("F15", "3", "5", "computed", None, "2.000000", "0.6666666667", "66.67"),
    (
        "F16",
        "-0.000001",
        "-" + BIG,
        "computed",
        None,
        "-99999999999999999999999999999999.999998",
        "-99999999999999999999999999999999999998.0000000000",
        "-9999999999999999999999999999999999999800.00",
    ),
]


@pytest.mark.parametrize(
    ("name", "prior", "current", "status", "reason", "change", "value", "percent"), FIXTURES
)
def test_fixture(
    name: str,
    prior: str,
    current: str,
    status: str,
    reason: str | None,
    change: str,
    value: str | None,
    percent: str | None,
) -> None:
    assert run(prior, current) == (status, reason, change, value, percent), name


def test_direction() -> None:
    def direction(prior: str, current: str) -> object:
        return compare(
            "net_profit", val(current), val(prior), [],
            currency_metric=True, company_is_sample=False, company_mixed=False,
        ).direction  # fmt: skip

    assert (direction("1", "2"), direction("2", "1"), direction("0", "0")) == (
        "up",
        "down",
        "unchanged",
    )
    assert direction("-40", "60") == "up"  # change_only still has a direction


def micro(n: int) -> str:
    """n millionths as an exact 6-decimal string (no Decimal context involved)."""
    digits = str(abs(n)).rjust(7, "0")
    return f"{'-' if n < 0 else ''}{digits[:-6]}.{digits[-6:]}"


def test_random_pairs_match_the_oracle() -> None:
    rng = random.Random(20261126)  # noqa: S311 - deterministic test data, not security
    limit = 10**38 - 1  # below 10^32 with 6 decimals, the stored maximum
    for _ in range(600):
        p, c = rng.randint(-limit, limit), rng.randint(-limit, limit)
        if rng.random() < 0.3:  # close values, where rounding ties and tiny changes live
            c = max(-limit, min(limit, p + rng.randint(-999, 999)))
        if rng.random() < 0.1:
            p = rng.randint(-999, 999)  # tiny priors: huge percentages
        status, _, change, value, percent = run(micro(p), micro(c))
        exact = Fraction(c - p, 10**6)
        assert Fraction(Decimal(str(change))) == exact
        if status == "computed":
            growth = exact / abs(Fraction(p, 10**6))
            assert (value, percent) == (oracle(growth, 10, "even"), oracle(growth * 100, 2, "up"))


def test_no_negative_zero_and_no_exponent() -> None:
    for prior, current in (("-5", "-5"), ("0.000001", "0.000001"), ("-200", "-199.999999")):
        _, _, change, value, percent = run(prior, current)
        for s in (change, value, percent):
            assert s is None or ("E" not in str(s) and not re.fullmatch(r"-0(\.0+)?", str(s)))


# ---------------------------------------------------------------- reasons and isolation


def test_precedence_lists_every_issue() -> None:
    out = compare(
        "net_profit",
        val("10", VerificationStatus.REJECTED),
        val("5", VerificationStatus.SAMPLE, unit="VND/share", end=PRIOR_END),
        [],
        currency_metric=True,
        company_is_sample=False,
        company_mixed=False,
    )
    assert [(i.code, i.side) for i in out.issues] == [
        ("mixed_sample_and_real", "previous"),
        ("input_disputed_or_rejected", "current"),
        ("unit_or_currency_mismatch", "previous"),
    ]
    assert (out.status, out.reason, out.input_verification) == (
        "not_comparable",
        "mixed_sample_and_real",
        None,
    )
    assert (out.absolute_change, out.growth_percent, out.direction) == (None, None, None)


def test_rank_9_runs_only_when_nothing_else_applies() -> None:
    out = compare(
        "net_profit",
        val("30", VerificationStatus.SUPERSEDED),
        val("0", end=PRIOR_END),
        [],
        currency_metric=True,
        company_is_sample=False,
        company_mixed=False,
    )
    assert [i.code for i in out.issues] == ["input_superseded"]


def test_missing_sides_come_from_the_caller() -> None:
    missing = [Issue("missing_previous_period", "previous", "net_profit", None)]
    out = compare(
        "net_profit", val("1"), None, missing,
        currency_metric=True, company_is_sample=False, company_mixed=False,
    )  # fmt: skip
    assert (out.status, out.reason, out.input_verification) == (
        "not_comparable",
        "missing_previous_period",
        "some_unverified",
    )


@pytest.mark.parametrize(
    ("company_is_sample", "company_mixed", "statuses"),
    [
        (False, False, (VerificationStatus.SAMPLE, U)),
        (True, False, (VerificationStatus.SAMPLE, U)),
        (False, True, (U, U)),
    ],
)
def test_mixed_sample_and_real_is_refused(
    company_is_sample: bool, company_mixed: bool, statuses: tuple[VerificationStatus, ...]
) -> None:
    out = compare(
        "net_profit",
        val("10", statuses[0]),
        val("5", statuses[1], end=PRIOR_END),
        [],
        currency_metric=True,
        company_is_sample=company_is_sample,
        company_mixed=company_mixed,
    )
    assert (out.status, out.reason, out.input_verification) == (
        "not_comparable",
        "mixed_sample_and_real",
        None,
    )


def test_labels_describe_inputs_only() -> None:
    def label(statuses: tuple[VerificationStatus, VerificationStatus], sample: bool) -> object:
        return compare(
            "net_profit", val("2", statuses[0]), val("1", statuses[1], end=PRIOR_END), [],
            currency_metric=True, company_is_sample=sample, company_mixed=False,
        ).input_verification  # fmt: skip

    v = VerificationStatus.VERIFIED
    s = VerificationStatus.SAMPLE
    assert (label((v, v), False), label((v, U), False), label((s, s), True)) == (
        "all_verified",
        "some_unverified",
        "sample",
    )


def test_units_of_non_currency_metrics() -> None:
    eps = compare(
        "eps_basic",
        Value(Decimal("1200"), "VND/share", "VND", U, END),
        Value(Decimal("1000"), "VND/share", "VND", U, PRIOR_END),
        [],
        currency_metric=False,
        company_is_sample=False,
        company_mixed=False,
    )
    assert (eps.status, eps.growth_percent) == ("computed", Decimal("20.00"))
    shares = compare(
        "shares_outstanding",
        Value(Decimal("10"), "shares", "VND", U, END),
        Value(Decimal("10"), "VND", "VND", U, PRIOR_END),
        [],
        currency_metric=False,
        company_is_sample=False,
        company_mixed=False,
    )
    assert shares.reason == "unit_or_currency_mismatch"


# ---------------------------------------------------------------- matching (W3-D9)


def flow(fy: int, start: str, end: str, q: int | None = None) -> Period:
    return Period(fy, q, date.fromisoformat(start), date.fromisoformat(end), False)


def bs(fy: int, end: str, q: int | None = None) -> Period:
    d = date.fromisoformat(end)
    return Period(fy, q, d, d, True)


def found(kind: str, current: Period, *pool: Period) -> tuple[Period | None, str | None]:
    result = match(kind, current, list(pool), lambda p: p)  # type: ignore[arg-type]
    return result


def test_previous_year_moves_leap_day() -> None:
    assert previous_year(date(2024, 2, 29)) == date(2023, 2, 28)
    assert previous_year(date(2025, 3, 31)) == date(2024, 3, 31)


def test_annual_yoy() -> None:
    m1 = flow(2024, "2024-01-01", "2024-12-31")
    assert found("annual_yoy", flow(2025, "2025-01-01", "2025-12-31"), m1) == (m1, None)
    m2 = flow(2024, "2023-04-01", "2024-03-31")
    assert found("annual_yoy", flow(2025, "2024-04-01", "2025-03-31"), m2) == (m2, None)
    m3 = flow(2023, "2022-03-01", "2023-02-28")
    assert found("annual_yoy", flow(2024, "2023-03-01", "2024-02-29"), m3) == (m3, None)


def test_seven_day_window() -> None:
    current = bs(2025, "2025-12-31")
    seven = bs(2024, "2024-12-24")
    assert found("annual_yoy", current, seven) == (seven, None)
    assert found("annual_yoy", current, bs(2024, "2024-12-23")) == (None, "missing_previous_period")


def test_flows_must_also_be_contiguous() -> None:
    # previous ends a year earlier, but the current flow starts 20 days after it ends
    current = flow(2025, "2025-01-21", "2025-12-31")
    assert found("annual_yoy", current, flow(2024, "2024-01-01", "2024-12-31")) == (
        None,
        "missing_previous_period",
    )


def test_fiscal_year_end_moved() -> None:
    current = flow(2026, "2025-04-01", "2026-03-31")
    assert found("annual_yoy", current, flow(2024, "2024-01-01", "2024-12-31")) == (
        None,
        "missing_previous_period",
    )


def test_two_candidates_are_ambiguous() -> None:
    current = bs(2025, "2025-12-31")
    pool = (bs(2024, "2024-12-28"), bs(2024, "2024-12-31"))
    assert found("annual_yoy", current, *pool) == (None, "ambiguous_previous_period")


def test_annual_label_must_be_previous_fiscal_year() -> None:
    wrong = bs(2023, "2024-12-28")  # a label that the dates contradict
    assert found("annual_yoy", bs(2025, "2025-12-31"), wrong) == (wrong, "period_mismatch")


def test_quarter_on_quarter() -> None:
    q1 = flow(2025, "2025-01-01", "2025-03-31", 1)
    q4 = flow(2024, "2024-10-01", "2024-12-31", 4)
    assert found("quarterly_qoq", flow(2025, "2025-04-01", "2025-06-30", 2), q1, q4) == (q1, None)
    assert found("quarterly_qoq", q1, q4) == (q4, None)


@pytest.mark.parametrize(("days", "matched"), [(80, True), (100, True), (79, False), (101, False)])
def test_balance_sheet_quarter_on_quarter(days: int, matched: bool) -> None:
    current = bs(2025, "2025-06-30", 2)
    prev = bs(2025, date.fromordinal(date(2025, 6, 30).toordinal() - days).isoformat(), 1)
    expected = (prev, None) if matched else (None, "missing_previous_period")
    assert found("quarterly_qoq", current, prev) == expected


def test_label_and_dates_disagree() -> None:
    q1 = flow(2025, "2025-01-01", "2025-03-31", 1)
    assert found("quarterly_qoq", flow(2025, "2025-04-01", "2025-06-30", 3), q1) == (
        q1,
        "period_mismatch",
    )


def test_quarter_year_on_year() -> None:
    current = flow(2025, "2025-04-01", "2025-06-30", 2)
    q2 = flow(2024, "2024-04-01", "2024-06-30", 2)
    assert found("quarterly_yoy", current, q2) == (q2, None)
    q3 = flow(2024, "2024-04-01", "2024-06-30", 3)
    assert found("quarterly_yoy", current, q3) == (q3, "period_mismatch")


def test_annual_and_quarter_never_pair() -> None:
    assert found("annual_yoy", bs(2025, "2025-12-31"), bs(2024, "2024-12-31", 4)) == (
        None,
        "missing_previous_period",
    )
    assert found("quarterly_yoy", bs(2025, "2025-12-31", 4), bs(2024, "2024-12-31")) == (
        None,
        "missing_previous_period",
    )

"""WS4-3: period comparisons from stored statements through the API (plan §12.9, M and A cases).
All data is fictional test data (example.test URLs, TST tickers)."""

import json
import uuid
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from app.models import (
    Company,
    EntityType,
    Evidence,
    FinancialMetric,
    FinancialStatement,
    ReviewDecision,
    VerificationStatus,
)
from tests.factories import bundle, company, evidence, run, statement
from tests.test_calculated_metrics import SAMPLE, _review, load
from tests.test_sample_isolation import _disable_triggers, _evidence, _statement

API = "/api/v1"


def st(
    fy: int,
    start: str,
    end: str,
    *,
    kind: str = "income_statement",
    q: int | None = None,
    scope: str = "consolidated",
    revision: int = 1,
    **metrics: str,
) -> Any:
    record = statement(
        statement_type=kind,
        reporting_period_start=start,
        reporting_period_end=end,
        fiscal_year=fy,
        scope=scope,
        revision=revision,
        evidence=evidence(f"https://example.test/{kind}-{scope}-{end}-q{q}-r{revision}.pdf"),
        metrics=metrics,
    )
    if q is not None:
        record["fiscal_quarter"] = q
    return record


def bs(fy: int, end: str, **kw: Any) -> Any:
    return st(fy, end, end, kind="balance_sheet", **kw)


def cid(client: TestClient) -> str:
    return str(client.get(f"{API}/companies").json()["items"][0]["id"])


def rows(client: TestClient, kind: str = "annual_yoy", **params: Any) -> list[dict[str, Any]]:
    res = client.get(f"{API}/companies/{cid(client)}/comparisons", params={"type": kind, **params})
    assert res.status_code == 200, res.text
    assert "E-" not in res.text and "E+" not in res.text  # fixed-point decimals only
    body = json.loads(res.text, parse_float=lambda s: pytest.fail(f"float in JSON: {s}"))
    return list(body["items"])


def one(items: list[dict[str, Any]], metric: str, end: str | None = None) -> dict[str, Any]:
    return next(
        r
        for r in items
        if r["metric_code"] == metric and (end is None or r["current"]["period_end"] == end)
    )


YEARS = (
    st(2025, "2025-01-01", "2025-12-31", net_revenue="120", net_profit="-40"),
    st(2024, "2024-01-01", "2024-12-31", net_revenue="100", net_profit="60"),
)


# ---------------------------------------------------------------- contract and provenance (A1, A4)


def test_annual_comparison_with_provenance(client: TestClient, ref: Session) -> None:
    load(ref, *YEARS)
    items = rows(client)
    assert [(r["current"]["fiscal_year"], r["metric_code"]) for r in items] == [
        (2025, "net_revenue"),
        (2025, "net_profit"),
        (2024, "net_revenue"),
        (2024, "net_profit"),
    ]
    r = one(items, "net_revenue", "2025-12-31")
    assert (r["kind"], r["type"], r["formula_id"], r["formula_version"]) == (
        "comparison",
        "annual_yoy",
        "growth_abs_prior",
        1,
    )
    assert (r["status"], r["reason"], r["issues"], r["direction"]) == ("computed", None, [], "up")
    assert (r["absolute_change"], r["growth_value"], r["growth_percent"]) == (
        "20.000000",
        "0.2000000000",
        "20.00",
    )
    assert (r["metric_name_vi"], r["metric_name_en"], r["unit"]) == (
        "Doanh thu thuần",
        "Net revenue",
        "VND",
    )
    assert (r["statement_type"], r["scope"], r["input_verification"]) == (
        "income_statement",
        "consolidated",
        "some_unverified",
    )
    assert "verification_status" not in r  # a comparison is never "verified" (A8)
    cur, prev = r["current"], r["previous"]
    assert (cur["value"], cur["period_start"], cur["revision"]) == ("120.000000", "2025-01-01", 1)
    assert (prev["value"], prev["period_end"], prev["fiscal_quarter"]) == (
        "100.000000",
        "2024-12-31",
        None,
    )
    for side in (cur, prev):
        assert side["source"]["page"] == 7 and side["source"]["link_status"] == "linkable"
        assert side["source"]["document_url"].startswith("https://example.test/")
    sign = one(items, "net_profit", "2025-12-31")  # 60 -> -40
    assert (sign["status"], sign["reason"], sign["absolute_change"], sign["growth_percent"]) == (
        "change_only",
        "sign_change",
        "-100.000000",
        None,
    )
    first = one(items, "net_revenue", "2024-12-31")
    assert (first["status"], first["reason"], first["previous"]) == (
        "not_comparable",
        "missing_previous_period",
        None,
    )
    assert first["issues"] == [
        {
            "code": "missing_previous_period",
            "side": "previous",
            "metric_code": "net_revenue",
            "period_end": None,
        }
    ]


# ---------------------------------------------------------------- matching (M cases)


def test_non_calendar_and_leap_day_years(client: TestClient, ref: Session) -> None:
    load(
        ref,
        st(2025, "2024-04-01", "2025-03-31", net_revenue="110"),  # FY ending 31 March
        st(2024, "2023-04-01", "2024-03-31", net_revenue="100"),
        st(2024, "2023-03-01", "2024-02-29", scope="separate", net_revenue="12"),  # leap day
        st(2023, "2022-03-01", "2023-02-28", scope="separate", net_revenue="10"),
    )
    items = rows(client)
    march = one(items, "net_revenue", "2025-03-31")
    assert (march["growth_percent"], march["previous"]["period_end"]) == ("10.00", "2024-03-31")
    leap = one(items, "net_revenue", "2024-02-29")
    assert (leap["growth_percent"], leap["previous"]["period_end"]) == ("20.00", "2023-02-28")


def test_ambiguous_previous_balance_sheet(client: TestClient, ref: Session) -> None:
    load(
        ref,
        bs(2025, "2025-12-31", total_assets="10"),
        bs(2024, "2024-12-28", total_assets="8"),
        bs(2024, "2024-12-31", total_assets="9"),
    )
    r = one(rows(client), "total_assets", "2025-12-31")
    assert (r["reason"], r["previous"], r["growth_value"]) == (
        "ambiguous_previous_period",
        None,
        None,
    )


def test_quarter_on_quarter_and_prior_q4(client: TestClient, ref: Session) -> None:
    load(
        ref,
        st(2025, "2025-04-01", "2025-06-30", q=2, net_revenue="30"),
        st(2025, "2025-01-01", "2025-03-31", q=1, net_revenue="20"),
        st(2024, "2024-10-01", "2024-12-31", q=4, net_revenue="0"),
        bs(2025, "2025-06-30", q=2, total_assets="5"),
        bs(2025, "2025-03-31", q=1, total_assets="4"),
    )
    items = rows(client, "quarterly_qoq")
    q2 = one(items, "net_revenue", "2025-06-30")
    assert (q2["growth_percent"], q2["previous"]["fiscal_quarter"]) == ("50.00", 1)
    q1 = one(items, "net_revenue", "2025-03-31")  # Q1 against Q4 of the previous year
    assert (q1["status"], q1["reason"], q1["absolute_change"]) == (
        "change_only",
        "prior_zero",
        "20.000000",
    )
    assert q1["previous"]["fiscal_year"] == 2024
    assets = one(items, "total_assets", "2025-06-30")
    assert (assets["growth_percent"], assets["statement_type"]) == ("25.00", "balance_sheet")
    assert rows(client, "annual_yoy") == []  # quarters never appear in annual comparisons


def test_label_that_contradicts_dates(client: TestClient, ref: Session) -> None:
    load(
        ref,
        st(2025, "2025-04-01", "2025-06-30", q=3, net_revenue="30"),  # "Q3" with Q2's dates
        st(2025, "2025-01-01", "2025-03-31", q=1, net_revenue="20"),
    )
    r = one(rows(client, "quarterly_qoq"), "net_revenue", "2025-06-30")
    assert (r["status"], r["reason"], r["growth_value"]) == (
        "not_comparable",
        "period_mismatch",
        None,
    )
    assert (
        r["previous"]["fiscal_quarter"] == 1 and r["previous"]["value"] is None
    )  # shown, not used


def test_quarter_year_on_year(client: TestClient, ref: Session) -> None:
    load(
        ref,
        st(2025, "2025-04-01", "2025-06-30", q=2, net_revenue="30"),
        st(2024, "2024-04-01", "2024-06-30", q=2, net_revenue="20"),
        st(2025, "2025-01-01", "2025-03-31", q=1, net_revenue="25"),
    )
    r = one(rows(client, "quarterly_yoy"), "net_revenue", "2025-06-30")
    assert (r["growth_percent"], r["previous"]["period_end"]) == ("50.00", "2024-06-30")


def test_annual_and_q4_on_the_same_dates_never_pair(client: TestClient, ref: Session) -> None:
    load(
        ref,
        bs(2025, "2025-12-31", total_assets="12"),
        bs(2024, "2024-12-31", total_assets="10"),
        bs(2025, "2025-12-31", q=4, total_assets="100"),
        bs(2024, "2024-12-31", q=4, total_assets="50"),
    )
    annual = one(rows(client, "annual_yoy"), "total_assets", "2025-12-31")
    quarter = one(rows(client, "quarterly_yoy"), "total_assets", "2025-12-31")
    assert (annual["growth_percent"], quarter["growth_percent"]) == ("20.00", "100.00")


def test_scopes_are_never_mixed(client: TestClient, ref: Session) -> None:
    load(ref, YEARS[0], st(2024, "2024-01-01", "2024-12-31", scope="separate", net_revenue="1"))
    items = rows(client, scope="consolidated")
    assert {r["reason"] for r in items} == {"missing_previous_period"}
    assert {r["scope"] for r in rows(client, scope="separate")} == {"separate"}


def test_missing_values_on_either_side(client: TestClient, ref: Session) -> None:
    load(
        ref,
        st(2025, "2025-01-01", "2025-12-31", net_revenue="120"),
        st(2024, "2024-01-01", "2024-12-31", gross_profit="30"),
    )
    items = rows(client, fiscal_year=2025)
    assert [(r["metric_code"], r["reason"]) for r in items] == [
        ("net_revenue", "missing_previous_value"),
        ("gross_profit", "missing_current_value"),
    ]
    gross = one(items, "gross_profit")
    assert (gross["current"]["value"], gross["previous"]["value"]) == (None, "30.000000")
    assert gross["current"]["source"] is None  # never a zero or a guessed figure


def test_cash_flow_without_a_stand_alone_previous_quarter(client: TestClient, ref: Session) -> None:
    load(
        ref,
        st(2026, "2026-01-01", "2026-03-31", kind="cash_flow", q=1, operating_cash_flow="7"),
        st(2025, "2025-10-01", "2025-12-31", q=4, net_revenue="5"),  # an income statement only
    )
    r = one(rows(client, "quarterly_qoq"), "operating_cash_flow")
    assert (r["reason"], r["absolute_change"]) == ("missing_previous_period", None)


# ---------------------------------------------------------------- revisions and evidence (M13, M17)


def _statement_evidence(ref: Session, end: str, revision: int) -> Evidence:
    return ref.scalars(
        select(Evidence)
        .join(FinancialStatement, FinancialStatement.source_evidence_id == Evidence.id)
        .where(
            FinancialStatement.reporting_period_end == date.fromisoformat(end),
            FinancialStatement.revision == revision,
        )
    ).one()


def test_restated_previous_year_is_used_and_disclosed(client: TestClient, ref: Session) -> None:
    load(ref, *YEARS)
    load(ref, st(2024, "2024-01-01", "2024-12-31", revision=2, net_revenue="80"))
    r = one(rows(client), "net_revenue", "2025-12-31")
    assert (r["previous"]["revision"], r["previous"]["value"], r["growth_percent"]) == (
        2,
        "80.000000",
        "50.00",
    )


@pytest.mark.parametrize(
    ("decision", "code"),
    [
        (ReviewDecision.REJECTED, "input_disputed_or_rejected"),
        (ReviewDecision.DISPUTED, "input_disputed_or_rejected"),
        (ReviewDecision.SUPERSEDED, "input_superseded"),
    ],
)
def test_bad_latest_revision_never_falls_back(
    client: TestClient, ref: Session, decision: ReviewDecision, code: str
) -> None:
    load(ref, *YEARS)
    load(ref, st(2024, "2024-01-01", "2024-12-31", revision=2, net_revenue="80"))
    _review(ref, _statement_evidence(ref, "2024-12-31", 1), ReviewDecision.VERIFIED)
    _review(ref, _statement_evidence(ref, "2024-12-31", 2), decision)
    r = one(rows(client), "net_revenue", "2025-12-31")
    assert (r["status"], r["reason"], r["growth_value"]) == ("not_comparable", code, None)
    assert r["previous"]["revision"] == 2  # the verified revision 1 is not used instead


def test_verified_and_sample_labels(client: TestClient, ref: Session) -> None:
    load(ref, *YEARS)
    for ev in ref.scalars(select(Evidence).where(Evidence.entity_type == "financial_statement")):
        _review(ref, ev, ReviewDecision.VERIFIED)
    r = one(rows(client), "net_revenue", "2025-12-31")
    assert (r["input_verification"], r["status"]) == ("all_verified", "computed")
    assert r["current"]["source"]["verification_status"] == "verified"  # the figure's evidence


def test_sample_company_is_labelled_sample(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1, evidence=[evidence(status="sample")])], source=SAMPLE))
    sample = []
    for record in YEARS:
        record = dict(record)
        record["evidence"] = evidence(
            record["evidence"]["source_url"].replace("https://example.test", "fixture://"),
            status="sample",
        )
        sample.append(record)
    load(ref, *sample, source=SAMPLE)
    r = one(rows(client), "net_revenue", "2025-12-31")
    assert (r["status"], r["input_verification"]) == ("computed", "sample")


# ---------------------------------------------------------------- defensive checks (M15, M16)


def test_mixed_legacy_data_is_refused(client: TestClient, ref: Session) -> None:
    load(ref, bs(2025, "2025-12-31", total_assets="12"), bs(2024, "2024-12-31", total_assets="10"))
    co = ref.scalars(select(Company)).one()
    _disable_triggers(ref)  # a legacy mixed row, as before migration 8de09b58f4c2
    sid = uuid.uuid4()
    ev = _evidence(ref, VerificationStatus.SAMPLE, EntityType.FINANCIAL_STATEMENT, sid)
    _statement(ref, co, ev, sid, year=2023)
    ref.flush()
    ref.execute(
        text(
            "INSERT INTO financial_metrics (id, financial_statement_id, metric_code, metric_name, "
            "value, unit, source_page, reported_value, reported_scale) VALUES "
            "(gen_random_uuid(), :st, 'total_assets', 'x', 8, 'VND', 1, 8, 1)"
        ),
        {"st": sid},
    )
    ref.execute(text("SET LOCAL session_replication_role = origin"))
    items = rows(client)
    assert len(items) == 3
    for r in items:  # the company is mixed, so even its consistent pairs are refused
        assert (r["reason"], r["input_verification"], r["growth_value"]) == (
            "mixed_sample_and_real",
            None,
            None,
        )


def test_unit_mismatch_written_directly(client: TestClient, ref: Session) -> None:
    load(ref, *YEARS)
    _disable_triggers(ref)  # history is append-only; this simulates a legacy direct write
    ref.execute(
        text(
            "UPDATE financial_metrics SET unit = 'VND/share' WHERE metric_code = 'net_revenue' "
            "AND financial_statement_id IN (SELECT id FROM financial_statements "
            "WHERE fiscal_year = 2024)"
        )
    )
    ref.execute(text("SET LOCAL session_replication_role = origin"))
    r = one(rows(client), "net_revenue", "2025-12-31")
    assert (r["reason"], r["growth_value"]) == ("unit_or_currency_mismatch", None)


# ---------------------------------------------------------------- API rules (A2, A3, A7, A9)


def test_filters_paging_and_errors(client: TestClient, ref: Session) -> None:
    load(ref, *YEARS)
    url = f"{API}/companies/{cid(client)}/comparisons"
    assert [r["metric_code"] for r in rows(client, metric="net_profit")] == ["net_profit"] * 2
    assert {r["current"]["fiscal_year"] for r in rows(client, fiscal_year=2024)} == {2024}
    page = client.get(url, params={"type": "annual_yoy", "limit": 1, "offset": 1}).json()
    assert (page["total"], len(page["items"]), page["items"][0]["metric_code"]) == (
        4,
        1,
        "net_profit",
    )
    past = client.get(url, params={"type": "annual_yoy", "offset": 50}).json()
    assert (past["total"], past["items"]) == (4, [])
    for bad in (
        {},
        {"type": "monthly"},
        {"type": "annual_yoy", "scope": "group"},
        {"type": "annual_yoy", "metric": "roe"},
        {"type": "annual_yoy", "metric": "not_a_metric"},
        {"type": "annual_yoy", "limit": 0},
        {"type": "annual_yoy", "limit": 101},
        {"type": "annual_yoy", "fiscal_year": 1989},
    ):
        assert client.get(url, params=bad).status_code == 422, bad
    missing = client.get(
        f"{API}/companies/00000000-0000-0000-0000-000000000000/comparisons",
        params={"type": "annual_yoy"},
    )
    assert missing.status_code == 404


def test_read_only_and_bounded_queries(client: TestClient, ref: Session) -> None:
    load(ref, *YEARS)
    ref.flush()

    def counts() -> tuple[int | None, int | None]:
        return (
            ref.scalar(select(func.count()).select_from(FinancialStatement)),
            ref.scalar(select(func.count()).select_from(FinancialMetric)),
        )

    before = counts()
    rows(client)
    assert counts() == before  # nothing is stored
    executed: list[str] = []
    conn = ref.connection()

    def count(*args: Any) -> None:
        executed.append(str(args[2]))

    event.listen(conn, "before_cursor_execute", count)
    try:
        rows(client)
        first = len(executed)
        load(
            ref,
            st(2023, "2023-01-01", "2023-12-31", net_revenue="90"),
            bs(2023, "2023-12-31", total_assets="1"),
        )
        ref.flush()
        executed.clear()
        rows(client)
        assert len(executed) == first  # same number of queries for more years
    finally:
        event.remove(conn, "before_cursor_execute", count)
    assert not any(s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for s in executed)


def test_openapi_documents_comparisons(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    props = spec["components"]["schemas"]["PeriodComparisonOut"]["properties"]
    assert "verification_status" not in props
    for field in ("absolute_change", "growth_value", "growth_percent"):
        types = json.dumps(props[field])
        assert '"string"' in types and '"number"' not in types
    params = {
        p["name"]
        for p in spec["paths"]["/api/v1/companies/{company_id}/comparisons"]["get"]["parameters"]
    }
    assert {"type", "scope", "metric", "fiscal_year", "limit", "offset"} <= params

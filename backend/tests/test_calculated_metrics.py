"""WS4-2: ROE and ROA from stored statements through the API. All data is fictional test data
(example.test URLs, TST tickers)."""

import json
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from app.ingestion.review import record_review
from app.models import (
    Evidence,
    FinancialMetric,
    FinancialStatement,
    ReviewDecision,
)
from tests.factories import SOURCE, bundle, company, evidence, run, statement

API = "/api/v1"
SAMPLE = dict(SOURCE, name="Sample", source_type="sample_fixture")


def income(fy: int, start: str, end: str, scope: str = "consolidated", **metrics: str) -> Any:
    return statement(
        reporting_period_start=start,
        reporting_period_end=end,
        fiscal_year=fy,
        scope=scope,
        evidence=evidence(f"https://example.test/is-{scope}-{end}.pdf"),
        metrics=metrics,
    )


def balance(
    fy: int, end: str, scope: str = "consolidated", revision: int = 1, quarter: int | None = None,
    **metrics: str,
) -> Any:  # fmt: skip
    record = statement(
        statement_type="balance_sheet",
        reporting_period_start=end,
        reporting_period_end=end,
        fiscal_year=fy,
        scope=scope,
        revision=revision,
        evidence=evidence(f"https://example.test/bs-{scope}-{end}-r{revision}-q{quarter}.pdf"),
        metrics=metrics,
    )
    if quarter is not None:
        record["fiscal_quarter"] = quarter
    return record


def load(ref: Session, *statements: Any, source: dict[str, Any] | None = None) -> None:
    if source is None:
        run(ref, bundle([company(1)]))
    r = run(ref, bundle(statements=list(statements), source=source))
    assert r.status.value == "succeeded", r.issues


def results(client: TestClient, **params: Any) -> list[dict[str, Any]]:
    cid = client.get(f"{API}/companies").json()["items"][0]["id"]
    res = client.get(f"{API}/companies/{cid}/calculated-metrics", params=params)
    assert res.status_code == 200, res.text
    raw = res.text
    assert "E-" not in raw and "E+" not in raw  # fixed-point decimals only
    body = json.loads(raw, parse_float=lambda s: pytest.fail(f"float in JSON: {s}"))
    return list(body["items"])


def one(items: list[dict[str, Any]], formula_id: str, fy: int = 2025) -> dict[str, Any]:
    return next(r for r in items if r["formula_id"] == formula_id and r["fiscal_year"] == fy)


def issues(r: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    return [(i["code"], i["role"], i["metric_code"], i["period_end"]) for i in r["issues"]]


CALENDAR = (
    income(2025, "2025-01-01", "2025-12-31", net_profit_parent="30", net_profit="40"),
    balance(2025, "2025-12-31", equity_parent="220", total_equity="260", total_assets="1000"),
    balance(2024, "2024-12-31", equity_parent="180", total_equity="240", total_assets="900"),
)


# ---------------------------------------------------------------- computed, with provenance


def test_consolidated_roe_and_roa(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR)
    items = results(client)
    assert [(r["code"], r["formula_id"]) for r in items] == [
        ("roa", "roa_avg_assets"),
        ("roe", "roe_parent_avg_equity"),
    ]
    roe = one(items, "roe_parent_avg_equity")
    assert (roe["status"], roe["reason"], roe["issues"]) == ("computed", None, [])
    assert (roe["value"], roe["percent"], roe["denominator_average"]) == (
        "0.1500000000",
        "15.00",
        "200.0000000",
    )
    roa = one(items, "roa_avg_assets")
    # 40 / 950 = 0.04210526315789...: one half-even rounding at 10 decimals, half-up at 2.
    assert (roa["value"], roa["percent"], roa["denominator_average"]) == (
        "0.0421052632",
        "4.21",
        "950.0000000",
    )
    assert roe["kind"] == "calculated" and roe["formula_version"] == 1
    assert (roe["period_start"], roe["period_end"], roe["scope"]) == (
        "2025-01-01",
        "2025-12-31",
        "consolidated",
    )
    assert roe["input_verification"] == "some_unverified"  # imported evidence is unverified
    assert "verification_status" not in roe


def test_every_input_carries_its_provenance(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR)
    roe = one(results(client), "roe_parent_avg_equity")
    by_role = {i["role"]: i for i in roe["inputs"]}
    assert set(by_role) == {"numerator", "denominator_closing", "denominator_opening"}
    n, c, o = by_role["numerator"], by_role["denominator_closing"], by_role["denominator_opening"]
    assert (n["metric_code"], n["value"], n["period_end"]) == (
        "net_profit_parent",
        "30.000000",
        "2025-12-31",
    )
    assert (c["metric_code"], c["value"], o["value"]) == (
        "equity_parent",
        "220.000000",
        "180.000000",
    )
    assert o["metric_name_vi"] == "Vốn chủ sở hữu của cổ đông công ty mẹ"
    assert o["metric_name_en"] == "Equity attributable to owners of the parent"
    assert (
        o["source"]["document_url"]
        == "https://example.test/bs-consolidated-2024-12-31-r1-qNone.pdf"
    )
    assert o["source"]["page"] == 7 and o["source"]["verification_status"] == "unverified"
    assert (o["reported_value"], o["reported_scale"], o["revision"]) == ("180.000000", 1, 1)


# ---------------------------------------------------------------- missing inputs (D3, D12)


def test_equity_parent_is_never_replaced_by_total_equity(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", net_profit_parent="30", net_profit="40"),
        balance(2025, "2025-12-31", total_equity="260", total_assets="1000"),
        balance(2024, "2024-12-31", equity_parent="180", total_equity="240", total_assets="900"),
    )
    items = results(client)
    roe = one(items, "roe_parent_avg_equity")
    assert (roe["status"], roe["reason"], roe["value"]) == ("not_computable", "missing_input", None)
    assert issues(roe) == [("missing_input", "denominator_closing", "equity_parent", "2025-12-31")]
    assert one(items, "roa_avg_assets")["status"] == "computed"  # ROA is unaffected
    assert (roe["issues"][0]["metric_name_vi"], roe["issues"][0]["metric_name_en"]) == (
        "Vốn chủ sở hữu của cổ đông công ty mẹ",
        "Equity attributable to owners of the parent",
    )
    assert {i["metric_code"] for i in roe["inputs"]} == {"net_profit_parent", "equity_parent"}


def test_missing_opening_balance_prevents_calculation(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR[:2])
    for r in results(client):
        assert (r["status"], r["reason"], r["value"], r["percent"]) == (
            "not_computable",
            "missing_opening_balance",
            None,
            None,
        )
        assert issues(r)[0][1:] == (
            "denominator_opening",
            r["issues"][0]["metric_code"],
            "2024-12-31",
        )
        assert len(r["inputs"]) == 2  # what was found is still shown


def test_opening_without_the_figure(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR[:2], balance(2024, "2024-12-31", total_assets="900"))
    roe = one(results(client), "roe_parent_avg_equity")
    assert issues(roe) == [
        ("missing_opening_balance", "denominator_opening", "equity_parent", "2024-12-31")
    ]


def test_missing_numerator_and_opening_are_both_listed(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", net_profit="40"),
        balance(2025, "2025-12-31", equity_parent="220", total_assets="1000"),
    )
    roe = one(results(client), "roe_parent_avg_equity")
    assert roe["reason"] == "missing_input"
    assert issues(roe) == [
        ("missing_input", "numerator", "net_profit_parent", "2025-12-31"),
        ("missing_opening_balance", "denominator_opening", "equity_parent", "2024-12-31"),
    ]


def test_no_income_statement_means_no_result(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR[1:])
    assert results(client) == []


# ---------------------------------------------------------------- opening-balance matching


@pytest.mark.parametrize(
    ("opening_end", "expected"),
    [
        ("2024-12-31", "computed"),
        ("2024-12-24", "computed"),  # 7 days early: inside the window
        ("2024-12-23", "missing_opening_balance"),  # 8 days: outside
    ],
)
def test_seven_day_window(
    client: TestClient, ref: Session, opening_end: str, expected: str
) -> None:
    load(ref, *CALENDAR[:2], balance(2024, opening_end, equity_parent="180", total_assets="900"))
    roe = one(results(client), "roe_parent_avg_equity")
    assert (roe["reason"] or roe["status"]) == expected


def test_two_candidates_are_ambiguous(client: TestClient, ref: Session) -> None:
    load(
        ref,
        *CALENDAR[:2],
        balance(2024, "2024-12-27", equity_parent="170", total_assets="880"),
        balance(2024, "2024-12-31", equity_parent="180", total_assets="900"),
    )
    for r in results(client):
        assert (r["reason"], r["value"]) == ("ambiguous_opening_balance", None)


def test_non_calendar_fiscal_year(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2024-04-01", "2025-03-31", net_profit_parent="30", net_profit="40"),
        balance(2025, "2025-03-31", equity_parent="220", total_assets="1000"),
        balance(2024, "2024-03-31", equity_parent="180", total_assets="900"),
    )
    assert one(results(client), "roe_parent_avg_equity")["value"] == "0.1500000000"


def test_quarterly_and_closing_balance_sheets_are_never_the_opening(
    client: TestClient, ref: Session
) -> None:
    load(
        ref,
        *CALENDAR[:2],
        balance(2024, "2024-12-31", quarter=4, equity_parent="180", total_assets="900"),
    )
    roe = one(results(client), "roe_parent_avg_equity")
    assert roe["reason"] == "missing_opening_balance"


def test_closing_must_match_the_income_statement_end(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", net_profit_parent="30", net_profit="40"),
        balance(2025, "2025-12-30", equity_parent="220", total_assets="1000"),
        balance(2024, "2024-12-31", equity_parent="180", total_assets="900"),
    )
    roe = one(results(client), "roe_parent_avg_equity")
    assert issues(roe) == [("missing_input", "denominator_closing", "equity_parent", "2025-12-31")]


# ---------------------------------------------------------------- scope


def test_scopes_are_never_mixed(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", scope="separate", net_profit="20"),
        balance(2025, "2025-12-31", scope="separate", total_equity="110", total_assets="500"),
        *CALENDAR[1:],  # consolidated balance sheets only for the opening
    )
    items = results(client)
    assert {(r["scope"], r["formula_id"]) for r in items} == {
        ("separate", "roe_separate_avg_equity"),
        ("separate", "roa_avg_assets"),
    }
    for r in items:
        assert r["reason"] == "missing_opening_balance"


def test_separate_roe_uses_total_equity(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", scope="separate", net_profit="20"),
        balance(2025, "2025-12-31", scope="separate", total_equity="110", total_assets="500"),
        balance(2024, "2024-12-31", scope="separate", total_equity="90", total_assets="300"),
    )
    items = results(client, scope="separate")
    roe = one(items, "roe_separate_avg_equity")
    assert (roe["value"], roe["percent"]) == ("0.2000000000", "20.00")
    assert {i["metric_code"] for i in roe["inputs"]} == {"net_profit", "total_equity"}
    assert one(items, "roa_avg_assets")["value"] == "0.0500000000"


# ---------------------------------------------------------------- revisions and evidence


def _evidence_of(ref: Session, end: str, revision: int = 1) -> Evidence:
    return ref.scalars(
        select(Evidence)
        .join(FinancialStatement, FinancialStatement.source_evidence_id == Evidence.id)
        .where(
            FinancialStatement.statement_type == "balance_sheet",
            FinancialStatement.reporting_period_end == date.fromisoformat(end),
            FinancialStatement.revision == revision,
        )
    ).one()


def _review(ref: Session, ev: Evidence, decision: ReviewDecision) -> None:
    record_review(
        ref,
        evidence_id=ev.id,
        from_status=ev.verification_status,
        decision=decision,
        curator="Curator A",
        reviewer="Reviewer B",
        checked_against="Fictional test document p. 7",
    )
    ref.expire_all()


def test_latest_revision_is_used_and_disclosed(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR)
    load(ref, balance(2025, "2025-12-31", revision=2, equity_parent="300", total_assets="1100"))
    roe = one(results(client), "roe_parent_avg_equity")
    closing = next(i for i in roe["inputs"] if i["role"] == "denominator_closing")
    assert (closing["value"], closing["revision"]) == ("300.000000", 2)
    assert roe["value"] == "0.1250000000"  # 30 / ((180 + 300) / 2)


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
    load(ref, *CALENDAR)
    load(ref, balance(2025, "2025-12-31", revision=2, equity_parent="300", total_assets="1100"))
    _review(ref, _evidence_of(ref, "2025-12-31", revision=1), ReviewDecision.VERIFIED)
    _review(ref, _evidence_of(ref, "2025-12-31", revision=2), decision)
    for r in results(client):
        assert (r["status"], r["reason"], r["value"]) == ("not_computable", code, None)
        closing = next(i for i in r["inputs"] if i["role"] == "denominator_closing")
        assert closing["revision"] == 2  # the verified revision 1 is not used instead


def test_all_verified_inputs(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR)
    for ev in ref.scalars(select(Evidence).where(Evidence.entity_type == "financial_statement")):
        _review(ref, ev, ReviewDecision.VERIFIED)
    for r in results(client):
        assert r["input_verification"] == "all_verified" and r["status"] == "computed"
        assert "verification_status" not in r  # the ratio itself is never "verified"


def test_sample_company_results_are_labelled_sample(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1, evidence=[evidence(status="sample")])], source=SAMPLE))

    def sample(record: Any) -> Any:
        record["evidence"] = evidence(
            record["evidence"]["source_url"].replace("https://example.test", "fixture://"),
            status="sample",
        )
        return record

    load(ref, *(sample(dict(s)) for s in CALENDAR), source=SAMPLE)
    for r in results(client):
        assert (r["status"], r["input_verification"]) == ("computed", "sample")


# ---------------------------------------------------------------- signs, filters, API contract


def test_negative_equity_is_not_meaningful(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", net_profit_parent="-30", net_profit="-40"),
        balance(2025, "2025-12-31", equity_parent="40", total_assets="1000"),
        balance(2024, "2024-12-31", equity_parent="-10", total_assets="900"),
    )
    items = results(client)
    roe = one(items, "roe_parent_avg_equity")
    assert issues(roe) == [
        ("equity_not_positive", "denominator_opening", "equity_parent", "2024-12-31")
    ]
    roa = one(items, "roa_avg_assets")
    assert (roa["value"], roa["percent"]) == ("-0.0421052632", "-4.21")  # a loss, shown as is


def test_zero_profit_is_a_fixed_point_zero(client: TestClient, ref: Session) -> None:
    load(
        ref,
        income(2025, "2025-01-01", "2025-12-31", net_profit_parent="0", net_profit="-0.000001"),
        *CALENDAR[1:],
    )
    items = results(client)
    assert one(items, "roe_parent_avg_equity")["value"] == "0.0000000000"
    roa = one(items, "roa_avg_assets")
    # -0.000001 / 950 = -0.00000000105...: the ratio keeps its sign; the percent rounds to
    # zero and is never "-0.00".
    assert (roa["value"], roa["percent"]) == ("-0.0000000011", "0.00")


def test_filters_pagination_and_404(client: TestClient, ref: Session) -> None:
    load(
        ref,
        *CALENDAR,
        income(2024, "2024-01-01", "2024-12-31", net_profit_parent="20", net_profit="25"),
    )
    assert [(r["fiscal_year"], r["code"]) for r in results(client)] == [
        (2025, "roa"),
        (2025, "roe"),
        (2024, "roa"),
        (2024, "roe"),
    ]
    assert {r["fiscal_year"] for r in results(client, fiscal_year=2024)} == {2024}
    assert results(client, scope="separate") == []
    cid = client.get(f"{API}/companies").json()["items"][0]["id"]
    page = client.get(f"{API}/companies/{cid}/calculated-metrics", params={"limit": 1, "offset": 1})
    assert (page.json()["total"], len(page.json()["items"])) == (4, 1)
    missing = client.get(f"{API}/companies/00000000-0000-0000-0000-000000000000/calculated-metrics")
    assert missing.status_code == 404


def _row_counts(ref: Session) -> tuple[int | None, int | None]:
    return (
        ref.scalar(select(func.count()).select_from(FinancialStatement)),
        ref.scalar(select(func.count()).select_from(FinancialMetric)),
    )


def test_read_only_and_bounded_queries(client: TestClient, ref: Session) -> None:
    load(ref, *CALENDAR)
    ref.flush()
    before = _row_counts(ref)
    results(client)
    assert _row_counts(ref) == before  # nothing is stored
    statements_run: list[str] = []
    conn = ref.connection()

    def count(*args: Any) -> None:
        statements_run.append(str(args[2]))

    event.listen(conn, "before_cursor_execute", count)
    try:
        results(client)
        first = len(statements_run)
        load(
            ref,
            income(2024, "2024-01-01", "2024-12-31", net_profit_parent="20", net_profit="25"),
            balance(2023, "2023-12-31", equity_parent="150", total_assets="800"),
        )
        ref.flush()  # the import's own pending writes are not part of the request
        statements_run.clear()
        results(client)
        assert len(statements_run) == first  # same number of queries for more years
    finally:
        event.remove(conn, "before_cursor_execute", count)
    assert not any(
        s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for s in statements_run
    )


def test_openapi_documents_calculated_metrics(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    props = schemas["CalculatedMetricOut"]["properties"]
    assert "verification_status" not in props
    assert {
        "value",
        "percent",
        "denominator_average",
        "issues",
        "inputs",
        "input_verification",
    } <= set(props)
    value_types = json.dumps(props["value"])
    assert '"string"' in value_types and '"number"' not in value_types

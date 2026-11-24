"""WS3: per-figure source transparency in GET /companies/{id}/financial-statements.

All data is fictional test data (example.test URLs, TST tickers)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas import linkable_url
from app.ingestion.review import record_review
from app.models import (
    Company,
    Evidence,
    FinancialStatement,
    ReviewDecision,
    VerificationStatus,
)
from tests.factories import SOURCE, bundle, company, evidence, run, statement
from tests.test_models import fails, new_company

API = "/api/v1"
SAMPLE = dict(SOURCE, name="Sample", source_type="sample_fixture")
SOURCE_KEYS = {
    "evidence_id",
    "document_title",
    "document_url",
    "link_status",
    "page",
    "verification_status",
}


def statements(client: TestClient, ref: Session, ticker: str = "TST1") -> list[dict[str, Any]]:
    cid = ref.scalars(select(Company.id).where(Company.short_name == f"Test Co {ticker[-1]}")).one()
    res = client.get(f"{API}/companies/{cid}/financial-statements")
    assert res.status_code == 200, res.text
    return list(res.json()["items"])


def metric(items: list[dict[str, Any]], code: str, **where: Any) -> dict[str, Any]:
    st = next(s for s in items if all(s[k] == v for k, v in where.items()))
    return next(m for m in st["metrics"] if m["metric_code"] == code)


# ---------------------------------------------------------------- C01, C06: valid provenance


def test_each_figure_carries_its_document_and_page(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    fs = statement(amount_scale="trieu_dong", metrics={"net_revenue": "1234567.89"})
    fs["metrics"].append({"code": "eps_basic", "value": "4321", "source_page": 9})
    fs["evidence"]["document_title"] = "Consolidated FS 2025 (fictional)"
    assert run(ref, bundle(statements=[fs])).status.value == "succeeded"

    items = statements(client, ref)
    revenue = metric(items, "net_revenue")
    ev_id = ref.scalars(select(FinancialStatement.source_evidence_id)).one()
    assert revenue["source"] == {
        "evidence_id": str(ev_id),
        "document_title": "Consolidated FS 2025 (fictional)",
        "document_url": "https://example.test/fs-2025.pdf",
        "link_status": "linkable",
        "page": 7,
        "verification_status": "unverified",
    }
    # Exact decimal strings, never floats; as-printed value and scale kept beside full units.
    assert revenue["value"] == "1234567890000.000000"
    assert revenue["reported_value"] == "1234567.890000"
    assert revenue["reported_scale"] == 1_000_000
    eps = metric(items, "eps_basic")
    assert (eps["value"], eps["reported_value"], eps["reported_scale"]) == (
        "4321.000000",
        "4321.000000",
        1,
    )
    assert eps["source"]["page"] == 9  # each figure has its own page


def test_decimals_are_json_strings(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    run(ref, bundle(statements=[statement(metrics={"net_profit": "-0.000001"})]))
    cid = ref.scalars(select(Company.id)).one()
    raw = client.get(f"{API}/companies/{cid}/financial-statements").text
    body = json.loads(raw, parse_float=lambda s: pytest.fail(f"float in JSON: {s}"))
    m = body["items"][0]["metrics"][0]
    assert m["value"] == "-0.000001" and m["reported_value"] == "-0.000001"


# ---------------------------------------------------------------- C05: no shared sources


def test_figures_link_to_their_own_statement_document(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    annual = statement(metrics={"net_revenue": "10"})
    quarter = statement(
        fiscal_quarter=4,
        reporting_period_start="2025-10-01",
        evidence=evidence("https://example.test/q4-2025.pdf"),
        metrics={"net_revenue": "3"},
    )
    quarter["metrics"][0]["source_page"] = 21
    assert run(ref, bundle(statements=[annual, quarter])).status.value == "succeeded"

    items = statements(client, ref)
    fy = metric(items, "net_revenue", fiscal_quarter=None)
    q4 = metric(items, "net_revenue", fiscal_quarter=4)
    assert (fy["source"]["document_url"], fy["source"]["page"]) == (
        "https://example.test/fs-2025.pdf",
        7,
    )
    assert (q4["source"]["document_url"], q4["source"]["page"]) == (
        "https://example.test/q4-2025.pdf",
        21,
    )
    assert fy["source"]["evidence_id"] != q4["source"]["evidence_id"]


def test_company_evidence_is_never_used_as_a_figure_source(
    client: TestClient, ref: Session
) -> None:
    run(ref, bundle([company(1, evidence=[evidence("https://example.test/annual-report.pdf")])]))
    run(ref, bundle(statements=[statement()]))
    sources = {m["source"]["document_url"] for s in statements(client, ref) for m in s["metrics"]}
    assert sources == {"https://example.test/fs-2025.pdf"}


# ---------------------------------------------------------------- C02, C04, C07: missing and sample


def test_sample_figures_show_unknown_page_and_no_link(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1, evidence=[evidence(status="sample")])], source=SAMPLE))
    fs = statement(evidence=evidence("fixture://fs-2025", status="sample"))
    for m in fs["metrics"]:
        del m["source_page"]
    assert run(ref, bundle(statements=[fs], source=SAMPLE)).status.value == "succeeded"

    src = statements(client, ref)[0]["metrics"][0]["source"]
    assert src["page"] is None  # unknown, never 0
    assert src["document_url"] is None and src["link_status"] == "not_linkable"
    assert src["verification_status"] == "sample"


# ---------------------------------------------------------------- C03, C04: impossible by schema


def test_a_statement_cannot_exist_without_evidence(ref: Session) -> None:
    c = new_company(ref)
    fails(
        ref,
        lambda: ref.add(
            FinancialStatement(
                company_id=c.id,
                reporting_period_start=date(2025, 1, 1),
                reporting_period_end=date(2025, 12, 31),
                fiscal_year=2025,
                statement_type="income_statement",
                scope="consolidated",
                currency="VND",
                source_evidence_id=None,
            )
        ),
    )


def test_evidence_cannot_lack_a_url(ref: Session) -> None:
    from tests.test_verification import new_evidence

    ev = new_evidence(ref)
    ref.expunge(ev)
    fails(ref, lambda: ref.add(Evidence(**{**_cols(ev), "id": None, "source_url": None})))


def _cols(ev: Evidence) -> dict[str, Any]:
    return {c.name: getattr(ev, c.key) for c in Evidence.__table__.columns if c.key != "created_at"}


# ---------------------------------------------------------------- C08: verification status


def test_figure_status_follows_reviews(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    run(ref, bundle(statements=[statement()]))
    ev = ref.scalars(select(Evidence).where(Evidence.entity_type == "financial_statement")).one()
    record_review(
        ref,
        evidence_id=ev.id,
        from_status=VerificationStatus.UNVERIFIED,
        decision=ReviewDecision.DISPUTED,
        curator="Curator A",
        reviewer="Reviewer B",
        checked_against="FS 2025 p. 7 (fictional)",
    )
    ref.expire_all()
    statuses = {
        m["source"]["verification_status"] for s in statements(client, ref) for m in s["metrics"]
    }
    assert statuses == {"disputed"}


# ---------------------------------------------------------------- C09: URL safety


@pytest.mark.parametrize(
    "url",
    [
        "https://example.test/fs.pdf",
        "http://example.test/fs.pdf?x=1",
        "HTTPS://Example.test/a%20b.pdf",
        "https://xn--bcher-kva.example/fs.pdf",
    ],
)
def test_linkable_urls(url: str) -> None:
    assert linkable_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,hi",
        "file:///etc/passwd",
        "fixture://sample",
        "ftp://example.test/fs.pdf",
        "https://",
        "https:///path-only",
        "//example.test/protocol-relative",
        "https://user:pw@example.test/fs.pdf",
        "https://example.test@evil.test/fs.pdf",
        " https://example.test/leading-space",
        "https://exa mple.test/space",
        "https://example.test/\nnewline",
        "https://example.test/\x7f",
        "https://[::1/unclosed",
        "",
    ],
)
def test_unsafe_or_malformed_urls_are_not_links(url: str) -> None:
    assert linkable_url(url) is None


# ---------------------------------------------------------------- C10, C11: compatibility


def test_existing_fields_unchanged_and_source_exposes_nothing_private(
    client: TestClient, ref: Session
) -> None:
    run(ref, bundle([company(1)]))
    run(ref, bundle(statements=[statement()]))
    st = statements(client, ref)[0]
    m = st["metrics"][0]
    # Phase 1 / WS2 fields are still there with the same meaning.
    assert {"metric_code", "metric_name", "metric_name_vi", "value", "unit"} <= m.keys()
    assert st["source_evidence"]["source_url"] == "https://example.test/fs-2025.pdf"
    # The per-figure source exposes only these keys: no hash, notes, data-source ids or paths.
    assert set(m["source"]) == SOURCE_KEYS
    assert m["source"]["evidence_id"] == st["source_evidence"]["id"]


def test_openapi_documents_the_contract(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    assert set(schemas["MetricSourceOut"]["properties"]) == SOURCE_KEYS
    assert {"reported_value", "reported_scale", "source"} <= set(schemas["MetricOut"]["properties"])


def test_values_round_trip_unchanged(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    big = "99999999999999999999999999.999999"
    run(
        ref, bundle(statements=[statement(amount_scale="trieu_dong", metrics={"net_revenue": big})])
    )
    m = statements(client, ref)[0]["metrics"][0]
    assert (
        m["value"] == "9" * 32 + ".000000"
    )  # exact; Decimal(big) * 10**6 would round at 28 digits
    assert Decimal(m["reported_value"]) == Decimal(big)

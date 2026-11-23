import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.models import Company, Sector, Security
from tests.factories import bundle, company, evidence, run, statement

API = "/api/v1"


@pytest.fixture
def catalog(ref: Session) -> dict[str, Any]:
    """Deterministic fictional catalogue: 5 companies across sectors/exchanges."""
    delisted = company(5, ticker="OLD5", exchange="HNX", sector="ENERGY")
    delisted["securities"][0].update(listing_status="delisted", delisted_at="2024-01-31")
    two_listings = company(4, sector="ENERGY", english_name="Fourth Power Corp")
    two_listings["securities"].append(
        {
            "ticker": "TST4P",
            "exchange_code": "UPCOM",
            "security_type": "preferred_stock",
            "currency": "VND",
            "listing_status": "listed",
        }
    )
    r = run(
        ref,
        bundle(
            [
                company(1),
                company(2, sector="BANKING_FINANCIAL", exchange="HNX"),
                company(3, legal_name="100% Real_Name JSC"),
                two_listings,
                delisted,
            ],
            [
                statement(),
                statement(revision=2, metrics={"net_revenue": "2000000000.000001"}),
                statement(
                    fiscal_quarter=4,
                    reporting_period_start="2025-10-01",
                    metrics={"net_revenue": "1"},
                ),
            ],
        ),
    )
    assert r.status.value == "succeeded", r.issues
    ids = {c.short_name: c.id for c in ref.scalars(select(Company))}
    return {"ids": ids}


def get(client: TestClient, path: str, **params: Any) -> Any:
    res = client.get(API + path, params=params)
    assert res.status_code == 200, res.text
    return res.json()


def names(page: dict[str, Any]) -> list[str]:
    return [c["short_name"] for c in page["items"]]


# ---------------------------------------------------------------- reference


def test_exchanges(client: TestClient, ref: Session) -> None:
    page = get(client, "/exchanges")
    assert [e["code"] for e in page["items"]] == ["HNX", "HOSE", "UPCOM"]
    assert page["total"] == 3


def test_sectors_with_company_counts(client: TestClient, catalog: dict[str, Any]) -> None:
    page = get(client, "/sectors")
    counts = {s["code"]: s["company_count"] for s in page["items"]}
    assert page["total"] == 7
    assert counts["TECHNOLOGY"] == 2 and counts["ENERGY"] == 2 and counts["REAL_ESTATE"] == 0
    first = page["items"][0]
    assert first["taxonomy_version"] == "1.0.0" and first["name_vi"]
    detail = get(client, f"/sectors/{first['id']}")
    assert detail == first


def test_sector_not_found_and_bad_id(client: TestClient, ref: Session) -> None:
    res = client.get(f"{API}/sectors/{uuid.uuid4()}")
    assert res.status_code == 404 and res.json() == {"detail": "Sector not found"}
    assert client.get(f"{API}/sectors/not-a-uuid").status_code == 422


# ---------------------------------------------------------------- company list


def test_pagination_is_stable_and_complete(client: TestClient, catalog: dict[str, Any]) -> None:
    all_names = names(get(client, "/companies", limit=100))
    assert all_names == sorted(all_names)
    pages = [get(client, "/companies", limit=2, offset=o) for o in (0, 2, 4)]
    assert [n for p in pages for n in names(p)] == all_names
    assert all(p["total"] == 5 and p["limit"] == 2 for p in pages)
    assert get(client, "/companies", offset=50)["items"] == []


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"q": "test co 2"}, ["Test Co 2"]),  # case-insensitive name
        ({"q": "tst4p"}, ["Test Co 4"]),  # ticker
        ({"q": "fourth power"}, ["Test Co 4"]),  # english name
        ({"q": "100%"}, ["Test Co 3"]),  # % taken literally
        ({"q": "%"}, ["Test Co 3"]),  # not a wildcard
        ({"q": "l_name"}, ["Test Co 3"]),  # _ taken literally
        ({"q": "zzz"}, []),
        ({"sector": "ENERGY"}, ["Test Co 4", "Test Co 5"]),
        ({"exchange": "HNX"}, ["Test Co 2"]),  # Test Co 5's HNX listing is delisted
        ({"exchange": "UPCOM"}, ["Test Co 4"]),
        ({"sector": "ENERGY", "exchange": "HOSE"}, ["Test Co 4"]),
        ({"sector": "REAL_ESTATE"}, []),
        ({"exchange": "NYSE"}, []),  # well-formed but unknown
    ],
)
def test_search_and_filters(
    client: TestClient, catalog: dict[str, Any], params: dict[str, str], expected: list[str]
) -> None:
    page = get(client, "/companies", **params)
    assert names(page) == expected
    assert page["total"] == len(expected)


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"sector": "energy"},
        {"exchange": "HO SE"},
        {"q": ""},
        {"q": "x" * 101},
    ],
)
def test_invalid_query_is_422(client: TestClient, ref: Session, params: dict[str, Any]) -> None:
    res = client.get(f"{API}/companies", params=params)
    assert res.status_code == 422
    assert res.json()["detail"][0]["loc"][0] == "query"


def test_list_item_shape_hides_internal_fields(client: TestClient, catalog: dict[str, Any]) -> None:
    item = get(client, "/companies", q="Test Co 4")["items"][0]
    assert set(item) == {
        "id",
        "short_name",
        "legal_name",
        "english_name",
        "is_sample",
        "sector",
        "securities",
    }
    assert [s["ticker"] for s in item["securities"]] == ["TST4", "TST4P"]
    assert item["securities"][1]["exchange"] == {
        "code": "UPCOM",
        "name": "Unlisted Public Company Market",
    }
    assert item["sector"]["code"] == "ENERGY"


@contextmanager
def count_queries(db: Session) -> Iterator[list[str]]:
    statements: list[str] = []
    conn = db.connection()

    def before(*args: Any) -> None:
        statements.append(args[2])

    event.listen(conn, "before_cursor_execute", before)
    try:
        yield statements
    finally:
        event.remove(conn, "before_cursor_execute", before)


def test_company_list_has_no_n_plus_one(
    client: TestClient, catalog: dict[str, Any], ref: Session
) -> None:
    with count_queries(ref) as one_page:
        get(client, "/companies", limit=1)
    with count_queries(ref) as full_page:
        get(client, "/companies", limit=100)
    assert len(full_page) == len(one_page) <= 3


# ---------------------------------------------------------------- details


def test_company_detail(client: TestClient, catalog: dict[str, Any]) -> None:
    cid = catalog["ids"]["Test Co 4"]
    body = get(client, f"/companies/{cid}")
    assert body["legal_name"] == "Test Company 4 JSC"
    assert body["is_sample"] is False
    assert [s["security_type"] for s in body["securities"]] == ["common_stock", "preferred_stock"]
    assert "sector_id" not in body


def test_missing_records_are_404(client: TestClient, ref: Session) -> None:
    missing = uuid.uuid4()
    for path, detail in [
        (f"/companies/{missing}", "Company not found"),
        (f"/securities/{missing}", "Security not found"),
        (f"/companies/{missing}/evidence", "Company not found"),
        (f"/companies/{missing}/financial-statements", "Company not found"),
    ]:
        res = client.get(API + path)
        assert res.status_code == 404, path
        assert res.json() == {"detail": detail}


def test_security_detail(client: TestClient, catalog: dict[str, Any], ref: Session) -> None:
    sec = ref.scalars(select(Security).where(Security.ticker == "OLD5")).one()
    body = get(client, f"/securities/{sec.id}")
    assert body["listing_status"] == "delisted" and body["delisted_at"] == "2024-01-31"
    assert body["company"]["short_name"] == "Test Co 5"
    assert body["exchange"]["code"] == "HNX"


def test_company_evidence_includes_provenance(
    client: TestClient, catalog: dict[str, Any], ref: Session
) -> None:
    cid = catalog["ids"]["Test Co 1"]
    newer = company(
        1,
        evidence=[
            evidence(
                "https://example.test/annual-report.pdf", retrieved_at="2026-03-01T08:00:00+07:00"
            )
        ],
    )
    run(ref, bundle([newer]))
    page = get(client, f"/companies/{cid}/evidence")
    assert page["total"] == 2
    first = page["items"][0]
    assert first["source_url"] == "https://example.test/annual-report.pdf"  # newest first
    assert first["data_source"] == {
        "name": "Test disclosure source",
        "source_type": "company_disclosure",
        "commercial_usage_status": "unknown",
        "terms_url": None,
    }
    assert "data_source_id" not in first


# ---------------------------------------------------------------- financial statements


def test_financial_statements_latest_revision_and_exact_values(
    client: TestClient, catalog: dict[str, Any]
) -> None:
    cid = catalog["ids"]["Test Co 1"]
    page = get(client, f"/companies/{cid}/financial-statements")
    assert page["total"] == 2  # FY revision 2 + Q4; FY revision 1 is superseded
    fy = next(s for s in page["items"] if s["fiscal_quarter"] is None)
    assert fy["revision"] == 2 and fy["is_superseded"] is False and fy["supersedes_id"]
    values = {m["metric_code"]: m["value"] for m in fy["metrics"]}
    assert values == {"net_revenue": "2000000000.000001"}  # decimal string, not a float
    # Vietnamese label comes from the versioned metric dictionary (WS2), not from storage.
    assert fy["metrics"][0]["metric_name_vi"] == "Doanh thu thuần"
    assert fy["source_evidence"]["data_source"]["name"] == "Test disclosure source"

    history = get(client, f"/companies/{cid}/financial-statements", include_superseded=True)
    assert history["total"] == 3
    old = next(s for s in history["items"] if s["revision"] == 1 and s["fiscal_quarter"] is None)
    assert old["is_superseded"] is True
    assert {m["metric_code"]: m["value"] for m in old["metrics"]}["net_profit"] == "-25.000001"


def test_financial_statement_filters(client: TestClient, catalog: dict[str, Any]) -> None:
    cid = catalog["ids"]["Test Co 1"]
    path = f"/companies/{cid}/financial-statements"
    assert get(client, path, fiscal_year=2024)["total"] == 0
    assert get(client, path, statement_type="balance_sheet")["total"] == 0
    assert get(client, path, scope="consolidated")["total"] == 2
    assert client.get(API + path, params={"statement_type": "nope"}).status_code == 422
    other = catalog["ids"]["Test Co 2"]
    assert get(client, f"/companies/{other}/financial-statements")["total"] == 0


def test_openapi_documents_catalog(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    for p in [
        "/api/v1/sectors",
        "/api/v1/sectors/{sector_id}",
        "/api/v1/companies",
        "/api/v1/companies/{company_id}",
        "/api/v1/securities/{security_id}",
        "/api/v1/exchanges",
        "/api/v1/companies/{company_id}/evidence",
        "/api/v1/companies/{company_id}/financial-statements",
    ]:
        assert p in paths


def test_sector_is_a_real_model(ref: Session) -> None:  # guard against fixture drift
    assert ref.scalars(select(Sector.code).order_by(Sector.code)).first() == "BANKING_FINANCIAL"

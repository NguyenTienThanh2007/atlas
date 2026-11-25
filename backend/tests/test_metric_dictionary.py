"""WS4-1: metric dictionary 1.1.0 (owner decision WS4-D10: G-1 definitions, G-2 applicability,
G-4 equity_parent). All imported data is fictional test data (example.test URLs, TST tickers)."""

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.reference import (
    REFERENCE_DIR,
    MetricDictionary,
    metric_dictionary,
    metric_dictionary_document,
)
from app.models import Evidence, FinancialMetric, FinancialStatement
from tests.factories import bundle, company, run, statement

API = "/api/v1"
GLOSSARY = Path(__file__).resolve().parents[2] / "docs" / "GLOSSARY.md"
RAW = json.loads((REFERENCE_DIR / "metric_dictionary.json").read_text(encoding="utf-8"))

# Dictionary 1.0.0 exactly as released (commit 4be30b7). 1.1.0 may add fields and metrics but
# must not change any of these, except the one owner-approved rename below (RENAMED).
V1_0_0 = [
    ("net_revenue", "Net revenue", "Doanh thu thuần", "income_statement", "currency"),
    (
        "net_interest_income",
        "Net interest income",
        "Thu nhập lãi thuần",
        "income_statement",
        "currency",
    ),
    ("gross_profit", "Gross profit", "Lợi nhuận gộp", "income_statement", "currency"),
    (
        "operating_profit",
        "Operating profit",
        "Lợi nhuận thuần từ hoạt động kinh doanh",
        "income_statement",
        "currency",
    ),
    (
        "profit_before_tax",
        "Profit before tax",
        "Lợi nhuận trước thuế",
        "income_statement",
        "currency",
    ),
    ("net_profit", "Net profit after tax", "Lợi nhuận sau thuế", "income_statement", "currency"),
    (
        "net_profit_parent",
        "Net profit attributable to parent",
        "Lợi nhuận sau thuế của cổ đông công ty mẹ",
        "income_statement",
        "currency",
    ),
    (
        "eps_basic",
        "Basic earnings per share",
        "Lãi cơ bản trên cổ phiếu",
        "income_statement",
        "currency_per_share",
    ),
    ("total_assets", "Total assets", "Tổng tài sản", "balance_sheet", "currency"),
    ("total_liabilities", "Total liabilities", "Tổng nợ phải trả", "balance_sheet", "currency"),
    ("total_equity", "Total owners' equity", "Vốn chủ sở hữu", "balance_sheet", "currency"),
    (
        "cash_and_equivalents",
        "Cash and cash equivalents",
        "Tiền và các khoản tương đương tiền",
        "balance_sheet",
        "currency",
    ),
    (
        "shares_outstanding",
        "Shares outstanding",
        "Số lượng cổ phiếu đang lưu hành",
        "balance_sheet",
        "shares",
    ),
    (
        "operating_cash_flow",
        "Net cash from operating activities",
        "Lưu chuyển tiền thuần từ hoạt động kinh doanh",
        "cash_flow",
        "currency",
    ),
    (
        "investing_cash_flow",
        "Net cash from investing activities",
        "Lưu chuyển tiền thuần từ hoạt động đầu tư",
        "cash_flow",
        "currency",
    ),
    (
        "financing_cash_flow",
        "Net cash from financing activities",
        "Lưu chuyển tiền thuần từ hoạt động tài chính",
        "cash_flow",
        "currency",
    ),
]

# (non_bank, bank). Bank values come only from approved decisions (confirmed in the owner's
# review of WS4-1, 2026-11-24): not_applicable for net_revenue and gross_profit (D5); applicable
# for net_interest_income (D4) and for the inputs of bank ROE/ROA (D1, D2, D4); unclassified
# everywhere else. Non-bank
# values follow the approved specification (WS4 plan §3.1); net_interest_income stays unclassified.
APPLICABILITY = {
    "net_revenue": ("applicable", "not_applicable"),
    "net_interest_income": ("unclassified", "applicable"),
    "gross_profit": ("applicable", "not_applicable"),
    "operating_profit": ("applicable", "unclassified"),
    "profit_before_tax": ("applicable", "unclassified"),
    "net_profit": ("applicable", "applicable"),
    "net_profit_parent": ("applicable", "applicable"),
    "eps_basic": ("applicable", "unclassified"),
    "total_assets": ("applicable", "applicable"),
    "total_liabilities": ("applicable", "unclassified"),
    "total_equity": ("applicable", "applicable"),
    "equity_parent": ("applicable", "applicable"),
    "cash_and_equivalents": ("applicable", "unclassified"),
    "shares_outstanding": ("applicable", "unclassified"),
    "operating_cash_flow": ("applicable", "unclassified"),
    "investing_cash_flow": ("applicable", "unclassified"),
    "financing_cash_flow": ("applicable", "unclassified"),
}


def _glossary_statements() -> dict[str, tuple[str, str]]:
    """statement_type -> (Vietnamese, English) from GLOSSARY.md 'Statements and periods'."""
    rows = dict(
        (m[0], (m[1], m[2]))
        for m in re.findall(r"^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", GLOSSARY.read_text(), re.M)
    )
    return {
        "income_statement": rows["Income statement"],
        "balance_sheet": rows["Balance sheet"],
        "cash_flow": rows["Cash flow statement"],
    }


# ---------------------------------------------------------------- 1, 4, 10: version, stability


def test_version_is_1_1_0() -> None:
    assert RAW["version"] == "1.1.0"
    assert metric_dictionary_document().version == "1.1.0"


# Owner review of WS4-1 (2026-11-24): English name "Total equity", to avoid confusion with
# equity attributable to owners of the parent. Code, Vietnamese name, statement and unit unchanged.
RENAMED = {"total_equity": "Total equity"}


def test_existing_identifiers_and_fields_are_unchanged() -> None:
    d = metric_dictionary()
    for code, name, name_vi, statement_type, unit in V1_0_0:
        m = d[code]
        name = RENAMED.get(code, name)
        assert (m.name, m.name_vi, m.statement_type.value, m.unit) == (
            name,
            name_vi,
            statement_type,
            unit,
        ), code
    assert list(d) == [
        "net_revenue",
        "net_interest_income",
        "gross_profit",
        "operating_profit",
        "profit_before_tax",
        "net_profit",
        "net_profit_parent",
        "eps_basic",
        "total_assets",
        "total_liabilities",
        "total_equity",
        "equity_parent",
        "cash_and_equivalents",
        "shares_outstanding",
        "operating_cash_flow",
        "investing_cash_flow",
        "financing_cash_flow",
    ]  # the only new code is equity_parent


def test_1_0_0_codes_still_import_and_label(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    assert run(ref, bundle(statements=[statement()])).status.value == "succeeded"
    company_id = client.get(f"{API}/companies").json()["items"][0]["id"]
    m = client.get(f"{API}/companies/{company_id}/financial-statements").json()["items"][0]
    labels = {x["metric_code"]: x["metric_name_vi"] for x in m["metrics"]}
    assert labels == {"net_revenue": "Doanh thu thuần", "net_profit": "Lợi nhuận sau thuế"}


# ---------------------------------------------------------------- 2, 3: definitions


def test_every_metric_has_both_definitions() -> None:
    for m in metric_dictionary().values():
        assert m.definition_vi.strip() and m.definition_en.strip(), m.code
        assert m.definition_vi != m.definition_en, m.code


def test_definitions_use_the_glossary_statement_terms() -> None:
    terms = _glossary_statements()
    for m in metric_dictionary().values():
        vi, en = terms[m.statement_type.value]
        assert vi.casefold() in m.definition_vi.casefold(), m.code
        assert en.casefold() in m.definition_en.casefold(), m.code


def test_definitions_describe_figures_as_presented_not_computed() -> None:
    # No formula is introduced: reported metrics are taken as the document presents them.
    for m in metric_dictionary().values():
        assert re.search(r"trình bày|công bố", m.definition_vi), m.code
        assert re.search(r"as presented|as disclosed|presents this line", m.definition_en), m.code


# ---------------------------------------------------------------- 5: equity_parent


def test_equity_parent_is_registered_once() -> None:
    entries = [m for m in RAW["metrics"] if m["code"] == "equity_parent"]
    assert len(entries) == 1
    m = metric_dictionary()["equity_parent"]
    assert m.name == "Equity attributable to owners of the parent"
    assert m.name_vi == "Vốn chủ sở hữu của cổ đông công ty mẹ"
    assert (m.statement_type.value, m.unit) == ("balance_sheet", "currency")
    # Owner decision WS4-D12: recorded only when presented; never derived, never substituted.
    assert "chỉ ghi khi báo cáo trình bày riêng" in m.definition_vi
    assert "trừ lợi ích cổ đông không kiểm soát" in m.definition_vi
    assert "không thay bằng tổng vốn chủ sở hữu" in m.definition_vi
    assert "only when the statement presents this line explicitly" in m.definition_en
    assert "never derived as total equity minus non-controlling interests" in m.definition_en
    assert "never replaced by total equity" in m.definition_en


def test_duplicate_codes_are_rejected() -> None:
    doc = json.loads(json.dumps(RAW))
    doc["metrics"].append(doc["metrics"][0])
    with pytest.raises(ValidationError, match="duplicate metric code"):
        MetricDictionary.model_validate(doc)


# ---------------------------------------------------------------- 6, 7, 8: applicability


def test_applicability_is_explicit_and_as_approved() -> None:
    got = {
        code: (m.applicability.non_bank, m.applicability.bank)
        for code, m in metric_dictionary().items()
    }
    assert got == APPLICABILITY


def test_gross_profit_and_net_revenue_do_not_apply_to_banks() -> None:
    not_applicable = {
        (code, kind)
        for code, m in metric_dictionary().items()
        for kind, value in m.applicability.model_dump().items()
        if value == "not_applicable"
    }
    assert not_applicable == {("gross_profit", "bank"), ("net_revenue", "bank")}
    # Applicability lives in its metadata, not repeated in the definitions.
    for code in ("gross_profit", "net_revenue"):
        m = metric_dictionary()[code]
        assert "ngân hàng" not in m.definition_vi and "bank" not in m.definition_en, code


def test_bank_classifications_come_only_from_decisions() -> None:
    bank = {code: m.applicability.bank for code, m in metric_dictionary().items()}
    assert {c for c, v in bank.items() if v == "applicable"} == {
        "net_interest_income",  # D4
        "net_profit",  # D2 ROA, D1 separate ROE
        "net_profit_parent",  # D1 consolidated ROE
        "total_assets",  # D2 ROA
        "total_equity",  # D1 separate ROE
        "equity_parent",  # D1 consolidated ROE
    }
    assert {c for c, v in bank.items() if v == "not_applicable"} == {"net_revenue", "gross_profit"}


@pytest.mark.parametrize("missing", ["applicability", "non_bank", "bank"])
def test_applicability_has_no_default(missing: str) -> None:
    doc = json.loads(json.dumps(RAW))
    entry = doc["metrics"][0]
    if missing == "applicability":
        del entry["applicability"]
    else:
        del entry["applicability"][missing]
    with pytest.raises(ValidationError):
        MetricDictionary.model_validate(doc)


def test_a_missing_value_is_not_turned_into_not_applicable(
    client: TestClient, ref: Session
) -> None:
    # A statement without gross_profit returns only the figures it has: no synthesized entry,
    # no zero, no "not applicable" (that comes from the dictionary, never from absence).
    run(ref, bundle([company(1)]))
    run(ref, bundle(statements=[statement(metrics={"net_revenue": "10"})]))
    company_id = client.get(f"{API}/companies").json()["items"][0]["id"]
    st = client.get(f"{API}/companies/{company_id}/financial-statements").json()["items"][0]
    assert [m["metric_code"] for m in st["metrics"]] == ["net_revenue"]
    assert "not_applicable" not in json.dumps(st)


def test_unknown_applicability_value_is_rejected() -> None:
    doc = json.loads(json.dumps(RAW))
    doc["metrics"][0]["applicability"]["bank"] = "n/a"
    with pytest.raises(ValidationError):
        MetricDictionary.model_validate(doc)


# ---------------------------------------------------------------- 9: API


def test_api_serves_the_dictionary(client: TestClient) -> None:
    res = client.get(f"{API}/metric-dictionary")
    assert res.status_code == 200
    body: dict[str, Any] = res.json()
    assert body == RAW  # the API serves the reference file unchanged
    gp = next(m for m in body["metrics"] if m["code"] == "gross_profit")
    assert gp["applicability"] == {"non_bank": "applicable", "bank": "not_applicable"}


def test_openapi_documents_the_dictionary(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    props = set(schemas["MetricDef"]["properties"])
    assert {"definition_vi", "definition_en", "applicability"} <= props
    assert set(schemas["MetricApplicability"]["properties"]) == {"non_bank", "bank"}


# ---------------------------------------------------------------- 11, 12: import of equity_parent


def test_equity_parent_imports_exactly_with_provenance_and_unverified(
    client: TestClient, ref: Session
) -> None:
    run(ref, bundle([company(1)]))
    bs = statement(
        statement_type="balance_sheet",
        reporting_period_start="2025-12-31",
        amount_scale="trieu_dong",
        metrics={"equity_parent": "1234567.890001", "total_equity": "1300000"},
    )
    bs["metrics"][0]["source_page"] = 12
    assert run(ref, bundle(statements=[bs])).status.value == "succeeded"

    company_id = client.get(f"{API}/companies").json()["items"][0]["id"]
    st = client.get(f"{API}/companies/{company_id}/financial-statements").json()["items"][0]
    m = next(x for x in st["metrics"] if x["metric_code"] == "equity_parent")
    assert (m["value"], m["reported_value"], m["reported_scale"]) == (
        "1234567890001.000000",
        "1234567.890001",
        1_000_000,
    )
    assert (m["unit"], m["metric_name_vi"]) == ("VND", "Vốn chủ sở hữu của cổ đông công ty mẹ")
    assert m["source"]["page"] == 12
    # Never verified by import: the figure carries its evidence's status, which is unverified.
    assert m["source"]["verification_status"] == "unverified"
    statuses = set(ref.scalars(select(Evidence.verification_status)))
    assert {s.value for s in statuses} == {"unverified"}


def test_equity_parent_belongs_to_the_balance_sheet(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    r = run(ref, bundle(statements=[statement(metrics={"equity_parent": "1"})]))
    assert r.status.value != "succeeded"
    assert "belongs to balance_sheet" in json.dumps(r.issues)


# ---------------------------------------------------------------- display names (metric_name_en)


def _balance_sheet_with_legacy_rows(ref: Session) -> None:
    """A balance sheet imported today, plus rows as an import before 1.1.0 would have stored
    them: `total_equity` under its old English name, and a code no longer in the dictionary."""
    run(ref, bundle([company(1)]))
    bs = statement(
        statement_type="balance_sheet",
        reporting_period_start="2025-12-31",
        metrics={"total_assets": "900"},
    )
    assert run(ref, bundle(statements=[bs])).status.value == "succeeded"
    st = ref.scalars(select(FinancialStatement)).one()
    for code, stored_name in [
        ("total_equity", "Total owners' equity"),
        ("legacy_metric", "Legacy metric"),
    ]:
        ref.add(
            FinancialMetric(
                financial_statement_id=st.id,
                metric_code=code,
                metric_name=stored_name,
                value=Decimal("400"),
                unit="VND",
                source_page=3,
                reported_value=Decimal("400"),
                reported_scale=1,
            )
        )
    ref.flush()


def test_display_names_come_from_the_current_dictionary(client: TestClient, ref: Session) -> None:
    _balance_sheet_with_legacy_rows(ref)
    company_id = client.get(f"{API}/companies").json()["items"][0]["id"]
    st = client.get(f"{API}/companies/{company_id}/financial-statements").json()["items"][0]
    m = {x["metric_code"]: x for x in st["metrics"]}

    # Historical row: the stored name is returned unchanged; the display name is current.
    te = m["total_equity"]
    assert te["metric_name"] == "Total owners' equity"
    assert te["metric_name_en"] == "Total equity"
    assert te["metric_name_vi"] == "Vốn chủ sở hữu"
    # Its figure and provenance are untouched.
    assert (te["value"], te["reported_value"], te["reported_scale"], te["source"]["page"]) == (
        "400.000000",
        "400.000000",
        1,
        3,
    )

    # Row imported under 1.1.0: stored and current names agree.
    ta = m["total_assets"]
    assert ta["metric_name"] == ta["metric_name_en"] == "Total assets"
    assert ta["metric_name_vi"] == "Tổng tài sản"

    # A code missing from the dictionary: no invented label; clients fall back to metric_name.
    lm = m["legacy_metric"]
    assert (lm["metric_name"], lm["metric_name_en"], lm["metric_name_vi"]) == (
        "Legacy metric",
        None,
        None,
    )


def test_stored_names_are_not_rewritten(client: TestClient, ref: Session) -> None:
    _balance_sheet_with_legacy_rows(ref)
    company_id = client.get(f"{API}/companies").json()["items"][0]["id"]
    client.get(f"{API}/companies/{company_id}/financial-statements")
    ref.expire_all()
    stored = dict(
        ref.execute(select(FinancialMetric.metric_code, FinancialMetric.metric_name)).all()
    )
    assert stored["total_equity"] == "Total owners' equity"


def test_openapi_documents_both_display_names(client: TestClient) -> None:
    props = client.get("/openapi.json").json()["components"]["schemas"]["MetricOut"]["properties"]
    assert {"metric_name", "metric_name_vi", "metric_name_en"} <= set(props)

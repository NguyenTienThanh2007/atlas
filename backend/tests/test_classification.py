"""WS4-4 Phase A: reviewed company classifications (WS4-4-D1, D2, D7, D9) and how the metric
dictionary's applicability is applied per company (D3, D4). All data is fictional."""

import contextlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.calculations import service
from app.calculations.applicability import company_kind, effective
from app.db import get_engine
from app.ingestion import __main__ as cli
from app.ingestion.reference import metric_dictionary
from app.ingestion.review import record_classification
from app.models import (
    AccessMethod,
    Company,
    CompanyClassification,
    CompanyKind,
    DataSource,
    EntityType,
    Evidence,
    FinancialStatement,
    ReviewDecision,
    Sector,
    SourceType,
)
from app.models import VerificationStatus as S
from tests.factories import bundle, company, evidence, run, statement
from tests.test_calculated_metrics import SAMPLE
from tests.test_sample_isolation import _disable_triggers
from tests.test_verification import new_evidence, review

API = "/api/v1"
K = CompanyKind


def classify(db: Session, co: uuid.UUID, kind: CompanyKind, ev: uuid.UUID, **kw: Any) -> Any:
    fields: dict[str, Any] = {
        "basis": "Fictional licence page, p. 2",
        "curator": "Curator A",
        "reviewer": "Reviewer B",
    }
    fields.update(kw)
    return record_classification(db, company_id=co, kind=kind, evidence_id=ev, **fields)


def refused(db: Session, match: str, fn: Any) -> None:
    with pytest.raises((IntegrityError, DBAPIError), match=match), db.begin_nested():
        fn()


def imported(ref: Session, n: int = 1, *statements: Any) -> Company:
    assert run(ref, bundle([company(n)])).status.value == "succeeded"
    if statements:
        r = run(ref, bundle(statements=list(statements)))
        assert r.status.value == "succeeded", r.issues
    return ref.scalars(select(Company).where(Company.short_name == f"Test Co {n}")).one()


def company_evidence(ref: Session, co: Company) -> Evidence:
    return ref.scalars(
        select(Evidence).where(Evidence.entity_type == "company", Evidence.entity_id == co.id)
    ).first() or pytest.fail("no company evidence")


def income(fy: int, ticker: str = "TST1", **metrics: str) -> Any:
    return statement(
        ticker,
        reporting_period_start=f"{fy}-01-01",
        reporting_period_end=f"{fy}-12-31",
        fiscal_year=fy,
        evidence=evidence(f"https://example.test/{ticker}-is-{fy}.pdf"),
        metrics=metrics,
    )


# ---------------------------------------------------------------- database rules (W4-C1 to C5)


def test_classification_is_recorded_and_current(ref: Session) -> None:
    co = imported(ref)
    assert company_kind(ref, co.id) is None  # unknown by default; nothing is inferred
    first = classify(ref, co.id, K.BANK, company_evidence(ref, co).id)
    assert company_kind(ref, co.id) is K.BANK
    second = classify(ref, co.id, K.OTHER_FINANCIAL, first.evidence_id, supersedes_id=first.id)
    assert company_kind(ref, co.id) is K.OTHER_FINANCIAL  # the last row of the chain counts
    assert second.decided_at >= first.decided_at


@pytest.mark.parametrize(
    ("kw", "constraint"),
    [
        ({"curator": "Curator A", "reviewer": " curator a "}, "curator_is_not_reviewer"),
        ({"reviewer": "AI"}, "reviewer_is_a_person"),
        ({"reviewer": "system"}, "reviewer_is_a_person"),
        ({"basis": "  "}, "basis_present"),
    ],
)
def test_two_person_rule(ref: Session, kw: dict[str, str], constraint: str) -> None:
    co = imported(ref)
    ev = company_evidence(ref, co)
    refused(ref, constraint, lambda: classify(ref, co.id, K.BANK, ev.id, **kw))


def test_evidence_must_be_about_the_same_company(ref: Session) -> None:
    co = imported(ref, 1)
    other = imported(ref, 2)
    refused(
        ref,
        "must cite evidence about that company",
        lambda: classify(ref, co.id, K.BANK, company_evidence(ref, other).id),
    )


@pytest.mark.parametrize("decision", [ReviewDecision.DISPUTED, ReviewDecision.REJECTED])
def test_withdrawn_evidence_cannot_be_cited(ref: Session, decision: ReviewDecision) -> None:
    co = imported(ref)
    ev = new_evidence(ref, entity_id=co.id)
    review(ref, ev, S.UNVERIFIED, decision)
    ref.expire_all()
    refused(ref, "cannot rest on", lambda: classify(ref, co.id, K.BANK, ev.id))


@pytest.mark.parametrize("decision", [ReviewDecision.DISPUTED, ReviewDecision.REJECTED])
def test_classification_stops_counting_when_its_evidence_is_withdrawn(
    client: TestClient, ref: Session, decision: ReviewDecision
) -> None:
    co = imported(ref)
    ev = new_evidence(ref, entity_id=co.id)
    classify(ref, co.id, K.BANK, ev.id)
    assert company_kind(ref, co.id) is K.BANK
    review(ref, ev, S.UNVERIFIED, decision)
    ref.expire_all()
    assert company_kind(ref, co.id) is None  # WS4-4-D7
    body = client.get(f"{API}/companies/{co.id}").json()
    assert body["classification"]["kind"] == "unclassified"


def test_sample_and_real_classifications_never_mix(ref: Session) -> None:
    co = imported(ref)
    _disable_triggers(ref)  # a legacy mixed evidence row, as before migration 8de09b58f4c2
    ev = new_evidence(ref, S.SAMPLE, entity_id=co.id)
    ref.execute(text("SET LOCAL session_replication_role = origin"))
    refused(ref, "sample/real isolation", lambda: classify(ref, co.id, K.BANK, ev.id))


def test_sample_company_is_classified_with_sample_evidence(ref: Session) -> None:
    sample_co = company(5, evidence=[evidence("fixture://co5", status="sample")])
    assert run(ref, bundle([sample_co], source=SAMPLE)).status.value == "succeeded"
    co = ref.scalars(select(Company).where(Company.short_name == "Test Co 5")).one()
    classify(ref, co.id, K.BANK, company_evidence(ref, co).id, reviewer="Fixture reviewer")
    assert company_kind(ref, co.id) is K.BANK


def test_classifications_are_append_only(ref: Session) -> None:
    co = imported(ref)
    c = classify(ref, co.id, K.BANK, company_evidence(ref, co).id)
    for sql in (
        "UPDATE company_classifications SET kind = 'non_bank' WHERE id = :id",
        "DELETE FROM company_classifications WHERE id = :id",
    ):
        refused(ref, "append-only", lambda sql=sql: ref.execute(text(sql), {"id": c.id}))


def test_one_linear_chain_per_company(ref: Session) -> None:
    co = imported(ref, 1)
    other = imported(ref, 2)
    ev = company_evidence(ref, co).id
    first = classify(ref, co.id, K.BANK, ev)
    refused(ref, "uq_company_classifications_first", lambda: classify(ref, co.id, K.BANK, ev))
    classify(ref, co.id, K.NON_BANK, ev, supersedes_id=first.id)
    refused(
        ref,
        "uq_company_classifications_supersedes_id",
        lambda: classify(ref, co.id, K.BANK, ev, supersedes_id=first.id),
    )
    other_first = classify(ref, other.id, K.BANK, company_evidence(ref, other).id)
    refused(
        ref,
        "belongs to another company",
        lambda: classify(ref, co.id, K.BANK, ev, supersedes_id=other_first.id),
    )


@pytest.fixture
def committed_company(engine: Engine) -> Any:
    """A real company with company evidence, committed so two connections see them."""
    engine = get_engine()
    with Session(engine) as db:
        sector = Sector(
            code=f"T{uuid.uuid4().hex[:8].upper()}",
            name="t",
            name_vi="t",
            description="t",
            taxonomy_version="t",
        )
        db.add(sector)
        db.flush()
        co = Company(legal_name="Lock JSC", short_name="Lock", sector_id=sector.id)
        db.add(co)
        db.flush()
        src = DataSource(
            name=f"src-{uuid.uuid4()}",
            source_type=SourceType.COMPANY_DISCLOSURE,
            description="test",
            access_method=AccessMethod.FILE_IMPORT,
        )
        db.add(src)
        db.flush()
        ev = Evidence(
            data_source_id=src.id,
            entity_type=EntityType.COMPANY,
            entity_id=co.id,
            source_url="https://example.test/lock.pdf",
            retrieved_at=datetime.now(UTC),
            verification_status=S.UNVERIFIED,
        )
        db.add(ev)
        db.commit()
        ids = {"co": co.id, "ev": ev.id, "src": src.id, "sector": sector.id}
    yield ids
    with engine.begin() as conn:  # no classification was committed
        conn.execute(text("DELETE FROM evidence WHERE id = :ev"), ids)
        conn.execute(text("DELETE FROM data_sources WHERE id = :src"), ids)
        conn.execute(text("DELETE FROM companies WHERE id = :co"), ids)
        conn.execute(text("DELETE FROM sectors WHERE id = :sector"), ids)


def test_concurrent_first_classifications_serialize(committed_company: dict[str, Any]) -> None:
    """Two curators classifying the same company at once: the second waits on the first's
    unique-index entry instead of creating a second chain."""
    insert = text(
        "INSERT INTO company_classifications (company_id, kind, evidence_id, basis, curator, "
        "reviewer) VALUES (:co, 'bank', :ev, 'p. 2', 'Curator A', 'Reviewer B')"
    )
    engine = get_engine()
    with engine.connect() as a, engine.connect() as b:
        ta, tb = a.begin(), b.begin()
        try:
            a.execute(insert, committed_company)
            b.execute(text("SET LOCAL lock_timeout = '300ms'"))
            with pytest.raises(OperationalError, match="lock timeout"):
                b.execute(insert, committed_company)
        finally:
            ta.rollback()
            tb.rollback()


# ---------------------------------------------------------------- effective applicability (D3)


def test_effective_applicability_never_turns_unknown_into_not_applicable() -> None:
    d = metric_dictionary()
    for m in d.values():
        for kind, column in (
            (K.BANK, m.applicability.bank),
            (K.NON_BANK, m.applicability.non_bank),
        ):
            expected = "unknown" if column == "unclassified" else column
            assert effective(kind, m) == expected, (m.code, kind)
        assert effective(K.OTHER_FINANCIAL, m) == "unknown"  # no dictionary column yet
        assert effective(None, m) == "unknown"  # unclassified company
    bank_na = {m.code for m in d.values() if effective(K.BANK, m) == "not_applicable"}
    assert bank_na == {"net_revenue", "gross_profit"}  # WS4-D5, and nothing else
    assert not any(effective(K.NON_BANK, m) == "not_applicable" for m in d.values())


# ---------------------------------------------------------------- API (W4-D, W4-E, W4-F)


def statements(client: TestClient, co: Company) -> list[dict[str, Any]]:
    res = client.get(f"{API}/companies/{co.id}/financial-statements")
    assert res.status_code == 200, res.text
    return list(res.json()["items"])


def absent(st: dict[str, Any]) -> dict[str, tuple[str, str | None]]:
    return {a["metric_code"]: (a["state"], a["applicability_basis"]) for a in st["absent_metrics"]}


def test_unclassified_company_marks_nothing_not_applicable(
    client: TestClient, ref: Session
) -> None:
    co = imported(ref, 1, income(2025, net_interest_income="50", net_profit="0"))
    [st] = statements(client, co)
    assert {s for s, _ in absent(st).values()} == {"not_yet_collected"}
    assert absent(st)["net_revenue"] == ("not_yet_collected", None)
    assert "net_profit" not in absent(st)  # a real zero is reported, never absent
    assert [m["value"] for m in st["metrics"] if m["metric_code"] == "net_profit"] == ["0.000000"]
    assert not any(m["applicability_conflict"] for m in st["metrics"])
    assert client.get(f"{API}/companies/{co.id}").json()["classification"]["kind"] == "unclassified"


def test_bank_shows_not_applicable_only_where_the_dictionary_says_so(
    client: TestClient, ref: Session
) -> None:
    co = imported(ref, 1, income(2025, net_interest_income="50", net_profit="20"))
    classify(ref, co.id, K.BANK, company_evidence(ref, co).id, basis="Licence, p. 2")
    [st] = statements(client, co)
    a = absent(st)
    assert a["net_revenue"] == a["gross_profit"] == ("not_applicable", "dictionary_bank")
    assert a["operating_profit"] == ("not_yet_collected", None)  # bank value unclassified
    assert a["net_profit_parent"] == ("not_yet_collected", None)  # applicable, not collected
    assert set(a) == {
        d.code
        for d in metric_dictionary().values()
        if d.statement_type == "income_statement"
        and d.code not in {"net_interest_income", "net_profit"}
    }
    c = client.get(f"{API}/companies/{co.id}").json()["classification"]
    assert (c["kind"], c["basis"]) == ("bank", "Licence, p. 2")
    assert c["source"]["link_status"] == "linkable" and c["decided_at"] is not None


@pytest.mark.parametrize("kind", [K.NON_BANK, K.OTHER_FINANCIAL])
def test_other_kinds(client: TestClient, ref: Session, kind: CompanyKind) -> None:
    co = imported(ref, 1, income(2025, net_profit="20"))
    classify(ref, co.id, kind, company_evidence(ref, co).id)
    a = absent(statements(client, co)[0])
    assert {s for s, _ in a.values()} == {"not_yet_collected"}  # nothing N/A for these kinds
    assert a["net_interest_income"] == ("not_yet_collected", None)  # non-bank value unclassified


def test_importer_refuses_figures_that_do_not_apply(client: TestClient, ref: Session) -> None:
    co = imported(ref)
    classify(ref, co.id, K.BANK, company_evidence(ref, co).id)
    r = run(ref, bundle(statements=[income(2025, net_revenue="100", net_profit="20")]))
    assert r.status.value in ("partial", "failed")
    assert any("does not apply to a company classified bank" in str(i) for i in r.issues)
    assert ref.scalars(select(FinancialStatement)).first() is None  # nothing stored


def test_conflicting_rows_are_flagged_and_not_compared(client: TestClient, ref: Session) -> None:
    co = imported(
        ref,
        1,
        income(2025, net_revenue="120", net_profit="30"),
        income(2024, net_revenue="100", net_profit="20"),
    )
    classify(ref, co.id, K.BANK, company_evidence(ref, co).id)  # after the figures
    for st in statements(client, co):
        flags = {m["metric_code"]: m["applicability_conflict"] for m in st["metrics"]}
        assert flags == {"net_revenue": True, "net_profit": False}  # shown, flagged, kept
    res = client.get(f"{API}/companies/{co.id}/comparisons", params={"type": "annual_yoy"})
    rows = {(r["metric_code"], r["current"]["fiscal_year"]): r for r in res.json()["items"]}
    revenue = rows[("net_revenue", 2025)]
    assert (revenue["status"], revenue["reason"], revenue["growth_percent"]) == (
        "not_comparable",
        "metric_not_applicable",
        None,
    )
    assert rows[("net_profit", 2025)]["growth_percent"] == "50.00"  # unaffected


def test_roe_roa_input_not_applicable_is_defensive(
    client: TestClient, ref: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dictionary 1.1.0 makes every ROE/ROA input applicable to banks; a changed dictionary that
    did not would stop the calculation instead of using the figure."""
    co = imported(
        ref,
        1,
        income(2025, net_profit="40", net_profit_parent="30"),
        statement(
            statement_type="balance_sheet",
            reporting_period_start="2025-12-31",
            reporting_period_end="2025-12-31",
            evidence=evidence("https://example.test/bs-2025.pdf"),
            metrics={"total_assets": "1000", "equity_parent": "220"},
        ),
        statement(
            statement_type="balance_sheet",
            reporting_period_start="2024-12-31",
            reporting_period_end="2024-12-31",
            fiscal_year=2024,
            evidence=evidence("https://example.test/bs-2024.pdf"),
            metrics={"total_assets": "900", "equity_parent": "180"},
        ),
    )
    classify(ref, co.id, K.BANK, company_evidence(ref, co).id)
    real = metric_dictionary()
    assets = real["total_assets"]
    changed = assets.model_copy(
        update={"applicability": assets.applicability.model_copy(update={"bank": "not_applicable"})}
    )
    monkeypatch.setattr(service, "metric_dictionary", lambda: {**real, "total_assets": changed})
    items = client.get(f"{API}/companies/{co.id}/calculated-metrics").json()["items"]
    roa = next(r for r in items if r["code"] == "roa")
    roe = next(r for r in items if r["code"] == "roe")
    assert (roa["status"], roa["reason"], roa["value"]) == (
        "not_computable",
        "input_not_applicable",
        None,
    )
    assert roe["value"] == "0.1500000000"  # inputs still applicable: unchanged


def test_classify_cli(
    ref: Session, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_sessionmaker", lambda: lambda: contextlib.nullcontext(ref))
    co = imported(ref)
    ev = company_evidence(ref, co)
    base = ["classify", str(co.id), "--kind", "bank", "--evidence", str(ev.id), "--basis", "p. 2"]
    assert cli.main([*base, "--curator", "A", "--reviewer", "a"]) == 1
    assert "curator_is_not_reviewer" in capsys.readouterr().err
    assert cli.main([*base, "--curator", "A", "--reviewer", "B"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert (out["kind"], out["supersedes_id"]) == ("bank", None)
    assert ref.scalars(select(CompanyClassification)).one().company_id == co.id

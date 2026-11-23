import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion import __main__ as cli
from app.ingestion.connectors import read_local_file
from app.ingestion.importer import import_bundle
from app.ingestion.reference import REFERENCE_DIR, seed_reference
from app.models import (
    Company,
    Evidence,
    FinancialMetric,
    FinancialStatement,
    IngestionRun,
    IngestionStatus,
    Sector,
    Security,
)
from tests.factories import SOURCE, bundle, company, evidence, kinds, run, statement

SAMPLE_FIXTURE = Path(__file__).resolve().parents[2] / "data" / "seed" / "sample_companies.json"


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


# ---------------------------------------------------------------- reference data


def test_reference_seed_is_idempotent(db: Session) -> None:
    first = seed_reference(db)
    assert [r.counts for r in first] == [{"exchanges.created": 3}, {"sectors.created": 7}]
    second = seed_reference(db)
    assert [r.counts for r in second] == [{"exchanges.unchanged": 3}, {"sectors.unchanged": 7}]
    assert all(r.status is IngestionStatus.SUCCEEDED for r in first + second)


def test_taxonomy_changes_need_a_version_bump(db: Session, tmp_path: Path) -> None:
    seed_reference(db)
    shutil.copytree(REFERENCE_DIR, tmp_path, dirs_exist_ok=True)
    path = tmp_path / "sector_taxonomy.json"
    data = json.loads(path.read_text())
    data["sectors"][0]["name"] = "Renamed"
    path.write_text(json.dumps(data))
    same_version = seed_reference(db, tmp_path)[1]
    assert same_version.status is IngestionStatus.PARTIAL
    assert kinds(same_version) == ["conflict"]
    assert db.scalar(select(Sector.name).where(Sector.code == data["sectors"][0]["code"])) != (
        "Renamed"
    )

    data["version"] = "1.1.0"
    path.write_text(json.dumps(data))
    bumped = seed_reference(db, tmp_path)[1]
    assert bumped.counts["sectors.updated"] == 1
    assert db.scalar(select(Sector.taxonomy_version).where(Sector.name == "Renamed")) == "1.1.0"


# ---------------------------------------------------------------- companies


def test_sample_fixture_imports_flagged_and_idempotently(ref: Session) -> None:
    first = import_bundle(ref, read_local_file(SAMPLE_FIXTURE))
    assert first.status is IngestionStatus.SUCCEEDED, first.issues
    assert first.counts["companies.created"] == 3
    assert first.counts["securities.created"] == 4
    assert first.counts["evidence.created"] == 3
    assert all(ref.scalars(select(Company.is_sample)))

    second = import_bundle(ref, read_local_file(SAMPLE_FIXTURE))
    assert second.status is IngestionStatus.SUCCEEDED
    assert second.counts == {"companies.seen": 3, "companies.unchanged": 3}
    assert (count(ref, Company), count(ref, Security), count(ref, Evidence)) == (3, 4, 3)
    assert first.input_sha256 == second.input_sha256


def test_valid_import_creates_records_with_provenance(ref: Session) -> None:
    second = evidence("https://example.test/other.pdf", retrieved_at="2026-02-01T10:00:00+07:00")
    r = run(ref, bundle([company(1, tax_code="0100 000 001", evidence=[evidence(), second])]))
    assert r.status is IngestionStatus.SUCCEEDED
    c = ref.scalars(select(Company)).one()
    assert c.tax_code == "0100000001"  # normalised
    assert c.is_sample is False
    assert c.last_verified_at is None  # an import never verifies (WS1)
    evs = ref.scalars(select(Evidence).where(Evidence.entity_id == c.id)).all()
    assert {e.verification_status.value for e in evs} == {"unverified"}
    assert r.data_source_id == evs[0].data_source_id


@pytest.mark.parametrize("status", ["verified", "rejected", "disputed", "superseded"])
def test_imports_cannot_set_a_reviewed_state(ref: Session, status: str) -> None:
    r = run(ref, bundle([company(1, evidence=[evidence(status=status)])]))
    assert kinds(r) == ["invalid"]
    assert "only through a review" in str(r.issues[0]["message"])
    assert count(ref, Company) == 0


def test_text_and_codes_are_normalised(ref: Session) -> None:
    decomposed = "Cong ty Co phan Vie\u0302\u0323t"  # "ệ" as e + combining circumflex + dot
    run(ref, bundle([company(1, ticker=" tst1 ", legal_name=f"  {decomposed}   JSC ")]))
    c = ref.scalars(select(Company)).one()
    assert c.legal_name == "Cong ty Co phan Việt JSC"
    assert ref.scalar(select(Security.ticker)) == "TST1"


def test_invalid_record_is_reported_and_others_still_import(ref: Session) -> None:
    no_evidence = company(2, evidence=[])
    bad_listing = company(3)
    bad_listing["securities"][0]["listing_status"] = "delisted"  # without delisted_at
    unknown_field = company(4, ceo="someone")
    r = run(ref, bundle([company(1), no_evidence, bad_listing, unknown_field]))
    assert r.status is IngestionStatus.PARTIAL
    assert kinds(r) == ["invalid", "invalid", "invalid"]
    assert [i["record"] for i in r.issues] == ["companies[1]", "companies[2]", "companies[3]"]
    assert "evidence" in str(r.issues[0]["message"])
    assert count(ref, Company) == 1


def test_duplicate_in_bundle_is_flagged(ref: Session) -> None:
    r = run(ref, bundle([company(1), company(1)]))
    assert kinds(r) == ["duplicate"]
    assert count(ref, Company) == 1


def test_conflicting_record_never_overwrites(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    r = run(ref, bundle([company(1, legal_name="A Different Name JSC")]))
    assert r.status is IngestionStatus.PARTIAL
    assert kinds(r) == ["conflict"]
    assert "legal_name" in str(r.issues[0]["message"])
    assert ref.scalar(select(Company.legal_name)) == "Test Company 1 JSC"


def test_conflicting_record_rolls_back_as_a_unit(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    changed = company(1, evidence=[evidence("https://example.test/new.pdf")])
    changed["securities"][0]["isin"] = "VN0000000001"  # differs from stored (None)
    r = run(ref, bundle([changed]))
    assert kinds(r) == ["conflict"]
    assert count(ref, Evidence) == 1  # the new evidence was not kept either


def test_identifiers_pointing_at_two_companies_conflict(ref: Session) -> None:
    run(ref, bundle([company(1, tax_code="0100000001"), company(2)]))
    r = run(ref, bundle([company(2, tax_code="0100000001")]))
    assert kinds(r) == ["conflict"]


def test_missing_references_are_reported(ref: Session) -> None:
    r = run(ref, bundle([company(1, sector="NOT_A_SECTOR"), company(2, exchange="NYSE")]))
    assert kinds(r) == ["missing_reference", "missing_reference"]


def test_sample_and_real_data_never_mix(ref: Session) -> None:
    fake_verified = company(1, evidence=[evidence(status="sample")])
    fixture_url_verified = company(2, evidence=[evidence("fixture://x", status="verified")])
    r = run(ref, bundle([fake_verified, fixture_url_verified]))
    assert kinds(r) == ["invalid", "invalid"]

    sample_source = dict(SOURCE, name="Sample", source_type="sample_fixture")
    r = run(ref, bundle([company(3, evidence=[evidence(status="verified")])], source=sample_source))
    assert kinds(r) == ["invalid"]
    assert count(ref, Company) == 0


def test_changed_data_source_terms_fail_the_run(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    r = run(ref, bundle([company(2)], source=dict(SOURCE, commercial_usage_status="licensed")))
    assert r.status is IngestionStatus.FAILED
    assert kinds(r) == ["fatal"]
    assert count(ref, Company) == 1


@pytest.mark.parametrize(
    ("content", "needle"),
    [
        (b"{not json", "not valid JSON"),
        (b'{"schema_version": "1", "schema_version": "1"}', "duplicate JSON keys"),
        (b'{"schema_version": "2", "data_source": {}}', "schema_version"),
        (b"\xff\xfe", "UTF-8"),
    ],
)
def test_unreadable_bundle_fails_and_is_recorded(ref: Session, content: bytes, needle: str) -> None:
    r = run(ref, content)
    assert r.status is IngestionStatus.FAILED
    assert needle in str(r.issues[0]["message"])
    assert ref.get(IngestionRun, r.id) is not None
    assert r.finished_at is not None


# ---------------------------------------------------------------- financial statements


def test_statement_import_is_exact_and_idempotent(ref: Session) -> None:
    data = bundle([company(1)], [statement()])
    first = run(ref, data)
    assert first.status is IngestionStatus.SUCCEEDED, first.issues
    assert first.counts["financial_statements.created"] == 1
    values = dict(ref.execute(select(FinancialMetric.metric_code, FinancialMetric.value)).all())
    assert values == {"net_revenue": Decimal("1000000000.5"), "net_profit": Decimal("-25.000001")}
    assert ref.scalar(select(FinancialMetric.unit)) == "VND"

    second = run(ref, data)
    assert second.counts["financial_statements.unchanged"] == 1
    assert count(ref, FinancialStatement) == 1
    assert count(ref, FinancialMetric) == 2


def test_json_numbers_are_parsed_as_decimals_not_floats(ref: Session) -> None:
    raw = json.dumps(bundle([company(1)], [statement()]))
    raw = raw.replace('"1000000000.50"', "0.1").replace('"-25.000001"', "123456789012.345678")
    r = run(ref, raw.encode())
    assert r.status is IngestionStatus.SUCCEEDED, r.issues
    values = sorted(ref.scalars(select(FinancialMetric.value)))
    assert values == [Decimal("0.1"), Decimal("123456789012.345678")]


@pytest.mark.parametrize(
    ("metrics", "needle"),
    [
        ({"made_up_metric": "1"}, "not in the metric dictionary"),
        ({"total_assets": "1"}, "belongs to balance_sheet"),
        ({"net_revenue": "NaN"}, "metrics.0.value: Input should be a finite number"),
        ({"net_revenue": "1.0000001"}, "decimal places"),
    ],
)
def test_invalid_metrics_are_rejected(ref: Session, metrics: dict[str, str], needle: str) -> None:
    r = run(ref, bundle([company(1)], [statement(metrics=metrics)]))
    assert kinds(r) == ["invalid"]
    assert needle in str(r.issues[0]["message"])
    assert count(ref, FinancialStatement) == 0


def test_changed_figures_are_a_conflict_not_an_overwrite(ref: Session) -> None:
    run(ref, bundle([company(1)], [statement()]))
    r = run(ref, bundle([company(1)], [statement(metrics={"net_revenue": "999"})]))
    assert kinds(r) == ["conflict"]
    assert "revision 2" in str(r.issues[0]["message"])
    assert ref.scalar(
        select(FinancialMetric.value).where(FinancialMetric.metric_code == "net_revenue")
    ) == Decimal("1000000000.5")


def test_restatement_is_a_new_revision_and_history_is_kept(ref: Session) -> None:
    run(ref, bundle([company(1)], [statement()]))
    r = run(ref, bundle([company(1)], [statement(revision=2, metrics={"net_revenue": "999"})]))
    assert r.counts["financial_statements.created"] == 1
    rows = ref.scalars(select(FinancialStatement).order_by(FinancialStatement.revision)).all()
    assert [s.revision for s in rows] == [1, 2]
    assert rows[1].supersedes_id == rows[0].id
    assert count(ref, FinancialMetric) == 3  # original two metrics are still there


def test_revision_gap_and_unknown_company_are_reported(ref: Session) -> None:
    r = run(ref, bundle([company(1)], [statement(revision=3), statement("NOPE")]))
    assert kinds(r) == ["missing_reference", "missing_reference"]


def test_statement_for_sample_company_from_real_source_is_rejected(ref: Session) -> None:
    import_bundle(ref, read_local_file(SAMPLE_FIXTURE))
    r = run(ref, bundle([], [statement("SAMPLE1")]))
    assert kinds(r) == ["invalid"]


# ---------------------------------------------------------------- CLI


def test_cli_exit_codes(engine: object, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    assert cli.main(["import", str(bad)]) == 1
    assert cli.main(["import", str(tmp_path / "missing.json")]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out[0]["status"] == "failed"


def test_database_constraint_violation_rejects_only_that_record(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    # Different company (new tax code) claiming an active ticker another company holds would be
    # caught as a conflict by identity rules; force the DB path with a duplicate ISIN instead.
    first = company(2)
    first["securities"][0]["isin"] = "VN0000000002"
    second = company(3)
    second["securities"][0]["isin"] = "VN0000000002"
    r = run(ref, bundle([first, second, company(4)]))
    assert kinds(r) == ["conflict"]
    assert "uq_securities_isin" in str(r.issues[0]["message"])
    assert count(ref, Company) == 3  # companies 1, 2 and 4

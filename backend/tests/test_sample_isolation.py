"""Audit AU-3: sample (fictional) and real data never mix within a company.

Layer 1, database triggers (migration 8de09b58f4c2): writes that would mix are refused, including
direct SQL that bypasses the importer. Layer 2, the calculation engine refuses mixed inputs on its
own (tested here with triggers disabled, as data written before the migration could be).
All data is fictional."""

import importlib.util
import json
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import (
    AccessMethod,
    Company,
    DataSource,
    EntityType,
    Evidence,
    FinancialStatement,
    Sector,
    SourceType,
    VerificationStatus,
)
from tests.factories import SOURCE, bundle, company, evidence, run, statement
from tests.test_models import fails, new_company, new_security, new_statement

S = VerificationStatus
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
MIGRATION = next(
    (Path(__file__).resolve().parents[1] / "migrations" / "versions").glob("*-8de09b58f4c2_*.py")
)
SAMPLE_SOURCE = dict(SOURCE, name="Sample", source_type="sample_fixture")


def _audit_sql() -> str:
    spec = importlib.util.spec_from_file_location("isolation_migration", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return str(module.AUDIT_SQL)


def _source(db: Session, sample: bool) -> DataSource:
    src = DataSource(
        name=f"src-{uuid.uuid4()}",
        source_type=SourceType.SAMPLE_FIXTURE if sample else SourceType.COMPANY_DISCLOSURE,
        description="test",
        access_method=AccessMethod.FILE_IMPORT,
    )
    db.add(src)
    db.flush()
    return src


def _evidence(
    db: Session, status: S, kind: EntityType, entity_id: uuid.UUID, flush: bool = True
) -> Evidence:
    ev = Evidence(
        data_source_id=_source(db, status is S.SAMPLE).id,
        entity_type=kind,
        entity_id=entity_id,
        source_url="https://example.test/x.pdf",
        retrieved_at=datetime.now(UTC),
        verification_status=status,
    )
    db.add(ev)
    if flush:
        db.flush()
    return ev


def _statement(
    db: Session, co: Company, ev: Evidence, sid: uuid.UUID | None = None, year: int = 2025
) -> None:
    db.add(
        FinancialStatement(
            id=sid or uuid.uuid4(),
            company_id=co.id,
            reporting_period_start=date(year, 12, 31),
            reporting_period_end=date(year, 12, 31),
            fiscal_year=year,
            statement_type="balance_sheet",
            scope="consolidated",
            currency="VND",
            source_evidence_id=ev.id,
        )
    )


# ---------------------------------------------------------------- layer 1: direct writes refused


@pytest.mark.parametrize(
    ("company_sample", "evidence_status"), [(False, S.SAMPLE), (True, S.UNVERIFIED)]
)
def test_statement_with_the_other_classification_is_refused(
    ref: Session, company_sample: bool, evidence_status: S
) -> None:
    co = new_company(ref, is_sample=company_sample)
    sid = uuid.uuid4()
    ev = _evidence(ref, evidence_status, EntityType.FINANCIAL_STATEMENT, sid)
    fails(ref, lambda: _statement(ref, co, ev, sid))


def test_statement_with_mismatched_entity_evidence_is_refused(ref: Session) -> None:
    co = new_company(ref)
    sid = uuid.uuid4()
    good = _evidence(ref, S.UNVERIFIED, EntityType.FINANCIAL_STATEMENT, sid)
    _evidence(ref, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, sid)  # statement not inserted yet
    fails(ref, lambda: _statement(ref, co, good, sid))


@pytest.mark.parametrize("kind", [EntityType.COMPANY, EntityType.SECURITY])
@pytest.mark.parametrize(("company_sample", "status"), [(False, S.SAMPLE), (True, S.UNVERIFIED)])
def test_company_and_security_evidence_must_match(
    ref: Session, kind: EntityType, company_sample: bool, status: S
) -> None:
    co = new_company(ref, is_sample=company_sample)
    target = co.id if kind is EntityType.COMPANY else new_security(ref, co).id
    fails(ref, lambda: _evidence(ref, status, kind, target, flush=False))


def test_evidence_for_an_existing_statement_must_match(ref: Session) -> None:
    st = new_statement(ref, new_company(ref))
    fails(ref, lambda: _evidence(ref, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, st.id, flush=False))


def test_raw_sql_insert_is_refused(ref: Session) -> None:
    co = new_company(ref)
    sid = uuid.uuid4()
    ev = _evidence(ref, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, sid)
    sql = text(
        "INSERT INTO financial_statements (id, company_id, reporting_period_start, "
        "reporting_period_end, fiscal_year, statement_type, scope, currency, source_evidence_id) "
        "VALUES (:id, :co, '2025-12-31', '2025-12-31', 2025, 'balance_sheet', 'consolidated', "
        "'VND', :ev)"
    )
    with pytest.raises(IntegrityError, match="sample/real isolation"), ref.begin_nested():
        ref.execute(sql, {"id": sid, "co": co.id, "ev": ev.id})


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE evidence SET verification_status = 'sample' WHERE id = :ev",
        "UPDATE financial_statements SET source_evidence_id = :other WHERE id = :st",
        "UPDATE companies SET is_sample = true WHERE id = :co",
    ],
)
def test_raw_sql_updates_cannot_bypass(ref: Session, sql: str) -> None:
    co = new_company(ref)
    st = new_statement(ref, co)
    other = _evidence(ref, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, uuid.uuid4())
    with pytest.raises(IntegrityError), ref.begin_nested():
        ref.execute(
            text(sql), {"ev": st.source_evidence_id, "other": other.id, "st": st.id, "co": co.id}
        )


def test_company_classification_frozen_once_it_has_evidence(ref: Session) -> None:
    co = new_company(ref)
    _evidence(ref, S.UNVERIFIED, EntityType.COMPANY, co.id)
    with pytest.raises(IntegrityError, match="is_sample cannot change"), ref.begin_nested():
        ref.execute(text("UPDATE companies SET is_sample = true WHERE id = :co"), {"co": co.id})


def test_company_without_data_may_still_be_reclassified(ref: Session) -> None:
    co = new_company(ref)
    ref.execute(text("UPDATE companies SET is_sample = true WHERE id = :co"), {"co": co.id})
    ref.expire_all()
    assert ref.get(Company, co.id).is_sample is True  # type: ignore[union-attr]


def test_moving_a_security_to_a_company_of_the_other_kind_is_refused(ref: Session) -> None:
    real = new_company(ref)
    fake = new_company(ref, short_name="Sample Co", legal_name="Sample Co JSC", is_sample=True)
    sec = new_security(ref, real)
    _evidence(ref, S.UNVERIFIED, EntityType.SECURITY, sec.id)
    with pytest.raises(IntegrityError, match="sample/real isolation"), ref.begin_nested():
        ref.execute(
            text("UPDATE securities SET company_id = :to WHERE id = :sec"),
            {"to": fake.id, "sec": sec.id},
        )


def test_legitimate_sample_and_real_companies_import(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    assert run(ref, bundle(statements=[statement()])).status.value == "succeeded"
    run(ref, bundle([company(2, evidence=[evidence(status="sample")])], source=SAMPLE_SOURCE))
    fixture = statement("TST2", evidence=evidence("fixture://fs", status="sample"))
    assert run(ref, bundle(statements=[fixture], source=SAMPLE_SOURCE)).status.value == "succeeded"


# ---------------------------------------------------------------- migration safety


def _disable_triggers(db: Session | Connection) -> None:
    # Simulates data written before migration 8de09b58f4c2 (or by a superuser bypass).
    db.execute(text("SET LOCAL session_replication_role = replica"))


def test_audit_refuses_existing_mixed_data(ref: Session) -> None:
    co = new_company(ref)
    sid = uuid.uuid4()
    _disable_triggers(ref)
    ev = _evidence(ref, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, sid)
    _statement(ref, co, ev, sid)
    ref.flush()
    with (
        pytest.raises(DBAPIError, match="existing data mixes sample and real") as err,
        ref.begin_nested(),
    ):
        ref.execute(text(_audit_sql()))
    assert str(sid) in str(err.value)  # record ids only; no names


def test_upgrade_preserves_legitimate_data_and_refuses_mixed_data(engine: Engine) -> None:
    cfg = Config(str(ALEMBIC_INI))
    with get_engine().connect() as conn, conn.begin() as outer:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "31b1317163eb")
        db = Session(bind=conn, join_transaction_mode="create_savepoint")
        sector = Sector(
            code="TST_ISO", name="t", name_vi="t", description="t", taxonomy_version="t"
        )
        db.add(sector)
        db.flush()
        real = Company(legal_name="Real JSC", short_name="Real", sector_id=sector.id)
        fake = Company(
            legal_name="Fake JSC", short_name="Fake", sector_id=sector.id, is_sample=True
        )
        db.add_all([real, fake])
        db.flush()
        for co, status in ((real, S.UNVERIFIED), (fake, S.SAMPLE)):
            sid = uuid.uuid4()
            _statement(db, co, _evidence(db, status, EntityType.FINANCIAL_STATEMENT, sid), sid)
        db.flush()
        before = db.scalar(select(text("count(*)")).select_from(FinancialStatement))

        command.upgrade(cfg, "head")  # legitimate data: the audit passes
        db.expire_all()
        assert db.scalar(select(text("count(*)")).select_from(FinancialStatement)) == before

        command.downgrade(cfg, "31b1317163eb")
        sid = uuid.uuid4()
        _statement(
            db, real, _evidence(db, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, sid), sid, 2024
        )
        db.flush()
        with pytest.raises(DBAPIError, match="existing data mixes sample and real"):
            command.upgrade(cfg, "head")
        outer.rollback()  # nothing leaves this test
    cfg.attributes.pop("connection", None)


# ---------------------------------------------------------------- concurrency


@pytest.fixture
def committed_company(engine: Engine) -> Any:
    """A real company and an unused real evidence row, committed so two connections see them;
    removed afterwards (neither table is append-only)."""
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
        sid = uuid.uuid4()
        ev = _evidence(db, S.UNVERIFIED, EntityType.FINANCIAL_STATEMENT, sid)
        db.commit()
        ids = {"co": co.id, "ev": ev.id, "src": ev.data_source_id, "sector": sector.id, "sid": sid}
    yield ids
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM evidence WHERE id = :ev"), ids)
        conn.execute(text("DELETE FROM data_sources WHERE id = :src"), ids)
        conn.execute(text("DELETE FROM companies WHERE id = :co"), ids)
        conn.execute(text("DELETE FROM sectors WHERE id = :sector"), ids)


_INSERT_STATEMENT = text(
    "INSERT INTO financial_statements (id, company_id, reporting_period_start, "
    "reporting_period_end, fiscal_year, statement_type, scope, currency, source_evidence_id) "
    "VALUES (:sid, :co, '2025-12-31', '2025-12-31', 2025, 'balance_sheet', 'consolidated', "
    "'VND', :ev)"
)
_FLIP = text("UPDATE companies SET is_sample = true WHERE id = :co")


@pytest.mark.parametrize("first", ["statement", "flip"])
def test_concurrent_insert_and_reclassification_serialize(
    committed_company: dict[str, Any], first: str
) -> None:
    """The statement check holds FOR SHARE on the company row and the reclassification needs the
    row's exclusive lock, so whichever comes second waits instead of slipping past the check."""
    engine = get_engine()
    with engine.connect() as a, engine.connect() as b:
        ta, tb = a.begin(), b.begin()
        try:
            first_conn, second_conn = (a, b) if first == "statement" else (b, a)
            first_sql, second_sql = (
                (_INSERT_STATEMENT, _FLIP) if first == "statement" else (_FLIP, _INSERT_STATEMENT)
            )
            first_conn.execute(first_sql, committed_company)
            second_conn.execute(text("SET LOCAL lock_timeout = '300ms'"))
            with pytest.raises(OperationalError, match="lock timeout"):
                second_conn.execute(second_sql, committed_company)
        finally:
            ta.rollback()
            tb.rollback()


# ---------------------------------------------------------------- layer 2: calculation engine


def test_calculation_refuses_mixed_legacy_data(client: TestClient, ref: Session) -> None:
    run(ref, bundle([company(1)]))
    for st in (
        statement(metrics={"net_profit_parent": "30", "net_profit": "40"}),
        statement(
            statement_type="balance_sheet",
            reporting_period_start="2024-12-31",
            reporting_period_end="2024-12-31",
            fiscal_year=2024,
            evidence=evidence("https://example.test/o.pdf"),
            metrics={"equity_parent": "180", "total_assets": "900"},
        ),
    ):
        assert run(ref, bundle(statements=[st])).status.value == "succeeded"
    co = ref.scalars(select(Company)).one()
    _disable_triggers(ref)  # legacy mixed row, as before the migration
    sid = uuid.uuid4()
    ev = _evidence(ref, S.SAMPLE, EntityType.FINANCIAL_STATEMENT, sid)
    _statement(ref, co, ev, sid)
    ref.flush()
    ref.execute(
        text(
            "INSERT INTO financial_metrics (id, financial_statement_id, metric_code, metric_name, "
            "value, unit, source_page, reported_value, reported_scale) VALUES "
            "(gen_random_uuid(), :st, :code, 'x', 220, 'VND', 1, 220, 1)"
        ),
        [{"st": sid, "code": "equity_parent"}, {"st": sid, "code": "total_assets"}],
    )
    ref.execute(text("SET LOCAL session_replication_role = origin"))
    res = client.get(f"/api/v1/companies/{co.id}/calculated-metrics")
    body = json.loads(res.text, parse_float=lambda s: pytest.fail(s))
    assert body["items"], body
    for r in body["items"]:
        assert (r["status"], r["reason"], r["value"], r["percent"]) == (
            "not_computable",
            "mixed_sample_and_real",
            None,
            None,
        )
        assert r["input_verification"] is None  # no "sample" or "unverified" label hides the mix
        assert {i["code"] for i in r["issues"]} >= {"mixed_sample_and_real"}

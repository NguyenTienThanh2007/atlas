"""Phase 2 WS1: two-person verification, figure provenance, amount scales and period rules.

Database guarantees are tested with direct SQL/ORM writes that bypass the importer and CLI, so
they hold whatever client writes to the database."""

import contextlib
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.orm import Session

from app.ingestion import __main__ as cli
from app.ingestion.review import history, record_review
from app.models import (
    AccessMethod,
    Company,
    DataSource,
    EntityType,
    Evidence,
    FinancialMetric,
    ReviewDecision,
    SourceType,
    VerificationReview,
    VerificationStatus,
)
from tests.factories import SOURCE, bundle, company, evidence, kinds, run, statement
from tests.test_models import fails, new_company, new_statement

S = VerificationStatus
D = ReviewDecision

ALLOWED = {
    (S.UNVERIFIED, D.VERIFIED),
    (S.UNVERIFIED, D.REJECTED),
    (S.UNVERIFIED, D.DISPUTED),
    (S.UNVERIFIED, D.SUPERSEDED),
    (S.DISPUTED, D.VERIFIED),
    (S.DISPUTED, D.REJECTED),
    (S.DISPUTED, D.UNVERIFIED),
    (S.DISPUTED, D.SUPERSEDED),
    (S.VERIFIED, D.DISPUTED),
    (S.VERIFIED, D.SUPERSEDED),
    (S.REJECTED, D.UNVERIFIED),
}
# How to reach each starting state from a freshly imported (unverified) record.
PATH = {
    S.UNVERIFIED: [],
    S.VERIFIED: [D.VERIFIED],
    S.DISPUTED: [D.DISPUTED],
    S.REJECTED: [D.REJECTED],
    S.SUPERSEDED: [D.SUPERSEDED],
}


def new_evidence(
    db: Session, status: S = S.UNVERIFIED, entity_id: uuid.UUID | None = None
) -> Evidence:
    src = DataSource(
        name=f"src-{uuid.uuid4()}",
        source_type=SourceType.SAMPLE_FIXTURE
        if status is S.SAMPLE
        else SourceType.COMPANY_DISCLOSURE,
        description="test",
        access_method=AccessMethod.FILE_IMPORT,
    )
    db.add(src)
    db.flush()
    ev = Evidence(
        data_source_id=src.id,
        entity_type=EntityType.COMPANY,
        entity_id=entity_id or uuid.uuid4(),
        source_url="https://example.test/ar.pdf",
        retrieved_at=datetime.now(UTC),
        verification_status=status,
    )
    db.add(ev)
    db.flush()
    return ev


def review(db: Session, ev: Evidence, frm: S, decision: D, **kw: Any) -> VerificationReview:
    fields: dict[str, Any] = {
        "curator": "Curator A",
        "reviewer": "Reviewer B",
        "checked_against": "Audited FS 2025, p. 6",
    }
    fields.update(kw)
    return record_review(db, evidence_id=ev.id, from_status=frm, decision=decision, **fields)


def status_of(db: Session, ev: Evidence) -> S:
    return db.scalars(select(Evidence.verification_status).where(Evidence.id == ev.id)).one()


# ---------------------------------------------------------------- evidence is born unreviewed


@pytest.mark.parametrize("status", [S.VERIFIED, S.REJECTED, S.DISPUTED, S.SUPERSEDED])
def test_evidence_cannot_be_inserted_in_a_reviewed_state(ref: Session, status: S) -> None:
    fails(ref, lambda: new_evidence(ref, status))


def test_status_and_content_cannot_be_updated_directly(ref: Session) -> None:
    ev = new_evidence(ref)
    fails(ref, lambda: ref.execute(update(Evidence).values(verification_status="verified")))
    fails(ref, lambda: ref.execute(update(Evidence).values(source_url="https://elsewhere.test/x")))
    assert status_of(ref, ev) is S.UNVERIFIED


# ---------------------------------------------------------------- two-person rule


@pytest.mark.parametrize(
    ("curator", "reviewer"),
    [
        ("Curator A", "Curator A"),
        ("Curator A", "  curator a "),  # case and spacing don't make a second person
        ("Curator A", "system"),
        ("Curator A", "Claude"),
        ("Curator A", "importer"),
        ("Curator A", " "),
        ("", "Reviewer B"),
    ],
)
def test_reviewer_must_be_another_person(ref: Session, curator: str, reviewer: str) -> None:
    ev = new_evidence(ref)
    fails(
        ref, lambda: review(ref, ev, S.UNVERIFIED, D.VERIFIED, curator=curator, reviewer=reviewer)
    )
    assert status_of(ref, ev) is S.UNVERIFIED


def test_review_must_say_what_was_checked(ref: Session) -> None:
    ev = new_evidence(ref)
    fails(ref, lambda: review(ref, ev, S.UNVERIFIED, D.VERIFIED, checked_against="  "))
    assert status_of(ref, ev) is S.UNVERIFIED


def test_raw_sql_review_is_held_to_the_same_rules(ref: Session) -> None:
    ev = new_evidence(ref)
    insert = text(
        "INSERT INTO verification_reviews (evidence_id, from_status, decision, curator, reviewer,"
        " checked_against) VALUES (:e, 'unverified', 'verified', :c, :r, 'p. 6')"
    )
    fails(ref, lambda: ref.execute(insert, {"e": ev.id, "c": "Same", "r": "same"}))
    assert status_of(ref, ev) is S.UNVERIFIED
    ref.execute(insert, {"e": ev.id, "c": "Curator A", "r": "Reviewer B"})
    assert status_of(ref, ev) is S.VERIFIED


# ---------------------------------------------------------------- state transitions


@pytest.mark.parametrize("frm", list(PATH))
@pytest.mark.parametrize("decision", list(D))
def test_transition_matrix(ref: Session, frm: S, decision: D) -> None:
    ev = new_evidence(ref)
    for step in PATH[frm]:
        review(ref, ev, S.UNVERIFIED, step)
    assert status_of(ref, ev) is frm
    if (frm, decision) in ALLOWED:
        review(ref, ev, frm, decision)
        assert status_of(ref, ev) is S(decision.value)
    else:
        fails(ref, lambda: review(ref, ev, frm, decision))
        assert status_of(ref, ev) is frm


@pytest.mark.parametrize("decision", list(D))
def test_sample_evidence_can_never_be_reviewed(ref: Session, decision: D) -> None:
    ev = new_evidence(ref, S.SAMPLE)
    fails(ref, lambda: review(ref, ev, S.SAMPLE, decision))
    assert status_of(ref, ev) is S.SAMPLE


def test_stale_from_status_is_refused(ref: Session) -> None:
    ev = new_evidence(ref)
    review(ref, ev, S.UNVERIFIED, D.DISPUTED)
    fails(ref, lambda: review(ref, ev, S.UNVERIFIED, D.VERIFIED))  # it is disputed now
    assert status_of(ref, ev) is S.DISPUTED


# ---------------------------------------------------------------- history


def test_reviews_are_append_only_and_history_is_kept(ref: Session) -> None:
    ev = new_evidence(ref)
    review(ref, ev, S.UNVERIFIED, D.VERIFIED)
    review(ref, ev, S.VERIFIED, D.DISPUTED, notes="figure differs from p. 7")
    review(ref, ev, S.DISPUTED, D.REJECTED)
    review(ref, ev, S.REJECTED, D.UNVERIFIED)
    review(ref, ev, S.UNVERIFIED, D.VERIFIED, reviewer="Reviewer C")
    steps = [(r.from_status, r.decision) for r in history(ref, ev.id)]
    assert steps == [
        (S.UNVERIFIED, D.VERIFIED),
        (S.VERIFIED, D.DISPUTED),
        (S.DISPUTED, D.REJECTED),
        (S.REJECTED, D.UNVERIFIED),
        (S.UNVERIFIED, D.VERIFIED),
    ]
    fails(ref, lambda: ref.execute(update(VerificationReview).values(decision="rejected")))
    fails(ref, lambda: ref.execute(delete(VerificationReview)))
    fails(ref, lambda: ref.execute(delete(Evidence).where(Evidence.id == ev.id)))
    assert len(history(ref, ev.id)) == 5


def test_verifying_company_evidence_stamps_last_verified(ref: Session) -> None:
    c = new_company(ref)
    ev = new_evidence(ref, entity_id=c.id)
    assert c.last_verified_at is None
    r = review(ref, ev, S.UNVERIFIED, D.VERIFIED)
    ref.refresh(c)
    assert c.last_verified_at == r.reviewed_at


# ---------------------------------------------------------------- figure provenance (DB)


def add_metric(db: Session, statement_id: uuid.UUID, **kw: Any) -> None:
    fields: dict[str, Any] = {
        "metric_code": "net_revenue",
        "metric_name": "Net revenue",
        "value": Decimal("5000000"),
        "unit": "VND",
        "source_page": 12,
        "reported_value": Decimal("5"),
        "reported_scale": 1_000_000,
    }
    fields.update(kw)
    db.add(FinancialMetric(financial_statement_id=statement_id, **fields))
    db.flush()


def test_real_figures_need_page_and_reported_value(ref: Session) -> None:
    st = new_statement(ref, new_company(ref))
    fails(ref, lambda: add_metric(ref, st.id, source_page=None))
    fails(ref, lambda: add_metric(ref, st.id, reported_value=None, reported_scale=None))
    fails(ref, lambda: add_metric(ref, st.id, source_page=0))
    add_metric(ref, st.id)
    row = ref.scalars(select(FinancialMetric)).one()
    assert (row.value, row.reported_value, row.reported_scale, row.source_page) == (
        Decimal("5000000"),
        Decimal("5"),
        1_000_000,
        12,
    )


def test_sample_figures_may_omit_page(ref: Session) -> None:
    st = new_statement(ref, new_company(ref, is_sample=True))
    add_metric(ref, st.id, source_page=None, reported_value=None, reported_scale=None)


@pytest.mark.parametrize(
    "kw",
    [
        {"value": Decimal("5000001")},  # not reported x scale
        {"reported_scale": 10},  # unsupported scale
        {"reported_scale": None},  # half a pair
        {"reported_value": None},
    ],
)
def test_conversion_provenance_is_consistent(ref: Session, kw: dict[str, Any]) -> None:
    st = new_statement(ref, new_company(ref))
    fails(ref, lambda: add_metric(ref, st.id, **kw))


# ---------------------------------------------------------------- import: scales and currency


def stored(db: Session) -> dict[str, tuple[Decimal, Decimal | None, int | None, int | None]]:
    return {
        m.metric_code: (m.value, m.reported_value, m.reported_scale, m.source_page)
        for m in db.scalars(select(FinancialMetric))
    }


@pytest.mark.parametrize(
    ("scale", "reported", "full"),
    [
        ("dong", "1234567.89", Decimal("1234567.89")),
        ("nghin_dong", "1234567.89", Decimal("1234567890")),
        ("trieu_dong", "1234567.89", Decimal("1234567890000")),
        ("trieu_dong", "0.000001", Decimal("1")),  # smallest step converts exactly
        ("trieu_dong", "-8.5", Decimal("-8500000")),
        # Largest value that still fits NUMERIC(38,6) after scaling: 32 nines.
        ("trieu_dong", "99999999999999999999999999.999999", Decimal("9" * 32)),
    ],
)
def test_amount_scales_convert_exactly(
    ref: Session, scale: str, reported: str, full: Decimal
) -> None:
    run(ref, bundle([company(1)]))
    r = run(
        ref, bundle(statements=[statement(amount_scale=scale, metrics={"net_revenue": reported})])
    )
    assert r.status.value == "succeeded", r.issues
    assert stored(ref)["net_revenue"] == (
        full,
        Decimal(reported),
        {"dong": 1, "nghin_dong": 1000, "trieu_dong": 1_000_000}[scale],
        7,
    )


def test_per_share_and_share_counts_are_not_scaled(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    st = statement(amount_scale="trieu_dong", metrics={"net_revenue": "2", "eps_basic": "4321"})
    r = run(ref, bundle(statements=[st]))
    assert r.status.value == "succeeded", r.issues
    values = stored(ref)
    assert values["net_revenue"][:3] == (Decimal("2000000"), Decimal("2"), 1_000_000)
    assert values["eps_basic"][:3] == (Decimal("4321"), Decimal("4321"), 1)


@pytest.mark.parametrize(
    ("change", "needle"),
    [
        ({"amount_scale": "ty_dong"}, "amount_scale"),
        ({"amount_scale": "1000"}, "amount_scale"),
        ({"amount_scale": None}, "amount_scale"),
        ({"currency": "USD"}, "not supported"),
    ],
)
def test_unsupported_scale_or_currency_is_rejected(
    ref: Session, change: dict[str, Any], needle: str
) -> None:
    run(ref, bundle([company(1)]))
    st = statement()
    st.update(change)
    if change.get("amount_scale", "x") is None:
        del st["amount_scale"]
    r = run(ref, bundle(statements=[st]))
    assert kinds(r) == ["invalid"] and needle in str(r.issues[0]["message"])


def test_overflow_after_scaling_is_rejected(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    st = statement(
        amount_scale="trieu_dong", metrics={"net_revenue": "100000000000000000000000000"}
    )
    r = run(ref, bundle(statements=[st]))
    assert kinds(r) == ["invalid"] and "too large" in str(r.issues[0]["message"])


def test_real_figures_need_a_source_page_on_import(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    st = statement()
    del st["metrics"][0]["source_page"]
    r = run(ref, bundle(statements=[st]))
    assert kinds(r) == ["invalid"] and "source_page" in str(r.issues[0]["message"])


def test_sample_statements_do_not_need_a_page(ref: Session) -> None:
    sample = dict(SOURCE, name="Sample", source_type="sample_fixture")
    run(ref, bundle([company(1, evidence=[evidence(status="sample")])], source=sample))
    st = statement(evidence=evidence("fixture://fs", status="sample"))
    for m in st["metrics"]:
        del m["source_page"]
    r = run(ref, bundle(statements=[st], source=sample))
    assert r.status.value == "succeeded", r.issues


def test_reimport_with_scale_is_idempotent(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    data = bundle(statements=[statement(amount_scale="trieu_dong")])
    run(ref, data)
    again = run(ref, data)
    assert again.counts.get("financial_statements.unchanged") == 1, again.issues
    changed = bundle(statements=[statement(amount_scale="trieu_dong")])
    changed["financial_statements"][0]["metrics"][0]["source_page"] = 8
    assert kinds(run(ref, changed)) == ["conflict"]  # a different page is a different record


# ---------------------------------------------------------------- import: reporting periods


def fy(year: int, start: str, end: str, **kw: Any) -> dict[str, Any]:
    return statement(
        fiscal_year=year,
        reporting_period_start=start,
        reporting_period_end=end,
        evidence=evidence(f"https://example.test/{year}-{start}-{kw.get('fiscal_quarter')}.pdf"),
        **kw,
    )


@pytest.mark.parametrize(
    ("record", "needle"),
    [
        (fy(2024, "2025-01-01", "2025-12-31"), "fiscal year 2025"),  # wrong fiscal year
        (fy(2025, "2025-01-01", "2025-06-30"), "span"),  # half-year called annual
        (fy(2025, "2025-01-01", "2025-04-30", fiscal_quarter=1), "span"),  # 120-day quarter
        (fy(2027, "2025-01-01", "2025-03-31", fiscal_quarter=1), "cannot belong"),
        (
            fy(
                2025,
                "2025-01-01",
                "2025-12-31",
                statement_type="balance_sheet",
                metrics={"total_assets": "1"},
            ),
            "one date",
        ),
    ],
)
def test_period_rules(ref: Session, record: dict[str, Any], needle: str) -> None:
    run(ref, bundle([company(1)]))
    r = run(ref, bundle(statements=[record]))
    assert kinds(r) == ["invalid"] and needle in str(r.issues[0]["message"]), r.issues


def test_valid_periods_including_non_calendar_and_leap_years(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    records = [
        fy(2024, "2024-01-01", "2024-12-31"),  # 366 days (leap year)
        # Non-calendar fiscal year July-June, named after the year it ends in; its first quarter
        # ends in the previous calendar year.
        fy(2026, "2025-07-01", "2026-06-30", scope="separate"),
        fy(2026, "2025-07-01", "2025-09-30", scope="separate", fiscal_quarter=1),
        fy(
            2025,
            "2025-12-31",
            "2025-12-31",
            statement_type="balance_sheet",
            metrics={"total_assets": "1"},
        ),
    ]
    r = run(ref, bundle(statements=records))
    assert r.status.value == "succeeded", r.issues


def test_overlap_rules(ref: Session) -> None:
    run(ref, bundle([company(1)]))
    base = [
        fy(2025, "2025-01-01", "2025-12-31"),
        *(
            fy(2025, s, e, fiscal_quarter=q)
            for q, s, e in [
                (1, "2025-01-01", "2025-03-31"),
                (2, "2025-04-01", "2025-06-30"),
                (3, "2025-07-01", "2025-09-30"),
                (4, "2025-10-01", "2025-12-31"),
            ]
        ),
    ]
    # Annual and quarterly statements of the same year legitimately cover the same months.
    r = run(ref, bundle(statements=base))
    assert r.status.value == "succeeded", r.issues

    clashes = [
        fy(2026, "2025-04-01", "2026-03-31"),  # another annual period overlapping FY2025
        fy(2025, "2025-02-01", "2025-04-30", fiscal_quarter=2),  # quarter overlapping Q1
    ]
    r = run(ref, bundle(statements=clashes))
    assert kinds(r) == ["conflict", "conflict"]
    assert "overlaps the stored 2025" in str(r.issues[0]["message"])

    allowed = [
        fy(
            2025,
            "2025-01-01",
            "2025-12-31",
            revision=2,
            metrics={"net_revenue": "2", "net_profit": "1"},
        ),  # restatement, same period
        fy(2025, "2025-01-01", "2025-12-31", scope="separate"),  # other scope
    ]
    r = run(ref, bundle(statements=allowed))
    assert r.status.value == "succeeded", r.issues


# ---------------------------------------------------------------- CLI (local only)


def test_review_cli(
    ref: Session, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_sessionmaker", lambda: lambda: contextlib.nullcontext(ref))
    ev = new_evidence(ref)
    base = [str(ev.id), "--from", "unverified", "--checked-against", "AR 2025 p. 6"]

    assert (
        cli.main(["review", *base, "--decision", "verified", "--curator", "A", "--reviewer", "a"])
        == 1
    )
    assert "curator_is_not_reviewer" in capsys.readouterr().err

    assert (
        cli.main(["review", *base, "--decision", "verified", "--curator", "A", "--reviewer", "B"])
        == 0
    )
    assert json.loads(capsys.readouterr().out)["decision"] == "verified"

    assert cli.main(["reviews", str(ev.id)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [(r["from_status"], r["decision"], r["reviewer"]) for r in out] == [
        ("unverified", "verified", "B")
    ]

    with pytest.raises(SystemExit):  # no silent default reviewer
        cli.main(["review", *base, "--decision", "verified", "--curator", "A"])


def test_no_public_review_api(client: Any) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert not [p for p in paths if "review" in p or "verif" in p]
    assert all(set(ops) == {"get"} for ops in paths.values())


def test_existing_sample_data_still_imports(ref: Session) -> None:
    from pathlib import Path

    from app.ingestion.connectors import read_local_file
    from app.ingestion.importer import import_bundle

    fixture = Path(__file__).resolve().parents[2] / "data" / "seed" / "sample_companies.json"
    r = import_bundle(ref, read_local_file(fixture))
    assert r.status.value == "succeeded", r.issues
    assert set(ref.scalars(select(Evidence.verification_status))) == {S.SAMPLE}
    assert not ref.scalars(select(Company).where(Company.is_sample.is_(False))).all()


def _guard_sql() -> str:
    import importlib.util
    from pathlib import Path

    path = next((Path(__file__).parents[1] / "migrations" / "versions").glob("*31b1317163eb*.py"))
    spec = importlib.util.spec_from_file_location("ws1_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return str(module.DOWNGRADE_GUARD)


def test_downgrade_refuses_to_discard_review_history(ref: Session) -> None:
    from sqlalchemy.exc import ProgrammingError

    guard = text(_guard_sql())
    with ref.begin_nested():
        ref.execute(guard)  # nothing to lose: allowed
    ev = new_evidence(ref)
    review(ref, ev, S.UNVERIFIED, D.REJECTED)
    with pytest.raises(ProgrammingError, match="discard review history"), ref.begin_nested():
        ref.execute(guard)

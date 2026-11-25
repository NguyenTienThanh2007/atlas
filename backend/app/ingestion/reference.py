"""Seeds versioned reference data (exchanges, sector taxonomy) and serves the metric dictionary."""

import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.connectors import InputError, parse_json, read_local_file
from app.ingestion.runs import RunRecorder
from app.ingestion.schemas import ExchangeCode, LongText, SectorCode, Text200, describe_error
from app.models import Exchange, IngestionRun, Sector, StatementType

REFERENCE_DIR = Path(__file__).resolve().parents[1] / "reference"
SemVer = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]


class _Ref(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# "unclassified" = no approved classification yet. It never means "not applicable", and
# applicability describes the metric, never a missing value (WS4-D6, WS4-D10).
Applicability = Literal["applicable", "not_applicable", "unclassified"]


class MetricApplicability(_Ref):
    # Both required, no defaults: a metric is never "not applicable" by omission.
    non_bank: Applicability
    bank: Applicability


class MetricDef(_Ref):
    code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,63}$")]
    name: Text200
    name_vi: Text200
    statement_type: StatementType
    unit: Literal["currency", "currency_per_share", "shares"]
    applicability: MetricApplicability
    definition_vi: LongText
    definition_en: LongText


class MetricDictionary(_Ref):
    dictionary: str
    version: SemVer
    notes: LongText
    metrics: list[MetricDef] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_codes(self) -> "MetricDictionary":
        codes = [m.code for m in self.metrics]
        if len(codes) != len(set(codes)):
            raise ValueError("duplicate metric code")
        return self


class _SectorIn(_Ref):
    code: SectorCode
    name: Text200
    name_vi: Text200
    description: LongText


class _Taxonomy(_Ref):
    taxonomy: str
    version: SemVer
    effective_from: date
    methodology: LongText
    sectors: list[_SectorIn] = Field(min_length=1)


class _ExchangeIn(_Ref):
    code: ExchangeCode
    name: Text200
    country_code: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]


class _Exchanges(_Ref):
    version: SemVer
    notes: LongText
    exchanges: list[_ExchangeIn] = Field(min_length=1)


@lru_cache
def metric_dictionary_document() -> MetricDictionary:
    raw = read_local_file(REFERENCE_DIR / "metric_dictionary.json")
    return MetricDictionary.model_validate(parse_json(raw))


@lru_cache
def metric_dictionary() -> dict[str, MetricDef]:
    return {m.code: m for m in metric_dictionary_document().metrics}


def _semver(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", v))


def seed_reference(session: Session, directory: Path = REFERENCE_DIR) -> list[IngestionRun]:
    """Idempotent: inserts missing rows, leaves identical rows alone, records conflicts.
    Sector names/descriptions change only when the taxonomy version increases."""
    return [
        _seed_exchanges(session, directory / "exchanges.json"),
        _seed_sectors(session, directory / "sector_taxonomy.json"),
    ]


def _seed_exchanges(session: Session, path: Path) -> IngestionRun:
    raw = read_local_file(path)
    rec = RunRecorder(session, "reference.exchanges", raw)
    try:
        data = _Exchanges.model_validate(parse_json(raw))
    except (InputError, ValidationError) as exc:
        rec.issue("fatal", path.name, describe_error(exc))
        return rec.finish()

    existing = {e.code: e for e in session.scalars(select(Exchange))}
    for i, ex in enumerate(data.exchanges):
        row = existing.get(ex.code)
        if row is None:
            session.add(Exchange(code=ex.code, name=ex.name, country_code=ex.country_code))
            rec.counts["exchanges.created"] += 1
        elif (row.name, row.country_code) == (ex.name, ex.country_code):
            rec.counts["exchanges.unchanged"] += 1
        else:
            rec.issue(
                "conflict", f"exchanges[{i}]", "stored exchange differs; not overwritten", ex.code
            )
    session.flush()
    return rec.finish()


def _seed_sectors(session: Session, path: Path) -> IngestionRun:
    raw = read_local_file(path)
    rec = RunRecorder(session, "reference.sectors", raw)
    try:
        data = _Taxonomy.model_validate(parse_json(raw))
    except (InputError, ValidationError) as exc:
        rec.issue("fatal", path.name, describe_error(exc))
        return rec.finish()

    existing = {s.code: s for s in session.scalars(select(Sector))}
    for i, s in enumerate(data.sectors):
        row = existing.get(s.code)
        fields = {"name": s.name, "name_vi": s.name_vi, "description": s.description}
        if row is None:
            session.add(Sector(code=s.code, taxonomy_version=data.version, **fields))
            rec.counts["sectors.created"] += 1
        elif all(getattr(row, k) == v for k, v in fields.items()):
            rec.counts["sectors.unchanged"] += 1
        elif _semver(data.version) > _semver(row.taxonomy_version):
            for k, v in fields.items():
                setattr(row, k, v)
            row.taxonomy_version = data.version
            rec.counts["sectors.updated"] += 1
        else:
            rec.issue(
                "conflict",
                f"sectors[{i}]",
                f"differs from stored v{row.taxonomy_version} without a version bump",
                s.code,
            )
    session.flush()
    return rec.finish()

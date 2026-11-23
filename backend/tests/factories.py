"""Deterministic test bundles. All names are obviously fictional test data."""

import copy
import json
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.ingestion.connectors import RawInput
from app.ingestion.importer import import_bundle
from app.models import IngestionRun

SOURCE: dict[str, Any] = {
    "name": "Test disclosure source",
    "source_type": "company_disclosure",
    "base_url": "https://example.test",
    "description": "Deterministic test data; fictional.",
    "access_method": "file_import",
    "commercial_usage_status": "unknown",
}


def evidence(
    url: str = "https://example.test/doc.pdf",
    status: str = "unverified",
    retrieved_at: str = "2026-01-15T09:00:00+07:00",
) -> dict[str, Any]:
    return {
        "source_url": url,
        "document_title": "Test document",
        "retrieved_at": retrieved_at,
        "verification_status": status,
    }


def company(
    n: int = 1,
    *,
    ticker: str | None = None,
    exchange: str = "HOSE",
    sector: str = "TECHNOLOGY",
    **overrides: Any,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "legal_name": f"Test Company {n} JSC",
        "short_name": f"Test Co {n}",
        "sector_code": sector,
        "securities": [
            {
                "ticker": ticker or f"TST{n}",
                "exchange_code": exchange,
                "security_type": "common_stock",
                "currency": "VND",
                "listing_status": "listed",
            }
        ],
        "evidence": [evidence()],
    }
    record.update(overrides)
    return record


def statement(
    ticker: str = "TST1",
    *,
    revision: int = 1,
    metrics: dict[str, str] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "company": {"exchange_code": "HOSE", "ticker": ticker},
        "reporting_period_start": "2025-01-01",
        "reporting_period_end": "2025-12-31",
        "fiscal_year": 2025,
        "statement_type": "income_statement",
        "scope": "consolidated",
        "currency": "VND",
        "amount_scale": "dong",
        "revision": revision,
        "evidence": evidence("https://example.test/fs-2025.pdf"),
        "metrics": [
            {"code": k, "value": v, "source_page": 7}
            for k, v in (
                metrics or {"net_revenue": "1000000000.50", "net_profit": "-25.000001"}
            ).items()
        ],
    }
    record.update(overrides)
    return record


def bundle(
    companies: list[dict[str, Any]] | None = None,
    statements: list[dict[str, Any]] | None = None,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "data_source": copy.deepcopy(source or SOURCE),
        "companies": companies or [],
        "financial_statements": statements or [],
    }


def run(db: Session, data: dict[str, Any] | bytes, ref: str = "test://bundle") -> IngestionRun:
    content = data if isinstance(data, bytes) else json.dumps(data, default=str).encode()
    return import_bundle(db, RawInput(ref=ref, content=content))


def kinds(r: IngestionRun) -> list[str]:
    return [str(i["kind"]) for i in r.issues]


D = Decimal

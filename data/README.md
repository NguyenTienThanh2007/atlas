# data/

Data files that ATLAS imports, and the rules for them. Ingestion **code** lives in
`backend/app/ingestion/`, so it shares models, settings, tests and CI with the API.

| Path | What |
| --- | --- |
| `seed/sample_companies.json` | **Fictional** sample fixture for local development (3 companies, 4 securities, no financial figures) |
| `SOURCES.md` | Candidate data providers: what is known, what is unknown, and their licensing status |
| `../backend/app/reference/sector_taxonomy.json` | ATLAS sector taxonomy (versioned) |
| `../backend/app/reference/exchanges.json` | HOSE, HNX, UPCoM |
| `../backend/app/reference/metric_dictionary.json` | Allowed financial metric codes and units (versioned) |

**Phase 1 status: 0 verified real companies.** No provider is licensed or reachable yet (see
`SOURCES.md`), so ATLAS ships only the clearly labelled fictional fixture. Never commit invented
data presented as real.

## Commands

```bash
cd backend
uv run python -m app.ingestion reference                        # exchanges + taxonomy (also runs on container start)
uv run python -m app.ingestion import ../data/seed/sample_companies.json
```

Exit codes: `0` succeeded, `2` partial (some records rejected or conflicting; see the printed
issues), `1` failed (nothing imported, for example unreadable JSON or a changed data source). Every
run is stored in `ingestion_runs` with input SHA-256, counts and issues.

## Import bundle format (schema_version "1")

```jsonc
{
  "schema_version": "1",
  "data_source": {                       // matched by name; must equal the stored row exactly
    "name": "…", "source_type": "company_disclosure", "access_method": "file_import",
    "commercial_usage_status": "unknown", "description": "…",
    "base_url": "https://…", "terms_url": "https://…"            // optional
  },
  "companies": [{
    "legal_name": "…", "short_name": "…", "english_name": "…", "tax_code": "0101234567",
    "description": "…", "website": "https://…", "sector_code": "TECHNOLOGY",
    "securities": [{ "ticker": "ABC", "exchange_code": "HOSE", "security_type": "common_stock",
                     "isin": "VN000000ABC0", "currency": "VND", "listing_status": "listed",
                     "listed_at": "2010-01-04", "delisted_at": null }],
    "evidence": [{ "source_url": "https://…", "document_title": "…",
                   "retrieved_at": "2026-11-22T09:00:00+07:00",   // timezone required
                   "published_at": null, "verification_status": "unverified",
                   "content_hash": "<sha256 of the document>", "notes": "…" }]
  }],
  "financial_statements": [{
    "company": { "exchange_code": "HOSE", "ticker": "ABC" },
    "reporting_period_start": "2025-01-01", "reporting_period_end": "2025-12-31",
    "fiscal_year": 2025, "fiscal_quarter": null,
    "statement_type": "income_statement", "scope": "consolidated", "currency": "VND",
    "amount_scale": "trieu_dong",        // how the document prints amounts: dong | nghin_dong | trieu_dong
    "publication_date": "2026-03-30", "revision": 1,
    "evidence": { "source_url": "https://…", "retrieved_at": "…", "verification_status": "unverified" },
    "metrics": [{ "code": "net_revenue", "value": "123456.789", "source_page": 7 }]   // as printed; exact
  }]
}
```

### Rules the importer enforces

- **Validation per record.** Unknown fields, malformed tickers, ISINs, tax codes, URLs, naive
  timestamps, more than 6 decimal places, NaN or Infinity all reject that record only.
- **Normalisation.** Text is Unicode NFC (Vietnamese diacritics), whitespace collapsed; tickers,
  exchange and currency codes upper-cased; tax codes stripped of spaces and dots. JSON numbers are
  parsed as exact decimals, never floats.
- **Evidence is mandatory.** A company needs at least one evidence item, and a statement needs one.
- **Imports never verify.** Real sources must use `verification_status: "unverified"`;
  sample-fixture sources must use `"sample"`, and nothing else may. Verification is a two-person
  review recorded locally ([docs/VERIFICATION_WORKFLOW.md](../docs/VERIFICATION_WORKFLOW.md)).
- **Figures are stored in full units, exactly.** `value` is multiplied by the statement's required
  `amount_scale` (currency amounts only; per-share figures and share counts stay as printed). The
  as-printed value, scale and `source_page` are kept. Real figures need `source_page`.
- **Reporting periods are checked.** Statement currency must be VND; fiscal year, period length,
  balance-sheet date and overlaps follow [VERIFICATION_WORKFLOW.md §7](../docs/VERIFICATION_WORKFLOW.md#7-reporting-periods-p2-64).
- **Idempotent.** Re-importing the same bundle changes nothing. Evidence is de-duplicated by
  (source, entity, URL, retrieved_at).
- **No silent overwrites.** A company, security or statement that differs from what's stored is a
  `conflict`. The whole record is rolled back and reported. Restated financials must be sent as
  `revision: N+1` of an existing revision N; the old revision is kept and marked superseded.
- **Duplicates within a bundle** are reported as `duplicate`.
- **Sample and real data never mix.** A real source can't add statements to a sample company,
  and the reverse is also rejected.
- **Data-source terms can't change through an import.** If `commercial_usage_status` or any other
  field differs from the stored data source, the run fails.

## Sector taxonomy (v1.0.0)

ATLAS's **own** initial product taxonomy. It is **not** an official classification by HOSE, HNX,
the State Securities Commission or any index provider (ICB, GICS, VSIC). Codes are stable and
never reused. Names and descriptions change only with a version bump. The seeder records a
conflict, without applying it, if the file changes without a bump.

| Code | English | Tiếng Việt |
| --- | --- | --- |
| `BANKING_FINANCIAL` | Banking & Financial Services | Ngân hàng & Dịch vụ tài chính |
| `TECHNOLOGY` | Technology | Công nghệ |
| `REAL_ESTATE` | Real Estate | Bất động sản |
| `ENERGY` | Energy | Năng lượng |
| `MATERIALS_CONSTRUCTION` | Materials & Construction | Vật liệu & Xây dựng |
| `CONSUMER_RETAIL` | Consumer & Retail | Tiêu dùng & Bán lẻ |
| `LOGISTICS_INDUSTRIAL` | Logistics & Industrial | Logistics & Công nghiệp |

Methodology: a company is assigned by its primary revenue-generating activity as stated in its own
disclosures, and every assignment must carry evidence.

## Metric dictionary (v1.0.0)

Reported line items only. Ratios are derived at read time, never stored. Values are in full
units of the statement currency (not thousands or millions). The stored `unit` is the currency
(`VND`), `VND/share`, or `shares`.

| Statement | Codes |
| --- | --- |
| Income statement | `net_revenue`, `net_interest_income`, `gross_profit`, `operating_profit`, `profit_before_tax`, `net_profit`, `net_profit_parent`, `eps_basic` |
| Balance sheet | `total_assets`, `total_liabilities`, `total_equity`, `cash_and_equivalents`, `shares_outstanding` |
| Cash flow | `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow` |

Each metric's English and Vietnamese names, statement type and unit are in
`metric_dictionary.json`. Per-metric definitions and bank applicability ("not applicable" vs "not
reported") are **not written yet** (Phase 1 exit audit F-1, F-2).

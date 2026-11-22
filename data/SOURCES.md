# Data sources

Research date: 2026-11-22. **No provider is integrated.** Public accessibility is not treated as
permission to store or redistribute. Every source below stays `commercial_usage_status: unknown`
until its terms are confirmed in writing.

No connector performs network requests. Scraping is not implemented and must not be added without
written permission from the site owner.

## Summary

| Source | Offers (from docs) | Access | Licence / redistribution | Status |
| --- | --- | --- | --- | --- |
| SSI FastConnect Data | Symbol lists by exchange, security reference data (incl. ISIN, listed shares), daily/intraday OHLC, index data | REST + streaming API; SSI trading account required; API keys issued via iBoard after registering at the counter / through an account executive | **Not found** in the docs | BLOCKED: no account, no credentials, terms unknown |
| State Securities Commission disclosure portal (congbothongtin.ssc.gov.vn) | Official disclosures (expected) | Web | Unknown | BLOCKED: not reachable from our environment (DNS failure); ssc.gov.vn redirect loop |
| HOSE (hsx.vn) | Listed-company information (expected) | Web | Unknown | BLOCKED: homepage returned no content to an automated fetch; robots.txt allows all crawling, but that is **not** a licence |
| HNX (hnx.vn), incl. UPCoM | Listed-company information (expected) | Web | Unknown | BLOCKED: TLS certificate verification failed from our environment |
| Company investor-relations sites | Annual reports, audited financial statements | Web / PDF | Per company; usually unstated | Not started: manual, per-company review needed |

## SSI FastConnect Data: details

- Docs read: `https://guide.ssi.com.vn/ssi-products/` (overview, service registration, API
  specs, sample client guide).
- Endpoints listed (`https://fc-data.ssi.com.vn/api/v2/Market/...`): `Securities`,
  `SecuritiesDetails`, `IndexList`, `IndexComponents`, `DailyOhlc`, `IntradayOhlc`, `DailyIndex`,
  `DailyStockPrice`. There are **no financial-statement endpoints**.
- Authentication: ConsumerID, ConsumerSecret and PrivateKey generated on iBoard. The key is shown
  once, and an optional fixed IP can be registered. You must open an SSI trading account first.
- Unknown: pricing, rate limits, whether commercial use is permitted, whether storing history is
  permitted, whether derived data can be redistributed.
- Use for ATLAS: possibly security reference data (ticker, exchange, ISIN). It can't provide
  company profiles or financials.

## What's needed to unblock real data

1. **A decision from the project owner**: which provider(s) to pursue, and for what use (personal
   research or a commercial product).
2. **Written terms** covering storage, display and redistribution for that use. Record them in a
   `data_sources` row (`commercial_usage_status`, `terms_url`).
3. **Credentials**, stored only in environment variables or a secret manager, never in the repo.
4. Then write a connector in `backend/app/ingestion/connectors.py` that emits the bundle format in
   `data/README.md`. Its tests must use recorded fixtures, not live credentials.

Until then, real companies can only be added by hand-curating bundles from documents a person has
reviewed, each with `verification_status` set honestly (`unverified` until checked).

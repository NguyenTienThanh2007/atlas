// Pure API helpers (no Next.js imports) so they can be unit-tested with `node --test`.
import type { FigureSource } from "./provenance.ts";

export type Page<T> = { items: T[]; total: number; limit: number; offset: number };

export type ListingStatus = "pending" | "listed" | "suspended" | "delisted";

export type ExchangeRef = { code: string; name: string };
export type Exchange = ExchangeRef & { id: string; country_code: string };

export type SectorRef = { id: string; code: string; name: string; name_vi: string };
export type Sector = SectorRef & {
  description: string;
  taxonomy_version: string;
  parent_sector_id: string | null;
  company_count: number;
};

export type SecurityBrief = {
  id: string;
  ticker: string;
  exchange: ExchangeRef;
  listing_status: ListingStatus;
};
export type Security = SecurityBrief & {
  security_type: string;
  isin: string | null;
  currency: string;
  listed_at: string | null;
  delisted_at: string | null;
  last_verified_at: string | null;
};

export type CompanyListItem = {
  id: string;
  short_name: string;
  legal_name: string;
  english_name: string | null;
  is_sample: boolean;
  sector: SectorRef;
  securities: SecurityBrief[];
};
export type Company = Omit<CompanyListItem, "securities"> & {
  tax_code: string | null;
  description: string | null;
  website: string | null;
  last_verified_at: string | null;
  securities: Security[];
};

export type Evidence = {
  id: string;
  entity_type: string;
  source_url: string;
  document_title: string | null;
  published_at: string | null;
  retrieved_at: string;
  verification_status: "unverified" | "verified" | "disputed" | "rejected" | "superseded" | "sample";
  notes: string | null;
  data_source: {
    name: string;
    source_type: string;
    commercial_usage_status: string;
    terms_url: string | null;
  };
};

export type FinancialStatement = {
  id: string;
  reporting_period_start: string;
  reporting_period_end: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  statement_type: "income_statement" | "balance_sheet" | "cash_flow";
  scope: "separate" | "consolidated";
  currency: string;
  publication_date: string | null;
  revision: number;
  is_superseded: boolean;
  source_evidence: Evidence;
  // Values arrive as decimal strings so no precision is lost; never parse them to floats.
  metrics: {
    metric_code: string;
    metric_name: string;
    metric_name_vi: string | null;
    metric_name_en: string | null; // current dictionary label; metric_name is the stored one
    value: string; // full units
    unit: string;
    reported_value: string | null; // as printed in the document (null for rows from before WS1)
    reported_scale: number | null; // 1, 1000 or 1000000
    source: FigureSource; // WS3: the document and page this figure comes from
  }[];
};

// WS4-2: ratios computed by ATLAS at read time. Values are fixed-point decimal strings; the
// browser only formats them and never does arithmetic.
export type CalculationRole = "numerator" | "denominator_closing" | "denominator_opening";
export type CalculationReason =
  | "missing_input"
  | "missing_opening_balance"
  | "ambiguous_opening_balance"
  | "input_disputed_or_rejected"
  | "input_superseded"
  | "unit_mismatch"
  | "equity_not_positive"
  | "assets_not_positive";

export type CalculatedMetric = {
  code: "roe" | "roa";
  kind: "calculated";
  formula_id: string;
  formula_version: number;
  name_vi: string;
  name_en: string;
  formula_text_vi: string;
  formula_text_en: string;
  fiscal_year: number;
  scope: "separate" | "consolidated";
  period_start: string;
  period_end: string;
  status: "computed" | "not_computable";
  reason: CalculationReason | null;
  value: string | null; // ratio, 10 decimals
  percent: string | null; // 2 decimals, already rounded by the API
  denominator_average: string | null;
  inputs: {
    role: CalculationRole;
    metric_code: string;
    metric_name_vi: string | null;
    metric_name_en: string | null;
    statement_id: string;
    revision: number;
    period_end: string;
    value: string;
    unit: string;
    reported_value: string | null;
    reported_scale: number | null;
    source: FigureSource;
  }[];
  issues: {
    code: CalculationReason;
    role: CalculationRole;
    metric_code: string;
    metric_name_vi: string | null;
    metric_name_en: string | null;
    period_end: string;
  }[];
  input_verification: "all_verified" | "some_unverified" | "sample" | null;
};

// Failures carry a kind, not text: pages translate it (src/i18n/text.ts).
export type ApiFailure = {
  ok: false;
  status: number | null;
  kind: "unreachable" | "bad_response" | "not_found" | "invalid_query" | "server";
};
export type ApiResult<T> = { ok: true; data: T } | ApiFailure;

type Params = Record<string, string | number | boolean | null | undefined>;

export function buildUrl(base: string, path: string, params: Params = {}): string {
  const url = new URL(`/api/v1${path}`, base);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export async function fetchJson<T>(
  url: string,
  fetchImpl: typeof fetch = fetch,
  timeoutMs = 5000,
): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetchImpl(url, { cache: "no-store", signal: AbortSignal.timeout(timeoutMs) });
  } catch {
    return { ok: false, status: null, kind: "unreachable" };
  }
  if (res.ok) {
    try {
      return { ok: true, data: (await res.json()) as T };
    } catch {
      return { ok: false, status: res.status, kind: "bad_response" };
    }
  }
  if (res.status === 404) return { ok: false, status: 404, kind: "not_found" };
  if (res.status === 422) return { ok: false, status: 422, kind: "invalid_query" };
  return { ok: false, status: res.status, kind: "server" };
}

export type DisplayLocale = "vi" | "en";

// Vietnamese groups thousands with "." and uses "," for decimals; English the reverse.
const SEPARATORS: Record<DisplayLocale, { group: string; decimal: string }> = {
  vi: { group: ".", decimal: "," },
  en: { group: ",", decimal: "." },
};

/** Group a decimal string for display without converting it to a float. */
/** Metric label for display: the current dictionary name for the locale, falling back to the name
 * stored at import time when the code is not in the dictionary. */
export function metricLabel(
  m: { metric_name: string; metric_name_vi: string | null; metric_name_en: string | null },
  locale: DisplayLocale,
): string {
  return (locale === "vi" ? m.metric_name_vi : m.metric_name_en) ?? m.metric_name;
}

/** Format a fixed-point string keeping every decimal it has ("18.30" → "18,30"): no rounding,
 * no parsing to a number. For values the API has already rounded (percentages). */
export function formatFixed(value: string, locale: DisplayLocale): string {
  const match = /^(-?)(\d+)\.(\d+)$/.exec(value.trim());
  if (!match) return value;
  const [, sign, int, frac] = match;
  const { group, decimal } = SEPARATORS[locale];
  return `${sign}${int.replace(/\B(?=(\d{3})+(?!\d))/g, group)}${decimal}${frac}`;
}

export function formatDecimal(value: string, locale: DisplayLocale): string {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value.trim());
  if (!match) return value;
  const [, sign, int, frac] = match;
  const { group, decimal } = SEPARATORS[locale];
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, group);
  const trimmed = frac?.replace(/0+$/, "");
  return `${sign}${grouped}${trimmed ? `${decimal}${trimmed}` : ""}`;
}

/** Search-param helpers: keep only well-formed values; the API validates again. */
export function cleanParam(value: string | string[] | undefined, pattern?: RegExp): string | undefined {
  const v = (Array.isArray(value) ? value[0] : value)?.trim();
  if (!v || v.length > 100) return undefined;
  return pattern && !pattern.test(v) ? undefined : v;
}

export function pageNumber(value: string | string[] | undefined): number {
  const n = Number(Array.isArray(value) ? value[0] : value);
  return Number.isInteger(n) && n >= 1 && n <= 5000 ? n : 1;
}

export const SECTOR_CODE = /^[A-Z][A-Z0-9_]{1,31}$/;
export const EXCHANGE_CODE = /^[A-Z]{2,16}$/;
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const VN_DATE = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" });

/** Vietnamese DD/MM/YYYY, English YYYY-MM-DD. Plain dates are never shifted; timestamps are
 * shown in Vietnam time (UTC+7). */
export function formatDate(value: string | null, locale: DisplayLocale): string {
  if (!value) return "—";
  let iso = value;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    iso = VN_DATE.format(d);
  }
  const [y, m, day] = iso.split("-");
  return locale === "vi" ? `${day}/${m}/${y}` : iso;
}

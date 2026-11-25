import assert from "node:assert/strict";
import { test } from "node:test";
import {
  buildUrl,
  cleanParam,
  fetchJson,
  formatDate,
  formatDecimal,
  calculationLabel,
  denominatorUnit,
  formatFixed,
  metricLabel,
  pageRange,
  pageNumber,
  SECTOR_CODE,
} from "./api-core.ts";

const respond = (status: number, body: unknown): typeof fetch =>
  (async () => new Response(JSON.stringify(body), { status })) as typeof fetch;

test("buildUrl drops empty params and encodes the rest", () => {
  assert.equal(
    buildUrl("http://api:8000", "/companies", { q: "Hòa Phát & co", sector: "", page: undefined, limit: 20 }),
    "http://api:8000/api/v1/companies?q=H%C3%B2a+Ph%C3%A1t+%26+co&limit=20",
  );
});

test("fetchJson returns data on 200", async () => {
  const r = await fetchJson("http://x", respond(200, { items: [], total: 0 }));
  assert.deepEqual(r, { ok: true, data: { items: [], total: 0 } });
});

test("fetchJson maps 404, 422 and 5xx to error kinds (translated by the page)", async () => {
  assert.deepEqual(await fetchJson("http://x", respond(404, { detail: "Company not found" })), {
    ok: false,
    status: 404,
    kind: "not_found",
  });
  const invalid = await fetchJson("http://x", respond(422, {}));
  assert.deepEqual(invalid, { ok: false, status: 422, kind: "invalid_query" });
  const down = await fetchJson("http://x", respond(503, {}));
  assert.deepEqual(down, { ok: false, status: 503, kind: "server" });
});

test("fetchJson reports an unreachable API without throwing", async () => {
  const failing = (async () => {
    throw new TypeError("fetch failed");
  }) as typeof fetch;
  const r = await fetchJson("http://x", failing);
  assert.equal(r.ok, false);
  assert.equal(!r.ok && r.status, null);
  assert.equal(!r.ok && r.kind, "unreachable");
});

test("fetchJson handles a non-JSON success body", async () => {
  const html = (async () => new Response("<html>", { status: 200 })) as typeof fetch;
  const r = await fetchJson("http://x", html);
  assert.deepEqual(r, { ok: false, status: 200, kind: "bad_response" });
});

test("formatDecimal groups digits without float rounding, per language", () => {
  assert.equal(formatDecimal("12345678901234567890.123456", "en"), "12,345,678,901,234,567,890.123456");
  assert.equal(formatDecimal("12345678901234567890.123456", "vi"), "12.345.678.901.234.567.890,123456");
  assert.equal(formatDecimal("-25.000001", "en"), "-25.000001");
  assert.equal(formatDecimal("-25.000001", "vi"), "-25,000001");
  assert.equal(formatDecimal("-1234567.5", "vi"), "-1.234.567,5");
  assert.equal(formatDecimal("2000000000.000000", "en"), "2,000,000,000");
  assert.equal(formatDecimal("2000000000.000000", "vi"), "2.000.000.000");
  assert.equal(formatDecimal("999", "vi"), "999");
  assert.equal(formatDecimal("not a number", "vi"), "not a number");
});

test("cleanParam and pageNumber reject malformed input", () => {
  assert.equal(cleanParam("  ENERGY ", SECTOR_CODE), "ENERGY");
  assert.equal(cleanParam("energy", SECTOR_CODE), undefined);
  assert.equal(cleanParam(["a", "b"]), "a");
  assert.equal(cleanParam("x".repeat(101)), undefined);
  assert.equal(pageNumber("3"), 3);
  assert.equal(pageNumber("-1"), 1);
  assert.equal(pageNumber("2.5"), 1);
  assert.equal(pageNumber(undefined), 1);
});

test("formatDate shows timestamps in Vietnam time and never shifts plain dates", () => {
  assert.equal(formatDate("2026-11-21T17:00:00Z", "en"), "2026-11-22"); // midnight in Hanoi
  assert.equal(formatDate("2026-11-21T17:00:00Z", "vi"), "22/11/2026");
  assert.equal(formatDate("2026-11-22T00:00:00+07:00", "vi"), "22/11/2026");
  assert.equal(formatDate("2024-06-28", "en"), "2024-06-28");
  assert.equal(formatDate("2024-06-28", "vi"), "28/06/2024");
  assert.equal(formatDate(null, "vi"), "—");
  assert.equal(formatDate("garbage", "vi"), "garbage");
});

test("metric labels use the current dictionary name, never a stale stored one", () => {
  const legacy = { metric_name: "Total owners' equity", metric_name_vi: "Vốn chủ sở hữu", metric_name_en: "Total equity" };
  assert.equal(metricLabel(legacy, "en"), "Total equity");
  assert.equal(metricLabel(legacy, "vi"), "Vốn chủ sở hữu");
  const unknown = { metric_name: "Legacy metric", metric_name_vi: null, metric_name_en: null };
  assert.equal(metricLabel(unknown, "en"), "Legacy metric");
  assert.equal(metricLabel(unknown, "vi"), "Legacy metric");
});

test("fixed-point values keep their decimals and are never recomputed", () => {
  assert.equal(formatFixed("18.30", "vi"), "18,30");
  assert.equal(formatFixed("18.30", "en"), "18.30");
  assert.equal(formatFixed("-5.00", "vi"), "\u22125,00"); // minus sign U+2212 (WS4-D8)
  assert.equal(formatFixed("-45.45", "en"), "\u221245.45");
  assert.ok(!formatFixed("-1.00", "vi").includes("-"));
  assert.equal(formatFixed("0.00", "en"), "0.00");
  assert.equal(formatFixed("1234567.10", "vi"), "1.234.567,10");
  assert.equal(formatFixed("99999999999999999999999999999999.99", "en"), "99,999,999,999,999,999,999,999,999,999,999.99");
  assert.equal(formatFixed("1E-10", "vi"), "1E-10"); // not a fixed-point string: shown as is
});

test("only a computed ratio shows an input-verification label (audit AU-1)", () => {
  assert.equal(calculationLabel({ status: "computed", input_verification: "some_unverified" }), "some_unverified");
  assert.equal(calculationLabel({ status: "computed", input_verification: "all_verified" }), "all_verified");
  assert.equal(calculationLabel({ status: "not_computable", input_verification: "some_unverified" }), null);
  assert.equal(calculationLabel({ status: "not_computable", input_verification: null }), null);
});

const input = (role: "numerator" | "denominator_closing" | "denominator_opening", unit: string) => ({ role, unit });

test("the average's unit comes from the denominator inputs, never a default currency (AU-4)", () => {
  // ROE and ROA alike: the numerator's unit is not the denominator's.
  const roe = [input("numerator", "VND"), input("denominator_closing", "VND"), input("denominator_opening", "VND")];
  assert.equal(denominatorUnit({ inputs: roe } as never), "VND");
  const usd = [input("numerator", "USD"), input("denominator_closing", "USD"), input("denominator_opening", "USD")];
  assert.equal(denominatorUnit({ inputs: usd } as never), "USD");
  assert.equal(denominatorUnit({ inputs: [input("numerator", "VND")] } as never), null); // no denominator input
  assert.equal(denominatorUnit({ inputs: [input("denominator_closing", "")] } as never), null); // no unit metadata
  const mixed = [input("denominator_closing", "VND"), input("denominator_opening", "USD")];
  assert.equal(denominatorUnit({ inputs: mixed } as never), null); // mismatch: no unit is claimed
});

test("page ranges for server-paginated lists (AU-5)", () => {
  assert.deepEqual(pageRange(1, 20, 85), { from: 1, to: 20, pages: 5, beyond: false });
  assert.deepEqual(pageRange(3, 20, 85), { from: 41, to: 60, pages: 5, beyond: false });
  assert.deepEqual(pageRange(5, 20, 85), { from: 81, to: 85, pages: 5, beyond: false });
  assert.deepEqual(pageRange(6, 20, 85), { from: 101, to: 85, pages: 5, beyond: true });
  assert.deepEqual(pageRange(1, 20, 0), { from: 1, to: 0, pages: 1, beyond: false });
  assert.deepEqual(pageRange(1, 20, 20), { from: 1, to: 20, pages: 1, beyond: false });
});

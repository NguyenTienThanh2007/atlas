import assert from "node:assert/strict";
import { test } from "node:test";
import {
  buildUrl,
  cleanParam,
  fetchJson,
  formatDate,
  formatDecimal,
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

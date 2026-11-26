import assert from "node:assert/strict";
import { test } from "node:test";
import { en } from "./en.ts";
import { localePath, routeRequest, stripLocale } from "./routing.ts";
import { errorText, unitText } from "./text.ts";
import { vi } from "./vi.ts";

/** Every leaf path of a dictionary, with its kind (string or function). */
function shape(value: unknown, prefix = ""): string[] {
  if (typeof value === "string" || typeof value === "function") return [`${prefix}:${typeof value}`];
  return Object.entries(value as object)
    .flatMap(([k, v]) => shape(v, prefix ? `${prefix}.${k}` : k))
    .sort();
}

test("English has exactly the Vietnamese keys, with the same kinds", () => {
  assert.deepEqual(shape(en), shape(vi));
});

test("no dictionary entry is empty", () => {
  for (const dict of [vi, en]) {
    for (const leaf of shape(dict)) assert.ok(!leaf.startsWith(":"), leaf);
    const strings = JSON.stringify(dict, (_k, v) => (typeof v === "function" ? "fn" : v));
    assert.ok(!strings.includes('""'), "empty string in dictionary");
  }
});

test("the glossary covers every status value the API can return", () => {
  // Mirrors backend enums (app/models.py); a new value must get a label in both languages.
  const expected = {
    statementType: ["balance_sheet", "cash_flow", "income_statement"],
    scope: ["consolidated", "separate"],
    listingStatus: ["delisted", "listed", "pending", "suspended"],
    securityType: ["bond", "common_stock", "covered_warrant", "fund_certificate", "other", "preferred_stock"],
    verification: ["disputed", "rejected", "sample", "superseded", "unverified", "verified"],
    usage: ["licensed", "personal_only", "public_official", "restricted", "unknown"],
  } as const;
  for (const dict of [vi, en]) {
    for (const [group, values] of Object.entries(expected)) {
      const labels = dict.glossary[group as keyof typeof expected];
      assert.deepEqual(Object.keys(labels).sort(), [...values], group);
    }
  }
});

test("Vietnamese UI text contains no leftover English UI copy", () => {
  const values = (v: unknown): string[] =>
    typeof v === "string" ? [v] : typeof v === "function" ? [String(v(1, 2))] : Object.values(v as object).flatMap(values);
  const text = values(vi).join("\n");
  for (const english of ["Companies", "Sectors", "Loading", "Search", "Not found", "Couldn't", "Sample data", "Previous", "Next"]) {
    assert.ok(!text.includes(english), `"${english}" found in vi.ts`);
  }
});

test("Vietnamese terms for core statement concepts", () => {
  assert.equal(vi.glossary.statementType.income_statement, "Báo cáo kết quả kinh doanh");
  assert.equal(vi.glossary.statementType.balance_sheet, "Bảng cân đối kế toán");
  assert.equal(vi.glossary.statementType.cash_flow, "Báo cáo lưu chuyển tiền tệ");
  assert.equal(vi.glossary.scope.consolidated, "Hợp nhất");
  assert.equal(vi.company.period(2025, null), "Năm tài chính 2025");
  assert.equal(vi.company.period(2025, 2), "Quý 2/2025");
  assert.equal(en.company.period(2025, 2), "FY2025 Q2");
  assert.equal(vi.companies.count(1), "1 doanh nghiệp");
  assert.equal(en.companies.count(1), "1 company");
  assert.equal(en.companies.count(3), "3 companies");
});

test("units read naturally in each language", () => {
  assert.equal(unitText(vi, "VND"), "đồng");
  assert.equal(unitText(vi, "VND/share"), "đồng/cổ phiếu");
  assert.equal(unitText(vi, "shares"), "cổ phiếu");
  assert.equal(unitText(en, "VND"), "VND");
  assert.equal(unitText(en, "VND/share"), "VND/share");
  assert.equal(unitText(en, "USD"), "USD");
});

test("API failures become text in the page's language", () => {
  assert.equal(errorText(vi, { ok: false, status: 404, kind: "not_found" }), "Không tìm thấy.");
  assert.equal(errorText(en, { ok: false, status: 503, kind: "server" }), "The ATLAS API returned an error (503).");
  assert.match(errorText(vi, { ok: false, status: null, kind: "unreachable" }), /không phản hồi/);
  assert.match(errorText(vi, { ok: false, status: 422, kind: "invalid_query" }), /không hợp lệ/);
  assert.match(errorText(vi, { ok: false, status: 200, kind: "bad_response" }), /không đọc được/);
});

test("Vietnamese keeps unprefixed URLs; English lives under /en", () => {
  assert.equal(localePath("vi", "/"), "/");
  assert.equal(localePath("vi", "/companies"), "/companies");
  assert.equal(localePath("en", "/"), "/en");
  assert.equal(localePath("en", "/companies/abc"), "/en/companies/abc");
  assert.deepEqual(stripLocale("/en/companies"), { locale: "en", path: "/companies" });
  assert.deepEqual(stripLocale("/en"), { locale: "en", path: "/" });
  assert.deepEqual(stripLocale("/companies"), { locale: "vi", path: "/companies" });
  assert.deepEqual(stripLocale("/english"), { locale: "vi", path: "/english" });
});

test("proxy: rewrite Vietnamese, pass English, redirect /vi to the canonical URL", () => {
  assert.deepEqual(routeRequest("/"), { type: "rewrite", pathname: "/vi" });
  assert.deepEqual(routeRequest("/companies"), { type: "rewrite", pathname: "/vi/companies" });
  assert.deepEqual(routeRequest("/english"), { type: "rewrite", pathname: "/vi/english" });
  assert.deepEqual(routeRequest("/en"), { type: "next" });
  assert.deepEqual(routeRequest("/en/sectors/x"), { type: "next" });
  assert.deepEqual(routeRequest("/vi/companies"), { type: "redirect", pathname: "/companies" });
  assert.deepEqual(routeRequest("/vi"), { type: "redirect", pathname: "/" });
});

test("every calculation reason and input label has text in both languages (WS4-2)", () => {
  const codes = [
    "mixed_sample_and_real",
    "missing_input",
    "missing_opening_balance",
    "ambiguous_opening_balance",
    "input_not_applicable", // WS4-4-D4
    "input_disputed_or_rejected",
    "input_superseded",
    "unit_mismatch",
    "equity_not_positive",
    "assets_not_positive",
  ] as const;
  for (const dict of [vi, en]) {
    const k = dict.company.calculated;
    assert.deepEqual(Object.keys(k.reason).sort(), [...codes].sort());
    assert.deepEqual(Object.keys(k.verification).sort(), ["all_verified", "sample", "some_unverified"]);
  }
  assert.equal(vi.company.calculated.reason.missing_input("Vốn chủ sở hữu của cổ đông công ty mẹ"),
    "Không tính được: thiếu số liệu đầu vào (Vốn chủ sở hữu của cổ đông công ty mẹ)");
  assert.equal(en.company.calculated.reason.missing_opening_balance, "Not calculable: opening balance missing");
  assert.equal(vi.company.calculated.verification.some_unverified, "Tính từ số liệu chưa kiểm chứng");
  assert.equal(en.company.calculated.verification.some_unverified, "Calculated from unverified figures");
});

test("pagination ranges and the mixed-data reason read naturally (AU-3, AU-5)", () => {
  assert.equal(vi.pagination.range(1, 20, 85), "Đang hiển thị 1–20 / 85");
  assert.equal(en.pagination.range(1, 20, 85), "Showing 1–20 of 85");
  assert.match(vi.pagination.beyond(9, 85), /Trang 9 không có mục nào/);
  assert.match(en.pagination.beyond(9, 85), /Page 9 has no items/);
  assert.equal(vi.company.calculated.reason.mixed_sample_and_real, "Không tính được: dữ liệu mẫu và dữ liệu thật bị trộn lẫn");
  assert.equal(en.company.calculated.reason.mixed_sample_and_real, "Not calculable: sample and real data are mixed");
});

test("WS4-4: comparison reasons, company kinds and absent states have text in both languages", () => {
  const reasons = [
    "mixed_sample_and_real",
    "missing_current_value",
    "missing_previous_period",
    "ambiguous_previous_period",
    "period_mismatch",
    "missing_previous_value",
    "input_disputed_or_rejected",
    "input_superseded",
    "unit_or_currency_mismatch",
    "metric_not_applicable",
    "prior_zero",
    "sign_change",
  ];
  for (const dict of [vi, en]) {
    assert.deepEqual(Object.keys(dict.company.comparison.reason).sort(), [...reasons].sort());
    assert.deepEqual(Object.keys(dict.company.kind).sort(), ["bank", "label", "non_bank", "other_financial", "unclassified"]);
    assert.deepEqual(Object.keys(dict.company.absent).sort(), ["basis", "not_applicable", "not_yet_collected"]);
  }
  assert.equal(vi.company.absent.not_yet_collected, "Chưa thu thập");
  assert.equal(en.company.absent.not_applicable, "Not applicable");
});

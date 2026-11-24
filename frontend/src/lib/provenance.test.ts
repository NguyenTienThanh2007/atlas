import assert from "node:assert/strict";
import { test } from "node:test";
import { en } from "../i18n/en.ts";
import { vi } from "../i18n/vi.ts";
import { figureHref, safeHref, type FigureSource } from "./provenance.ts";

const source = (over: Partial<FigureSource> = {}): FigureSource => ({
  evidence_id: "00000000-0000-0000-0000-000000000001",
  document_title: "Consolidated FS 2025 (fictional)",
  document_url: "https://example.test/fs-2025.pdf",
  link_status: "linkable",
  page: 42,
  verification_status: "unverified",
  ...over,
});

test("a figure links to its document, opened at its page", () => {
  assert.equal(figureHref(source()), "https://example.test/fs-2025.pdf#page=42");
});

test("an unknown page still links to the document, without inventing a page", () => {
  assert.equal(figureHref(source({ page: null })), "https://example.test/fs-2025.pdf");
});

test("a URL with its own fragment is not altered", () => {
  assert.equal(figureHref(source({ document_url: "https://example.test/doc#s3" })), "https://example.test/doc#s3");
});

test("not-linkable or missing documents never become links", () => {
  assert.equal(figureHref(source({ link_status: "not_linkable", document_url: null })), null);
  // Defence in depth: even if the API said linkable, unsafe URLs are refused in the UI.
  for (const url of [
    "javascript:alert(1)",
    "data:text/html,x",
    "file:///etc/passwd",
    "fixture://sample",
    "https://user:pw@example.test/x",
    "https://exa mple.test/x",
    "https://example.test/\u0007",
    "not a url",
    "",
  ]) {
    assert.equal(safeHref(url), null, url);
    assert.equal(figureHref(source({ document_url: url })), null, url);
  }
  assert.equal(safeHref(null), null);
});

test("safe http(s) URLs pass unchanged", () => {
  for (const url of ["https://example.test/a.pdf", "http://example.test/b?x=1", "HTTPS://Example.test/c"]) {
    assert.equal(safeHref(url), url);
  }
});

test("figure source labels in Vietnamese", () => {
  const f = vi.company.figure;
  assert.equal(f.source, "Nguồn");
  assert.equal(f.page(42), "Trang 42");
  assert.equal(f.noPage, "Chưa có số trang nguồn");
  assert.equal(f.noLink, "Liên kết nguồn không khả dụng");
  assert.equal(f.scale(1000000, "VND"), "triệu đồng");
  assert.equal(f.scale(1000, "VND"), "nghìn đồng");
  assert.equal(f.reported("1.234.567,89", "triệu đồng"), "Giá trị báo cáo: 1.234.567,89 triệu đồng");
  assert.equal(
    f.open("Doanh thu thuần", "BCTC 2025", 42),
    "Mở tài liệu gốc cho chỉ tiêu Doanh thu thuần: BCTC 2025, trang 42 (mở trong thẻ mới)",
  );
  assert.match(f.open("Doanh thu thuần", "BCTC 2025", null), /chưa có số trang/);
});

test("figure source labels in English", () => {
  const f = en.company.figure;
  assert.equal(f.page(42), "Page 42");
  assert.equal(f.noPage, "Source page not recorded");
  assert.equal(f.noLink, "Source link not available");
  assert.equal(f.scale(1000000, "VND"), "million VND");
  assert.equal(f.reported("1,234,567.89", "million VND"), "As reported: 1,234,567.89 million VND");
  assert.match(f.open("Net revenue", "FS 2025", 42), /Net revenue: FS 2025, page 42 \(opens in a new tab\)$/);
  assert.match(f.open("Net revenue", "FS 2025", null), /page not recorded/);
});

// Route check against a running ATLAS frontend (production build), no dependencies.
//   BASE_URL=http://localhost:3000 node scripts/check-routes.mjs            # backend up, sample data loaded
//   BASE_URL=http://localhost:3000 EXPECT=offline node scripts/check-routes.mjs   # backend stopped
// Checks the <html lang>, key text per language, status codes, and that no English UI copy
// leaks into Vietnamese pages.

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const OFFLINE = process.env.EXPECT === "offline";
const failures = [];

async function get(path) {
  const res = await fetch(BASE + path, { redirect: "manual" });
  return { status: res.status, location: res.headers.get("location"), html: await res.text() };
}

function check(ok, message) {
  if (!ok) failures.push(message);
}

// Visible text only: drop scripts (RSC payload) and tags.
const text = (html) =>
  html
    .replace(/<script[\s\S]*?<\/script>/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ");
const ENGLISH_UI = ["Companies", "Sectors", "Watchlist", "Loading", "Search", "Couldn't", "Sample data", "Previous", "Next", "Not found", "API unreachable"];

const ROUTES = [
  { path: "/", vi: "Khám phá thị trường niêm yết Việt Nam", en: "Explore Vietnam’s listed economy" },
  { path: "/companies", vi: "Tra cứu các doanh nghiệp niêm yết", en: "Browse listed companies" },
  { path: "/sectors", vi: "So sánh các ngành", en: "Compare industries" },
  { path: "/watchlist", vi: "Danh sách theo dõi đang trống", en: "Your watchlist is empty" },
];
const OFFLINE_TEXT = {
  "/companies": { vi: "Không tải được danh sách doanh nghiệp", en: "Couldn't load companies" },
  "/sectors": { vi: "Không tải được danh sách ngành", en: "Couldn't load sectors" },
};

for (const route of ROUTES) {
  for (const lang of ["vi", "en"]) {
    const url = lang === "vi" ? route.path : `/en${route.path === "/" ? "" : route.path}`;
    const { status, html } = await get(url);
    check(status === 200, `${url}: status ${status}`);
    check(html.includes(`<html lang="${lang}"`), `${url}: <html lang="${lang}"> missing`);
    check(text(html).includes(route[lang]), `${url}: expected "${route[lang]}"`);
    if (OFFLINE && OFFLINE_TEXT[route.path]) {
      const expected = OFFLINE_TEXT[route.path][lang];
      check(text(html).includes(expected), `${url}: expected error "${expected}"`);
    }
    if (lang === "vi") {
      // Company and source names are data and may be English; UI copy may not.
      const visible = text(html).replace(/Sample (Alpha|Beta|Gamma)[^·]*/g, "");
      for (const word of ENGLISH_UI) check(!visible.includes(word), `${url}: English UI text "${word}"`);
    }
  }
}

// Canonical Vietnamese URLs and not-found pages.
const vi = await get("/vi/companies?q=a");
check(vi.status === 308 && vi.location?.endsWith("/companies?q=a"), `/vi/companies: expected 308 to /companies?q=a, got ${vi.status} ${vi.location}`);
// Unknown URLs: real 404. Their first HTML is Next's error shell; <html lang> is applied when the
// layout renders (checked in the browser). Unknown records: streamed not-found inside the layout.
for (const [url, lang, expected, status404] of [
  ["/no-such-page", "vi", "Không tìm thấy trang", true],
  ["/en/no-such-page", "en", "Page not found", true],
  ["/companies/00000000-0000-0000-0000-000000000000", "vi", "Không tìm thấy trang", false],
  ["/en/sectors/00000000-0000-0000-0000-000000000000", "en", "Page not found", false],
]) {
  const { status, html } = await get(url);
  if (status404) check(status === 404, `${url}: expected 404, got ${status}`);
  else check(html.includes(`<html lang="${lang}"`), `${url}: <html lang="${lang}"> missing`);
  // Streamed not-found content may arrive in the RSC payload rather than the static shell.
  check(html.includes(expected), `${url}: expected "${expected}"`);
}

if (!OFFLINE) {
  // With the sample fixture: filters keep working, labels are localized.
  const filtered = await get("/companies?q=sample2");
  check(text(filtered.html).includes("1 doanh nghiệp"), "/companies?q=sample2: expected 1 result");
  const enFiltered = await get("/en/companies?q=sample2");
  check(text(enFiltered.html).includes("1 company"), "/en/companies?q=sample2: expected 1 result");
  check(text(filtered.html).includes("Dữ liệu mẫu"), "/companies: sample badge not localized");
}

// WS3 (optional): every figure's source in the API is what the page renders, figure by figure.
//   PROVENANCE_COMPANY_ID=<uuid> API_URL=http://localhost:8000 node scripts/check-routes.mjs
const companyId = process.env.PROVENANCE_COMPANY_ID;
if (companyId && !OFFLINE) {
  const api = process.env.API_URL ?? "http://localhost:8000";
  const body = await (await fetch(`${api}/api/v1/companies/${companyId}/financial-statements`)).json();
  for (const lang of ["vi", "en"]) {
    const url = `${lang === "vi" ? "" : "/en"}/companies/${companyId}`;
    const { html } = await get(url);
    const anchors = [...html.matchAll(/<a [^>]*href="([^"]*)"[^>]*aria-label="([^"]*)"/g)].map((m) => ({
      href: m[1].replace(/&amp;/g, "&"),
      label: m[2],
    }));
    let figures = 0;
    for (const st of body.items) {
      for (const m of st.metrics) {
        figures++;
        const s = m.source;
        const name = (lang === "vi" ? m.metric_name_vi : m.metric_name_en) ?? m.metric_name;
        const mine = anchors.filter((a) => a.label.includes(name) && a.href.startsWith(s.document_url ?? "\u0000"));
        if (s.link_status === "linkable") {
          const expected = s.page === null ? s.document_url : `${s.document_url}#page=${s.page}`;
          check(mine.some((a) => a.href === expected), `${url}: ${m.metric_code} should link to ${expected}`);
        } else {
          check(mine.length === 0, `${url}: ${m.metric_code} must not be a link`);
          const noLink = lang === "vi" ? "Liên kết nguồn không khả dụng" : "Source link not available";
          check(text(html).includes(noLink), `${url}: expected "${noLink}"`);
        }
        if (s.page === null) {
          const noPage = lang === "vi" ? "Chưa có số trang nguồn" : "Source page not recorded";
          check(text(html).includes(noPage), `${url}: ${m.metric_code} expected "${noPage}"`);
        }
      }
    }
    // Every external figure link opens safely in a new tab.
    for (const tag of html.match(/<a [^>]*target="_blank"[^>]*>/g) ?? []) {
      check(/rel="noopener noreferrer"/.test(tag), `${url}: external link without rel=noopener noreferrer`);
      check(/href="https?:\/\//.test(tag), `${url}: non-http(s) external link ${tag}`);
    }
    check(figures > 0, `${url}: no figures to check`);
  }
}

if (failures.length) {
  console.error(`route check FAILED (${failures.length}):\n- ${failures.join("\n- ")}`);
  process.exit(1);
}
console.log(`route check passed (${OFFLINE ? "backend offline" : "backend online"}) against ${BASE}`);

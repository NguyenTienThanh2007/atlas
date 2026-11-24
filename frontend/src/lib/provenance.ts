// Pure per-figure source helpers (no Next.js imports) so they can be unit-tested with `node --test`.

export type FigureSource = {
  evidence_id: string;
  document_title: string | null;
  document_url: string | null;
  link_status: "linkable" | "not_linkable";
  page: number | null;
  verification_status: "unverified" | "verified" | "disputed" | "rejected" | "superseded" | "sample";
};

/** Defence in depth: the API already sends only linkable URLs, but the UI renders a link only for
 * an absolute http(s) URL with a host and no credentials. */
export function safeHref(url: string | null): string | null {
  if (!url || /[\s\u0000-\u001f\u007f]/.test(url)) return null;
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  const ok =
    (parsed.protocol === "http:" || parsed.protocol === "https:") &&
    parsed.hostname !== "" &&
    parsed.username === "" &&
    parsed.password === "";
  return ok ? url : null;
}

/** Link to the document, opened at the figure's page when the page is known and the URL has no
 * fragment of its own (`#page=N` is the PDF open parameter honoured by browser PDF viewers). */
export function figureHref(source: FigureSource): string | null {
  const href = source.link_status === "linkable" ? safeHref(source.document_url) : null;
  if (!href) return null;
  return source.page !== null && !href.includes("#") ? `${href}#page=${source.page}` : href;
}

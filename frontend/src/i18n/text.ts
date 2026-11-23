// Pure text helpers (no Next.js imports) so they can be unit-tested with `node --test`.
import type { ApiFailure } from "../lib/api-core.ts";
import type { Dictionary } from "./vi.ts";

/** User-facing text for a failed API call. */
export function errorText(t: Dictionary, failure: ApiFailure): string {
  switch (failure.kind) {
    case "unreachable":
      return t.errors.unreachable;
    case "bad_response":
      return t.errors.badResponse;
    case "not_found":
      return t.errors.notFound;
    case "invalid_query":
      return t.errors.invalidQuery;
    case "server":
      return t.errors.server(failure.status);
  }
}

/** Unit label for a stored metric unit: "VND", "VND/share" or "shares". */
export function unitText(t: Dictionary, unit: string): string {
  if (unit === "shares") return t.glossary.unit.shares;
  const perShare = /^([A-Z]{3})\/share$/.exec(unit);
  return perShare ? t.glossary.unit.perShare(perShare[1]) : t.glossary.unit.currency(unit);
}

// Pure locale routing helpers (no Next.js imports) so they can be unit-tested with `node --test`.
//
// Vietnamese is the default and keeps the unprefixed URLs (`/companies`); the proxy rewrites them
// to the internal `/vi/...` route. English lives under `/en/...`. The language is never guessed
// from the browser (A-4: Vietnamese-first).

export const LOCALES = ["vi", "en"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "vi";

export function hasLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

/** Public URL of an app path (which starts with "/") in a locale. */
export function localePath(locale: Locale, path: string): string {
  if (locale === DEFAULT_LOCALE) return path;
  return path === "/" ? `/${locale}` : `/${locale}${path}`;
}

/** Split a public pathname into its locale and app path. */
export function stripLocale(pathname: string): { locale: Locale; path: string } {
  const match = /^\/(en|vi)(?=\/|$)(.*)$/.exec(pathname);
  if (!match || !hasLocale(match[1])) return { locale: DEFAULT_LOCALE, path: pathname || "/" };
  return { locale: match[1], path: match[2] || "/" };
}

export type ProxyDecision =
  | { type: "next" }
  | { type: "rewrite"; pathname: string }
  | { type: "redirect"; pathname: string };

/** What the proxy does with a request path. */
export function routeRequest(pathname: string): ProxyDecision {
  const { locale, path } = stripLocale(pathname);
  const prefixed = pathname === `/${locale}` || pathname.startsWith(`/${locale}/`);
  if (!prefixed) return { type: "rewrite", pathname: `/${DEFAULT_LOCALE}${path === "/" ? "" : path}` };
  // `/vi/...` is reachable only through the rewrite; send visitors to the canonical URL.
  if (locale === DEFAULT_LOCALE) return { type: "redirect", pathname: path };
  return { type: "next" };
}

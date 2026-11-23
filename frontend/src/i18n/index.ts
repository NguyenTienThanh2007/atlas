import { lang } from "next/root-params";
import { notFound } from "next/navigation";
import { en } from "./en";
import { hasLocale, localePath, type Locale } from "./routing";
import { vi, type Dictionary } from "./vi";

export { localePath, type Locale } from "./routing";
export type { Dictionary } from "./vi";
export { errorText, unitText } from "./text";

const DICTIONARIES: Record<Locale, Dictionary> = { vi, en };

/** The request's locale and dictionary, plus a helper for locale-aware internal links. Server only. */
export async function getI18n() {
  const value = await lang();
  if (!hasLocale(value)) notFound();
  const locale: Locale = value;
  return {
    locale,
    t: DICTIONARIES[locale],
    href: (path: string) => localePath(locale, path),
  };
}

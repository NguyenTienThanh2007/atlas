"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, type ReactNode } from "react";
import type { Dictionary } from "@/i18n/vi";
import { LOCALES, localePath, stripLocale, type Locale } from "@/i18n/routing";

type Labels = Dictionary["shell"];

const NAV = [
  { path: "/", key: "discover" },
  { path: "/sectors", key: "sectors" },
  { path: "/companies", key: "companies" },
  { path: "/watchlist", key: "watchlist" },
] as const;

const LANGUAGE_NAME: Record<Locale, string> = { vi: "Tiếng Việt", en: "English" };

function Wordmark({ locale }: { locale: Locale }) {
  return (
    <Link href={localePath(locale, "/")} className="font-display text-2xl tracking-[0.22em] text-mist">
      ATLAS
    </Link>
  );
}

type NavLinkProps = { href: string; path: string; label: string; onNavigate?: () => void };

function ActiveNavLink(props: NavLinkProps) {
  const { path } = stripLocale(usePathname());
  const active = props.path === "/" ? path === "/" : path.startsWith(props.path);
  return <NavLink {...props} active={active} />;
}

function NavLink({ href, label, active, onNavigate }: NavLinkProps & { active: boolean }) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      onClick={onNavigate}
      className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
        active ? "bg-white/[0.06] text-mist" : "text-muted hover:bg-white/[0.03] hover:text-mist"
      }`}
    >
      <span aria-hidden className={`h-4 w-px ${active ? "bg-brass" : "bg-transparent"}`} />
      {label}
    </Link>
  );
}

const switchLink = "rounded px-1.5 py-0.5 text-xs hover:text-mist";

/** Same page and query in the other language. */
function CurrentPageSwitch({ locale }: { locale: Locale }) {
  const { path } = stripLocale(usePathname());
  const query = useSearchParams().toString();
  return <SwitchLinks locale={locale} target={(l) => localePath(l, path) + (query ? `?${query}` : "")} />;
}

function SwitchLinks({ locale, target }: { locale: Locale; target: (l: Locale) => string }) {
  return (
    <>
      {LOCALES.map((l) =>
        l === locale ? (
          <span key={l} aria-current="true" className={`${switchLink} text-mist`}>
            {LANGUAGE_NAME[l]}
          </span>
        ) : (
          <Link key={l} href={target(l)} hrefLang={l} lang={l} className={`${switchLink} text-muted`}>
            {LANGUAGE_NAME[l]}
          </Link>
        ),
      )}
    </>
  );
}

function LanguageSwitch({ locale, label }: { locale: Locale; label: string }) {
  return (
    <nav aria-label={label} className="flex items-center gap-1">
      {/* The path and query are unknown while prerendering: link to each home page first. */}
      <Suspense fallback={<SwitchLinks locale={locale} target={(l) => localePath(l, "/")} />}>
        <CurrentPageSwitch locale={locale} />
      </Suspense>
    </nav>
  );
}

type ShellProps = { children: ReactNode; status: ReactNode; locale: Locale; labels: Labels };

export function Shell({ children, status, locale, labels }: ShellProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[15.5rem_1fr]">
      <header className="glass sticky top-0 z-50 flex items-center justify-between border-b border-line px-4 py-3 lg:hidden">
        <Wordmark locale={locale} />
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="sidebar"
          className="rounded-md border border-line px-3 py-1.5 text-sm text-mist"
        >
          {open ? labels.close : labels.menu}
        </button>
      </header>

      {open && (
        <div
          aria-hidden
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-30 bg-ink/70 lg:hidden"
        />
      )}

      <aside
        id="sidebar"
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-line bg-charcoal px-5 pt-20 pb-6 transition-transform lg:glass lg:sticky lg:pt-6 lg:top-0 lg:h-dvh lg:w-auto lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full max-lg:invisible"
        }`}
      >
        <div className="hidden lg:block">
          <Wordmark locale={locale} />
          <p className="mt-1 text-xs text-muted">{labels.tagline}</p>
        </div>

        <nav aria-label={labels.navLabel} className="mt-2 lg:mt-10">
          <ul className="space-y-1">
            {NAV.map(({ path, key }) => {
              const href = localePath(locale, path);
              const label = labels.nav[key];
              return (
                <li key={path}>
                  {/* The path is unknown while prerendering dynamic routes: render the plain
                      link first, then highlight once the pathname resolves. */}
                  <Suspense fallback={<NavLink href={href} path={path} label={label} active={false} />}>
                    <ActiveNavLink href={href} path={path} label={label} onNavigate={() => setOpen(false)} />
                  </Suspense>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="mt-auto space-y-3 border-t border-line pt-4">
          <LanguageSwitch locale={locale} label={labels.language} />
          {status}
        </div>
      </aside>

      <main className="min-w-0 px-4 py-8 sm:px-8 lg:px-12 lg:py-12">{children}</main>
    </div>
  );
}

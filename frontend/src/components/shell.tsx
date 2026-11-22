"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense, useEffect, useState, type ReactNode } from "react";

const NAV = [
  { href: "/", label: "Discover" },
  { href: "/sectors", label: "Sectors" },
  { href: "/companies", label: "Companies" },
  { href: "/watchlist", label: "Watchlist" },
] as const;

function Wordmark() {
  return (
    <Link href="/" className="font-display text-2xl tracking-[0.22em] text-mist">
      ATLAS
    </Link>
  );
}

type NavLinkProps = { href: string; label: string; onNavigate?: () => void };

function ActiveNavLink(props: NavLinkProps) {
  const pathname = usePathname();
  const active = props.href === "/" ? pathname === "/" : pathname.startsWith(props.href);
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

export function Shell({ children, status }: { children: ReactNode; status: ReactNode }) {
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
        <Wordmark />
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="sidebar"
          className="rounded-md border border-line px-3 py-1.5 text-sm text-mist"
        >
          {open ? "Close" : "Menu"}
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
          <Wordmark />
          <p className="mt-1 text-xs text-muted">Vietnam investment discovery</p>
        </div>

        <nav aria-label="Main" className="mt-2 lg:mt-10">
          <ul className="space-y-1">
            {NAV.map(({ href, label }) => (
              <li key={href}>
                {/* The path is unknown while prerendering dynamic routes: render the plain
                    link first, then highlight once the pathname resolves. */}
                <Suspense fallback={<NavLink href={href} label={label} active={false} />}>
                  <ActiveNavLink href={href} label={label} onNavigate={() => setOpen(false)} />
                </Suspense>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mt-auto border-t border-line pt-4">{status}</div>
      </aside>

      <main className="min-w-0 px-4 py-8 sm:px-8 lg:px-12 lg:py-12">{children}</main>
    </div>
  );
}

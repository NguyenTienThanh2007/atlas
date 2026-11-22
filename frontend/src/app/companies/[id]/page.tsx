import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import { ApiErrorState, BackLink, SampleBadge } from "@/components/states";
import {
  apiGet,
  formatDate,
  formatDecimal,
  UUID,
  type Company,
  type Evidence,
  type FinancialStatement,
  type Page,
} from "@/lib/api";

export const metadata: Metadata = { title: "Company" };

const STATEMENT_LABEL: Record<FinancialStatement["statement_type"], string> = {
  income_statement: "Income statement",
  balance_sheet: "Balance sheet",
  cash_flow: "Cash flow statement",
};

const date = formatDate;

export default async function CompanyPage({ params }: PageProps<"/companies/[id]">) {
  const { id } = await params;
  if (!UUID.test(id)) notFound();

  const [company, evidence, statements] = await Promise.all([
    apiGet<Company>(`/companies/${id}`),
    apiGet<Page<Evidence>>(`/companies/${id}/evidence`, { limit: 50 }),
    apiGet<Page<FinancialStatement>>(`/companies/${id}/financial-statements`, { limit: 20 }),
  ]);
  if (!company.ok && company.status === 404) notFound();
  if (!company.ok) {
    return (
      <>
        <BackLink href="/companies">Companies</BackLink>
        <ApiErrorState title="Couldn't load this company" message={company.message} />
      </>
    );
  }
  const c = company.data;

  return (
    <article className="max-w-3xl">
      <BackLink href="/companies">Companies</BackLink>
      <header className="mt-6">
        <h1 className="flex flex-wrap items-center gap-3 font-display text-3xl font-light text-mist sm:text-4xl">
          {c.short_name}
          {c.is_sample && <SampleBadge />}
        </h1>
        <p className="mt-2 text-muted">{c.legal_name}</p>
        {c.english_name && <p className="text-sm text-muted">{c.english_name}</p>}
        {c.is_sample && (
          <p className="mt-4 text-sm text-brass">
            This is a fictional record from the ATLAS sample fixture. It does not describe a real
            company.
          </p>
        )}
      </header>

      <dl className="mt-8 grid grid-cols-1 gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
        <Fact label="Sector">
          <Link href={`/sectors/${c.sector.id}`} className="text-mist underline-offset-4 hover:underline">
            {c.sector.name}
          </Link>
        </Fact>
        <Fact label="Tax code">{c.tax_code ?? "—"}</Fact>
        <Fact label="Website">
          {c.website ? (
            <a href={c.website} rel="noopener noreferrer" target="_blank" className="text-mist hover:underline">
              {c.website}
            </a>
          ) : (
            "—"
          )}
        </Fact>
        <Fact label="Last verified">{c.last_verified_at ? date(c.last_verified_at) : "Not yet verified"}</Fact>
        {c.description && <Fact label="About" wide>{c.description}</Fact>}
      </dl>

      <Section title="Listings">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-muted">
              <tr>
                <th className="py-2 pr-4 font-normal">Ticker</th>
                <th className="py-2 pr-4 font-normal">Exchange</th>
                <th className="py-2 pr-4 font-normal">Type</th>
                <th className="py-2 pr-4 font-normal">Status</th>
                <th className="py-2 font-normal">Listed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {c.securities.map((s) => (
                <tr key={s.id}>
                  <td className="py-2 pr-4 text-mist">{s.ticker}</td>
                  <td className="py-2 pr-4 text-muted">{s.exchange.code}</td>
                  <td className="py-2 pr-4 text-muted">{s.security_type.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4 text-muted">{s.listing_status}</td>
                  <td className="py-2 text-muted">
                    {date(s.listed_at)}
                    {s.delisted_at && ` – ${date(s.delisted_at)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Financial statements">
        {!statements.ok ? (
          <p className="text-sm text-bad">{statements.message}</p>
        ) : statements.data.items.length === 0 ? (
          <p className="text-sm text-muted">
            No financial statements have been imported for this company.
          </p>
        ) : (
          <div className="space-y-6">
            {statements.data.items.map((s) => (
              <div key={s.id} className="rounded-lg border border-line px-5 py-4">
                <h3 className="text-sm font-medium text-mist">
                  {STATEMENT_LABEL[s.statement_type]} · FY{s.fiscal_year}
                  {s.fiscal_quarter ? ` Q${s.fiscal_quarter}` : ""} · {s.scope}
                  {s.revision > 1 && <span className="text-brass"> · restated (revision {s.revision})</span>}
                </h3>
                <p className="mt-1 text-xs text-muted">
                  {date(s.reporting_period_start)} to {date(s.reporting_period_end)} · {s.currency} ·
                  source:{" "}
                  <SourceLink evidence={s.source_evidence} />{" "}
                  ({s.source_evidence.verification_status})
                </p>
                <table className="mt-3 w-full text-sm">
                  <tbody className="divide-y divide-line">
                    {s.metrics.map((m) => (
                      <tr key={m.metric_code}>
                        <td className="py-1.5 pr-4 text-muted">{m.metric_name}</td>
                        <td className="py-1.5 text-right font-medium text-mist tabular-nums">
                          {formatDecimal(m.value)} <span className="text-xs text-muted">{m.unit}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Sources">
        {!evidence.ok ? (
          <p className="text-sm text-bad">{evidence.message}</p>
        ) : evidence.data.items.length === 0 ? (
          <p className="text-sm text-muted">No source evidence is recorded for this company.</p>
        ) : (
          <ul className="space-y-3 text-sm">
            {evidence.data.items.map((e) => (
              <li key={e.id} className="border-l border-line pl-4">
                <p className="text-mist">
                  <SourceLink evidence={e} />
                </p>
                <p className="text-xs text-muted">
                  {e.data_source.name} · retrieved {date(e.retrieved_at)} · {e.verification_status} ·
                  usage rights: {e.data_source.commercial_usage_status.replace(/_/g, " ")}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </article>
  );
}

// Only http(s) sources are linkable; fixture:// and file:// references are shown as text.
function SourceLink({ evidence }: { evidence: Evidence }) {
  const label = evidence.document_title ?? evidence.data_source.name;
  return /^https?:\/\//.test(evidence.source_url) ? (
    <a href={evidence.source_url} rel="noopener noreferrer" target="_blank" className="hover:text-mist hover:underline">
      {label}
    </a>
  ) : (
    <span>{label}</span>
  );
}

function Fact({ label, children, wide }: { label: string; children: ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 leading-relaxed text-mist">{children}</dd>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-12">
      <h2 className="mb-4 font-display text-xl font-light text-mist">{title}</h2>
      {children}
    </section>
  );
}

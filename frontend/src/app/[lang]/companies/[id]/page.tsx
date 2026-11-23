import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import { ApiErrorState, BackLink, SampleBadge } from "@/components/states";
import { errorText, getI18n, unitText } from "@/i18n";
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

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t.meta.titles.company };
}

export default async function CompanyPage({ params }: PageProps<"/[lang]/companies/[id]">) {
  const [{ id }, { locale, t, href }] = await Promise.all([params, getI18n()]);
  if (!UUID.test(id)) notFound();
  const date = (value: string | null) => formatDate(value, locale);
  const tc = t.company;
  const g = t.glossary;

  const [company, evidence, statements] = await Promise.all([
    apiGet<Company>(`/companies/${id}`),
    apiGet<Page<Evidence>>(`/companies/${id}/evidence`, { limit: 50 }),
    apiGet<Page<FinancialStatement>>(`/companies/${id}/financial-statements`, { limit: 20 }),
  ]);
  if (!company.ok && company.kind === "not_found") notFound();
  if (!company.ok) {
    return (
      <>
        <BackLink path="/companies">{tc.back}</BackLink>
        <ApiErrorState title={tc.loadError} message={errorText(t, company)} />
      </>
    );
  }
  const c = company.data;

  return (
    <article className="max-w-3xl">
      <BackLink path="/companies">{tc.back}</BackLink>
      <header className="mt-6">
        <h1 className="flex flex-wrap items-center gap-3 font-display text-3xl font-light text-mist sm:text-4xl">
          {c.short_name}
          {c.is_sample && <SampleBadge />}
        </h1>
        <p lang="vi" className="mt-2 text-muted">
          {c.legal_name}
        </p>
        {c.english_name && (
          <p lang="en" className="text-sm text-muted">
            {c.english_name}
          </p>
        )}
        {c.is_sample && <p className="mt-4 text-sm text-brass">{tc.sampleNotice}</p>}
      </header>

      <dl className="mt-8 grid grid-cols-1 gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
        <Fact label={tc.sector}>
          <Link href={href(`/sectors/${c.sector.id}`)} className="text-mist underline-offset-4 hover:underline">
            {locale === "vi" ? c.sector.name_vi : c.sector.name}
          </Link>
        </Fact>
        <Fact label={tc.taxCode}>{c.tax_code ?? t.common.none}</Fact>
        <Fact label={tc.website}>
          {c.website ? (
            <a href={c.website} rel="noopener noreferrer" target="_blank" className="text-mist hover:underline">
              {c.website}
            </a>
          ) : (
            t.common.none
          )}
        </Fact>
        <Fact label={tc.lastVerified}>{c.last_verified_at ? date(c.last_verified_at) : tc.notVerified}</Fact>
        {c.description && (
          <Fact label={tc.about} wide>
            {c.description}
          </Fact>
        )}
      </dl>

      <Section title={tc.listings}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-muted">
              <tr>
                <th className="py-2 pr-4 font-normal">{tc.ticker}</th>
                <th className="py-2 pr-4 font-normal">{tc.exchange}</th>
                <th className="py-2 pr-4 font-normal">{tc.type}</th>
                <th className="py-2 pr-4 font-normal">{tc.status}</th>
                <th className="py-2 font-normal">{tc.listed}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {c.securities.map((s) => (
                <tr key={s.id}>
                  <td className="py-2 pr-4 text-mist">{s.ticker}</td>
                  <td className="py-2 pr-4 text-muted">{s.exchange.code}</td>
                  <td className="py-2 pr-4 text-muted">
                    {g.securityType[s.security_type as keyof typeof g.securityType] ?? s.security_type}
                  </td>
                  <td className="py-2 pr-4 text-muted">{g.listingStatus[s.listing_status]}</td>
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

      <Section title={tc.statements}>
        {!statements.ok ? (
          <p className="text-sm text-bad">{errorText(t, statements)}</p>
        ) : statements.data.items.length === 0 ? (
          <p className="text-sm text-muted">{tc.noStatements}</p>
        ) : (
          <div className="space-y-6">
            {statements.data.items.map((s) => (
              <div key={s.id} className="rounded-lg border border-line px-5 py-4">
                <h3 className="text-sm font-medium text-mist">
                  {g.statementType[s.statement_type]} · {tc.period(s.fiscal_year, s.fiscal_quarter)} ·{" "}
                  {g.scope[s.scope]}
                  {s.revision > 1 && <span className="text-brass"> · {tc.restated(s.revision)}</span>}
                </h3>
                <p className="mt-1 text-xs text-muted">
                  {tc.range(date(s.reporting_period_start), date(s.reporting_period_end))} · {s.currency} ·{" "}
                  {tc.source}: <SourceLink evidence={s.source_evidence} /> (
                  {g.verification[s.source_evidence.verification_status]})
                </p>
                <table className="mt-3 w-full text-sm">
                  <tbody className="divide-y divide-line">
                    {s.metrics.map((m) => (
                      <tr key={m.metric_code}>
                        <td className="py-1.5 pr-4 text-muted">
                          {locale === "vi" ? (m.metric_name_vi ?? m.metric_name) : m.metric_name}
                        </td>
                        <td className="py-1.5 text-right font-medium text-mist tabular-nums">
                          {formatDecimal(m.value, locale)}{" "}
                          <span className="text-xs text-muted">{unitText(t, m.unit)}</span>
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

      <Section title={tc.sources}>
        {!evidence.ok ? (
          <p className="text-sm text-bad">{errorText(t, evidence)}</p>
        ) : evidence.data.items.length === 0 ? (
          <p className="text-sm text-muted">{tc.noSources}</p>
        ) : (
          <ul className="space-y-3 text-sm">
            {evidence.data.items.map((e) => (
              <li key={e.id} className="border-l border-line pl-4">
                <p className="text-mist">
                  <SourceLink evidence={e} />
                </p>
                <p className="text-xs text-muted">
                  {e.data_source.name} · {tc.retrieved(date(e.retrieved_at))} ·{" "}
                  {g.verification[e.verification_status]} · {tc.usageRights}:{" "}
                  {g.usage[e.data_source.commercial_usage_status as keyof typeof g.usage] ??
                    e.data_source.commercial_usage_status}
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

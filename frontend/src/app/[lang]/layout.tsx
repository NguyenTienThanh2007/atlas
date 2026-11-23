import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans } from "next/font/google";
import { Suspense } from "react";
import { ApiStatus, ApiStatusPending } from "@/components/api-status";
import { Shell } from "@/components/shell";
import { getI18n } from "@/i18n";
import { LOCALES } from "@/i18n/routing";
import "../globals.css";

// Vietnamese subsets on both families so Vietnamese headings never fall back (D-7).
const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin", "vietnamese"] });
const plex = IBM_Plex_Sans({
  variable: "--font-plex",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
});

export function generateStaticParams() {
  return LOCALES.map((lang) => ({ lang }));
}

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: { default: "ATLAS", template: "%s · ATLAS" }, description: t.meta.description };
}

export default async function RootLayout({ children }: LayoutProps<"/[lang]">) {
  const { locale, t } = await getI18n();
  return (
    <html lang={locale} className={`${fraunces.variable} ${plex.variable} antialiased`}>
      <body className="min-h-dvh">
        <Shell
          locale={locale}
          labels={t.shell}
          status={
            <Suspense fallback={<ApiStatusPending />}>
              <ApiStatus />
            </Suspense>
          }
        >
          {children}
        </Shell>
      </body>
    </html>
  );
}

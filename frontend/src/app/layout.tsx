import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans } from "next/font/google";
import { Suspense } from "react";
import { ApiStatus, ApiStatusPending } from "@/components/api-status";
import { Shell } from "@/components/shell";
import "./globals.css";

const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"] });
const plex = IBM_Plex_Sans({
  variable: "--font-plex",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: { default: "ATLAS", template: "%s · ATLAS" },
  description: "Vietnam investment discovery.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${fraunces.variable} ${plex.variable} antialiased`}>
      <body className="min-h-dvh">
        <Shell
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

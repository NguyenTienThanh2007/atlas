import { NextResponse, type NextRequest } from "next/server";
import { routeRequest } from "./i18n/routing";

export function proxy(request: NextRequest) {
  const decision = routeRequest(request.nextUrl.pathname);
  if (decision.type === "next") return NextResponse.next();
  const url = request.nextUrl.clone(); // keeps the query string (search and filters)
  url.pathname = decision.pathname;
  return decision.type === "rewrite" ? NextResponse.rewrite(url) : NextResponse.redirect(url, 308);
}

export const config = {
  // Everything except Next.js internals and files with an extension (favicon, assets).
  matcher: ["/((?!_next/|.*\\.[A-Za-z0-9]+$).*)"],
};

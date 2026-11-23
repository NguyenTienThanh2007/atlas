import { notFound } from "next/navigation";

// Unknown URLs render the localized not-found page inside the layout (correct <html lang>)
// instead of Next.js's default 404, which has no root layout outside [lang].
export default function Missing() {
  notFound();
}

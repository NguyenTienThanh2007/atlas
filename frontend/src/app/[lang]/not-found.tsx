import Link from "next/link";
import { getI18n } from "@/i18n";

export default async function NotFound() {
  const { t, href } = await getI18n();
  return (
    <section className="max-w-xl">
      <h1 className="font-display text-3xl font-light text-mist sm:text-4xl">{t.notFound.title}</h1>
      <p className="mt-3 leading-relaxed text-muted">{t.notFound.body}</p>
      <Link href={href("/")} className="mt-6 inline-block text-sm text-mist underline-offset-4 hover:underline">
        {t.notFound.home}
      </Link>
    </section>
  );
}

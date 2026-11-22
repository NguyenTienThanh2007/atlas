import { BackLink, LoadingRows } from "@/components/states";

export default function Loading() {
  return (
    <>
      <BackLink href="/companies">Companies</BackLink>
      <div className="mt-6 h-10 w-64 animate-pulse rounded bg-white/[0.04] motion-reduce:animate-none" />
      <LoadingRows rows={4} />
    </>
  );
}

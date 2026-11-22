import { PageHeader } from "@/components/empty-state";
import { LoadingRows } from "@/components/states";

export default function Loading() {
  return (
    <>
      <PageHeader
        title="Companies"
        intro="Browse listed companies on HOSE, HNX and UPCoM and see what they do."
      />
      <LoadingRows />
    </>
  );
}

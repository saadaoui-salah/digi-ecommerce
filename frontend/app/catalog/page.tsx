import { Suspense } from "react";

import { CatalogClient } from "./catalog-client";

export default function CatalogPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return (
    <Suspense fallback={null}>
      <CatalogClient searchParams={searchParams} />
    </Suspense>
  );
}

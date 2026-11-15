import { Suspense } from "react";

import { ProductClient } from "./product-client";

export default function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  return (
    <Suspense fallback={null}>
      <ProductClient params={params} />
    </Suspense>
  );
}

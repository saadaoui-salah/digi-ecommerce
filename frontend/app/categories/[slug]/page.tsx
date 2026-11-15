import { Suspense } from "react";

import { CategoryClient } from "./category-client";

export default function CategoryPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  return (
    <Suspense fallback={null}>
      <CategoryClient params={params} />
    </Suspense>
  );
}

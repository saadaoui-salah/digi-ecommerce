import { Suspense } from "react";

import { CreditsClient } from "./credits-client";

export default function CreditsPage() {
  return (
    <Suspense fallback={null}>
      <CreditsClient />
    </Suspense>
  );
}

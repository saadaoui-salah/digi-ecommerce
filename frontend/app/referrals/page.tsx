import { Suspense } from "react";

import { ReferralsClient } from "./referrals-client";

export default function ReferralsPage() {
  return (
    <Suspense fallback={null}>
      <ReferralsClient />
    </Suspense>
  );
}

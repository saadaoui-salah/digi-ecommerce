import { Suspense } from "react";

import { OrdersClient } from "./orders-client";

export default function OrdersPage() {
  return (
    <Suspense fallback={null}>
      <OrdersClient />
    </Suspense>
  );
}

export type User = {
  id: number;
  username: string;
  email: string;
  phone: string;
  first_name: string;
  last_name: string;
  credit: string;
  free_spend: boolean;
  is_approved: boolean;
  is_staff: boolean;
  total_revenue: string;
  net_profit: string;
  net_profit_percentage: string;
  total_benefit: string;
  orders_count: number;
  pending_demand_orders: number;
  accepts_referrals: boolean;
  referral_percentage: string;
  referral_code: string;
  wilaya: number | null;
  balladia: number | null;
  date_joined: string;
};

export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
  parent: number | null;
  image: string | null;
  products_count: number;
  sales_count: number;
  total_revenue: string;
  net_profit: string;
  total_benefit: string;
  pending_demand_orders: number;
};

export type ItemType = "demand" | "immediate";

export type Promotion = {
  id: number;
  name: string;
  product: number | null;
  category: number | null;
  percentage: string | null;
  discounted_price: string | null;
  base_price: string | null;
  starts_at: string | null;
  ends_at: string | null;
  is_active: boolean;
  is_current: boolean;
  created_at: string;
};

export type ProductPromotion = {
  id: number;
  name: string;
  percentage: string | null;
  discounted_price: string | null;
  ends_at: string | null;
};

export type Product = {
  id: number;
  name: string;
  type: ItemType;
  slug: string;
  category: number;
  category_name: string;
  category_slug: string;
  short_description: string;
  image: string | null;
  video: string | null;
  requires_info: boolean;
  price_from: string | null;
  price_current: string | null;
  promotion: ProductPromotion | null;
  is_available: boolean;
  sales_count: number;
  total_revenue: string;
  net_profit: string;
  total_benefit: string;
  pending_demand_orders: number;
  created_at: string;
};

export type Package = {
  id: number;
  product: number;
  product_name: string;
  group: number | null;
  name: string;
  type: ItemType;
  price: string;
  price_current: string;
  cost: string;
  margin: string;
  stock: number | null;
  is_available: boolean;
  codes_available: number;
  sort_order: number;
  sales_count: number;
  total_revenue: string;
  net_profit: string;
  total_benefit: string;
};

export type PackageGroup = {
  id: number;
  product: number;
  name: string;
  is_active: boolean;
  sort_order: number;
  packages: Package[];
};

export type ProductImage = {
  id: number;
  image: string;
  sort_order: number;
};

export type ProductDetail = Product & {
  description: string;
  images: ProductImage[];
  packages: Package[];
  package_groups: PackageGroup[];
  related: Product[];
  coupon: Coupon | null;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type OrderSummary = {
  total_orders: number;
  total_spent: string;
  total_sold: string;
  sold_count: number;
};

export type Notification = {
  id: number;
  kind: string;
  title: string;
  body: string;
  is_read: boolean;
  order_id: number | null;
  created_at: string;
};

export type Order = {
  id: number;
  product: number | null;
  product_slug: string;
  product_name: string;
  category_name: string;
  package: number | null;
  package_name: string;
  group: number | null;
  group_name: string;
  price: string;
  sold_price: string | null;
  sold_at: string | null;
  is_sold: boolean;
  buyer_info: string;
  status:
    | "pending"
    | "in_progress"
    | "has_problems"
    | "delivered"
    | "refunded"
    | "cancelled";
  code_masked: string;
  code_ready: boolean;
  code_value: string;
  assigned_to: number | null;
  assigned_to_name: string;
  reports_count: number;
  created_at: string;
};

export type Transaction = {
  id: number;
  kind: "credit" | "debit" | "refund";
  kind_label: string;
  amount: string;
  amount_signed: string;
  balance_after: string | null;
  method: string;
  note: string;
  product_name: string;
  package_name: string;
  group_name: string;
  detail: string;
  order_id: number | null;
  created_at: string;
};

export type TransactionSummary = {
  total_credited: string;
  total_debited: string;
  credit_balance: string;
};

export type Credit = {
  id: number;
  kind: "debt" | "topup";
  kind_label: string;
  amount: string;
  note: string;
  order: number | null;
  order_name: string;
  created_at: string;
};

export type CreditSummary = {
  balance: string;
  free_spend: boolean;
  total_owed: string;
  total_granted: string;
  results: Credit[];
};

export type Balladia = {
  id: number;
  name: string;
  wilaya: number;
  is_active: boolean;
};

export type Wilaya = {
  id: number;
  name: string;
  region: number;
  is_active: boolean;
  balladias: Balladia[];
};

export type Region = {
  id: number;
  name: string;
  is_active: boolean;
  wilayas: Wilaya[];
};

export type Coupon = {
  code: string;
  percentage: string | null;
  discount_price: string | null;
  max_orders: number;
  used_orders: number;
  remaining_orders: number;
  price: string;
  discount_price_of: string;
};

export type ReferralEarning = {
  id: number;
  referred: number;
  referred_email: string;
  referred_name: string;
  order: number;
  order_total: string;
  product_name: string;
  amount: string;
  percentage: string;
  created_at: string;
};

export type ReferralProgram = {
  code: string;
  percentage: string;
  accepts_referrals: boolean;
  total_earned: string;
  referred_count: number;
  earnings: ReferralEarning[];
};

export type AnalyticsPeriod = "day" | "month" | "year";
/** Whose figures are shown: the customer's own, or the whole shop (staff). */
export type AnalyticsScope = "me" | "shop";

export type AnalyticsProduct = {
  product: number;
  product_name: string;
  product_slug: string;
  category_name: string;
  count: number;
  spend: string;
  benefit: string;
};

export type AnalyticsBucket = {
  bucket: string;
  count: number;
  spend: string;
  benefit: string;
};

export type AnalyticsCards = {
  net_profit: string;
  total_revenue: string;
  net_profit_percentage: string;
  orders_count: number;
  pending_demand_orders: number;
  total_benefit: string;
};

export type AnalyticsData = {
  period: AnalyticsPeriod;
  scope: AnalyticsScope;
  month: string | null;
  year: string | null;
  available_months: string[];
  available_years: number[];
  updated_at: string | null;
  totals: {
    count: number;
    spend: string;
    benefit: string;
    products: number;
  };
  cards: AnalyticsCards;
  products: AnalyticsProduct[];
  series: AnalyticsBucket[];
};

export type PackageCode = {
  id: number;
  package: number;
  email: string;
  password: string;
  claimed_at: string | null;
};

export type DeliveredCode = {
  id: number;
  package: number;
  email: string;
  password: string;
  product_name: string;
  product_slug: string;
  package_name: string;
  claimed_at: string | null;
};

const ENV_API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

function apiBase() {
  if (ENV_API_URL) return ENV_API_URL;
  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super("API request failed");
    this.status = status;
    this.data = data;
  }
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${apiBase()}/api${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}

export function errorMessage(error: unknown): string {  if (error instanceof ApiError) {
    const data = error.data;

    if (data && typeof data === "object") {
      const body = data as Record<string, unknown>;
      if (typeof body.detail === "string") {
        return body.detail;
      }

      for (const value of Object.values(body)) {
        if (Array.isArray(value) && value.length > 0) {
          return String(value[0]);
        }
        if (typeof value === "string") {
          return value;
        }
      }
    }

    if (error.status === 401) {
      return "Invalid email or password.";
    }

    return "Something went wrong. Please try again.";
  }

  return "Unable to reach the server. Please try again.";
}

/**
 * Requests that are still in flight, keyed by path. A component that mounts
 * twice (React strict mode) or a remount racing the first render shares the
 * same request instead of firing a second one.
 */
const inFlight = new Map<string, Promise<unknown>>();

export function apiOnce<T>(path: string): Promise<T> {
  const existing = inFlight.get(path);
  if (existing) return existing as Promise<T>;

  const request = api<T>(path).finally(() => {
    inFlight.delete(path);
  });
  inFlight.set(path, request);
  return request;
}

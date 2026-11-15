"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  BadgeDollarSign,
  Check,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Search,
  ShoppingBag,
  TrendingUp,
  X,
} from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import { CopyButton } from "@/components/copy-button";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { TableSkeleton } from "@/components/skeletons";
import { useToast } from "@/components/toast";
import { useSession } from "@/components/use-session";
import { api, type Order, type OrderSummary, type Paginated } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { formatDate } from "@/lib/datetime";

const PAGE_SIZE = 10;

type SoldFilter = "all" | "sold" | "unsold";

const statusStyles: Record<string, string> = {
  pending:
    "bg-surface-muted text-muted-foreground ring-1 ring-border ring-inset",
  in_progress:
    "bg-sky-500/10 text-sky-700 ring-1 ring-sky-500/20 ring-inset dark:text-sky-300",
  has_problems:
    "bg-rose-500/10 text-rose-700 ring-1 ring-rose-500/20 ring-inset dark:text-rose-300",
  delivered:
    "bg-emerald-500/10 text-emerald-700 ring-1 ring-emerald-500/20 ring-inset dark:text-emerald-300",
  refunded:
    "bg-amber-500/10 text-amber-700 ring-1 ring-amber-500/20 ring-inset dark:text-amber-300",
  cancelled:
    "bg-surface-muted text-muted-foreground ring-1 ring-border ring-inset",
};

type StatusKey =
  | "orders.statusPending"
  | "orders.statusInProgress"
  | "orders.statusHasProblems"
  | "orders.statusDelivered"
  | "orders.statusRefunded"
  | "orders.statusCancelled";

const statusKeys: Record<string, StatusKey> = {
  pending: "orders.statusPending",
  in_progress: "orders.statusInProgress",
  has_problems: "orders.statusHasProblems",
  delivered: "orders.statusDelivered",
  refunded: "orders.statusRefunded",
  cancelled: "orders.statusCancelled",
};

export function OrdersClient() {
  const { t, locale } = useI18n();
  const { user, signOut } = useSession();
  const { notify } = useToast();
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Order> | null>(null);
  const [summary, setSummary] = useState<OrderSummary | null>(null);
  const [error, setError] = useState(false);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [soldFilter, setSoldFilter] = useState<SoldFilter>("all");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftPrice, setDraftPrice] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<OrderSummary>("/auth/orders/summary/")
      .then((res) => {
        if (!cancelled) setSummary(res);
      })
      .catch(() => {
        if (!cancelled) setSummary(null);
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  // Debounce the search box so we do not query on every keystroke.
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setSearch(searchInput.trim()), 300);

    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [searchInput]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    const params = new URLSearchParams({ page: String(page) });
    if (search) params.set("search", search);
    if (soldFilter !== "all") params.set("sold", soldFilter === "sold" ? "true" : "false");

    api<Paginated<Order>>(`/auth/orders/?${params.toString()}`)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setError(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setData(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [user, page, search, soldFilter]);

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;
  const currentPage = Math.min(page, totalPages);

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (searchTimer.current) clearTimeout(searchTimer.current);
    setPage(1);
    setSearch(searchInput.trim());
  }

  function changeFilter(next: SoldFilter) {
    setSoldFilter(next);
    setPage(1);
  }

  function startEditing(order: Order) {
    setEditingId(order.id);
    setDraftPrice(order.sold_price ?? "");
  }

  function cancelEditing() {
    setEditingId(null);
    setDraftPrice("");
  }

  async function saveSold(order: Order) {
    const value = draftPrice.trim();
    if (value !== "" && (Number.isNaN(Number(value)) || Number(value) < 0)) {
      notify(t("orders.soldInvalid"), "error");
      return;
    }

    setSavingId(order.id);
    try {
      const updated = await api<Order>(`/auth/orders/${order.id}/sold/`, {
        method: "PATCH",
        body: JSON.stringify({
          sold_price: value === "" ? null : value,
        }),
      });
      setData((current) =>
        current
          ? {
              ...current,
              results: current.results.map((row) =>
                row.id === updated.id ? updated : row,
              ),
            }
          : current,
      );
      notify(
        value === "" ? t("orders.soldCleared") : t("orders.soldSaved"),
        "success",
      );
      cancelEditing();
      // Refresh the summary so the sold totals stay accurate.
      api<OrderSummary>("/auth/orders/summary/")
        .then((res) => setSummary(res))
        .catch(() => {});
    } catch {
      notify(t("orders.soldInvalid"), "error");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("orders.eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("orders.title")}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("orders.copy")}
            </p>
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <AccountGate>
              {() => (
                <>
                {/* Summary cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                        <ShoppingBag className="size-5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                          {t("orders.totalOrders")}
                        </p>
                        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                          {summary ? summary.total_orders : "—"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-300">
                        <TrendingUp className="size-5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                          {t("orders.totalSpent")}
                        </p>
                        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                          {summary ? `${summary.total_spent} DA` : "—"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-6 sm:col-span-2 lg:col-span-1">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-300">
                        <BadgeDollarSign className="size-5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                          {t("orders.totalSold")}
                        </p>
                        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                          {summary ? `${summary.total_sold} DA` : "—"}
                        </p>
                        {summary && summary.sold_count > 0 && (
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {t("orders.soldCount", {
                              count: summary.sold_count,
                            })}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Search + sold filter */}
                <div className="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <form
                    onSubmit={handleSearchSubmit}
                    role="search"
                    className="relative w-full lg:max-w-sm"
                  >
                    <Search className="pointer-events-none absolute start-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="search"
                      name="q"
                      autoComplete="off"
                      value={searchInput}
                      onChange={(event) => {
                        setSearchInput(event.target.value);
                        setPage(1);
                      }}
                      placeholder={t("orders.searchPlaceholder")}
                      aria-label={t("orders.searchAria")}
                      className="h-10 w-full rounded-lg border border-border bg-card ps-9 pe-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-sky-500 focus:outline-none"
                    />
                  </form>

                  <div className="no-scrollbar -mx-1 flex gap-3 overflow-x-auto px-1 pb-1 pt-1 lg:mx-0 lg:pb-0">
                    {(
                      [
                        ["all", t("orders.filterAll")],
                        ["sold", t("orders.filterSold")],
                        ["unsold", t("orders.filterUnsold")],
                      ] as const
                    ).map(([value, label]) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => changeFilter(value)}
                        aria-pressed={soldFilter === value}
                        className={
                          soldFilter === value
                            ? "btn-animate h-9 shrink-0 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground"
                            : "btn-animate h-9 shrink-0 cursor-pointer rounded-lg border border-border px-4 text-sm text-muted-foreground hover:border-foreground/25 hover:text-foreground"
                        }
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Orders table */}
                {error ? (
                  <div className="mt-6 rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                    {t("orders.errorTitle")}
                  </div>
                ) : data === null ? (
                  <TableSkeleton columns={7} rows={5} className="mt-6" />
                ) : data.results.length === 0 ? (
                  <div className="mt-6 rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                    <p className="text-sm font-medium text-foreground">
                      {search || soldFilter !== "all"
                        ? t("orders.noResults")
                        : t("orders.empty")}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {search || soldFilter !== "all"
                        ? t("orders.noResultsHint")
                        : t("orders.emptyHint")}
                    </p>
                    {search || soldFilter !== "all" ? (
                      <button
                        type="button"
                        onClick={() => {
                          setSearchInput("");
                          setSearch("");
                          setSoldFilter("all");
                          setPage(1);
                        }}
                        className="btn-animate mt-5 inline-flex h-9 items-center rounded-lg border border-border px-4 text-sm text-foreground hover:border-foreground/25 hover:bg-surface-muted"
                      >
                        {t("orders.filterAll")}
                      </button>
                    ) : null}
                  </div>
                ) : (
                  <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-card">
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[880px] text-sm">
                        <thead>
                          <tr className="border-b border-border bg-surface-muted/60 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("orders.colOrder")}
                            </th>
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("orders.colDate")}
                            </th>
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("orders.colProduct")}
                            </th>
                            <th className="px-5 py-3.5 text-end font-medium">
                              {t("orders.colTotal")}
                            </th>
                            <th className="px-5 py-3.5 text-end font-medium">
                              {t("orders.colSold")}
                            </th>
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("orders.colStatus")}
                            </th>
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("orders.colCode")}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.results.map((order) => (
                            <tr
                              key={order.id}
                              className="border-b border-border/60 transition-colors last:border-0 hover:bg-surface-muted/60"
                            >
                              <td className="px-5 py-4 font-medium whitespace-nowrap text-foreground">
                                #{order.id}
                              </td>
                              <td className="px-5 py-4 whitespace-nowrap text-muted-foreground">
                                {formatDate(order.created_at, locale)}
                              </td>
                              {/* Product, package and sub package in one column */}
                              <td className="px-5 py-4">
                                <p className="font-medium text-foreground">
                                  {order.product_name}
                                </p>
                                <p className="mt-0.5 text-xs text-muted-foreground">
                                  {[order.group_name, order.package_name]
                                    .filter(Boolean)
                                    .join(" · ") || "—"}
                                </p>
                                {order.assigned_to_name && (
                                  <p className="mt-0.5 text-[11px] text-muted-foreground/80">
                                    {t("orders.handledBy", {
                                      name: order.assigned_to_name,
                                    })}
                                  </p>
                                )}
                              </td>
                              <td className="px-5 py-4 font-medium whitespace-nowrap text-end text-foreground">
                                {Number(order.price).toFixed(2)} DA
                              </td>
                              {/* Resale price: shown, or recorded inline */}
                              <td className="px-5 py-4 text-end whitespace-nowrap">
                                {editingId === order.id ? (
                                  <form
                                    onSubmit={(event) => {
                                      event.preventDefault();
                                      void saveSold(order);
                                    }}
                                    className="flex items-center justify-end gap-1.5"
                                  >
                                    <input
                                      type="text"
                                      inputMode="decimal"
                                      name="sold_price"
                                      autoComplete="off"
                                      autoFocus
                                      value={draftPrice}
                                      onChange={(event) =>
                                        setDraftPrice(event.target.value)
                                      }
                                      placeholder={t(
                                        "orders.soldPricePlaceholder",
                                      )}
                                      aria-label={t("orders.soldPriceLabel")}
                                      className="h-8 w-24 rounded-md border border-border bg-surface-muted px-2 text-end text-sm text-foreground placeholder:text-muted-foreground focus:border-sky-500 focus:outline-none"
                                    />
                                    <button
                                      type="submit"
                                      disabled={savingId === order.id}
                                      aria-label={t("orders.saveSold")}
                                      className="btn-animate grid size-8 place-items-center rounded-md bg-emerald-500/15 text-emerald-700 ring-1 ring-emerald-500/25 ring-inset hover:bg-emerald-500/25 disabled:opacity-50 dark:text-emerald-300"
                                    >
                                      {savingId === order.id ? (
                                        <Loader2 className="size-4 animate-spin" />
                                      ) : (
                                        <Check className="size-4" />
                                      )}
                                    </button>
                                    <button
                                      type="button"
                                      onClick={cancelEditing}
                                      aria-label={t("orders.cancelSold")}
                                      className="btn-animate grid size-8 place-items-center rounded-md bg-surface-muted text-muted-foreground ring-1 ring-border ring-inset hover:text-foreground"
                                    >
                                      <X className="size-4" />
                                    </button>
                                  </form>
                                ) : order.is_sold && order.sold_price !== null ? (
                                  <button
                                    type="button"
                                    onClick={() => startEditing(order)}
                                    title={
                                      order.sold_at
                                        ? t("orders.soldOn", {
                                            date: new Date(
                                              order.sold_at,
                                            ).toLocaleDateString(),
                                          })
                                        : t("orders.soldPriceLabel")
                                    }
                                    className="btn-animate inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-500/20 ring-inset hover:bg-emerald-500/20 dark:text-emerald-300"
                                  >
                                    {Number(order.sold_price).toFixed(2)} DA
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    onClick={() => startEditing(order)}
                                    className="btn-animate rounded-md border border-dashed border-border px-2.5 py-1 text-xs text-muted-foreground hover:border-foreground/30 hover:text-foreground"
                                  >
                                    {t("orders.markSold")}
                                  </button>
                                )}
                              </td>
                              <td className="px-5 py-4">
                                <span
                                  className={`inline-flex items-center rounded-md px-2.5 py-1 text-[11px] font-medium ${
                                    statusStyles[order.status] ??
                                    "bg-surface-muted text-muted-foreground"
                                  }`}
                                >
                                  {t(
                                    statusKeys[order.status] ??
                                      "orders.statusPending",
                                  )}
                                </span>
                              </td>
                              <td className="px-5 py-4">
                                {order.status === "delivered" && order.code_ready ? (
                                  <div className="flex items-center gap-2">
                                    <code
                                      title={order.code_value}
                                      className="rounded-md bg-surface-muted px-2 py-1 font-mono text-xs text-foreground"
                                    >
                                      {order.code_masked}
                                    </code>
                                    <CopyButton value={order.code_value} showLabel />
                                  </div>
                                ) : order.status === "has_problems" ? (
                                  <span className="text-xs text-rose-600 dark:text-rose-400">
                                    {t("orders.hasProblems")}
                                  </span>
                                ) : (
                                  <span className="text-xs text-muted-foreground">
                                    {t("orders.codePending")}
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {totalPages > 1 && (
                  <div className="mt-8 flex items-center justify-center gap-3">
                    <button
                      type="button"
                      disabled={currentPage <= 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      className="btn-animate inline-flex h-10 items-center gap-1.5 rounded-lg border border-border bg-card px-4 text-sm font-medium text-foreground hover:border-foreground/25 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <ChevronLeft className="size-4 rtl:rotate-180" />
                      {t("catalog.prev")}
                    </button>
                    <span className="text-sm text-muted-foreground">
                      {t("catalog.page", { page: currentPage, pages: totalPages })}
                    </span>
                    <button
                      type="button"
                      disabled={currentPage >= totalPages}
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      className="btn-animate inline-flex h-10 items-center gap-1.5 rounded-lg border border-border bg-card px-4 text-sm font-medium text-foreground hover:border-foreground/25 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {t("catalog.next")}
                      <ChevronRight className="size-4 rtl:rotate-180" />
                    </button>
                  </div>
                )}
                </>
              )}
            </AccountGate>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

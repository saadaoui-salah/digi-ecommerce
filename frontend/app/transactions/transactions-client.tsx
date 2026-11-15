"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Plus, Minus, Wallet } from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { TableSkeleton } from "@/components/skeletons";
import { useSession } from "@/components/use-session";
import {
  api,
  type Paginated,
  type Transaction,
  type TransactionSummary,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { formatDate } from "@/lib/datetime";

const PAGE_SIZE = 10;

const kindStyles: Record<string, string> = {
  credit:
    "bg-emerald-500/10 text-emerald-700 ring-1 ring-emerald-500/20 ring-inset dark:text-emerald-300",
  refund:
    "bg-sky-500/10 text-sky-700 ring-1 ring-sky-500/20 ring-inset dark:text-sky-300",
  order:
    "bg-rose-500/10 text-rose-700 ring-1 ring-rose-500/20 ring-inset dark:text-rose-300",
};

export function TransactionsClient() {
  const { t, locale } = useI18n();
  const { user, signOut } = useSession();
  const [data, setData] = useState<Paginated<Transaction> | null>(null);
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<TransactionSummary>("/auth/transactions/summary/")
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

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<Paginated<Transaction>>(`/auth/transactions/?page=${page}`)
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
  }, [user, page]);

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;
  const currentPage = Math.min(page, totalPages);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("transactions.eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("transactions.title")}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("transactions.copy")}
            </p>
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <AccountGate>
              {() => (
                <>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-300">
                        <Plus className="size-5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                          {t("transactions.totalCredited")}
                        </p>
                        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                          {summary ? `${summary.total_credited} DA` : "—"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-300">
                        <Minus className="size-5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                          {t("transactions.totalDebited")}
                        </p>
                        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                          {summary ? `${summary.total_debited} DA` : "—"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                        <Wallet className="size-5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                          {t("transactions.balance")}
                        </p>
                        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                          {summary ? `${summary.credit_balance} DA` : "—"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {error ? (
                  <div className="mt-6 rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                    {t("transactions.errorTitle")}
                  </div>
                ) : data === null ? (
                  <TableSkeleton columns={5} rows={5} className="mt-6" />
                ) : data.results.length === 0 ? (
                  <div className="mt-6 rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                    <p className="text-sm font-medium text-foreground">
                      {t("transactions.empty")}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {t("transactions.emptyHint")}
                    </p>
                  </div>
                ) : (
                  <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-card">
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[640px] text-sm">
                        <thead>
                          <tr className="border-b border-border bg-surface-muted/60 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("transactions.colDate")}
                            </th>
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("transactions.colType")}
                            </th>
                            <th className="px-5 py-3.5 text-start font-medium">
                              {t("transactions.colDetail")}
                            </th>
                            <th className="px-5 py-3.5 text-end font-medium">
                              {t("transactions.colAmount")}
                            </th>
                            <th className="px-5 py-3.5 text-end font-medium">
                              {t("transactions.colBalance")}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.results.map((transaction) => (
                            <tr
                              key={transaction.id}
                              className="border-b border-border/60 transition-colors last:border-0 hover:bg-surface-muted/60"
                            >
                              <td className="px-5 py-4 whitespace-nowrap text-muted-foreground">
                                {formatDate(transaction.created_at, locale)}
                              </td>
                              <td className="px-5 py-4">
                                <span
                                  className={`inline-flex items-center rounded-md px-2.5 py-1 text-[11px] font-medium ${
                                    kindStyles[transaction.kind] ??
                                    "bg-surface-muted text-muted-foreground"
                                  }`}
                                >
                                  {t(
                                    transaction.kind === "credit"
                                      ? "transactions.kindCredit"
                                      : transaction.kind === "refund"
                                        ? "transactions.kindRefund"
                                        : "transactions.kindOrder",
                                  )}
                                </span>
                              </td>
                              <td className="px-5 py-4 text-muted-foreground">
                                {transaction.detail || "—"}
                              </td>
                              <td
                                className={`px-5 py-4 font-medium whitespace-nowrap text-end ${
                                  Number(transaction.amount_signed) >= 0
                                    ? "text-emerald-600 dark:text-emerald-400"
                                    : "text-rose-600 dark:text-rose-400"
                                }`}
                              >
                                {Number(transaction.amount_signed) >= 0 ? "+" : "-"}
                                {Math.abs(Number(transaction.amount_signed)).toFixed(2)} DA
                              </td>
                              <td className="px-5 py-4 font-medium whitespace-nowrap text-end text-foreground">
                                {transaction.balance_after
                                  ? `${Number(transaction.balance_after).toFixed(2)} DA`
                                  : "—"}
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

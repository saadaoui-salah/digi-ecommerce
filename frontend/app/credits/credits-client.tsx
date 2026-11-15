"use client";

import { useEffect, useState } from "react";
import { Gift, HandCoins, Wallet } from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { TableSkeleton } from "@/components/skeletons";
import { useSession } from "@/components/use-session";
import { api, type CreditSummary } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { formatDate } from "@/lib/datetime";

const kindStyles: Record<string, string> = {
  topup:
    "bg-emerald-500/10 text-emerald-700 ring-1 ring-emerald-500/20 ring-inset dark:text-emerald-300",
  debt: "bg-amber-500/10 text-amber-700 ring-1 ring-amber-500/20 ring-inset dark:text-amber-300",
};

export function CreditsClient() {
  const { t, locale } = useI18n();
  const { user, signOut } = useSession();
  const [data, setData] = useState<CreditSummary | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<CreditSummary>("/auth/credits/")
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
  }, [user]);

  const unlimited = Boolean(data?.free_spend) && Number(data?.balance ?? 0) === 0;

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("credits.eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("credits.title")}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("credits.copy")}
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
                        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                          <Wallet className="size-5" />
                        </span>
                        <div>
                          <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                            {t("credits.balance")}
                          </p>
                          <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                            {data === null
                              ? "—"
                              : unlimited
                                ? t("credits.unlimited")
                                : `${data.balance} DA`}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6">
                      <div className="flex items-center gap-3">
                        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-300">
                          <HandCoins className="size-5" />
                        </span>
                        <div>
                          <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                            {t("credits.owed")}
                          </p>
                          <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                            {data ? `${data.total_owed} DA` : "—"}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6">
                      <div className="flex items-center gap-3">
                        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-300">
                          <Gift className="size-5" />
                        </span>
                        <div>
                          <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                            {t("credits.granted")}
                          </p>
                          <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                            {data ? `${data.total_granted} DA` : "—"}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {error ? (
                    <div className="mt-6 rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                      {t("credits.error")}
                    </div>
                  ) : data === null ? (
                    <TableSkeleton columns={4} rows={5} className="mt-6" />
                  ) : data.results.length === 0 ? (
                    <div className="mt-6 rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                      <p className="text-sm font-medium text-foreground">
                        {t("credits.empty")}
                      </p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {t("credits.emptyHint")}
                      </p>
                    </div>
                  ) : (
                    <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-card">
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[640px] text-sm">
                          <thead>
                            <tr className="border-b border-border bg-surface-muted/60 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
                              <th className="px-5 py-3.5 text-start font-medium">
                                {t("credits.colDate")}
                              </th>
                              <th className="px-5 py-3.5 text-start font-medium">
                                {t("credits.colType")}
                              </th>
                              <th className="px-5 py-3.5 text-start font-medium">
                                {t("credits.colDetail")}
                              </th>
                              <th className="px-5 py-3.5 text-end font-medium">
                                {t("credits.colAmount")}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.results.map((credit) => (
                              <tr
                                key={credit.id}
                                className="border-b border-border/60 transition-colors last:border-0 hover:bg-surface-muted/60"
                              >
                                <td className="px-5 py-4 whitespace-nowrap text-muted-foreground">
                                  {formatDate(credit.created_at, locale)}
                                </td>
                                <td className="px-5 py-4">
                                  <span
                                    className={`inline-flex items-center rounded-md px-2.5 py-1 text-[11px] font-medium ${
                                      kindStyles[credit.kind] ??
                                      "bg-surface-muted text-muted-foreground"
                                    }`}
                                  >
                                    {t(
                                      credit.kind === "topup"
                                        ? "credits.kindTopup"
                                        : "credits.kindDebt",
                                    )}
                                  </span>
                                </td>
                                <td className="px-5 py-4 text-muted-foreground">
                                  {[credit.order_name, credit.note]
                                    .filter(Boolean)
                                    .join(" · ") || "—"}
                                </td>
                                <td className="px-5 py-4 font-medium whitespace-nowrap text-end text-foreground">
                                  {credit.kind === "topup" ? "+" : "-"}
                                  {Number(credit.amount).toFixed(2)} DA
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
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

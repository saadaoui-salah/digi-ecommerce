"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  BadgeDollarSign,
  HandCoins,
  Percent,
  ShoppingBag,
  TrendingUp,
  Wallet,
} from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { TableSkeleton } from "@/components/skeletons";
import { SelectMenu } from "@/components/ui/select-menu";
import { useSession } from "@/components/use-session";
import {
  api,
  type AnalyticsData,
  type AnalyticsPeriod,
  type AnalyticsScope,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";

const PERIODS: AnalyticsPeriod[] = ["day", "month", "year"];

/** The scopes a customer can ask for; only staff can ask for the shop. */
const SCOPES: AnalyticsScope[] = ["me", "shop"];

function money(value: string | number) {
  return `${Number(value).toFixed(2)} DA`;
}

export function AnalyticsClient() {
  const { t, locale } = useI18n();
  const { user, signOut } = useSession();
  const [period, setPeriod] = useState<AnalyticsPeriod>("month");
  const [scope, setScope] = useState<AnalyticsScope>("me");
  const [month, setMonth] = useState<string>("");
  const [year, setYear] = useState<string>("");
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [error, setError] = useState(false);
  // Counts the requests, so a late answer never overwrites a newer one.
  const request = useRef(0);

  const load = useCallback(
    (which: AnalyticsPeriod, whose: AnalyticsScope, whichMonth: string, whichYear: string) => {
      // The daily period is narrowed down to one month, the monthly period
      // to one year.
      const params = new URLSearchParams({ period: which, scope: whose });
      if (which === "day" && whichMonth) params.set("month", whichMonth);
      if (which === "month" && whichYear) params.set("year", whichYear);

      // Only the last answer counts: a slow request must not overwrite the
      // figures of the period the customer is looking at now.
      const ticket = ++request.current;

      api<AnalyticsData>(`/analytics/?${params.toString()}`)
        .then((res) => {
          if (ticket !== request.current) return;
          setData(res);
          setError(false);
        })
        .catch(() => {
          if (ticket !== request.current) return;
          setError(true);
          setData(null);
        });
    },
    [],
  );

  useEffect(() => {
    load(period, scope, month, year);
  }, [period, scope, month, year, load]);

  // The label of a bucket depends on the period it covers.
  const bucketLabel = useCallback(
    (bucket: string) => {
      if (period === "day") {
        return new Date(`${bucket}T00:00:00`).toLocaleDateString(
          locale === "en" ? "en-GB" : locale,
          { day: "2-digit", month: "short", timeZone: "UTC" },
        );
      }
      if (period === "month") {
        return new Date(`${bucket}T00:00:00`).toLocaleDateString(
          locale === "en" ? "en-GB" : locale,
          { month: "short", year: "2-digit", timeZone: "UTC" },
        );
      }
      return bucket.slice(0, 4);
    },
    [period, locale],
  );

  const spendPoints = (data?.series ?? []).map((row) => ({
    label: bucketLabel(row.bucket),
    value: Number(row.spend),
  }));

  const benefitPoints = (data?.series ?? []).map((row) => ({
    label: bucketLabel(row.bucket),
    value: Number(row.benefit),
  }));

  const productBars = (data?.products ?? []).map((row) => ({
    label: row.product_name,
    value: row.count,
    meta: `${row.count} · ${money(row.spend)}`,
  }));

  const cards = data?.cards;

  // The months and the years that hold figures, to narrow the period down.
  const months = data?.available_months ?? [];
  const years = data?.available_years ?? [];

  // The month of the daily period, written the way the customer writes it.
  const monthLabel = useCallback(
    (value: string) => {
      const [yearPart, monthPart] = value.split("-").map(Number);
      if (!yearPart || !monthPart) return value;

      return new Date(Date.UTC(yearPart, monthPart - 1, 1)).toLocaleDateString(
        locale === "en" ? "en-GB" : locale,
        { month: "long", year: "numeric", timeZone: "UTC" },
      );
    },
    [locale],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("analytics.eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("analytics.title")}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("analytics.copy")}
            </p>
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <AccountGate loading={<TableSkeleton columns={4} rows={6} />}>
              {() => (
                <>
                {error ? (
                  <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                    {t("analytics.error")}
                  </div>
                ) : (
                  <>
                    {/* Summary cards */}
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      <div className="rounded-2xl border border-border bg-card p-6">
                        <div className="flex items-center gap-3">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-300">
                            <TrendingUp className="size-5" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                              {t("analytics.netProfit")}
                            </p>
                            <p className="mt-1 truncate text-2xl font-semibold tracking-tight text-foreground">
                              {cards ? money(cards.net_profit) : "—"}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-2xl border border-border bg-card p-6">
                        <div className="flex items-center gap-3">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                            <Wallet className="size-5" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                              {t("analytics.totalRevenue")}
                            </p>
                            <p className="mt-1 truncate text-2xl font-semibold tracking-tight text-foreground">
                              {cards ? money(cards.total_revenue) : "—"}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-2xl border border-border bg-card p-6">
                        <div className="flex items-center gap-3">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-300">
                            <Percent className="size-5" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                              {t("analytics.netProfitPercentage")}
                            </p>
                            <p className="mt-1 truncate text-2xl font-semibold tracking-tight text-foreground">
                              {cards ? `${cards.net_profit_percentage}%` : "—"}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-2xl border border-border bg-card p-6">
                        <div className="flex items-center gap-3">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-300">
                            <ShoppingBag className="size-5" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                              {t("analytics.ordersCount")}
                            </p>
                            <p className="mt-1 truncate text-2xl font-semibold tracking-tight text-foreground">
                              {cards ? cards.orders_count : "—"}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-2xl border border-border bg-card p-6">
                        <div className="flex items-center gap-3">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-300">
                            <BadgeDollarSign className="size-5" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                              {t("analytics.pendingDemand")}
                            </p>
                            <p className="mt-1 truncate text-2xl font-semibold tracking-tight text-foreground">
                              {cards ? cards.pending_demand_orders : "—"}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* The scope and the period switchers */}
                    <div className="mt-8 flex flex-wrap items-center gap-3">
                      <div className="no-scrollbar flex gap-3 overflow-x-auto pt-1 pb-1">
                        {PERIODS.map((value) => (
                          <button
                            key={value}
                            type="button"
                            onClick={() => {
                              setPeriod(value);
                              // The month and the year only apply to their
                              // own period.
                              if (value !== "day") setMonth("");
                              if (value !== "month") setYear("");
                            }}
                            aria-pressed={period === value}
                            className={
                              period === value
                                ? "btn-animate h-9 shrink-0 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground"
                                : "btn-animate h-9 shrink-0 cursor-pointer rounded-lg border border-border px-4 text-sm text-muted-foreground hover:border-foreground/25 hover:text-foreground"
                            }
                          >
                            {t(`analytics.period.${value}`)}
                          </button>
                        ))}
                      </div>

                      {/* The daily period is narrowed down to one month. */}
                      {period === "day" && months.length > 0 && (
                        <SelectMenu
                          label={t("analytics.month")}
                          value={month || months[0]}
                          options={months.map((value) => ({
                            value,
                            label: monthLabel(value),
                          }))}
                          onChange={setMonth}
                        />
                      )}

                      {/* The monthly period is narrowed down to one year. */}
                      {period === "month" && years.length > 0 && (
                        <SelectMenu
                          label={t("analytics.year")}
                          value={year || String(years[0])}
                          options={years.map((value) => ({
                            value: String(value),
                            label: String(value),
                          }))}
                          onChange={setYear}
                        />
                      )}

                      {/* Only the staff can look at the figures of the whole shop. */}
                      {user?.is_staff && (
                        <div className="no-scrollbar flex gap-3 overflow-x-auto pt-1 pb-1">
                          {SCOPES.map((value) => (
                            <button
                              key={value}
                              type="button"
                              onClick={() => setScope(value)}
                              aria-pressed={scope === value}
                              className={
                                scope === value
                                  ? "btn-animate h-9 shrink-0 rounded-lg border border-sky-500/40 bg-sky-500/10 px-4 text-sm font-medium text-sky-700 dark:text-sky-300"
                                  : "btn-animate h-9 shrink-0 cursor-pointer rounded-lg border border-border px-4 text-sm text-muted-foreground hover:border-foreground/25 hover:text-foreground"
                              }
                            >
                              {t(`analytics.scope.${value}`)}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {data === null ? (
                      <div className="mt-6">
                        <TableSkeleton columns={4} rows={6} />
                      </div>
                    ) : (
                      <div className="mt-6 space-y-6">
                        {/* Bought products by count */}
                        <div className="rounded-2xl border border-border bg-card p-6">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <h2 className="text-base font-medium tracking-tight text-foreground">
                                {t("analytics.boughtByCount")}
                              </h2>
                              <p className="mt-1 text-xs text-muted-foreground">
                                {t("analytics.boughtByCountHint")}
                              </p>
                            </div>
                            <span className="inline-flex items-center gap-1.5 rounded-md bg-surface-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                              <HandCoins className="size-3.5" />
                              {data.totals.count} {t("analytics.orders")}
                            </span>
                          </div>
                          <BarChart
                            data={productBars}
                            formatValue={(value) => `${value}`}
                            className="mt-5"
                          />
                        </div>

                        {/* Spend over time */}
                        <div className="rounded-2xl border border-border bg-card p-6">
                          <h2 className="text-base font-medium tracking-tight text-foreground">
                            {t("analytics.spendOverTime")}
                          </h2>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {t("analytics.spendOverTimeHint")}
                          </p>
                          <LineChart
                            points={spendPoints}
                            formatValue={money}
                            className="mt-5"
                          />
                        </div>

                        {/* Benefits from the resales */}
                        <div className="rounded-2xl border border-border bg-card p-6">
                          <h2 className="text-base font-medium tracking-tight text-foreground">
                            {t("analytics.benefitsOverTime")}
                          </h2>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {t("analytics.benefitsOverTimeHint")}
                          </p>
                          <LineChart
                            points={benefitPoints}
                            formatValue={money}
                            className="mt-5"
                          />
                        </div>
                      </div>
                    )}
                  </>
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

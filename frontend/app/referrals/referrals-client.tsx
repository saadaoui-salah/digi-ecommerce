"use client";

import { useEffect, useState } from "react";
import { Link2, Percent, Users, Wallet } from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import { CopyButton } from "@/components/copy-button";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { TableSkeleton } from "@/components/skeletons";
import { useSession } from "@/components/use-session";
import { api, type ReferralProgram } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { formatDate } from "@/lib/datetime";

export function ReferralsClient() {
  const { t, locale } = useI18n();
  const { user, signOut } = useSession();
  const [data, setData] = useState<ReferralProgram | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<ReferralProgram>("/auth/referrals/")
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

  const link =
    typeof window !== "undefined" && data?.code
      ? `${window.location.origin}/?ref=${data.code}`
      : "";

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("referrals.eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("referrals.title")}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("referrals.copy")}
            </p>
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <AccountGate loading={<TableSkeleton columns={3} rows={5} />}>
              {() => (
                <>
                  {error ? (
                    <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                      {t("referrals.error")}
                    </div>
                  ) : data === null ? (
                    <TableSkeleton columns={3} rows={5} />
                  ) : (
                    <>
                      <div className="grid gap-4 sm:grid-cols-3">
                        <div className="rounded-2xl border border-border bg-card p-6">
                          <div className="flex items-center gap-3">
                            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-300">
                              <Wallet className="size-5" />
                            </span>
                            <div>
                              <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                                {t("referrals.totalEarned")}
                              </p>
                              <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                                {data.total_earned} DA
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="rounded-2xl border border-border bg-card p-6">
                          <div className="flex items-center gap-3">
                            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                              <Users className="size-5" />
                            </span>
                            <div>
                              <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                                {t("referrals.referredCount")}
                              </p>
                              <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                                {data.referred_count}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="rounded-2xl border border-border bg-card p-6">
                          <div className="flex items-center gap-3">
                            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-300">
                              <Percent className="size-5" />
                            </span>
                            <div>
                              <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                                {t("referrals.yourPercentage")}
                              </p>
                              <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                                {data.percentage}%
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* The link they share */}
                      <div className="mt-6 rounded-2xl border border-border bg-card p-6">
                        <div className="flex items-center gap-3">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                            <Link2 className="size-5" />
                          </span>
                          <div>
                            <p className="text-sm font-medium text-foreground">
                              {t("referrals.yourLink")}
                            </p>
                            <p className="mt-0.5 text-xs text-muted-foreground">
                              {t("referrals.yourLinkHint")}
                            </p>
                          </div>
                        </div>

                        <div className="mt-4 flex items-center gap-2 rounded-xl border border-border bg-background px-3 py-2">
                          <span className="min-w-0 flex-1 truncate font-mono text-sm text-foreground">
                            {link}
                          </span>
                          <CopyButton value={link} />
                        </div>

                        {!data.accepts_referrals && (
                          <p className="mt-3 text-xs text-muted-foreground">
                            {t("referrals.turnedOff")}
                          </p>
                        )}
                      </div>

                      {/* What they earned */}
                      <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-card">
                        <div className="border-b border-border px-5 py-4">
                          <h2 className="text-sm font-medium text-foreground">
                            {t("referrals.earnings")}
                          </h2>
                        </div>

                        {data.earnings.length === 0 ? (
                          <p className="px-5 py-10 text-center text-sm text-muted-foreground">
                            {t("referrals.empty")}
                          </p>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full min-w-[560px] text-sm">
                              <thead>
                                <tr className="border-b border-border bg-surface-muted/60 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
                                  <th className="px-5 py-3.5 text-start font-medium">
                                    {t("referrals.customer")}
                                  </th>
                                  <th className="px-5 py-3.5 text-start font-medium">
                                    {t("referrals.order")}
                                  </th>
                                  <th className="px-5 py-3.5 text-end font-medium">
                                    {t("referrals.earned")}
                                  </th>
                                  <th className="px-5 py-3.5 text-end font-medium">
                                    {t("referrals.date")}
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                {data.earnings.map((earning) => (
                                  <tr
                                    key={earning.id}
                                    className="border-b border-border/60 transition-colors last:border-0 hover:bg-surface-muted/60"
                                  >
                                    <td className="px-5 py-4">
                                      <p className="font-medium text-foreground">
                                        {earning.referred_name}
                                      </p>
                                      <p className="mt-0.5 text-xs text-muted-foreground">
                                        {earning.referred_email}
                                      </p>
                                    </td>
                                    <td className="px-5 py-4 text-muted-foreground">
                                      {earning.product_name}
                                    </td>
                                    <td className="px-5 py-4 text-end font-medium text-emerald-600 dark:text-emerald-400">
                                      {earning.amount} DA
                                    </td>
                                    <td className="px-5 py-4 text-end whitespace-nowrap text-muted-foreground">
                                      {formatDate(earning.created_at, locale)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
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

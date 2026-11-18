"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  LockKeyhole,
  Package,
  Search,
  ShieldCheck,
  Sparkles,
  User,
  Wallet,
  Zap,
} from "lucide-react";

import { CharacterCarousel } from "@/components/character-carousel";
import { PendingApproval } from "@/components/account-gate";
import {
  CategoryRail,
  CategoryRailSkeleton,
} from "@/components/category-rail";
import { ProductCard } from "@/components/product-card";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { useSession } from "@/components/use-session";
import { ProductGridSkeleton } from "@/components/skeletons";
import {
  api,
  type Category,
  type Paginated,
  type Product,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";

const steps = [
  { icon: User, title: "home.step1Title", copy: "home.step1Copy" },
  { icon: Search, title: "home.step2Title", copy: "home.step2Copy" },
  { icon: Package, title: "home.step3Title", copy: "home.step3Copy" },
  { icon: Zap, title: "home.step4Title", copy: "home.step4Copy" },
] as const;

const highlights = [
  {
    icon: ShieldCheck,
    title: "home.vettedTitle",
    copy: "home.vettedCopy",
  },
  {
    icon: Zap,
    title: "home.twoDeliveryTitle",
    copy: "home.twoDeliveryCopy",
  },
  {
    icon: Wallet,
    title: "home.oneAccountTitle",
    copy: "home.oneAccountCopy",
  },
] as const;

type CatalogState = {
  userId: number;
  status: "ready" | "error";
  categories: Category[];
};

type DealsState = {
  userId: number;
  status: "ready" | "error";
  products: Product[];
};

export default function HomePage() {
  const { t } = useI18n();
  const { user, checkingSession, signOut } = useSession();

  const [catalog, setCatalog] = useState<CatalogState | null>(null);
  const [deals, setDeals] = useState<DealsState | null>(null);

  const catalogForUser =
    user && catalog?.userId === user.id ? catalog : null;
  const categories = catalogForUser?.categories ?? [];
  const catalogLoading = Boolean(user) && catalogForUser === null;
  const catalogError = catalogForUser?.status === "error";

  const dealsForUser = user && deals?.userId === user.id ? deals : null;
  const dealProducts = dealsForUser?.products ?? [];

  const handleSignOut = useCallback(async () => {
    setCatalog(null);
    setDeals(null);
    await signOut();
  }, [signOut]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<Paginated<Category>>("/categories/")
      .then((categoryData) => {
        if (!cancelled) {
          setCatalog({
            userId: user.id,
            status: "ready",
            categories: categoryData.results,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCatalog({
            userId: user.id,
            status: "error",
            categories: [],
          });
        }
      });

    api<Paginated<Product>>("/products/?promoted=true")
      .then((dealsData) => {
        if (!cancelled) {
          setDeals({
            userId: user.id,
            status: "ready",
            products: dealsData.results,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDeals({ userId: user.id, status: "error", products: [] });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={handleSignOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="pointer-events-none absolute -top-40 left-1/2 h-96 w-[46rem] -translate-x-1/2 rounded-full bg-sky-500/10 blur-[120px] dark:bg-sky-600/20" />

          <div className="relative mx-auto grid w-full max-w-6xl items-center gap-14 px-5 py-20 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:py-28">
            <div>
              <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/70 px-3 py-1.5 text-xs text-muted-foreground">
                <span className="size-1.5 rounded-full bg-emerald-500" />
                {t("home.badge")}
              </span>

              <h1 className="mt-6 max-w-2xl text-4xl leading-[1.05] font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                {t("home.title1")}
                <span className="mt-1 block bg-gradient-to-r from-blue-700 via-sky-600 to-cyan-500 bg-clip-text text-transparent dark:from-sky-300 dark:via-cyan-300 dark:to-teal-200">
                  {t("home.title2")}
                </span>
              </h1>

              <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground">
                {t("home.copy")}
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/catalog"
                  className="btn-animate group/btn inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-primary px-6 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {t("home.browseCatalog")}
                  <ArrowRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                </Link>
                {!user && !checkingSession && (
                  <Link
                    href="/auth"
                    className="btn-animate inline-flex h-11 items-center justify-center gap-2 rounded-lg border border-border px-6 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-card"
                  >
                    {t("home.createAccount")}
                  </Link>
                )}
              </div>

              <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
                {[
                  t("home.perkFree"),
                  t("home.perkNoSubs"),
                  t("home.perkSecure"),
                ].map((item) => (
                  <span key={item} className="inline-flex items-center gap-1.5">
                    <Check className="size-3.5 text-emerald-600 dark:text-emerald-400" />
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="relative lg:justify-self-end">
              <CharacterCarousel />
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-6xl px-5 sm:px-8">
            <dl className="grid grid-cols-1 divide-y divide-border border-t border-border sm:grid-cols-3 sm:divide-x sm:divide-y-0">
              {highlights.map(({ icon: Icon, title, copy }) => (
                <div
                  key={title}
                  className="flex items-start gap-3 py-5 pe-4 sm:px-6 sm:first:ps-0"
                >
                  <Icon className="mt-0.5 size-4 shrink-0 text-sky-500 dark:text-sky-300" />
                  <div>
                    <dt className="text-sm font-medium text-foreground">
                      {t(title)}
                    </dt>
                    <dd className="mt-0.5 text-xs leading-5 text-muted-foreground">
                      {t(copy)}
                    </dd>
                  </div>
                </div>
              ))}
            </dl>
          </div>
        </section>

        <section
          id="how"
          className="mx-auto w-full max-w-6xl px-5 py-20 sm:px-8 lg:py-24"
        >
          <div className="max-w-2xl">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("home.howEyebrow")}
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("home.howTitle")}
            </h2>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              {t("home.howCopy")}
            </p>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            {steps.map(({ icon: Icon, title, copy }, index) => (
              <div
                key={title}
                className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 transition-colors hover:border-foreground/20"
              >
                <div className="absolute end-5 top-5 font-mono text-xs text-muted-foreground/60">
                  0{index + 1}
                </div>
                <div className="grid size-11 place-items-center rounded-xl bg-gradient-to-br from-sky-500/15 to-cyan-500/15 text-sky-700 ring-1 ring-sky-500/20 ring-inset transition-transform duration-200 group-hover:scale-105 dark:text-sky-300 dark:ring-white/10">
                  <Icon className="size-5" />
                </div>
                <h3 className="mt-5 text-base font-medium tracking-tight text-foreground">
                  {t(title)}
                </h3>
                <p className="mt-1.5 max-w-sm text-sm leading-6 text-muted-foreground">
                  {t(copy)}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-4 flex flex-col gap-5 rounded-2xl border border-sky-500/20 bg-sky-500/[0.06] p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-4">
              <div className="grid size-11 shrink-0 place-items-center rounded-xl bg-sky-500/15 text-sky-700 ring-1 ring-sky-500/20 ring-inset dark:text-sky-300">
                <Sparkles className="size-5" />
              </div>
              <div>
                <h3 className="text-base font-medium tracking-tight text-foreground">
                  {t("home.customTitle")}
                </h3>
                <p className="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">
                  {t("home.customCopy")}
                </p>
              </div>
            </div>
            <Link
              href="/catalog"
              className="btn-animate group/btn inline-flex h-10 shrink-0 items-center justify-center gap-1.5 rounded-lg border border-border bg-card px-5 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-surface-muted"
            >
              {t("home.customCta")}
              <ArrowUpRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5" />
            </Link>
          </div>
        </section>

        <section id="catalog" className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-20 sm:px-8 lg:py-24">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="max-w-2xl">
                <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
                  {t("home.catalogEyebrow")}
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                  {t("home.catalogTitle")}
                </h2>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {checkingSession
                    ? t("home.checkingSession")
                    : user
                      ? t("home.welcomeBack", {
                          name: user.first_name || user.username,
                        })
                      : t("home.membersCopy")}
                </p>
              </div>

              {user && (
                <div className="flex shrink-0 items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm">
                  <Wallet className="size-4 text-sky-600 dark:text-sky-300" />
                  <span className="text-muted-foreground">
                    {t("common.credit")}
                  </span>
                  <span className="font-semibold text-foreground">
                    {user.free_spend && Number(user.credit) === 0
                      ? t("credits.unlimited")
                      : `${Number(user.credit).toFixed(2)} DA`}
                  </span>
                </div>
              )}
            </div>

            {!user ? (
              <div className="relative mt-10 overflow-hidden rounded-3xl border border-border bg-card px-6 py-14 sm:px-12">
                <div className="pointer-events-none absolute -top-24 left-1/2 size-72 -translate-x-1/2 rounded-full bg-sky-500/10 blur-3xl dark:bg-sky-600/20" />
                <div className="relative mx-auto max-w-lg text-center">
                  <div className="mx-auto grid size-12 place-items-center rounded-xl border border-border bg-surface-muted text-sky-600 dark:text-sky-300">
                    <LockKeyhole className="size-5" />
                  </div>
                  <h3 className="mt-6 text-2xl font-semibold tracking-tight text-foreground">
                    {t("home.lockedTitle")}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {t("home.lockedCopy")}
                  </p>
                  <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                    <Link
                      href="/auth"
                      className="btn-animate group/btn inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      {t("home.signInCta")}
                      <ArrowRight className="size-3.5 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                    </Link>
                    <Link
                      href="/auth"
                      className="btn-animate inline-flex h-10 items-center justify-center rounded-lg border border-border px-5 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-surface-muted"
                    >
                      {t("home.createAccountCta")}
                    </Link>
                  </div>
                  <p className="mt-5 text-xs text-muted-foreground">
                    {t("home.freeJoinNoCard")}
                  </p>
                </div>
              </div>
            ) : !user.is_approved ? (
              <div className="mt-10">
                <PendingApproval />
              </div>
            ) : catalogLoading ? (
              <CategoryRailSkeleton className="mt-9" count={9} />
            ) : catalogError ? (
              <div className="mt-9 rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                {t("home.catalogError")}
              </div>
            ) : (
              <CategoryRail categories={categories} className="mt-9" />
            )}
          </div>
        </section>

        {user && user.is_approved && dealsForUser === null && (
          <section className="border-t border-border">
            <div className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 lg:py-20">
              <ProductGridSkeleton
                count={3}
                className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
              />
            </div>
          </section>
        )}

        {user && user.is_approved && dealProducts.length > 0 && (
          <section className="border-t border-border">
            <div className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 lg:py-20">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div className="max-w-2xl">
                  <p className="text-[11px] font-medium tracking-[0.22em] text-amber-700 uppercase dark:text-amber-300">
                    {t("home.dealsEyebrow")}
                  </p>
                  <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                    {t("home.dealsTitle")}
                  </h2>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">
                    {t("home.dealsCopy")}
                  </p>
                </div>
                <Link
                  href="/catalog"
                  className="btn-animate group/btn inline-flex h-10 shrink-0 items-center justify-center gap-1.5 rounded-lg border border-border bg-card px-5 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-surface-muted"
                >
                  {t("home.allProducts")}
                  <ArrowRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                </Link>
              </div>

              <div className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {dealProducts.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            </div>
          </section>
        )}

        <section className="mx-auto w-full max-w-6xl px-5 py-20 sm:px-8">
          <div className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-blue-700 via-sky-600 to-cyan-500 px-6 py-14 text-center sm:px-12">
            <div className="pointer-events-none absolute -top-24 -right-16 size-64 rounded-full bg-white/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-28 -left-10 size-64 rounded-full bg-cyan-200/20 blur-3xl" />

            <div className="relative">
              <p className="text-[11px] font-medium tracking-[0.22em] text-white/70 uppercase">
                {t("home.ctaEyebrow")}
              </p>
              <h2 className="mx-auto mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                {t("home.ctaTitle")}
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-white/80">
                {user ? t("home.ctaCopySignedIn") : t("home.ctaCopy")}
              </p>
              <Link
                href={user ? "/catalog" : "/auth"}
                className="btn-animate group/btn mt-7 inline-flex h-11 items-center gap-2 rounded-lg bg-white px-6 text-sm font-semibold text-[#070b18] hover:bg-white/90"
              >
                {user ? t("home.ctaButtonSignedIn") : t("home.ctaButton")}
                <ArrowRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

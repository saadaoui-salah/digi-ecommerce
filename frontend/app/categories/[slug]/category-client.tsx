"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { PendingApproval } from "@/components/account-gate";
import {
  LockedPanel,
} from "@/components/package-groups";
import { ProductCard } from "@/components/product-card";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { ProductGridSkeleton } from "@/components/skeletons";
import { useSession } from "@/components/use-session";
import {
  api,
  ApiError,
  type Category,
  type Paginated,
  type Product,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type CategoryState = {
  category: Category | null;
  products: Product[];
  children: Category[];
  notFound: boolean;
  error: boolean;
};

export function CategoryClient({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const { t } = useI18n();
  const { user, checkingSession, signOut } = useSession();
  const [state, setState] = useState<CategoryState | null>(null);
  useEffect(() => {    if (!user) return;
    let cancelled = false;

    async function load() {
      try {
        const category = await api<Category>(`/categories/${slug}/`);
        const [productData, childData] = await Promise.all([
          api<Paginated<Product>>(`/products/?category_slug=${slug}`),
          api<Paginated<Category>>(`/categories/?parent=${category.id}`),
        ]);
        if (!cancelled) {
          setState({
            category,
            products: productData.results,
            children: childData.results,
            notFound: false,
            error: false,
          });
        }
      } catch (error) {
        if (!cancelled) {
          const notFound =
            error instanceof ApiError && error.status === 404;
          setState({
            category: null,
            products: [],
            children: [],
            notFound,
            error: !notFound,
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [user, slug]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <nav
              aria-label="breadcrumb"
              className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground"
            >
              <Link href="/" className="transition-colors hover:text-foreground">
                {t("common.home")}
              </Link>
              <ChevronRight className="size-3.5 rtl:rotate-180" />
              <span className="text-foreground">{state?.category?.name ?? slug}</span>
            </nav>

            <div className="mt-6 max-w-2xl">
              <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
                {t("category.eyebrow")}
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                {state?.category?.name ?? slug}
              </h1>
              {state?.category?.description && (
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {state.category.description}
                </p>
              )}
              {state && !state.notFound && !state.error && (
                <p className="mt-3 text-xs text-muted-foreground">
                  {t("category.count", { count: state.products.length })} ·{" "}
                  {t("category.products")}
                </p>
              )}
            </div>

            {state && state.children.length > 0 && (
              <div className="mt-6">
                <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                  {t("category.subcategories")}
                </p>
                <div className="mt-2.5 flex flex-wrap gap-2">
                  {state.children.map((child) => (
                    <Link
                      key={child.id}
                      href={`/categories/${child.slug}`}
                      className="btn-animate inline-flex h-9 items-center rounded-lg border border-border bg-card px-4 text-sm text-muted-foreground hover:border-foreground/25 hover:text-foreground"
                    >
                      {child.name}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            {checkingSession ? (
              <ProductGridSkeleton count={3} />
            ) : !user ? (
              <LockedPanel />
            ) : !user.is_approved ? (
              <PendingApproval />
            ) : state?.notFound ? (
              <div className="rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                <p className="text-sm font-medium text-foreground">
                  {t("product.notFoundTitle")}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("product.notFoundCopy")}
                </p>
                <Link
                  href="/#catalog"
                  className="btn-animate mt-6 inline-flex h-10 items-center rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {t("category.backToCatalog")}
                </Link>
              </div>
            ) : state?.error ? (
              <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                {t("product.errorTitle")}
              </div>
            ) : state && state.products.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                <p className="text-sm font-medium text-foreground">
                  {t("category.empty")}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("category.emptyHint")}
                </p>
              </div>
            ) : state ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {state.products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            ) : (
              <ProductGridSkeleton count={3} />
            )}
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

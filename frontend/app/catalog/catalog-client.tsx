"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import {
  CategoryActionTile,
  CategoryFilterTile,
  CategoryTileSkeleton,
} from "@/components/category-rail";
import { ProductCard } from "@/components/product-card";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { ProductGridSkeleton } from "@/components/skeletons";
import { useSession } from "@/components/use-session";
import {
  api,
  type Category,
  type Paginated,
  type Product,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LayoutGrid, Tag } from "lucide-react";

const PAGE_SIZE = 20;

/**
 * The catalog filter is a single choice: everything, the running promotions,
 * or one category. Picking a category clears the promotion filter and the
 * other way round — the two are never combined, so "On sale" always lists
 * every promoted product and a category always lists its own products.
 */
type CatalogFilter =
  | { kind: "all" }
  | { kind: "promoted" }
  | { kind: "category"; id: number };

export function CatalogClient({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = use(searchParams);
  const raw = Number(params.category);
  const { t } = useI18n();
  const { user, checkingSession, signOut } = useSession();
  const [categories, setCategories] = useState<Category[]>([]);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<CatalogFilter>(() =>
    Number.isInteger(raw) && raw > 0 ? { kind: "category", id: raw } : { kind: "all" },
  );
  const [data, setData] = useState<Paginated<Product> | null>(null);
  const [error, setError] = useState(false);

  const activeCategory =
    filter.kind === "category" ? filter.id : "all";
  const onSale = filter.kind === "promoted";

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    api<Paginated<Category>>("/categories/")
      .then((res) => {
        if (!cancelled) setCategories(res.results);
      })
      .catch(() => {
        if (!cancelled) setCategories([]);
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    const query =
      filter.kind === "category"
        ? `category=${filter.id}`
        : filter.kind === "promoted"
          ? "promoted=true"
          : "";
    api<Paginated<Product>>(
      `/products/?page=${page}${query ? `&${query}` : ""}`,
    )
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
  }, [user, page, filter]);

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;
  const count = data?.count ?? 0;

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <nav className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Link href="/" className="transition-colors hover:text-foreground">
                {t("common.home")}
              </Link>
              <ChevronRight className="size-3.5 rtl:rotate-180" />
              <span className="text-foreground">{t("catalog.eyebrow")}</span>
            </nav>

            <div className="mt-6 max-w-2xl">
              <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
                {t("catalog.eyebrow")}
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                {t("catalog.title")}
              </h1>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {user
                  ? t("catalog.count", { count })
                  : checkingSession
                    ? t("home.checkingSession")
                    : t("home.membersCopy")}
              </p>
            </div>
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <AccountGate>
              {() => (
                <>
                <div className="no-scrollbar -mx-1 mb-2 flex snap-x gap-3 overflow-x-auto px-1 pb-1 sm:gap-4 lg:flex-wrap lg:overflow-visible lg:pb-0">
                  <CategoryActionTile
                    label={t("catalog.all")}
                    active={filter.kind === "all"}
                    icon={<LayoutGrid className="size-5" />}
                    onSelect={() => {
                      setFilter({ kind: "all" });
                      setPage(1);
                    }}
                  />
                  <CategoryActionTile
                    label={t("catalog.onSale")}
                    active={onSale}
                    icon={<Tag className="size-5" />}
                    onSelect={() => {
                      // Selecting the promotion filter clears any category.
                      setFilter({ kind: "promoted" });
                      setPage(1);
                    }}
                  />
                  {categories.length === 0
                    ? Array.from({ length: 6 }).map((_, index) => (
                        <CategoryTileSkeleton key={index} />
                      ))
                    : categories.map((category) => (
                        <CategoryFilterTile
                          key={category.id}
                          category={category}
                          active={activeCategory === category.id}
                          onSelect={() => {
                            // Selecting a category clears the promotion filter.
                            setFilter({ kind: "category", id: category.id });
                            setPage(1);
                          }}
                        />
                      ))}
                </div>

                {error ? (
                  <div className="mt-10 rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                    {t("catalog.errorTitle")}
                  </div>
                ) : data === null ? (
                  <ProductGridSkeleton
                    count={6}
                    className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
                  />
                ) : data.results.length === 0 ? (
                  <div className="mt-10 rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                    <p className="text-sm font-medium text-foreground">
                      {t("catalog.empty")}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {t("catalog.emptyHint")}
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {data.results.map((product) => (
                        <ProductCard key={product.id} product={product} />
                      ))}
                    </div>

                    {totalPages > 1 && (
                      <div className="mt-10 flex items-center justify-center gap-3">
                        <button
                          type="button"
                          disabled={page <= 1}
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          className="btn-animate inline-flex h-10 items-center gap-1.5 rounded-lg border border-border bg-card px-4 text-sm font-medium text-foreground hover:border-foreground/25 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          <ChevronLeft className="size-4 rtl:rotate-180" />
                          {t("catalog.prev")}
                        </button>
                        <span className="text-sm text-muted-foreground">
                          {t("catalog.page", { page, pages: totalPages })}
                        </span>
                        <button
                          type="button"
                          disabled={page >= totalPages}
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

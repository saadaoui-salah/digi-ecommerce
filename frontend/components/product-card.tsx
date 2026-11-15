"use client";

import Link from "next/link";
import { ArrowRight, Play } from "lucide-react";

import type { Product } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export function money(value: string | null | undefined) {
  if (!value) return "—";
  return `${Number(value).toFixed(2)} DA`;
}

export function ProductCard({ product }: { product: Product }) {
  const { t } = useI18n();
  const isInstant = product.type === "immediate";
  const promotion = product.promotion;
  const hasDiscount =
    promotion !== null &&
    product.price_current !== null &&
    product.price_from !== null &&
    Number(product.price_current) < Number(product.price_from);

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition duration-200 hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-lg hover:shadow-foreground/5">
      <Link
        href={`/products/${product.slug}`}
        className="relative block aspect-16/9 overflow-hidden bg-surface-muted"
      >
        {product.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image}
            alt={product.name}
            loading="lazy"
            className="size-full object-cover transition duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="size-full bg-gradient-to-br from-sky-500/20 to-cyan-500/10 dark:from-sky-600/25 dark:to-teal-500/10" />
        )}
        {product.video && (
          <span className="absolute bottom-3 end-3 inline-flex items-center gap-1.5 rounded-lg bg-black/55 px-2 py-1 text-[10px] font-medium text-white backdrop-blur">
            <Play className="size-3" />
            {t("product.hasVideo")}
          </span>
        )}
      </Link>
      <div className="flex flex-1 flex-col p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Link
            href={`/categories/${product.category_slug}`}
            className="truncate text-[10px] font-medium tracking-[0.18em] text-sky-700 uppercase transition-colors hover:text-sky-600 dark:text-sky-300 dark:hover:text-sky-200"
          >
            {product.category_name}
          </Link>
          <div className="flex shrink-0 items-center gap-1.5">
            {promotion && (
              <span
                title={promotion.name}
                className="rounded-md bg-amber-500/15 px-2 py-1 text-[10px] font-semibold text-amber-700 ring-1 ring-amber-500/25 ring-inset dark:text-amber-300"
              >
                {promotion.percentage
                  ? t("promotion.badge", {
                      percent: Number(promotion.percentage).toFixed(0),
                    })
                  : t("promotion.badgePrice")}
              </span>
            )}
            <span
              className={
                isInstant
                  ? "shrink-0 rounded-md bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-700 ring-1 ring-emerald-500/20 ring-inset dark:text-emerald-300"
                  : "shrink-0 rounded-md bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium text-amber-700 ring-1 ring-amber-500/20 ring-inset dark:text-amber-300"
              }
            >
              {isInstant ? t("home.instantBadge") : t("home.demandBadge")}
            </span>
          </div>
        </div>

        <Link
          href={`/products/${product.slug}`}
          className="mt-3 inline-flex items-center gap-1.5 text-lg font-medium tracking-tight text-foreground transition-colors hover:text-sky-600 dark:hover:text-sky-300"
        >
          {product.name}
          <ArrowRight className="size-4 shrink-0 -translate-x-0.5 opacity-0 transition duration-200 group-hover:translate-x-0 group-hover:opacity-100 rtl:rotate-180" />
        </Link>
        <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-muted-foreground">
          {product.short_description || t("home.fallbackDescription")}
        </p>

        <div className="mt-auto flex items-end justify-between gap-4 pt-6">
          <div>
            <p className="text-[10px] tracking-[0.16em] text-muted-foreground uppercase">
              {t("home.from")}
            </p>
            {hasDiscount ? (
              <p className="mt-0.5 flex flex-wrap items-baseline gap-2">
                <span className="text-xl font-semibold tracking-tight text-foreground">
                  {money(product.price_current)}
                </span>
                <span className="text-sm text-muted-foreground line-through">
                  {money(product.price_from)}
                </span>
              </p>
            ) : (
              <p className="mt-0.5 text-xl font-semibold tracking-tight text-foreground">
                {money(product.price_current ?? product.price_from)}
              </p>
            )}
          </div>
          <Link
            href={`/products/${product.slug}`}
            title={t("home.viewProduct")}
            className="btn-animate group/btn inline-flex h-9 items-center gap-1.5 rounded-lg border border-border px-4 text-sm font-medium text-foreground transition-colors hover:border-foreground/25 hover:bg-surface-muted"
          >
            {t("home.viewProduct")}
            <ArrowRight className="size-3.5 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
          </Link>
        </div>
      </div>
    </article>
  );
}

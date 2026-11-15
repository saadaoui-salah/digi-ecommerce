"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import type { Category } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export function CategoryCard({ category }: { category: Category }) {
  const { t } = useI18n();

  return (
    <Link
      href={`/categories/${category.slug}`}
      className="group relative block overflow-hidden rounded-2xl border border-border bg-card transition duration-200 hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-lg hover:shadow-foreground/5"
    >
      <div className="relative aspect-16/9 overflow-hidden bg-surface-muted">
        {category.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={category.image}
            alt={category.name}
            loading="lazy"
            className="size-full object-cover transition duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="size-full bg-gradient-to-br from-sky-500/20 to-cyan-500/10 dark:from-sky-600/25 dark:to-teal-500/10" />
        )}
      </div>

      <div className="flex items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <h3 className="truncate text-base font-medium tracking-tight text-foreground transition-colors group-hover:text-sky-600 dark:group-hover:text-sky-300">
            {category.name}
          </h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {category.products_count === 1
              ? t("category.countOne")
              : t("category.count", { count: category.products_count })}
          </p>
        </div>
        <ArrowRight className="size-4 shrink-0 text-muted-foreground transition duration-200 group-hover:translate-x-0.5 group-hover:text-sky-600 rtl:rotate-180 dark:group-hover:text-sky-300" />
      </div>
    </Link>
  );
}

"use client";

import Link from "next/link";

import type { Category } from "@/lib/api";

/**
 * The category rail look: a small rounded thumbnail with the name underneath,
 * laid out in one horizontal row (scrollable on small screens, wrapping on
 * large ones). The active ring sits on the thumbnail itself so it hugs the
 * tile instead of stretching across the whole button.
 */

const thumbClass =
  "relative size-14 shrink-0 overflow-hidden rounded-xl border border-border bg-surface-muted transition duration-200 sm:size-16";

const activeRing =
  " ring-2 ring-sky-500 ring-offset-2 ring-offset-background dark:ring-sky-400 dark:ring-offset-card";

const labelClass =
  "mt-2 block w-full truncate text-center text-[11px] leading-tight font-medium text-muted-foreground transition-colors group-hover:text-foreground";

function Thumb({
  category,
  active = false,
}: {
  category: Category;
  active?: boolean;
}) {
  const ring = active ? activeRing : "";

  if (category.image) {
    return (
      <div className={`${thumbClass}${ring}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={category.image}
          alt=""
          loading="lazy"
          className="size-full object-cover transition duration-300 group-hover:scale-[1.06]"
        />
      </div>
    );
  }

  return (
    <div
      className={`${thumbClass}${ring} grid place-items-center bg-gradient-to-br from-sky-500/20 to-cyan-500/10 dark:from-sky-600/25 dark:to-teal-500/10`}
    >
      <span className="text-sm font-semibold text-sky-700 uppercase dark:text-sky-300">
        {category.name.slice(0, 2)}
      </span>
    </div>
  );
}

export function CategoryTile({ category }: { category: Category }) {
  return (
    <Link
      href={`/categories/${category.slug}`}
      aria-label={category.name}
      className="group w-20 min-w-0 shrink-0 snap-start focus-visible:outline-none sm:w-24"
    >
      <span className="mx-auto block w-fit rounded-xl transition duration-200 group-hover:-translate-y-0.5 group-focus-visible:ring-2 group-focus-visible:ring-sky-500 group-focus-visible:ring-offset-2 group-focus-visible:ring-offset-background dark:group-focus-visible:ring-sky-400">
        <Thumb category={category} />
      </span>
      <span className={labelClass}>{category.name}</span>
    </Link>
  );
}

export function CategoryFilterTile({
  category,
  active,
  onSelect,
}: {
  category: Category;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      aria-label={category.name}
      className="group w-20 min-w-0 shrink-0 snap-start text-start focus-visible:outline-none sm:w-24"
    >
      <span className="mx-auto block w-fit rounded-xl transition duration-200 group-hover:-translate-y-0.5">
        <Thumb category={category} active={active} />
      </span>
      <span className={active ? `${labelClass} !text-foreground` : labelClass}>
        {category.name}
      </span>
    </button>
  );
}

/** Icon tile for the non-category catalog filters ("All", "On sale"). */
export function CategoryActionTile({
  label,
  active,
  icon,
  onSelect,
}: {
  label: string;
  active: boolean;
  icon: React.ReactNode;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      aria-label={label}
      className="group w-20 min-w-0 shrink-0 snap-start focus-visible:outline-none sm:w-24"
    >
      <span className="mx-auto block w-fit rounded-xl transition duration-200 group-hover:-translate-y-0.5">
        <span
          className={`${thumbClass}${active ? activeRing : ""} grid place-items-center ${
            active
              ? "bg-sky-500/15 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300"
              : "text-muted-foreground"
          }`}
        >
          {icon}
        </span>
      </span>
      <span className={active ? `${labelClass} !text-foreground` : labelClass}>
        {label}
      </span>
    </button>
  );
}

export function CategoryRail({
  categories,
  className = "",
}: {
  categories: Category[];
  className?: string;
}) {
  return (
    <div
      className={`no-scrollbar -mx-1 flex snap-x gap-3 overflow-x-auto px-1 pb-1 sm:gap-4 lg:flex-wrap lg:overflow-visible ${className}`}
    >
      {categories.map((category) => (
        <CategoryTile key={category.id} category={category} />
      ))}
    </div>
  );
}

export function CategoryTileSkeleton() {
  return (
    <div className="w-20 shrink-0 animate-pulse sm:w-24">
      <div className="size-14 rounded-xl bg-muted-foreground/10 sm:size-16" />
      <div className="mt-2 h-3 w-3/4 rounded bg-muted-foreground/15" />
    </div>
  );
}

export function CategoryRailSkeleton({
  count = 8,
  className = "",
}: {
  count?: number;
  className?: string;
}) {
  return (
    <div
      className={`no-scrollbar -mx-1 flex snap-x gap-3 overflow-x-auto px-1 pb-1 sm:gap-4 lg:flex-wrap lg:overflow-visible ${className}`}
    >
      {Array.from({ length: count }).map((_, index) => (
        <CategoryTileSkeleton key={index} />
      ))}
    </div>
  );
}

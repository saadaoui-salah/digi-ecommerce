"use client";

/**
 * Loading skeletons for API-driven lists. Each skeleton mirrors the shape of
 * the real card or table so the layout does not jump when the data arrives.
 */

export function ProductCardSkeleton() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-border bg-card/60">
      <div className="aspect-16/9 bg-muted-foreground/10" />
      <div className="p-5">
        <div className="flex items-center justify-between gap-2">
          <div className="h-2.5 w-20 rounded bg-muted-foreground/20" />
          <div className="flex items-center gap-1.5">
            <div className="h-4 w-10 rounded-md bg-muted-foreground/15" />
            <div className="h-4 w-14 rounded-md bg-muted-foreground/15" />
          </div>
        </div>
        <div className="mt-3 h-5 w-3/5 rounded bg-muted-foreground/20" />
        <div className="mt-2 h-3 w-full rounded bg-muted-foreground/10" />
        <div className="mt-1.5 h-3 w-4/5 rounded bg-muted-foreground/10" />
        <div className="mt-auto flex items-end justify-between gap-4 pt-6">
          <div>
            <div className="h-2.5 w-10 rounded bg-muted-foreground/15" />
            <div className="mt-1.5 h-5 w-24 rounded bg-muted-foreground/20" />
          </div>
          <div className="h-9 w-24 rounded-lg bg-muted-foreground/15" />
        </div>
      </div>
    </div>
  );
}

export function ProductGridSkeleton({
  count = 6,
  className = "grid gap-4 sm:grid-cols-2 lg:grid-cols-3",
}: {
  count?: number;
  className?: string;
}) {
  return (
    <div className={className}>
      {Array.from({ length: count }).map((_, index) => (
        <ProductCardSkeleton key={index} />
      ))}
    </div>
  );
}

export function CategoryCardSkeleton() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-border bg-card/60">
      <div className="aspect-16/9 bg-muted-foreground/10" />
      <div className="flex items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="h-4 w-2/3 rounded bg-muted-foreground/20" />
          <div className="mt-1.5 h-3 w-1/3 rounded bg-muted-foreground/10" />
        </div>
        <div className="size-4 shrink-0 rounded bg-muted-foreground/15" />
      </div>
    </div>
  );
}

export function CategoryGridSkeleton({
  count = 8,
  className = "grid gap-4 sm:grid-cols-2 lg:grid-cols-4",
}: {
  count?: number;
  className?: string;
}) {
  return (
    <div className={className}>
      {Array.from({ length: count }).map((_, index) => (
        <CategoryCardSkeleton key={index} />
      ))}
    </div>
  );
}

/**
 * Skeleton for the wide data tables (orders, transactions, credits). It
 * reproduces the table shell — header strip plus rows of cells — so the
 * surrounding cards do not resize when the real rows arrive.
 */
export function TableSkeleton({
  columns = 4,
  rows = 5,
  className = "",
}: {
  columns?: number;
  rows?: number;
  className?: string;
}) {
  return (
    <div
      className={`overflow-hidden rounded-2xl border border-border bg-card ${className}`}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-muted/60">
              {Array.from({ length: columns }).map((_, index) => (
                <th key={index} className="px-5 py-3.5 text-start">
                  <span className="block h-2.5 w-16 animate-pulse rounded bg-muted-foreground/20" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <tr key={rowIndex} className="border-b border-border/60 last:border-0">
                {Array.from({ length: columns }).map((__, columnIndex) => (
                  <td key={columnIndex} className="px-5 py-4">
                    <span
                      className="block h-3.5 animate-pulse rounded bg-muted-foreground/10"
                      style={{
                        width: `${45 + ((rowIndex + columnIndex) % 4) * 12}%`,
                      }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ProductDetailSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="grid gap-8 lg:grid-cols-[1fr_380px]">
        <div>
          <div className="h-4 w-40 rounded bg-muted-foreground/10" />
          <div className="mt-4 h-9 w-3/4 rounded bg-muted-foreground/15" />
          <div className="mt-3 h-4 w-full rounded bg-muted-foreground/10" />
          <div className="mt-2 h-4 w-5/6 rounded bg-muted-foreground/10" />
          <div className="mt-8 aspect-16/9 w-full rounded-2xl bg-muted-foreground/10" />
          <div className="mt-3 flex gap-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-16 w-24 rounded-xl bg-muted-foreground/10"
              />
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <div className="h-5 w-2/3 rounded bg-muted-foreground/15" />
          <div className="h-4 w-1/2 rounded bg-muted-foreground/10" />
          <PackagePickerSkeleton />
          <div className="h-11 w-full rounded-lg bg-muted-foreground/15" />
        </div>
      </div>
    </div>
  );
}

/** Skeleton for the two package dropdowns on the product page. */
export function PackagePickerSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: 2 }).map((_, index) => (
        <div key={index}>
          <div className="h-2.5 w-24 rounded bg-muted-foreground/20" />
          <div className="mt-2 h-14 rounded-xl border border-border bg-card/60" />
        </div>
      ))}
    </div>
  );
}

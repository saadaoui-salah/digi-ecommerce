"use client";

import { useState } from "react";

/**
 * A small SVG bar chart.
 *
 * The bars are plain rectangles — no chart library — so the page stays light
 * and the colours follow the theme. Hovering a bar shows its value.
 */

export type BarDatum = {
  label: string;
  value: number;
  /** Right-aligned text, usually the amount the bar stands for. */
  meta?: string;
};

export function BarChart({
  data,
  formatValue,
  className = "",
}: {
  data: BarDatum[];
  formatValue: (value: number) => string;
  className?: string;
}) {
  const [hovered, setHovered] = useState<number | null>(null);

  if (data.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        No data yet.
      </p>
    );
  }

  const max = Math.max(...data.map((item) => item.value), 1);

  return (
    <div className={className}>
      <ul className="space-y-2.5">
        {data.map((item, index) => {
          const width = Math.max((item.value / max) * 100, 1.5);
          const isHovered = hovered === index;

          return (
            <li
              key={`${item.label}-${index}`}
              className="group relative"
              onMouseEnter={() => setHovered(index)}
              onMouseLeave={() => setHovered(null)}
            >
              <div className="flex items-baseline justify-between gap-3 text-xs">
                <span className="truncate font-medium text-foreground">
                  {item.label}
                </span>
                <span className="shrink-0 text-muted-foreground">
                  {item.meta ?? formatValue(item.value)}
                </span>
              </div>
              <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-surface-muted">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-500 to-cyan-400 transition-[width,opacity] duration-500"
                  style={{
                    width: `${width}%`,
                    opacity: hovered === null || isHovered ? 1 : 0.45,
                  }}
                />
              </div>
              {isHovered && (
                <span
                  className="pointer-events-none absolute -top-1 right-0 z-10 -translate-y-full rounded-lg border border-border bg-popover px-2 py-1 text-[11px] font-medium whitespace-nowrap text-popover-foreground shadow-lg"
                  role="tooltip"
                >
                  {formatValue(item.value)}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

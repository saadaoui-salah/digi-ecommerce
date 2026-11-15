"use client";

import { useId, useState } from "react";

/**
 * A small SVG line chart with an area fill.
 *
 * Like the bar chart it is hand-drawn SVG — no chart library — so it follows
 * the theme and stays light. Hovering a point shows its value.
 */

export type LinePoint = {
  label: string;
  value: number;
};

export function LineChart({
  points,
  formatValue,
  className = "",
  height = 220,
}: {
  points: LinePoint[];
  formatValue: (value: number) => string;
  className?: string;
  height?: number;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const gradientId = useId();

  if (points.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        No data yet.
      </p>
    );
  }

  const width = 640;
  const padding = { top: 16, right: 12, bottom: 28, left: 52 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const values = points.map((point) => point.value);
  const max = Math.max(...values, 0);
  const min = Math.min(...values, 0);
  const span = max - min || 1;

  const x = (index: number) =>
    padding.left +
    (points.length === 1 ? innerWidth / 2 : (index / (points.length - 1)) * innerWidth);
  const y = (value: number) =>
    padding.top + innerHeight - ((value - min) / span) * innerHeight;

  const line = points
    .map((point, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(point.value)}`)
    .join(" ");
  const area = `${line} L${x(points.length - 1)},${padding.top + innerHeight} L${x(0)},${padding.top + innerHeight} Z`;

  // A label every few points keeps the axis readable.
  const labelStep = Math.max(1, Math.ceil(points.length / 8));
  const labelIndexes = points
    .map((_, index) => index)
    .filter((index) => index % labelStep === 0);

  // The first and the last label lean away from the plot, so they never
  // land on the value axis.
  const anchorOf = (index: number) => {
    const position = labelIndexes.indexOf(index);
    if (position === 0) return "start";
    if (position === labelIndexes.length - 1) return "end";
    return "middle";
  };

  return (
    <div className={className}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-auto w-full overflow-visible"
        role="img"
        onMouseLeave={() => setHovered(null)}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-sky-500)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-sky-500)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines and the value axis */}
        {[0, 0.25, 0.5, 0.75, 1].map((step) => {
          const value = min + span * step;
          const lineY = y(value);
          return (
            <g key={step}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={lineY}
                y2={lineY}
                className="stroke-border"
                strokeWidth="1"
                strokeDasharray="3 4"
              />
              <text
                x={padding.left - 8}
                y={lineY + 3}
                textAnchor="end"
                className="fill-muted-foreground text-[9px]"
              >
                {formatValue(value)}
              </text>
            </g>
          );
        })}

        <path d={area} fill={`url(#${gradientId})`} />
        <path
          d={line}
          fill="none"
          className="stroke-sky-500"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {points.map((point, index) => (
          <g key={`${point.label}-${index}`}>
            <circle
              cx={x(index)}
              cy={y(point.value)}
              r={hovered === index ? 5 : 3}
              className="fill-sky-500 stroke-background"
              strokeWidth="2"
            />
            {/* A wide invisible target so the points are easy to hover. */}
            <rect
              x={x(index) - 14}
              y={padding.top}
              width={28}
              height={innerHeight}
              fill="transparent"
              onMouseEnter={() => setHovered(index)}
            />
            {index % labelStep === 0 && (
              <text
                x={x(index)}
                y={height - 8}
                textAnchor={anchorOf(index)}
                className="fill-muted-foreground text-[9px]"
              >
                {point.label}
              </text>
            )}
            {hovered === index && (
              <text
                x={x(index)}
                y={y(point.value) - 12}
                textAnchor="middle"
                className="fill-foreground text-[10px] font-medium"
              >
                {formatValue(point.value)}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}

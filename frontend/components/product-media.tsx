"use client";

import { useState } from "react";
import { Play } from "lucide-react";

import type { ProductDetail } from "@/lib/api";

export function ProductMedia({ product }: { product: ProductDetail }) {
  const [selection, setSelection] = useState<{ id: number; index: number } | null>(
    null,
  );

  const gallery = product.images.length > 0
    ? product.images.map((img) => img.image)
    : product.image
      ? [product.image]
      : [];
  const hasVideo = Boolean(product.video);
  const count = gallery.length + (hasVideo ? 1 : 0);
  if (count === 0) return null;

  const index = selection?.id === product.id ? selection.index : 0;
  const videoIndex = hasVideo ? 0 : -1;

  return (
    <div className="mt-6">
      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        {hasVideo && index === videoIndex ? (
          <video
            key={product.id}
            controls
            preload="metadata"
            poster={gallery[0] ?? undefined}
            className="aspect-16/9 w-full bg-black object-cover"
          >
            <source src={product.video ?? ""} />
          </video>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={gallery[hasVideo ? index - 1 : index] ?? ""}
            alt={product.name}
            className="aspect-16/9 w-full object-cover"
          />
        )}
      </div>

      {count > 1 && (
        <div className="no-scrollbar mt-3 flex gap-2 overflow-x-auto pb-1">
          {hasVideo && (
            <button
              key="video"
              type="button"
              onClick={() => setSelection({ id: product.id, index: 0 })}
              aria-pressed={index === videoIndex}
              className="btn-animate relative h-16 w-24 shrink-0 cursor-pointer overflow-hidden rounded-xl border border-border bg-card transition-colors hover:border-foreground/25 aria-pressed:border-sky-500 aria-pressed:ring-1 aria-pressed:ring-sky-500/40"
            >
              {gallery[0] ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={gallery[0]}
                  alt=""
                  className="size-full object-cover opacity-50"
                />
              ) : (
                <span className="absolute inset-0 bg-gradient-to-br from-sky-500/30 to-cyan-500/20" />
              )}
              <span className="absolute inset-0 grid place-items-center bg-black/30 text-white">
                <Play className="size-4" />
              </span>
            </button>
          )}
          {gallery.map((src, i) => (
            <button
              key={src + i}
              type="button"
              onClick={() =>
                setSelection({ id: product.id, index: i + (hasVideo ? 1 : 0) })
              }
              aria-pressed={index === i + (hasVideo ? 1 : 0)}
              className="btn-animate h-16 w-24 shrink-0 cursor-pointer overflow-hidden rounded-xl border border-border bg-card transition-colors hover:border-foreground/25 aria-pressed:border-sky-500 aria-pressed:ring-1 aria-pressed:ring-sky-500/40"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt="" className="size-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { Check } from "lucide-react";

/** Small animated tick used when an action finished successfully. */
export function SuccessCheck({ className = "" }: { className?: string }) {
  return (
    <span
      className={`animate-success-pop grid size-6 shrink-0 place-items-center rounded-full bg-emerald-500 text-white ${className}`}
      aria-hidden="true"
    >
      <Check className="size-3.5" strokeWidth={3} />
    </span>
  );
}

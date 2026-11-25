"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

export type StyledOption = {
  value: string;
  label: string;
};

/**
 * The original dropdown styling (rounded trigger, animated chevron and menu),
 * without the search field. The open state is a hidden checkbox so the
 * show/hide animation stays CSS-only.
 */
export function StyledSelect({
  label,
  value,
  options,
  onChange,
  className = "",
}: {
  label: string;
  value: string;
  options: StyledOption[];
  onChange: (value: string) => void;
  className?: string;
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => {
    const box = document.getElementById(id) as HTMLInputElement | null;
    if (box) box.checked = false;
    setOpen(false);
  }, [id]);

  useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node | null;
      if (target && rootRef.current?.contains(target)) return;
      close();
    }
    document.addEventListener("pointerdown", handlePointerDown, true);
    return () =>
      document.removeEventListener("pointerdown", handlePointerDown, true);
  }, [open, close]);

  const selected = options.find((option) => option.value === value);

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <input
        id={id}
        type="checkbox"
        className="search-peer sr-only"
        checked={open}
        onChange={(event) => setOpen(event.target.checked)}
      />

      <label
        htmlFor={id}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        onKeyDown={(event) => {
          if (event.key === "Escape" && open) {
            event.preventDefault();
            close();
          }
        }}
        className="search-trigger flex min-h-12 w-full cursor-pointer items-center justify-between gap-2 rounded-xl border border-border bg-card px-4 py-3 text-start"
      >
        <span className="block truncate text-sm font-medium text-foreground">
          {selected?.label ?? options[0]?.label}
        </span>
        <ChevronDown className="search-chevron size-4 shrink-0 text-muted-foreground" />
      </label>

      <div
        role="listbox"
        aria-label={label}
        className="search-menu absolute z-50 mt-2 w-full min-w-44 overflow-hidden rounded-xl border border-border bg-popover p-2 text-popover-foreground shadow-2xl shadow-foreground/10"
      >
        <div className="flex max-h-64 flex-col gap-1 overflow-y-auto">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              role="option"
              aria-selected={option.value === value}
              onClick={() => {
                onChange(option.value);
                close();
              }}
              className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-3 text-start transition-colors ${
                option.value === value
                  ? "bg-surface-muted font-medium text-foreground"
                  : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
              }`}
            >
              <span className="block truncate text-sm">{option.label}</span>
              {option.value === value && (
                <Check className="size-4 shrink-0 text-sky-600 dark:text-sky-300" />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

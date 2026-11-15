"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "lucide-react";

export type SearchSelectOption = {
  value: string;
  label: string;
  /** Short line under the label — the region or the price. */
  hint?: string;
  /** Right-aligned text, usually the price. */
  meta?: string;
  disabled?: boolean;
};

/**
 * A dropdown with a search box on top of the list.
 *
 * The open/close state lives in a hidden checkbox (like the language
 * switcher), so the show/hide and the animation are pure CSS. JavaScript only
 * performs the real work: filtering the list while the user types and
 * unchecking the box once an option has been picked.
 */
export function SearchSelect({
  label,
  placeholder,
  searchPlaceholder,
  emptyText,
  value,
  options,
  searchOptions,
  onChange,
  disabled = false,
  className = "",
}: {
  label: string;
  placeholder: string;
  searchPlaceholder: string;
  emptyText: string;
  value: string | null;
  options: SearchSelectOption[];
  /**
   * Extra options that only show up while the user is searching. It lets a
   * narrow list stay narrow, yet still find every row of the data.
   */
  searchOptions?: SearchSelectOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string;
}) {
  const id = useId();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return options;
    const pool = searchOptions ? [...options, ...searchOptions] : options;
    const seen = new Set<string>();
    return pool.filter((option) => {
      if (seen.has(option.value)) return false;
      seen.add(option.value);
      return (
        option.label.toLowerCase().includes(needle) ||
        (option.hint ?? "").toLowerCase().includes(needle)
      );
    });
  }, [options, searchOptions, query]);

  const selected =
    options.find((option) => option.value === value) ??
    (searchOptions ?? []).find((option) => option.value === value) ??
    null;

  // Keep the checkbox and the React state in step, and move the focus into
  // the search box as soon as the list opens.
  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => searchRef.current?.focus(), 30);
    return () => clearTimeout(timer);
  }, [open]);

  const close = useCallback(() => {
    const box = document.getElementById(id) as HTMLInputElement | null;
    if (box) box.checked = false;
    setOpen(false);
    setQuery("");
  }, [id]);

  // A click anywhere outside the dropdown closes it.
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

  function pick(next: string) {
    onChange(next);
    close();
  }

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <input
        id={id}
        type="checkbox"
        className="search-peer sr-only"
        disabled={disabled}
        onChange={(event) => setOpen(event.target.checked)}
      />

      <span className="mb-1.5 block text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
        {label}
      </span>

      <label
        htmlFor={id}
        aria-haspopup="listbox"
        aria-expanded={open}
        onKeyDown={(event) => {
          if (event.key === "Escape" && open) {
            event.preventDefault();
            close();
          }
        }}
        className={`search-trigger flex w-full items-center justify-between gap-2 rounded-xl border border-border bg-card px-4 py-3 text-start ${
          disabled ? "cursor-not-allowed opacity-55" : "cursor-pointer"
        }`}
      >
        <span className="min-w-0">
          <span className="block truncate text-sm font-medium text-foreground">
            {selected ? selected.label : placeholder}
          </span>
          {selected?.hint && (
            <span className="mt-0.5 block truncate text-xs text-muted-foreground">
              {selected.hint}
            </span>
          )}
        </span>
        {selected?.meta && (
          <span className="shrink-0 text-sm font-semibold text-foreground">
            {selected.meta}
          </span>
        )}
        <ChevronDown className="search-chevron size-4 shrink-0 text-muted-foreground" />
      </label>

      <div
        role="listbox"
        aria-label={label}
        className="search-menu absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-border bg-popover p-2 text-popover-foreground shadow-2xl shadow-foreground/10"
      >
        <div className="relative mb-1.5">
          <Search className="pointer-events-none absolute start-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            ref={searchRef}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Escape") close();
            }}
            placeholder={searchPlaceholder}
            aria-label={searchPlaceholder}
            autoComplete="off"
            className="h-9 w-full rounded-lg border border-border bg-background ps-9 pe-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-sky-500 focus:outline-none"
          />
        </div>

        <div className="flex max-h-64 flex-col gap-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              {emptyText}
            </p>
          ) : (
            filtered.map((option) => (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={option.value === value}
                disabled={option.disabled}
                onClick={() => pick(option.value)}
                className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-start transition-colors ${
                  option.disabled
                    ? "cursor-not-allowed text-muted-foreground/70"
                    : option.value === value
                      ? "bg-surface-muted text-foreground"
                      : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">
                    {option.label}
                  </span>
                  {option.hint && (
                    <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                      {option.hint}
                    </span>
                  )}
                </span>
                {option.meta && (
                  <span className="shrink-0 text-sm font-semibold">
                    {option.meta}
                  </span>
                )}
                {option.value === value && (
                  <Check className="size-3.5 shrink-0 text-sky-600 dark:text-sky-300" />
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

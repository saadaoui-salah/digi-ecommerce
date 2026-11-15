"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

export type SelectMenuOption = {
  value: string;
  label: string;
};

/**
 * A small dropdown, styled like the language switcher.
 *
 * The open/close state lives in a hidden checkbox (like the language switcher
 * and the notification bell), so the show/hide and the animation are pure CSS.
 * JavaScript only performs the real work: picking an option and closing the
 * list again.
 */
export function SelectMenu({
  label,
  value,
  options,
  onChange,
  className = "",
  align = "start",
}: {
  /** The name of the list, read out by the screen readers. */
  label: string;
  value: string | null;
  options: SelectMenuOption[];
  onChange: (value: string) => void;
  className?: string;
  /** Which side the list opens on. */
  align?: "start" | "end";
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const selected = options.find((option) => option.value === value) ?? null;

  const close = useCallback(() => {
    const box = document.getElementById(id) as HTMLInputElement | null;
    if (box) box.checked = false;
    setOpen(false);
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
        className="dropdown-peer sr-only"
        onChange={(event) => setOpen(event.target.checked)}
      />

      <label
        htmlFor={id}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        title={label}
        onKeyDown={(event) => {
          if (event.key === "Escape" && open) {
            event.preventDefault();
            close();
          }
        }}
        className="dropdown-trigger btn-animate flex h-9 cursor-pointer items-center gap-2 rounded-lg border border-border bg-card/60 px-3 text-sm text-foreground outline-none hover:border-foreground/20 focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        <span className="min-w-0 truncate">{selected?.label ?? label}</span>
        <ChevronDown className="dropdown-chevron size-3.5 shrink-0 text-muted-foreground" />
      </label>

      <div
        role="listbox"
        aria-label={label}
        className={`dropdown-menu absolute top-full z-50 mt-2 w-48 space-y-1 rounded-xl border border-border bg-popover p-2 text-popover-foreground shadow-2xl shadow-foreground/10 ${
          align === "end" ? "end-0" : "start-0"
        }`}
      >
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="option"
            aria-selected={option.value === value}
            onClick={() => pick(option.value)}
            className={`flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-colors ${
              option.value === value
                ? "bg-surface-muted text-foreground"
                : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
            }`}
          >
            <span className="flex-1 text-start">{option.label}</span>
            {option.value === value && (
              <Check className="size-3.5 shrink-0 text-sky-600 dark:text-sky-300" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

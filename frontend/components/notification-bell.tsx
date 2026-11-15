"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Bell, CheckCheck } from "lucide-react";

import { useToast } from "@/components/toast";
import { useSession } from "@/components/use-session";
import { api, type Notification, type Paginated } from "@/lib/api";
import { formatDate } from "@/lib/datetime";
import { useI18n } from "@/lib/i18n";

const POLL_MS = 20000;

/**
 * Notification dropdown driven entirely by CSS: the hidden `.notification-peer`
 * checkbox is toggled by its <label>, and the sibling selectors in
 * globals.css open and close the panel with a fade. JavaScript only performs
 * the real action — marking the notifications as read — and unchecks the box
 * when the click lands outside of the panel or on Escape.
 */
export function NotificationBell() {
  const { t, locale } = useI18n();
  const { user } = useSession();
  const { notify } = useToast();
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const seen = useRef<Set<number>>(new Set());
  const firstLoad = useRef(true);
  const root = useRef<HTMLDivElement>(null);
  const id = useId();

  const load = useCallback(async () => {
    try {
      const res = await api<Paginated<Notification>>("/auth/notifications/");
      const results = res.results ?? [];

      if (!firstLoad.current) {
        const fresh = results.filter((item) => !seen.current.has(item.id));
        if (fresh.length > 0) {
          notify(fresh[0].title, "info");
        }
      }
      firstLoad.current = false;

      results.forEach((item) => seen.current.add(item.id));
      setItems(results);
      setUnread(results.filter((item) => !item.is_read).length);
    } catch {
      // Notifications are optional — keep the page working without them.
    }
  }, [notify]);

  useEffect(() => {
    if (!user) return;
    // Deferred so the first load happens outside of the effect body.
    const kickoff = setTimeout(load, 0);
    const timer = setInterval(load, POLL_MS);
    return () => {
      clearTimeout(kickoff);
      clearInterval(timer);
    };
  }, [user, load]);

  // The checkbox is the open state, so JavaScript only has to uncheck it.
  useEffect(() => {
    function handleClick(event: MouseEvent) {
      const box = document.getElementById(id) as HTMLInputElement | null;
      if (!box?.checked) return;
      if (root.current?.contains(event.target as Node)) return;
      box.checked = false;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      const box = document.getElementById(id) as HTMLInputElement | null;
      if (box?.checked) box.checked = false;
    }

    document.addEventListener("click", handleClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("click", handleClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [id]);

  const markAllRead = useCallback(async () => {
    setUnread(0);
    setItems((current) => current.map((item) => ({ ...item, is_read: true })));
    try {
      await api("/auth/notifications/", { method: "POST", body: JSON.stringify({}) });
    } catch {
      // Keep the optimistic state even if the request fails.
    }
  }, []);

  if (!user) return null;

  return (
    <div className="relative" ref={root}>
      {/* Hidden toggle: the panel and its animation are pure CSS. */}
      <input
        id={id}
        type="checkbox"
        className="notification-peer sr-only"
        aria-label={t("notifications.title")}
        onChange={(event) => {
          // Opening the panel is the moment the notifications are read.
          if (event.target.checked && unread > 0) markAllRead();
        }}
      />

      <label
        htmlFor={id}
        title={t("notifications.title")}
        className="btn-animate relative grid size-9 cursor-pointer place-items-center rounded-lg border border-border bg-card/60 text-muted-foreground outline-none hover:border-foreground/20 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        <Bell className="size-4" />
        {unread > 0 && (
          <span className="absolute -top-1 -end-1 grid min-w-4 place-items-center rounded-full bg-primary px-1 text-[10px] font-semibold leading-4 text-primary-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
        <span className="sr-only">{t("notifications.title")}</span>
      </label>

      <div className="notification-menu absolute end-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl shadow-foreground/10">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <p className="text-sm font-medium">{t("notifications.title")}</p>
          <button
            type="button"
            onClick={markAllRead}
            className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <CheckCheck className="size-3.5" />
            {t("notifications.markAllRead")}
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto">
          {items.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              {t("notifications.empty")}
            </p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className={`border-b border-border/60 px-4 py-3 last:border-0 ${
                  item.is_read ? "" : "bg-sky-500/5"
                }`}
              >
                <p className="text-sm font-medium text-foreground">
                  {item.title}
                </p>
                {item.body && (
                  <p className="mt-0.5 text-xs leading-5 text-muted-foreground">
                    {item.body}
                  </p>
                )}
                <p className="mt-1 text-[11px] text-muted-foreground/80">
                  {formatDate(item.created_at, locale)}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

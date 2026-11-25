"use client";

import type { ReactNode } from "react";
import { Clock, Loader2, RefreshCw } from "lucide-react";

import { LockedPanel } from "@/components/package-groups";
import { Button } from "@/components/ui/button";
import { useSession } from "@/components/use-session";
import type { User } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

/** The WhatsApp brand mark, which lucide-react does not ship. */
function WhatsAppIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2Zm0 18.16h-.01a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.23 8.23 0 0 1-1.26-4.39c0-4.55 3.7-8.25 8.25-8.25 2.2 0 4.28.86 5.84 2.42a8.2 8.2 0 0 1 2.41 5.83c0 4.55-3.7 8.25-8.26 8.25Zm4.52-6.17c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.12-.16.25-.64.81-.79.97-.14.16-.29.18-.54.06-.25-.13-1.04-.38-1.98-1.22a7.43 7.43 0 0 1-1.37-1.7c-.14-.25-.01-.38.11-.5.11-.11.25-.29.37-.43.13-.14.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.42-.56-.43h-.48c-.17 0-.43.06-.66.31-.23.25-.87.85-.87 2.07s.89 2.4 1.02 2.56c.12.17 1.76 2.69 4.26 3.77.6.26 1.06.41 1.43.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.08.15-1.18-.06-.1-.23-.16-.48-.28Z" />
    </svg>
  );
}

/**
 * Shown to a customer whose account still waits for an admin approval.
 */
export function PendingApproval() {
  const { t } = useI18n();
  const { user, refresh, signOut, signingOut } = useSession();

  return (
    <div className="rounded-2xl border border-border bg-card px-5 py-12 text-center sm:px-10">
      <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-300">
        <Clock className="size-6" />
      </span>

      <h2 className="mt-6 text-xl font-semibold tracking-tight text-foreground">
        {t("approval.title")}
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        {t("approval.copy")}
      </p>

      {user?.email && (
        <p className="mt-4 text-sm font-medium text-foreground">{user.email}</p>
      )}

      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <a
          href="https://wa.me/213794909201"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-animate inline-flex h-10 items-center gap-2 rounded-lg bg-green-600 px-4 text-sm font-semibold text-white hover:bg-green-700"
        >
          <WhatsAppIcon className="size-4" />
          {t("approval.whatsapp")}
        </a>
        <Button
          type="button"
          onClick={() => refresh()}
          className="btn-animate inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
        >
          <RefreshCw className="size-4" />
          {t("approval.checkAgain")}
        </Button>
        <Button
          type="button"
          onClick={() => signOut()}
          disabled={signingOut}
          variant="outline"
          className="btn-animate inline-flex h-10 items-center gap-2 rounded-lg px-4 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-surface-muted disabled:opacity-60"
        >
          {signingOut && <Loader2 className="size-4 animate-spin" />}
          {signingOut ? t("common.signingOut") : t("common.signOut")}
        </Button>
      </div>

      <p className="mt-4 text-sm text-muted-foreground">
        {t("approval.whatsappNumberLabel")}{" "}
        <a
          href="https://wa.me/213794909201"
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-foreground underline decoration-muted-foreground/50 underline-offset-4 hover:decoration-foreground"
        >
          +213 794 90 92 01
        </a>
      </p>
    </div>
  );
}

/**
 * Wraps the signed-in area of a page: signed-out visitors get the members
 * panel, customers waiting for approval get the review notice, everyone else
 * sees the page. The child receives the signed-in user.
 */
export function AccountGate({
  children,
  loading = null,
}: {
  children: (user: User) => ReactNode;
  loading?: ReactNode;
}) {
  const { user, checkingSession } = useSession();

  if (checkingSession) return <>{loading}</>;
  if (!user) return <LockedPanel />;
  if (!user.is_approved) return <PendingApproval />;

  return <>{children(user)}</>;
}

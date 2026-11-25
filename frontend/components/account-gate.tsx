"use client";

import type { ReactNode } from "react";
import { Clock, Loader2, RefreshCw } from "lucide-react";

import { LockedPanel } from "@/components/package-groups";
import { Button } from "@/components/ui/button";
import { useSession } from "@/components/use-session";
import type { User } from "@/lib/api";
import { WhatsAppIcon } from "@/components/whatsapp-icon";
import { useI18n } from "@/lib/i18n";

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

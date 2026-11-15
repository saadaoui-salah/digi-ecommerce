"use client";

import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";

import { useToast } from "@/components/toast";
import { copyText } from "@/lib/clipboard";
import { useI18n } from "@/lib/i18n";

/**
 * Small copy button with inline feedback: the icon turns into a tick and an
 * optional "Copied" label appears next to it.
 */
export function CopyButton({
  value,
  showLabel = false,
  className = "",
}: {
  value: string;
  showLabel?: boolean;
  className?: string;
}) {
  const { t } = useI18n();
  const { notify } = useToast();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(timer);
  }, [copied]);

  async function handleCopy() {
    if (!value) return;
    const ok = await copyText(value);
    if (ok) {
      setCopied(true);
      notify(t("common.copied"), "success");
    } else {
      notify(t("common.copyFailed"), "error");
    }
  }

  return (
    <span className="inline-flex items-center gap-1.5">
      <button
        type="button"
        onClick={handleCopy}
        disabled={!value}
        title={t("common.copy")}
        aria-label={t("common.copy")}
        className={`btn-animate grid size-7 shrink-0 cursor-pointer place-items-center rounded-md border border-border text-muted-foreground hover:border-foreground/25 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40 ${className}`}
      >
        {copied ? (
          <Check className="size-3.5 text-emerald-600 dark:text-emerald-400" />
        ) : (
          <Copy className="size-3.5" />
        )}
      </button>
      {showLabel && copied && (
        <span className="animate-success-pop text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
          {t("common.copied")}
        </span>
      )}
    </span>
  );
}

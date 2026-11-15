"use client";

import { AlertCircle } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  locales,
  messageFor,
  type Locale,
  type MessageKey,
} from "@/lib/i18n";

const invalidFieldClass =
  "[&:not(:placeholder-shown):invalid]:border-red-500 [&:not(:placeholder-shown):invalid]:focus-visible:border-red-500 [&:not(:placeholder-shown):invalid]:focus-visible:ring-red-500/20";

const errorLanguageClass: Record<Locale, string> = {
  en: "[html[lang=en]_&]:inline",
  fr: "[html[lang=fr]_&]:inline",
  ar: "[html[lang=ar]_&]:inline",
};

/**
 * Text field whose invalid state is pure CSS: the browser's own validation
 * (required / pattern / minLength / type) drives the red border and the
 * translated inline message, so no JavaScript is needed for field state.
 *
 * `serverErrorKey` shows an additional translated message for errors that
 * only the API can detect (duplicate email, wrong current password, …).
 */
export function FormField({
  label,
  id,
  name,
  errorKey,
  showInvalid,
  serverErrorKey,
  className = "",
  ...props
}: {
  label: string;
  id: string;
  name?: string;
  errorKey?: MessageKey;
  showInvalid?: boolean;
  serverErrorKey?: MessageKey;
  className?: string;
} & React.ComponentProps<"input">) {
  const errorId = `${id}-error`;

  return (
    <div className="group space-y-1.5">
      <Label htmlFor={id} className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      <Input
        id={id}
        name={name ?? id}
        aria-invalid={serverErrorKey ? true : undefined}
        aria-describedby={errorId}
        {...props}
        className={`h-11 rounded-lg border-border bg-card px-3.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus-visible:border-sky-500/60 focus-visible:ring-sky-500/20${
          showInvalid ? ` ${invalidFieldClass}` : ""
        }${serverErrorKey ? " border-red-500" : ""} ${className}`}
      />
      {errorKey && (
        <p
          id={errorId}
          className="hidden items-start gap-1 text-xs leading-4 text-red-600 group-has-[input:not(:placeholder-shown):invalid]:flex dark:text-red-400"
        >
          <AlertCircle className="mt-px size-3 shrink-0" />
          <span>
            {locales.map((locale) => (
              <span
                key={locale}
                lang={locale}
                className={`hidden ${errorLanguageClass[locale]}`}
              >
                {messageFor(locale, errorKey)}
              </span>
            ))}
          </span>
        </p>
      )}
      {serverErrorKey && (
        <p
          id={`${errorId}-server`}
          role="alert"
          className="flex items-start gap-1 text-xs leading-4 text-red-600 dark:text-red-400"
        >
          <AlertCircle className="mt-px size-3 shrink-0" />
          <span>
            {locales.map((locale) => (
              <span
                key={locale}
                lang={locale}
                className={`hidden ${errorLanguageClass[locale]}`}
              >
                {messageFor(locale, serverErrorKey)}
              </span>
            ))}
          </span>
        </p>
      )}
    </div>
  );
}

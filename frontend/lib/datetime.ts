/**
 * Dates and times in the shop are always Algerian time (UTC+1, no daylight
 * saving). The browser may sit in another timezone, so every date is
 * formatted through `timeZone: "Africa/Algiers"` instead of the local one.
 */

export const TIME_ZONE = "Africa/Algiers";

/** The locale tags used for the three languages of the shop. */
export function dateLocale(locale: string): string {
  return locale === "en" ? "en-GB" : locale;
}

/** A date such as 12 Nov 2026, in Algerian time. */
export function formatDate(value: string | Date, locale = "en"): string {
  return new Date(value).toLocaleDateString(dateLocale(locale), {
    year: "numeric",
    month: "short",
    day: "2-digit",
    timeZone: TIME_ZONE,
  });
}

/** A long date such as 12 November 2026, in Algerian time. */
export function formatLongDate(value: string | Date, locale = "en"): string {
  return new Date(value).toLocaleDateString(dateLocale(locale), {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: TIME_ZONE,
  });
}

/** A date with the time, such as 12 Nov 2026, 14:05, in Algerian time. */
export function formatDateTime(value: string | Date, locale = "en"): string {
  return new Date(value).toLocaleString(dateLocale(locale), {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: TIME_ZONE,
  });
}

/**
 * The parts of a date in Algerian time, so a chart can label its buckets.
 * The date is read back as plain numbers to dodge the timezone shift that
 * `toISOString` would introduce.
 */
export function dateParts(value: string | Date): {
  year: number;
  month: number;
  day: number;
} {
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: TIME_ZONE,
  }).formatToParts(new Date(value));

  const read = (type: string) =>
    Number(parts.find((part) => part.type === type)?.value ?? "0");

  return { year: read("year"), month: read("month"), day: read("day") };
}

import type { Locale } from "@/lib/i18n";

export function Flag({
  locale,
  className = "",
}: {
  locale: Locale;
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block shrink-0 overflow-hidden rounded-[3px] ring-1 ring-black/10 ${className}`}
    >
      {locale === "en" ? (
        <svg viewBox="0 0 60 40" className="h-full w-full">
          <rect width="60" height="40" fill="#012169" />
          <path d="M0 0 60 40M60 0 0 40" stroke="#ffffff" strokeWidth="8" />
          <path d="M0 0 60 40M60 0 0 40" stroke="#c8102e" strokeWidth="3" />
          <path d="M30 0v40M0 20h60" stroke="#ffffff" strokeWidth="13" />
          <path d="M30 0v40M0 20h60" stroke="#c8102e" strokeWidth="7" />
        </svg>
      ) : locale === "fr" ? (
        <svg viewBox="0 0 60 40" className="h-full w-full">
          <rect width="20" height="40" fill="#002395" />
          <rect x="20" width="20" height="40" fill="#ffffff" />
          <rect x="40" width="20" height="40" fill="#ed2939" />
        </svg>
      ) : (
        <svg viewBox="0 0 60 40" className="h-full w-full">
          <rect width="30" height="40" fill="#006233" />
          <rect x="30" width="30" height="40" fill="#ffffff" />
          <circle cx="36" cy="20" r="9.5" fill="#d21034" />
          <circle cx="39.5" cy="20" r="8" fill="#ffffff" />
          <polygon
            points="45.4,16.6 46.4,18.8 48.8,19 47,20.6 47.5,22.9 45.4,21.7 43.3,22.9 43.8,20.6 42,19 44.4,18.8"
            fill="#d21034"
          />
        </svg>
      )}
    </span>
  );
}

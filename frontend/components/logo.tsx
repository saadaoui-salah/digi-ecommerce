import Link from "next/link";

export function Logo({
  href = "/",
  inverse = false,
}: {
  href?: string;
  inverse?: boolean;
}) {
  return (
    <Link href={href} dir="ltr" className="group inline-flex items-center gap-2.5">
      <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-blue-600 via-sky-500 to-cyan-400 shadow-lg shadow-sky-500/25 transition-transform duration-200 group-hover:scale-105 group-hover:shadow-sky-500/40">
        <span className="text-sm font-semibold text-white">D</span>
      </span>
      <span
        className={`text-lg font-semibold tracking-tight ${
          inverse ? "text-white" : "text-foreground"
        }`}
      >
        digi
        <span className={inverse ? "text-white/80" : "text-sky-600 dark:text-sky-400"}>
          .
        </span>
      </span>
    </Link>
  );
}

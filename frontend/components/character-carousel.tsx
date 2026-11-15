"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { useI18n } from "@/lib/i18n";

const characters = [
  {
    id: "kratos",
    name: "Kratos",
    game: "God of War",
    tagline: "home.kratosTagline",
    image: "/characters/kratos.webp",
    width: 674,
    height: 1170,
  },
  {
    id: "lara-croft",
    name: "Lara Croft",
    game: "Tomb Raider",
    tagline: "home.laraTagline",
    image: "/characters/lara-croft.webp",
    width: 829,
    height: 1226,
  },
  {
    id: "master-chief",
    name: "Master Chief",
    game: "Halo",
    tagline: "home.chiefTagline",
    image: "/characters/master-chief.webp",
    width: 956,
    height: 1598,
  },
] as const;

type Direction = "next" | "prev";
type Outgoing = { index: number; direction: Direction } | null;

const animationMs = 560;

function entersFromRight(direction: Direction, rtl: boolean) {
  return direction === "next" ? !rtl : rtl;
}

export function CharacterCarousel() {
  const { t, dir } = useI18n();
  const [index, setIndex] = useState(0);
  const [outgoing, setOutgoing] = useState<Outgoing>(null);
  const timer = useRef<number | null>(null);

  const clearTimer = useCallback(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearTimer();
  }, [clearTimer]);

  const startTransition = useCallback(
    (next: number, direction: Direction) => {
      clearTimer();
      setOutgoing({ index, direction });
      setIndex(next);
      timer.current = window.setTimeout(() => {
        setOutgoing(null);
        timer.current = null;
      }, animationMs);
    },
    [clearTimer, index],
  );

  function go(direction: Direction) {
    const next =
      (index + (direction === "next" ? 1 : -1) + characters.length) %
      characters.length;
    startTransition(next, direction);
  }

  function goTo(next: number) {
    if (next === index) return;
    startTransition(next, next > index ? "next" : "prev");
  }

  const active = characters[index];
  const isRtl = dir === "rtl";
  const total = String(characters.length).padStart(2, "0");

  return (
    <section
      aria-roledescription="carousel"
      aria-label={t("home.charactersEyebrow")}
      className="relative mx-auto w-full max-w-[29rem]"
    >
      <div className="flex items-center justify-between gap-3 px-1">
        <span className="inline-flex items-center gap-2 text-[10px] font-medium tracking-[0.22em] text-muted-foreground uppercase">
          <span className="size-1.5 rounded-full bg-emerald-500" />
          {t("home.charactersEyebrow")}
        </span>
        <span
          dir="ltr"
          className="font-mono text-[11px] tracking-wider text-muted-foreground"
        >
          {String(index + 1).padStart(2, "0")}
          <span className="text-muted-foreground/50"> / {total}</span>
        </span>
      </div>

      <div className="relative mt-2 h-[22rem] sm:h-[27rem] lg:h-[33rem]">
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/2 h-[82%] w-[82%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-sky-500/15 blur-[90px] dark:bg-cyan-500/15" />
          <div className="absolute left-1/2 top-[62%] h-[46%] w-[46%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-teal-400/10 blur-3xl" />
          <div className="absolute left-1/2 top-1/2 aspect-square w-[84%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-foreground/[0.06]" />
          <div className="absolute left-1/2 top-1/2 aspect-square w-[62%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-foreground/[0.08]" />
          <div className="absolute bottom-4 left-1/2 h-8 w-[56%] -translate-x-1/2 rounded-[100%] bg-cyan-500/20 blur-2xl dark:bg-cyan-400/10" />
          <div className="absolute inset-0 grid place-items-center">
            <span className="font-mono text-[9rem] leading-none font-semibold tracking-tighter text-foreground/[0.05] sm:text-[11rem] lg:text-[13rem] dark:text-white/[0.055]">
              0{index + 1}
            </span>
          </div>
        </div>

        <div className="absolute inset-0 overflow-hidden">
          {characters.map((character, i) => {
            const isActive = i === index;
            const isOutgoing = outgoing?.index === i;
            const fromRight = outgoing
              ? entersFromRight(outgoing.direction, isRtl)
              : false;

            const animation = isActive
              ? outgoing
                ? fromRight
                  ? "animate-character-in-right"
                  : "animate-character-in-left"
                : ""
              : isOutgoing
                ? fromRight
                  ? "animate-character-out-left"
                  : "animate-character-out-right"
                : "pointer-events-none opacity-0";

            return (
              <div
                key={character.id}
                role="group"
                aria-roledescription="slide"
                aria-label={`${i + 1} / ${characters.length}`}
                aria-hidden={!isActive}
                className={`absolute inset-0 ${isActive ? "z-10" : "z-0"} ${animation}`}
              >
                <div className="animate-character-float flex h-full w-full items-end justify-center px-6 pb-1">
                  <Image
                    src={character.image}
                    alt={isActive ? character.name : ""}
                    width={character.width}
                    height={character.height}
                    preload={i === 0}
                    unoptimized
                    draggable={false}
                    sizes="(max-width: 1024px) 70vw, 32vw"
                    className="h-[94%] w-auto max-w-full object-contain object-bottom drop-shadow-[0_24px_40px_rgba(2,6,23,0.35)] select-none dark:drop-shadow-[0_24px_60px_rgba(0,0,0,0.85)]"
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="absolute start-1 top-1/2 z-20 -translate-y-1/2 sm:start-2">
          <button
            type="button"
            onClick={() => go("prev")}
            aria-label={t("home.previousCharacter")}
            title={t("home.previousCharacter")}
            className="btn-animate grid size-10 place-items-center rounded-lg border border-border bg-background/70 text-foreground shadow-sm backdrop-blur hover:border-foreground/25 hover:bg-card"
          >
            <ChevronLeft className="size-4 rtl:rotate-180" />
          </button>
        </div>

        <div className="absolute end-1 top-1/2 z-20 -translate-y-1/2 sm:end-2">
          <button
            type="button"
            onClick={() => go("next")}
            aria-label={t("home.nextCharacter")}
            title={t("home.nextCharacter")}
            className="btn-animate grid size-10 place-items-center rounded-lg border border-border bg-background/70 text-foreground shadow-sm backdrop-blur hover:border-foreground/25 hover:bg-card"
          >
            <ChevronRight className="size-4 rtl:rotate-180" />
          </button>
        </div>
      </div>

      <div className="mt-2 border-t border-border pt-5">
        <div className="flex items-end justify-between gap-4">
          <div key={active.id} className="animate-character-caption min-w-0">
            <p className="text-[10px] font-medium tracking-[0.2em] text-sky-700 uppercase dark:text-sky-300">
              <span dir="ltr">{active.game}</span>
            </p>
            <h3 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
              {active.name}
            </h3>
            <p className="mt-1.5 max-w-md text-sm leading-6 text-muted-foreground">
              {t(active.tagline)}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-1.5 pb-1.5">
            {characters.map((character, i) => (
              <button
                key={character.id}
                type="button"
                onClick={() => goTo(i)}
                aria-label={t("home.goToCharacter", { name: character.name })}
                aria-current={i === index ? "true" : undefined}
                className="group grid h-7 place-items-center px-0.5"
              >
                <span
                  className={`block h-1.5 rounded-full transition-all duration-300 ${
                    i === index
                      ? "w-7 bg-sky-500 dark:bg-sky-300"
                      : "w-1.5 bg-foreground/20 group-hover:bg-foreground/40"
                  }`}
                />
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

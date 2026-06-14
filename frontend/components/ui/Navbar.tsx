"use client";

import Link from "next/link";

interface NavbarProps {
  cta?: { label: string; href: string };
}

export function Navbar({ cta }: NavbarProps) {
  return (
    <header className="sticky top-0 z-40 w-full">
      <div className="glass-strong border-b border-white/10">
        <nav className="section-pad mx-auto flex max-w-9xl items-center justify-between py-4 md:py-5">
          <Link
            href="/"
            className="flex items-center gap-2.5 font-display text-2xl font-extrabold tracking-tight text-white md:text-3xl"
          >
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-600 text-lg md:h-11 md:w-11 md:text-xl">
              ✦
            </span>
            AI<span className="text-brand-400">Post</span>
          </Link>

          {cta && (
            <Link
              href={cta.href}
              className="rounded-xl bg-brand-600 px-5 py-2.5 text-base font-semibold text-white transition-colors hover:bg-brand-500 md:px-7 md:py-3 md:text-lg"
            >
              {cta.label}
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

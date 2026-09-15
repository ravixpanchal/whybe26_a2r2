import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const principles = [
  {
    number: "01",
    title: "Evidence first",
    body: "A validated ensemble reads the information you choose to share. No invented data, no hidden substitute model.",
  },
  {
    number: "02",
    title: "Plain language",
    body: "See the factors that shaped an assessment in language designed to inform, not overwhelm.",
  },
  {
    number: "03",
    title: "Your context matters",
    body: "Use the result as a starting point for reflection and preparation, never as an official lending decision.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen overflow-hidden">
      <header className="relative z-10 border-b border-[var(--line)] bg-[var(--cream)]/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">
          <Link href="/" className="flex items-center gap-3" aria-label="CrediLens home">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--brand)] text-sm font-bold text-white">
              C
            </span>
            <span className="text-sm font-bold tracking-[0.18em] text-[var(--brand-dark)]">
              CREDILENS
            </span>
          </Link>
          <nav className="hidden items-center gap-8 text-sm text-[var(--muted)] md:flex">
            <a href="#how-it-works" className="transition-colors hover:text-[var(--brand)]">
              How it works
            </a>
            <a href="#responsible-use" className="transition-colors hover:text-[var(--brand)]">
              Responsible use
            </a>
            <Link href="/assessment" className="font-semibold text-[var(--brand)]">
              Start assessment <span aria-hidden="true">↗</span>
            </Link>
          </nav>
          <Link href="/assessment" className="text-sm font-semibold text-[var(--brand)] md:hidden">
            Start <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </header>

      <main>
        <section className="relative bg-[var(--cream)]">
          <div className="grain absolute inset-0" aria-hidden="true" />
          <div className="relative mx-auto grid max-w-7xl gap-14 px-6 pb-24 pt-20 lg:grid-cols-[1.1fr_0.9fr] lg:px-10 lg:pb-32 lg:pt-28">
            <div className="max-w-3xl">
              <p className="mb-7 text-xs font-bold uppercase tracking-[0.28em] text-[var(--brand)]">
                Understand your financial picture
              </p>
              <h1 className="display-font max-w-2xl text-5xl leading-[0.98] tracking-[-0.04em] text-[var(--brand-dark)] sm:text-7xl">
                Clarity for your next financial step.
              </h1>
              <p className="mt-8 max-w-xl text-lg leading-8 text-[var(--muted)]">
                CrediLens turns your borrower profile into an educational,
                explainable assessment — so you can prepare with more context
                and less guesswork.
              </p>
              <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
                <Button href="/assessment">Start an assessment <span aria-hidden="true">→</span></Button>
                <a href="#how-it-works" className="px-2 text-sm font-semibold text-[var(--brand)]">
                  Learn how it works <span aria-hidden="true">↓</span>
                </a>
              </div>
              <p className="mt-8 max-w-md text-xs leading-5 text-[var(--muted)]">
                Educational tool only. CrediLens does not approve, reject, or
                guarantee access to credit.
              </p>
            </div>
            <div className="relative flex items-center justify-center lg:justify-end">
              <div className="absolute right-4 top-4 h-72 w-72 rounded-full bg-[#cfe7d8] blur-3xl" aria-hidden="true" />
              <Card className="relative w-full max-w-md rotate-1 p-7 shadow-[0_24px_70px_rgba(18,107,80,0.13)]">
                <div className="flex items-start justify-between border-b border-[var(--line)] pb-6">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--muted)]">Assessment preview</p>
                    <p className="mt-2 display-font text-2xl text-[var(--brand-dark)]">Your result, explained.</p>
                  </div>
                  <span className="rounded-full bg-[#e0f1e8] px-3 py-1 text-xs font-bold text-[var(--brand)]">Validated</span>
                </div>
                <div className="py-8">
                  <div className="flex items-end justify-between">
                    <span className="text-sm text-[var(--muted)]">Default-risk probability</span>
                    <span className="display-font text-5xl text-[var(--brand-dark)]">—</span>
                  </div>
                  <div className="mt-5 h-2 overflow-hidden rounded-full bg-[#e4eee9]">
                    <div className="h-full w-[58%] rounded-full bg-[var(--brand)]" />
                  </div>
                  <div className="mt-3 flex justify-between text-xs text-[var(--muted)]">
                    <span>Lower risk</span><span>Higher risk</span>
                  </div>
                </div>
                <div className="rounded-xl bg-[#f0f6f2] p-4 text-sm leading-6 text-[var(--muted)]">
                  See the strongest factors behind your result and a clear
                  reliability indicator.
                </div>
              </Card>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
          <div className="max-w-xl">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-[var(--brand)]">A considered approach</p>
            <h2 className="display-font mt-4 text-4xl tracking-[-0.03em] text-[var(--brand-dark)] sm:text-5xl">
              Insight without the black box.
            </h2>
          </div>
          <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--line)] md:grid-cols-3">
            {principles.map((principle) => (
              <div key={principle.number} className="bg-white p-8 lg:p-10">
                <p className="text-sm font-bold text-[var(--brand)]">{principle.number}</p>
                <h3 className="mt-16 text-xl font-bold text-[var(--brand-dark)]">{principle.title}</h3>
                <p className="mt-4 text-sm leading-6 text-[var(--muted)]">{principle.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="responsible-use" className="bg-[var(--brand-dark)] px-6 py-16 text-white lg:px-10">
          <div className="mx-auto flex max-w-7xl flex-col justify-between gap-8 md:flex-row md:items-end">
            <div className="max-w-2xl">
              <p className="text-xs font-bold uppercase tracking-[0.28em] text-[#9bd4bb]">Responsible by design</p>
              <h2 className="display-font mt-4 text-3xl tracking-[-0.02em] sm:text-4xl">
                A helpful signal, never the final word.
              </h2>
              <p className="mt-5 max-w-xl text-sm leading-7 text-[#c5ddd2]">
                Results are based on a machine-learning model and the
                information provided. They are not calibrated confidence,
                financial advice, or an official credit decision.
              </p>
            </div>
            <Button href="/assessment" variant="light">Explore your profile <span aria-hidden="true">→</span></Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-[var(--line)] bg-[var(--cream)] px-6 py-7 lg:px-10">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 text-xs leading-5 text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between">
          <span>© 2026 CrediLens AI</span>
          <span>For education and preparation only — not an official credit decision.</span>
        </div>
      </footer>
    </div>
  );
}

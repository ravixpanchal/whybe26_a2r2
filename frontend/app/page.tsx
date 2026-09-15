"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

type ModalKind = "why" | "how" | null;

const steps = [
  ["1. Share Your Information", "Enter relevant financial and profile details through the existing secure assessment flow."],
  ["2. Financial Analysis", "The validated assessment pipeline evaluates the information you provide without changing or supplementing it with invented data."],
  ["3. Alternative Assessment", "The model returns the existing assessment probability and risk category from the validated soft-voting ensemble."],
  ["4. Understand the Result", "Your report presents model-derived factors, data-quality observations, and practical recommendations in plain language."],
];

export default function Home() {
  const [modal, setModal] = useState<ModalKind>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!modal) return;
    closeButtonRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setModal(null);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [modal]);

  return (
    <main className="home-shell">
      <div className="home-pattern" aria-hidden="true" />
      <div className="home-frame">
        <header className="home-header">
          <Link href="/" className="home-brand" aria-label="CrediLens AI home">
            <span className="home-mark">C</span>
            <span>CrediLens AI</span>
          </Link>
          <Link href="/assessment" className="home-header-action home-header-action--highlight">Start Assessment <span aria-hidden="true">↗</span></Link>
        </header>

        <section className="home-hero">
          <div>
            <p className="home-eyebrow">Alternative financial insight</p>
            <h1>Understand Your<br /><span>Financial Profile</span></h1>
            <p className="home-lede">
              CrediLens AI provides an alternative, data-driven assessment based on your financial information and profile — explained clearly and responsibly.
            </p>
          </div>
          <div className="home-credit-card" aria-label="CrediLens AI context matters card">
            <div className="home-credit-lines" aria-hidden="true" />
            <div className="home-credit-top">
              <span className="home-credit-brand">CrediLens AI</span>
              <span className="home-credit-label">INSIGHTS FOR A<br />BRIGHTER TOMORROW</span>
            </div>
            <div className="home-credit-chip" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className="home-credit-copy">
              <span>Context matters.</span>
              <strong>Your information tells a fuller<br className="hidden sm:block" /> story.</strong>
            </div>
            <div className="home-credit-circles" aria-hidden="true"><span /><span /></div>
          </div>
        </section>

        <section className="home-tiles" aria-label="Learn about CrediLens AI">
          <button type="button" className="home-tile" onClick={() => setModal("why")}>
            <span className="home-tile-index">01</span>
            <span className="home-tile-title">Why This</span>
            <span className="home-tile-description">Traditional credit scores do not always reflect the complete financial picture. CrediLens AI explores additional financial indicators to create a broader assessment profile.</span>
            <span className="home-tile-arrow" aria-hidden="true">↗</span>
          </button>
          <button type="button" className="home-tile" onClick={() => setModal("how")}>
            <span className="home-tile-index">02</span>
            <span className="home-tile-title">How It Works</span>
            <span className="home-tile-description">See how your financial information is transformed into an understandable assessment.</span>
            <span className="home-tile-arrow" aria-hidden="true">↗</span>
          </button>
          <Link href="/assessment" className="home-tile home-tile-link">
            <span className="home-tile-index">03</span>
            <span className="home-tile-title">Take Assessment</span>
            <span className="home-tile-description">Complete a short financial assessment and receive your personalized CrediLens AI report.</span>
            <span className="home-tile-arrow" aria-hidden="true">↗</span>
          </Link>
        </section>

        <footer className="home-footer">
          <span>CrediLens AI · Built for clearer financial understanding</span>
          <span>Made with ♥ by AI &amp; DS Final Year Team (Prophetic Programmers)</span>
        </footer>
      </div>

      {modal && (
        <div className="home-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModal(null); }}>
          <section className="home-modal" role="dialog" aria-modal="true" aria-labelledby="home-modal-title">
            <div className="home-modal-header">
              <div>
                <p className="home-eyebrow">{modal === "how" ? "The CrediLens approach" : "A broader view"}</p>
                <h2 id="home-modal-title">{modal === "how" ? "How It Works" : "Why alternative assessment?"}</h2>
              </div>
              <button ref={closeButtonRef} type="button" className="home-modal-close" onClick={() => setModal(null)} aria-label="Close information panel">×</button>
            </div>
            <div className="home-modal-content">
              {modal === "how" ? (
                <>
                  {steps.map(([title, body]) => <article key={title} className="home-step"><span>{title.slice(0, 1)}</span><div><h3>{title}</h3><p>{body}</p></div></article>)}
                  <article className="home-important"><h3>Important Note</h3><p>CrediLens AI is an experimental financial assessment tool. It does not replace official credit bureaus, lenders, financial advisors, or formal loan underwriting. Results are informational and are not a financial guarantee.</p></article>
                </>
              ) : (
                <>
                  <p>Alternative credit assessment means looking beyond a single traditional score to understand more of a person&apos;s financial context.</p>
                  <p>Traditional credit scores may not capture every financial situation, especially when someone has limited formal credit history or a non-traditional income pattern.</p>
                  <p>Income stability, expenses, savings, obligations, and financial behavior can provide additional context for understanding a borrower profile.</p>
                  <div className="home-important"><h3>A responsible interpretation</h3><p>This result is an assessment insight, not an official credit score and not a guarantee of loan approval. It should be considered alongside a lender&apos;s complete evaluation.</p></div>
                </>
              )}
            </div>
          </section>
        </div>
      )}
    </main>
  );
}

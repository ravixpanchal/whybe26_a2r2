"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type LivingIdentityCardProps = {
  fullName: string;
  fieldValues: Record<string, unknown>;
  totalFactors: number;
};

function displayName(name: string) {
  return name.trim() ? name.trim().toUpperCase() : "YOUR NAME";
}

export function LivingIdentityCard({ fullName, fieldValues, totalFactors }: LivingIdentityCardProps) {
  const [flipped, setFlipped] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const cardContainerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const specularRef = useRef<HTMLDivElement>(null);
  const hologramRef = useRef<HTMLDivElement>(null);
  const tierBadgeRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLDivElement>(null);

  const completedFactors = useMemo(
    () => Object.values(fieldValues).filter((value) => value !== "" && value !== null && value !== undefined).length,
    [fieldValues],
  );
  const completeness = totalFactors > 0 ? Math.round((completedFactors / totalFactors) * 100) : 0;
  const monthlyIncome = useMemo(() => {
    const values = Array.from({ length: 6 }, (_, index) => Number(fieldValues[`income_month_${index + 1}`]));
    const available = values.filter((value) => Number.isFinite(value) && value > 0);
    return available.length ? available.reduce((sum, value) => sum + value, 0) / available.length : 0;
  }, [fieldValues]);
  const tier = monthlyIncome >= 190000 ? "CENTURION SOVEREIGN" : monthlyIncome >= 80000 ? "TIER 1 SOVEREIGN" : "TIER 3 FOUNDATION";

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const footer = footerRef.current;
    const tierBadge = tierBadgeRef.current;
    const pulse = (target: HTMLElement | null) => {
      if (!target || reducedMotion) return;
      target.classList.remove("sync-active");
      void target.offsetWidth;
      target.classList.add("sync-active");
    };
    pulse(footer);
    pulse(tierBadge);
  }, [fullName, tier, reducedMotion]);

  useEffect(() => {
    const container = cardContainerRef.current;
    const card = cardRef.current;
    const specular = specularRef.current;
    const hologram = hologramRef.current;
    if (!container || !card || !specular || !hologram || reducedMotion) return;

    const supportsHover = window.matchMedia("(hover: hover)").matches;
    if (!supportsHover) return;

    const reset = () => {
      card.style.transform = "rotateX(0deg) rotateY(0deg)";
      specular.style.setProperty("--spec-x", "40%");
      specular.style.setProperty("--spec-y", "25%");
      hologram.style.setProperty("--holo-angle", "135deg");
    };
    const move = (event: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const rotateX = ((y - rect.height / 2) / (rect.height / 2)) * -7;
      const rotateY = ((x - rect.width / 2) / (rect.width / 2)) * 8;
      specular.style.setProperty("--spec-x", `${100 - (x / rect.width) * 100}%`);
      specular.style.setProperty("--spec-y", `${Math.max(10, Math.min(80, (100 - (y / rect.height) * 100) * 0.7))}%`);
      hologram.style.setProperty("--holo-angle", `${110 + (x / rect.width) * 80}deg`);
      hologram.style.backgroundPosition = `${(x / rect.width) * 100}% ${(y / rect.height) * 100}%`;
      card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    };
    container.addEventListener("mousemove", move);
    container.addEventListener("mouseleave", reset);
    return () => {
      container.removeEventListener("mousemove", move);
      container.removeEventListener("mouseleave", reset);
    };
  }, [reducedMotion]);

  const toggleFlip = () => setFlipped((current) => !current);
  const name = displayName(fullName);

  return (
    <aside className="living-card-rail" data-purpose="living-credit-card-companion">
      <div className="living-card-header">
        <span className="living-card-kicker"><span className="living-card-status" /> LIVING IDENTITY CARD</span>
        <button
          id="flipTriggerBtn"
          type="button"
          className="living-card-flip-button"
          title="Flip Card View"
          aria-pressed={flipped}
          onClick={(event) => { event.stopPropagation(); toggleFlip(); }}
        >
          ↺ <span>Flip Card</span>
        </button>
      </div>

      <div
        id="cardContainer"
        ref={cardContainerRef}
        className="perspective-enclave"
        role="button"
        tabIndex={0}
        aria-label="Flip living identity card"
        onClick={toggleFlip}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            toggleFlip();
          }
        }}
      >
        <div id="card3D" ref={cardRef} className="card-chassis">
          <div id="cardInner" className={`card-flip-mechanism card-bevel-composite${flipped ? " is-flipped" : ""}`}>
            <div className="card-surface lacquered-metal-stock card-stepped-lip">
              <div className="anisotropic-brush" />
              <div id="cardSpecular" ref={specularRef} className="specular-streak ambient-sheen-drift" />
              <div className="card-top-row">
                <div className="card-brand"><span className="card-monogram">CL</span><span className="embossed-crest-text">CREDILENS</span></div>
                <div id="tierBadgeWrapper" ref={tierBadgeRef} className="tier-badge"><span id="hologramPatch" ref={hologramRef} className="hologram-patch" /><span id="cardBadgeCategory">{tier}</span></div>
              </div>
              <div className="card-chip-row">
                <div className="emv-die-base"><div className="chip-groove-h" /><div className="chip-groove-v" /><div className="chip-groove-v chip-groove-v-right" /><div className="chip-specular-glint" /></div>
                <span className="contactless-glyph">)))</span>
              </div>
              <div className="card-number"><span className="embossed-dots">••••</span><span className="embossed-dots">••••</span><span className="embossed-dots">••••</span><span className="embossed-silver-digits">4827</span></div>
              <div id="cardFooterRow" ref={footerRef} className="card-footer-row">
                <div><span className="card-label">MEMBER IDENTIFIER</span><span id="cardNameDisplay" className="embossed-gold-text card-name">{name}</span></div>
                <div className="card-expiry"><span className="card-label">VALID THRU</span><span className="tnum">09/30</span></div>
              </div>
            </div>
            <div className="card-surface card-reverse lacquered-metal-stock card-stepped-lip">
              <div className="anisotropic-brush" />
              <div className="magnetic-stripe"><span>HIGH-DENSITY CRYPTO-ENCLAVE TRACK</span><span>SHA-256</span></div>
              <div className="signature-row"><div className="signature-strip guilloche-waves"><span id="cardSignatureName">{fullName.trim() || "Your Name"}</span></div><div className="cvv"><span>CVV</span><b>842</b></div></div>
              <div className="card-terms"><span>HASH: 0x8842...F9A</span><span>Decentralized Attestation</span><p>Continuous context weighting model v3.2. Zero hard credit inquiries performed.</p></div>
            </div>
          </div>
        </div>
      </div>

      <div className="card-telemetry">
        <div className="telemetry-heading"><span>PROFILE COMPLETENESS</span><span id="completenessScore">{completeness}% · {completedFactors} of {totalFactors} factors calibrated</span></div>
        <div className="instrument-recessed-channel"><div className="brushed-brass-gauge" style={{ width: `${completeness}%` }} /></div>
        <div className="trust-strip"><span>● Zero score impact</span><span>•</span><span>● SHA-256 Verified</span></div>
      </div>
    </aside>
  );
}

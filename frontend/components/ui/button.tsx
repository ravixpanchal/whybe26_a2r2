import Link from "next/link";
import type { ComponentPropsWithoutRef } from "react";

type ButtonProps = {
  href?: string;
  variant?: "primary" | "light" | "outline";
} & ComponentPropsWithoutRef<"button">;

const variants = {
  primary: "bg-[var(--brand)] text-white hover:bg-[var(--brand-dark)]",
  light: "bg-[#d9f0e4] text-[var(--brand-dark)] hover:bg-white",
  outline: "border border-[var(--line)] bg-white text-[var(--brand-dark)] hover:border-[var(--brand)]",
};

export function Button({ href, variant = "primary", className = "", ...props }: ButtonProps) {
  const classes = `inline-flex min-h-12 shrink-0 items-center justify-center gap-3 whitespace-nowrap rounded-full px-6 text-center text-sm font-bold transition-colors ${variants[variant]} ${className}`;
  if (href) return <Link href={href} className={classes}>{props.children}</Link>;
  return <button {...props} className={classes} />;
}

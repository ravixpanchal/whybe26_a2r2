import type { ReactNode } from "react";

export function Field({
  id,
  label,
  description,
  error,
  children,
}: {
  id: string;
  label: string;
  description?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-semibold text-[var(--brand-dark)]">
        {label}
      </label>
      {description && <p className="text-xs leading-5 text-[var(--muted)]">{description}</p>}
      {children}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-xs font-semibold text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}

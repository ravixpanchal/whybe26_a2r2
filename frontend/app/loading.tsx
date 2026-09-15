export default function Loading() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-6">
      <div className="w-full max-w-md space-y-4" aria-label="Loading">
        <div className="h-3 w-32 animate-pulse rounded bg-[#d8e4de]" />
        <div className="h-12 w-4/5 animate-pulse rounded bg-[#d8e4de]" />
        <div className="h-24 animate-pulse rounded-2xl bg-white shadow-sm" />
      </div>
    </main>
  );
}

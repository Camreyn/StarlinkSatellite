export function Loading({ label = 'Loading' }: { label?: string }) {
  return <div className="rounded border border-zinc-200 bg-white p-4 text-sm text-zinc-600">{label}…</div>;
}

export function ErrorMessage({ error }: { error: unknown }) {
  return (
    <div className="rounded border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
      {error instanceof Error ? error.message : 'Something went wrong'}
    </div>
  );
}

import { ShieldAlert } from 'lucide-react';

export function Disclaimer() {
  return (
    <section className="border-b border-zinc-200 bg-amber-50 text-amber-950">
      <div className="mx-auto flex max-w-7xl gap-3 px-4 py-3 text-sm sm:px-6 lg:px-8">
        <ShieldAlert className="mt-0.5 h-5 w-5 flex-none" aria-hidden="true" />
        <p>
          Public satellite-tracking data can usually show which satellite reentered and when. It generally does not
          provide a definitive public per-satellite internal reason for deorbit. This app distinguishes sourced facts
          from computed values and inferences.
        </p>
      </div>
    </section>
  );
}

import type { FactLabel, ReliabilityRating } from '../types/api';
import { humanize } from '../utils/format';

const factStyles: Record<FactLabel, string> = {
  FACT: 'border-emerald-700 bg-emerald-50 text-emerald-900',
  AGGREGATE_EXPLANATION: 'border-amber-700 bg-amber-50 text-amber-900',
  COMPUTED: 'border-sky-700 bg-sky-50 text-sky-900',
  INFERENCE: 'border-rose-700 bg-rose-50 text-rose-900',
};

const reliabilityStyles: Record<ReliabilityRating, string> = {
  PRIMARY_REGULATORY: 'border-zinc-700 bg-zinc-50 text-zinc-900',
  PRIMARY_OPERATOR: 'border-teal-700 bg-teal-50 text-teal-900',
  OFFICIAL_CATALOG: 'border-cyan-700 bg-cyan-50 text-cyan-900',
  EXPERT_TRACKER: 'border-violet-700 bg-violet-50 text-violet-900',
  INDUSTRY_MEDIA: 'border-orange-700 bg-orange-50 text-orange-900',
  USER_MANUAL_NOTE: 'border-stone-700 bg-stone-50 text-stone-900',
};

export function FactBadge({ value }: { value: FactLabel }) {
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${factStyles[value]}`}>
      {humanize(value)}
    </span>
  );
}

export function ReliabilityBadge({ value }: { value: ReliabilityRating }) {
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${reliabilityStyles[value]}`}
    >
      {humanize(value)}
    </span>
  );
}

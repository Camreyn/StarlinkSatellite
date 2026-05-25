import { RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import { SectionHeader } from '../components/Layout';
import { ErrorMessage, Loading } from '../components/Loading';
import type { DashboardSummary } from '../types/api';
import { formatDate, formatNumber } from '../utils/format';

function Stat({ label, value }: { label: string; value?: number | string | null }) {
  return (
    <div className="rounded border border-zinc-200 bg-white p-4">
      <div className="text-sm text-zinc-600">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value ?? '—'}</div>
    </div>
  );
}

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .dashboard()
      .then(setSummary)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading label="Loading dashboard" />;
  if (error) return <ErrorMessage error={error} />;
  if (!summary) return null;

  const chart = [
    { label: 'Active', count: summary.active_count },
    { label: 'Decayed', count: summary.decayed_reentered_count },
    { label: 'Post election', count: summary.decayed_after_2024_11_05_count },
    { label: 'Dec-May period', count: summary.decayed_dec_2024_through_may_2025_count },
  ];

  return (
    <div>
      <SectionHeader
        title="Dashboard"
        actions={
          <button
            className="focus-ring inline-flex h-9 items-center gap-2 rounded bg-ink px-3 text-sm text-white"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" /> Refresh
          </button>
        }
      />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total Starlink satellites" value={formatNumber(summary.total_satellites)} />
        <Stat label="Active count" value={formatNumber(summary.active_count)} />
        <Stat label="Decayed/reentered count" value={formatNumber(summary.decayed_reentered_count)} />
        <Stat label="Decayed after Nov. 5, 2024" value={formatNumber(summary.decayed_after_2024_11_05_count)} />
        <Stat
          label="Dec. 1, 2024 through May 31, 2025"
          value={formatNumber(summary.decayed_dec_2024_through_may_2025_count)}
        />
        <Stat label="Missing decay reason" value={formatNumber(summary.satellites_missing_decay_reason)} />
        <Stat label="Inferred category only" value={formatNumber(summary.satellites_with_inferred_category_only)} />
        <Stat label="Last data refresh" value={formatDate(summary.last_data_refresh_time)} />
      </div>
      <section className="mt-6 rounded border border-zinc-200 bg-white p-4">
        <h3 className="mb-3 font-semibold">Lifecycle counts</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <XAxis dataKey="label" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

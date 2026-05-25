import { Filter, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { SectionHeader } from '../components/Layout';
import { ErrorMessage, Loading } from '../components/Loading';
import { SatelliteTable } from '../components/SatelliteTable';
import type { PaginatedSatellites } from '../types/api';

export function Satellites() {
  const [params, setParams] = useSearchParams({ page: '1', page_size: '50' });
  const [data, setData] = useState<PaginatedSatellites | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const query = useMemo(() => new URLSearchParams(params), [params]);

  useEffect(() => {
    setLoading(true);
    api
      .satellites(query)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [query]);

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.set('page', '1');
    setParams(next);
  }

  function setPostElection() {
    const next = new URLSearchParams(params);
    next.set('decayed_after', '2024-11-05');
    next.set('page', '1');
    setParams(next);
  }

  function setReportingPeriod() {
    const next = new URLSearchParams(params);
    next.set('decay_date_from', '2024-12-01');
    next.set('decay_date_to', '2025-05-31');
    next.set('page', '1');
    setParams(next);
  }

  return (
    <div>
      <SectionHeader title="Satellite Table" />
      <section className="mb-4 grid gap-3 rounded border border-zinc-200 bg-white p-4 lg:grid-cols-6">
        <label className="lg:col-span-2">
          <span className="mb-1 block text-sm font-medium text-zinc-700">Search</span>
          <span className="flex items-center gap-2 rounded border border-zinc-300 bg-white px-2">
            <Search className="h-4 w-4 text-zinc-500" aria-hidden="true" />
            <input
              className="h-9 w-full focus:outline-none"
              value={params.get('q') ?? ''}
              onChange={(event) => update('q', event.target.value)}
              placeholder="NORAD, name, designator"
            />
          </span>
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium text-zinc-700">Status</span>
          <input
            className="h-9 w-full rounded border border-zinc-300 px-2"
            value={params.get('status') ?? ''}
            onChange={(event) => update('status', event.target.value)}
          />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium text-zinc-700">Launch group</span>
          <input
            className="h-9 w-full rounded border border-zinc-300 px-2"
            value={params.get('launch_group') ?? ''}
            onChange={(event) => update('launch_group', event.target.value)}
          />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium text-zinc-700">Generation</span>
          <input
            className="h-9 w-full rounded border border-zinc-300 px-2"
            value={params.get('generation') ?? ''}
            onChange={(event) => update('generation', event.target.value)}
          />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium text-zinc-700">Fact label</span>
          <select
            className="h-9 w-full rounded border border-zinc-300 px-2"
            value={params.get('fact_vs_inference') ?? ''}
            onChange={(event) => update('fact_vs_inference', event.target.value)}
          >
            <option value="">Any</option>
            <option value="FACT">Fact</option>
            <option value="AGGREGATE_EXPLANATION">Aggregate explanation</option>
            <option value="COMPUTED">Computed</option>
            <option value="INFERENCE">Inference</option>
          </select>
        </label>
        <div className="flex flex-wrap gap-2 lg:col-span-6">
          <button className="focus-ring inline-flex h-9 items-center gap-2 rounded bg-orbit px-3 text-sm text-white" onClick={setPostElection}>
            <Filter className="h-4 w-4" aria-hidden="true" /> Decayed after Nov. 5, 2024
          </button>
          <button className="focus-ring inline-flex h-9 items-center gap-2 rounded bg-ink px-3 text-sm text-white" onClick={setReportingPeriod}>
            <Filter className="h-4 w-4" aria-hidden="true" /> Dec. 1, 2024 - May 31, 2025
          </button>
        </div>
      </section>
      {loading ? <Loading label="Loading satellites" /> : error ? <ErrorMessage error={error} /> : <SatelliteTable data={data?.items ?? []} />}
      {data ? <p className="mt-3 text-sm text-zinc-600">Showing {data.items.length} of {data.total} records.</p> : null}
    </div>
  );
}

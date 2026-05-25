import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { FactBadge, ReliabilityBadge } from '../components/Badge';
import { SectionHeader } from '../components/Layout';
import { ErrorMessage, Loading } from '../components/Loading';
import { SatelliteTable } from '../components/SatelliteTable';
import type { EvidenceDocument, PaginatedSatellites } from '../types/api';

const periods = [
  { label: 'June 1 through November 30, 2024', start: '2024-06-01', end: '2024-11-30' },
  { label: 'December 1, 2024 through May 31, 2025', start: '2024-12-01', end: '2025-05-31' },
];

export function ReportingPeriods() {
  const [active, setActive] = useState(periods[1]);
  const [satellites, setSatellites] = useState<PaginatedSatellites | null>(null);
  const [evidence, setEvidence] = useState<EvidenceDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ decay_date_from: active.start, decay_date_to: active.end, page_size: '250' });
    return params;
  }, [active]);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.satellites(query), api.evidence()])
      .then(([satData, docs]) => {
        setSatellites(satData);
        setEvidence(docs);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, [query]);

  const periodEvidence = evidence.filter((doc) =>
    doc.evidence_links.some(
      (link) => link.reporting_period_start === active.start && link.reporting_period_end === active.end,
    ),
  );

  return (
    <div>
      <SectionHeader title="Reporting Periods" />
      <div className="mb-4 flex flex-wrap gap-2">
        {periods.map((period) => (
          <button
            key={period.label}
            className={`focus-ring h-9 rounded px-3 text-sm ${
              active.label === period.label ? 'bg-orbit text-white' : 'border border-zinc-300 bg-white text-zinc-700'
            }`}
            onClick={() => setActive(period)}
          >
            {period.label}
          </button>
        ))}
      </div>
      {loading ? <Loading label="Loading period" /> : error ? <ErrorMessage error={error} /> : null}
      {!loading && !error ? (
        <>
          <section className="mb-4 rounded border border-zinc-200 bg-white p-4">
            <h3 className="font-semibold">Aggregate counts</h3>
            <p className="mt-2 text-sm text-zinc-700">{satellites?.total ?? 0} satellites decayed in this window.</p>
          </section>
          <SatelliteTable data={satellites?.items ?? []} />
          <section className="mt-4 rounded border border-zinc-200 bg-white p-4">
            <h3 className="font-semibold">Documents tied to this period</h3>
            <div className="mt-3 grid gap-3">
              {periodEvidence.length === 0 ? <p className="text-sm text-zinc-600">No reporting-period evidence linked.</p> : null}
              {periodEvidence.map((doc) => (
                <article key={doc.id} className="rounded border border-zinc-200 p-3">
                  <div className="flex flex-wrap gap-2">
                    <span className="font-medium">{doc.title}</span>
                    <ReliabilityBadge value={doc.reliability_rating} />
                  </div>
                  <p className="mt-1 text-sm text-zinc-600">{doc.summary}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {doc.evidence_links.map((link) => <FactBadge key={link.id} value={link.fact_vs_inference} />)}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

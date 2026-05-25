import { AlertTriangle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import { FactBadge, ReliabilityBadge } from '../components/Badge';
import { SectionHeader } from '../components/Layout';
import { ErrorMessage, Loading } from '../components/Loading';
import type { OrbitalPoint, SatelliteDetail as SatelliteDetailType } from '../types/api';
import { formatDate, formatNumber, humanize } from '../utils/format';

export function SatelliteDetail() {
  const { norad } = useParams();
  const [satellite, setSatellite] = useState<SatelliteDetailType | null>(null);
  const [history, setHistory] = useState<OrbitalPoint[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const noradId = Number(norad);

  useEffect(() => {
    Promise.all([api.satellite(noradId), api.orbitalHistory(noradId)])
      .then(([detail, orbital]) => {
        setSatellite(detail);
        setHistory(orbital);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, [noradId]);

  if (loading) return <Loading label="Loading satellite" />;
  if (error) return <ErrorMessage error={error} />;
  if (!satellite) return null;
  const inference = satellite.inferred_categories[0];

  return (
    <div>
      <SectionHeader title={`${satellite.object_name} (${satellite.norad_cat_id})`} />
      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded border border-zinc-200 bg-white p-4">
          <h3 className="font-semibold">Source-backed facts</h3>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <dt className="text-zinc-600">International designator</dt><dd>{satellite.international_designator ?? '—'}</dd>
            <dt className="text-zinc-600">Launch date</dt><dd>{formatDate(satellite.launch_date)}</dd>
            <dt className="text-zinc-600">Decay date</dt><dd>{formatDate(satellite.decay_date)}</dd>
            <dt className="text-zinc-600">Status</dt><dd>{satellite.operational_status ?? '—'}</dd>
            <dt className="text-zinc-600">Variant</dt><dd>{satellite.generation_or_variant ?? '—'}</dd>
            <dt className="text-zinc-600">Launch group</dt><dd>{satellite.launch_group ?? '—'}</dd>
          </dl>
        </section>
        <section className="rounded border border-zinc-200 bg-white p-4 lg:col-span-2">
          <h3 className="font-semibold">Inference explanation</h3>
          {inference ? (
            <div className="mt-3 space-y-3 text-sm">
              <div className="flex flex-wrap gap-2">
                <span className="rounded border border-rose-700 bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-900">
                  {humanize(inference.category)}
                </span>
                <span className="rounded border border-zinc-300 px-2 py-0.5 text-xs">{inference.confidence_level}</span>
              </div>
              <p>{inference.rationale}</p>
              <div className="flex gap-2 rounded border border-amber-200 bg-amber-50 p-3 text-amber-950">
                <AlertTriangle className="h-5 w-5 flex-none" aria-hidden="true" />
                <p>Rule output is not a direct disclosed internal cause unless a linked source explicitly says so.</p>
              </div>
            </div>
          ) : (
            <p className="mt-3 text-sm text-zinc-600">No inference has been generated yet.</p>
          )}
        </section>
      </div>
      <section className="mt-4 rounded border border-zinc-200 bg-white p-4">
        <h3 className="mb-3 font-semibold">Altitude, perigee, apogee history</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="epoch" tickFormatter={(value) => String(value).slice(0, 10)} />
              <YAxis tickFormatter={(value) => formatNumber(Number(value), 0)} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="altitude_estimate_km" stroke="#0f766e" dot={false} name="Altitude estimate" />
              <Line type="monotone" dataKey="perigee_km" stroke="#be123c" dot={false} name="Perigee" />
              <Line type="monotone" dataKey="apogee_km" stroke="#b45309" dot={false} name="Apogee" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="mt-4 rounded border border-zinc-200 bg-white p-4">
        <h3 className="font-semibold">Evidence documents</h3>
        <div className="mt-3 grid gap-3">
          {satellite.evidence_documents.length === 0 ? <p className="text-sm text-zinc-600">No linked evidence documents.</p> : null}
          {satellite.evidence_documents.map((doc) => (
            <article key={doc.id} className="rounded border border-zinc-200 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-medium">{doc.title}</h4>
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
    </div>
  );
}

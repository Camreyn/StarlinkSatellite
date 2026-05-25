import { Plus } from 'lucide-react';
import { FormEvent, useEffect, useState } from 'react';
import { api } from '../api/client';
import { FactBadge, ReliabilityBadge } from '../components/Badge';
import { SectionHeader } from '../components/Layout';
import { ErrorMessage, Loading } from '../components/Loading';
import type { EvidenceDocument, ReliabilityRating } from '../types/api';

const ratings: ReliabilityRating[] = [
  'PRIMARY_REGULATORY',
  'PRIMARY_OPERATOR',
  'OFFICIAL_CATALOG',
  'EXPERT_TRACKER',
  'INDUSTRY_MEDIA',
  'USER_MANUAL_NOTE',
];
const staticData = import.meta.env.VITE_STATIC_DATA === 'true';

export function EvidenceLibrary() {
  const [docs, setDocs] = useState<EvidenceDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [title, setTitle] = useState('');
  const [sourceName, setSourceName] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [rating, setRating] = useState<ReliabilityRating>('USER_MANUAL_NOTE');
  const [summary, setSummary] = useState('');

  function load() {
    setLoading(true);
    api
      .evidence()
      .then(setDocs)
      .catch(setError)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (staticData) return;
    await api.addEvidence({
      title,
      source_name: sourceName,
      source_url: sourceUrl || null,
      reliability_rating: rating,
      summary,
      document_type: 'manual entry',
    });
    setTitle('');
    setSourceName('');
    setSourceUrl('');
    setSummary('');
    load();
  }

  return (
    <div>
      <SectionHeader title="Evidence Library" />
      {staticData ? (
        <div className="mb-4 rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          This GitHub Pages build is a read-only public snapshot. Run the app locally to add or edit evidence
          documents.
        </div>
      ) : null}
      {!staticData ? <form className="mb-4 grid gap-3 rounded border border-zinc-200 bg-white p-4 md:grid-cols-2" onSubmit={submit}>
        <label>
          <span className="mb-1 block text-sm font-medium">Title</span>
          <input required className="h-9 w-full rounded border border-zinc-300 px-2" value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium">Source name</span>
          <input required className="h-9 w-full rounded border border-zinc-300 px-2" value={sourceName} onChange={(event) => setSourceName(event.target.value)} />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium">Source URL</span>
          <input className="h-9 w-full rounded border border-zinc-300 px-2" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium">Reliability</span>
          <select className="h-9 w-full rounded border border-zinc-300 px-2" value={rating} onChange={(event) => setRating(event.target.value as ReliabilityRating)}>
            {ratings.map((item) => <option key={item} value={item}>{item.replace(/_/g, ' ')}</option>)}
          </select>
        </label>
        <label className="md:col-span-2">
          <span className="mb-1 block text-sm font-medium">Summary</span>
          <textarea className="min-h-24 w-full rounded border border-zinc-300 p-2" value={summary} onChange={(event) => setSummary(event.target.value)} />
        </label>
        <button className="focus-ring inline-flex h-9 w-fit items-center gap-2 rounded bg-orbit px-3 text-sm text-white">
          <Plus className="h-4 w-4" aria-hidden="true" /> Add document
        </button>
      </form> : null}
      {loading ? <Loading label="Loading evidence" /> : error ? <ErrorMessage error={error} /> : null}
      <div className="grid gap-3">
        {docs.map((doc) => (
          <article key={doc.id} className="rounded border border-zinc-200 bg-white p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold">{doc.title}</h3>
              <ReliabilityBadge value={doc.reliability_rating} />
            </div>
            <p className="mt-1 text-sm text-zinc-600">{doc.summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {doc.evidence_links.map((link) => <FactBadge key={link.id} value={link.fact_vs_inference} />)}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

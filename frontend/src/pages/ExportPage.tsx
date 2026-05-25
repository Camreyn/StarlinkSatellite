import { Download } from 'lucide-react';
import { SectionHeader } from '../components/Layout';

const staticData = import.meta.env.VITE_STATIC_DATA === 'true';
const base = import.meta.env.BASE_URL;

function href(path: string) {
  return staticData ? `${base}${path.replace(/^\//, '')}` : path;
}

const csvHref = staticData ? href('/static-data/satellites.csv') : '/api/export/satellites.csv';
const reportHref = staticData ? href('/static-data/report.md') : '/api/export/report.md';

export function ExportPage() {
  return (
    <div>
      <SectionHeader title="Export" />
      <section className="grid gap-3 rounded border border-zinc-200 bg-white p-4 sm:grid-cols-2">
        <a
          className="focus-ring inline-flex h-10 items-center justify-center gap-2 rounded bg-orbit px-4 text-sm text-white"
          href={csvHref}
        >
          <Download className="h-4 w-4" aria-hidden="true" /> CSV satellite export
        </a>
        <a
          className="focus-ring inline-flex h-10 items-center justify-center gap-2 rounded bg-ink px-4 text-sm text-white"
          href={reportHref}
        >
          <Download className="h-4 w-4" aria-hidden="true" /> Markdown report
        </a>
      </section>
    </div>
  );
}

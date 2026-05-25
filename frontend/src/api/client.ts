import type {
  DashboardSummary,
  EvidenceDocument,
  OrbitalPoint,
  PaginatedSatellites,
  SatelliteDetail,
  SatelliteListItem,
  TimelineEvent,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';
const STATIC_DATA = import.meta.env.VITE_STATIC_DATA === 'true';
const staticCache = new Map<string, Promise<unknown>>();

function staticAsset(path: string): string {
  return `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;
}

async function staticJson<T>(path: string): Promise<T> {
  const url = staticAsset(path);
  if (!staticCache.has(url)) {
    staticCache.set(
      url,
      fetch(url).then((response) => {
        if (!response.ok) throw new Error(`Static data request failed: ${response.status}`);
        return response.json();
      }),
    );
  }
  return (await staticCache.get(url)) as T;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

function dateValue(value?: string | null): number | null {
  if (!value) return null;
  return new Date(`${value.slice(0, 10)}T00:00:00Z`).getTime();
}

function matchesDateRange(value: string | null | undefined, from?: string | null, to?: string | null): boolean {
  const time = dateValue(value);
  if (from && (time === null || time < dateValue(from)!)) return false;
  if (to && (time === null || time > dateValue(to)!)) return false;
  return true;
}

function filterStaticSatellites(items: SatelliteListItem[], query: URLSearchParams): SatelliteListItem[] {
  const q = query.get('q')?.toLowerCase();
  const status = query.get('status');
  const launchGroup = query.get('launch_group');
  const generation = query.get('generation');
  const inferredCategory = query.get('inferred_category');
  const decayedAfter = query.get('decayed_after');
  return items.filter((item) => {
    if (q) {
      const haystack = [
        item.norad_cat_id,
        item.object_name,
        item.starlink_name,
        item.international_designator,
      ]
        .join(' ')
        .toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    if (status && item.operational_status !== status) return false;
    if (launchGroup && item.launch_group !== launchGroup) return false;
    if (generation && item.generation_or_variant !== generation) return false;
    if (inferredCategory && item.inferred_category !== inferredCategory) return false;
    if (!matchesDateRange(item.launch_date, query.get('launch_date_from'), query.get('launch_date_to'))) {
      return false;
    }
    if (!matchesDateRange(item.decay_date, query.get('decay_date_from'), query.get('decay_date_to'))) {
      return false;
    }
    if (decayedAfter) {
      const decay = dateValue(item.decay_date);
      if (decay === null || decay <= dateValue(decayedAfter)!) return false;
    }
    return true;
  });
}

function sortStaticSatellites(items: SatelliteListItem[], sort: string | null): SatelliteListItem[] {
  const [field = 'norad_cat_id', direction = 'asc'] = (sort ?? 'norad_cat_id:asc').split(':');
  return [...items].sort((a, b) => {
    const av = a[field as keyof SatelliteListItem];
    const bv = b[field as keyof SatelliteListItem];
    const result = String(av ?? '').localeCompare(String(bv ?? ''), undefined, {
      numeric: true,
      sensitivity: 'base',
    });
    return direction === 'desc' ? -result : result;
  });
}

async function staticSatellites(query: URLSearchParams): Promise<PaginatedSatellites> {
  const all = await staticJson<SatelliteListItem[]>('/static-data/satellites.json');
  const filtered = sortStaticSatellites(filterStaticSatellites(all, query), query.get('sort'));
  const page = Number(query.get('page') ?? '1');
  const pageSize = Number(query.get('page_size') ?? '50');
  return {
    items: filtered.slice((page - 1) * pageSize, page * pageSize),
    total: filtered.length,
    page,
    page_size: pageSize,
  };
}

export const api = {
  dashboard: () =>
    STATIC_DATA
      ? staticJson<DashboardSummary>('/static-data/dashboard-summary.json')
      : request<DashboardSummary>('/api/dashboard/summary'),
  satellites: (query: URLSearchParams) =>
    STATIC_DATA ? staticSatellites(query) : request<PaginatedSatellites>(`/api/satellites?${query}`),
  satellite: async (norad: number) => {
    if (!STATIC_DATA) return request<SatelliteDetail>(`/api/satellites/${norad}`);
    const details = await staticJson<Record<string, SatelliteDetail>>('/static-data/satellite-details.json');
    const detail = details[String(norad)];
    if (!detail) throw new Error('Satellite not found in static snapshot');
    return detail;
  },
  orbitalHistory: async (norad: number) => {
    if (!STATIC_DATA) return request<OrbitalPoint[]>(`/api/satellites/${norad}/orbital-history`);
    const history = await staticJson<Record<string, OrbitalPoint[]>>('/static-data/orbital-history.json');
    return history[String(norad)] ?? [];
  },
  evidence: () =>
    STATIC_DATA
      ? staticJson<EvidenceDocument[]>('/static-data/evidence.json')
      : request<EvidenceDocument[]>('/api/evidence'),
  timeline: () =>
    STATIC_DATA ? staticJson<TimelineEvent[]>('/static-data/timeline.json') : request<TimelineEvent[]>('/api/timeline'),
  ingestCelestrakStarlink: () => request('/api/ingest/celestrak/starlink', { method: 'POST' }),
  ingestCelestrakSatcat: () => request('/api/ingest/celestrak/satcat', { method: 'POST' }),
  addEvidence: (payload: unknown) =>
    request<EvidenceDocument>('/api/evidence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
};

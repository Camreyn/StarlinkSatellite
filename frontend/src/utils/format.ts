export function formatNumber(value?: number | null, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(value);
}

export function formatDate(value?: string | null): string {
  if (!value) return '—';
  return value.slice(0, 10);
}

export function humanize(value?: string | null): string {
  if (!value) return '—';
  return value.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table';
import { ArrowUpDown, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { SatelliteListItem } from '../types/api';
import { formatDate, formatNumber, humanize } from '../utils/format';

const columnHelper = createColumnHelper<SatelliteListItem>();

const columns = [
  columnHelper.accessor('norad_cat_id', {
    header: 'NORAD',
    cell: (info) => (
      <Link className="inline-flex items-center gap-1 font-medium text-orbit hover:underline" to={`/satellites/${info.getValue()}`}>
        {info.getValue()} <ExternalLink className="h-3 w-3" aria-hidden="true" />
      </Link>
    ),
  }),
  columnHelper.accessor('object_name', { header: 'Name' }),
  columnHelper.accessor('international_designator', { header: 'Intl. designator', cell: (info) => info.getValue() ?? '—' }),
  columnHelper.accessor('launch_date', { header: 'Launch date', cell: (info) => formatDate(info.getValue()) }),
  columnHelper.accessor('decay_date', { header: 'Decay date', cell: (info) => formatDate(info.getValue()) }),
  columnHelper.accessor('operational_status', { header: 'Status', cell: (info) => info.getValue() ?? '—' }),
  columnHelper.accessor('launch_group', { header: 'Launch group', cell: (info) => info.getValue() ?? '—' }),
  columnHelper.accessor('generation_or_variant', { header: 'Variant', cell: (info) => info.getValue() ?? '—' }),
  columnHelper.accessor('latest_altitude_estimate_km', {
    header: 'Altitude km',
    cell: (info) => formatNumber(info.getValue(), 1),
  }),
  columnHelper.accessor('inferred_category', {
    header: 'Inferred category',
    cell: (info) => humanize(info.getValue()),
  }),
  columnHelper.accessor('inferred_confidence', { header: 'Confidence', cell: (info) => info.getValue() ?? '—' }),
  columnHelper.accessor('sources_count', { header: 'Sources' }),
];

export function SatelliteTable({ data }: { data: SatelliteListItem[] }) {
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });
  return (
    <div className="overflow-x-auto rounded border border-zinc-200 bg-white">
      <table className="min-w-full divide-y divide-zinc-200 text-sm">
        <thead className="bg-zinc-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="whitespace-nowrap px-3 py-2 text-left font-semibold text-zinc-700">
                  <span className="inline-flex items-center gap-1">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    <ArrowUpDown className="h-3 w-3 text-zinc-400" aria-hidden="true" />
                  </span>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="hover:bg-zinc-50">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="whitespace-nowrap px-3 py-2 text-zinc-800">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

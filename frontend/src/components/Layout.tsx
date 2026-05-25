import { BarChart3, BookOpen, Download, Home, Orbit, PanelTop, Satellite } from 'lucide-react';
import type React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Disclaimer } from './Disclaimer';

const nav = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/satellites', label: 'Satellites', icon: Satellite },
  { to: '/timeline', label: 'Timeline', icon: PanelTop },
  { to: '/periods', label: 'Periods', icon: BarChart3 },
  { to: '/evidence', label: 'Evidence', icon: BookOpen },
  { to: '/export', label: 'Export', icon: Download },
];

export function Layout() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded bg-ink text-white">
              <Orbit className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-semibold leading-tight">Starlink Lifecycle Research</h1>
              <p className="text-sm text-zinc-600">Local public-source catalog, evidence, and inference tracker</p>
            </div>
          </div>
          <nav className="flex flex-wrap gap-1" aria-label="Primary navigation">
            {nav.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `focus-ring inline-flex h-9 items-center gap-2 rounded px-3 text-sm ${
                      isActive ? 'bg-orbit text-white' : 'text-zinc-700 hover:bg-zinc-100'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </header>
      <Disclaimer />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}

export function SectionHeader({ title, actions }: { title: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <h2 className="text-xl font-semibold">{title}</h2>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

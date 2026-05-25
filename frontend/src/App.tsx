import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { useMemo } from 'react';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { EvidenceLibrary } from './pages/EvidenceLibrary';
import { ExportPage } from './pages/ExportPage';
import { ReportingPeriods } from './pages/ReportingPeriods';
import { SatelliteDetail } from './pages/SatelliteDetail';
import { Satellites } from './pages/Satellites';
import { Timeline } from './pages/Timeline';

function routerBasename() {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return base || '/';
}

export function App() {
  const router = useMemo(
    () =>
      createBrowserRouter(
        [
          {
            path: '/',
            element: <Layout />,
            children: [
              { index: true, element: <Dashboard /> },
              { path: 'satellites', element: <Satellites /> },
              { path: 'satellites/:norad', element: <SatelliteDetail /> },
              { path: 'timeline', element: <Timeline /> },
              { path: 'periods', element: <ReportingPeriods /> },
              { path: 'evidence', element: <EvidenceLibrary /> },
              { path: 'export', element: <ExportPage /> },
            ],
          },
        ],
        { basename: routerBasename() },
      ),
    [],
  );
  return <RouterProvider router={router} />;
}

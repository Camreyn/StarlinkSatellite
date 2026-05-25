import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';

const satellitePage = {
  items: [
    {
      id: 1,
      norad_cat_id: 70002,
      object_name: 'STARLINK-SAMPLE-DECAYED',
      decay_date: '2024-12-08',
      launch_date: '2023-10-10',
      sources_count: 1,
      has_direct_source: true,
      has_inference_only: false,
      missing_explanation: false,
      inferred_category: 'DECAYED_REENTERED',
      inferred_confidence: 'HIGH',
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
};

function mockFetch() {
  return vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
    const url = String(input);
    if (url.includes('/api/dashboard/summary')) {
      return Response.json({
        total_satellites: 1,
        active_count: 0,
        decayed_reentered_count: 1,
        decayed_after_2024_11_05_count: 1,
        decayed_dec_2024_through_may_2025_count: 1,
        satellites_missing_decay_reason: 0,
        satellites_with_inferred_category_only: 0,
      });
    }
    if (url.includes('/api/satellites/70002/orbital-history')) {
      return Response.json([{ epoch: '2024-12-01T00:00:00', altitude_estimate_km: 260, perigee_km: 240, apogee_km: 280, source_name: 'test' }]);
    }
    if (url.includes('/api/satellites/70002')) {
      return Response.json({
        ...satellitePage.items[0],
        orbital_elements: [],
        decay_events: [],
        launch_events: [],
        evidence_documents: [
          {
            id: 1,
            title: 'Catalog evidence',
            source_name: 'CelesTrak',
            reliability_rating: 'OFFICIAL_CATALOG',
            evidence_links: [{ id: 1, claim_type: 'decay', claim_text: 'Decay date', fact_vs_inference: 'FACT', confidence_level: 'HIGH' }],
          },
        ],
        inferred_categories: [
          {
            category: 'DECAYED_REENTERED',
            rationale: 'Catalog decay date; not a cause.',
            confidence_level: 'HIGH',
            created_from_rules_version: 'test',
          },
        ],
      });
    }
    if (url.includes('/api/satellites')) return Response.json(satellitePage);
    if (url.includes('/api/timeline')) {
      return Response.json([
        { id: 'marker-election-2024', date: '2024-11-05', type: 'marker', title: 'U.S. election' },
        { id: 'marker-reporting-dec-2024', date: '2024-12-01', type: 'marker', title: 'FCC reporting period start' },
      ]);
    }
    if (url.includes('/api/evidence')) {
      return Response.json([
        {
          id: 1,
          title: 'Catalog evidence',
          source_name: 'CelesTrak',
          reliability_rating: 'OFFICIAL_CATALOG',
          evidence_links: [{ id: 1, claim_type: 'decay', claim_text: 'Decay date', fact_vs_inference: 'FACT', confidence_level: 'HIGH' }],
        },
      ]);
    }
    return Response.json({});
  });
}

describe('App pages', () => {
  beforeEach(() => {
    mockFetch();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    window.history.pushState({}, '', '/');
  });

  it('filters update query params', async () => {
    window.history.pushState({}, '', '/satellites');
    render(<App />);
    await screen.findByText('STARLINK-SAMPLE-DECAYED');
    await userEvent.click(screen.getByText('Decayed after Nov. 5, 2024'));
    expect(window.location.search).toContain('decayed_after=2024-11-05');
  });

  it('satellite detail page shows fact and inference labels', async () => {
    window.history.pushState({}, '', '/satellites/70002');
    render(<App />);
    await screen.findByText('Catalog evidence');
    expect(screen.getByText('Fact')).toBeInTheDocument();
    expect(screen.getByText('Rule output is not a direct disclosed internal cause unless a linked source explicitly says so.')).toBeInTheDocument();
  });

  it('timeline markers render', async () => {
    window.history.pushState({}, '', '/timeline');
    render(<App />);
    await waitFor(() => expect(screen.getAllByText('U.S. election').length).toBeGreaterThan(0));
    expect(screen.getByText('FCC reporting period start')).toBeInTheDocument();
  });

  it('evidence documents display reliability labels', async () => {
    window.history.pushState({}, '', '/evidence');
    render(<App />);
    await screen.findByText('Catalog evidence');
    expect(screen.getByText('Official Catalog')).toBeInTheDocument();
  });
});

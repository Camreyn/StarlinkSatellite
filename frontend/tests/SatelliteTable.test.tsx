import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SatelliteTable } from '../src/components/SatelliteTable';

describe('SatelliteTable', () => {
  it('renders satellite rows', () => {
    render(
      <MemoryRouter>
        <SatelliteTable
          data={[
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
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText('STARLINK-SAMPLE-DECAYED')).toBeInTheDocument();
    expect(screen.getByText('70002')).toBeInTheDocument();
  });
});

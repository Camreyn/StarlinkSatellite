export type FactLabel = 'FACT' | 'AGGREGATE_EXPLANATION' | 'COMPUTED' | 'INFERENCE';
export type ReliabilityRating =
  | 'PRIMARY_REGULATORY'
  | 'PRIMARY_OPERATOR'
  | 'OFFICIAL_CATALOG'
  | 'EXPERT_TRACKER'
  | 'INDUSTRY_MEDIA'
  | 'USER_MANUAL_NOTE';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
export type InferredCategory =
  | 'ACTIVE_ORBIT'
  | 'DECAYED_REENTERED'
  | 'EARLY_DEORBIT'
  | 'POSSIBLE_FAILED_BEFORE_OPERATIONAL_ORBIT'
  | 'POSSIBLE_PLANNED_RETIREMENT'
  | 'POSSIBLE_OLDER_V1_RETIREMENT'
  | 'UNKNOWN';

export interface SatelliteListItem {
  id: number;
  norad_cat_id: number;
  object_name: string;
  starlink_name?: string | null;
  international_designator?: string | null;
  launch_date?: string | null;
  decay_date?: string | null;
  object_type?: string | null;
  operational_status?: string | null;
  generation_or_variant?: string | null;
  launch_group?: string | null;
  source_priority_status?: string | null;
  latest_altitude_estimate_km?: number | null;
  inferred_category?: InferredCategory | null;
  inferred_confidence?: ConfidenceLevel | null;
  sources_count: number;
  has_direct_source: boolean;
  has_inference_only: boolean;
  missing_explanation: boolean;
}

export interface PaginatedSatellites {
  items: SatelliteListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardSummary {
  total_satellites: number;
  active_count: number;
  decayed_reentered_count: number;
  decayed_after_2024_11_05_count: number;
  decayed_dec_2024_through_may_2025_count: number;
  satellites_missing_decay_reason: number;
  satellites_with_inferred_category_only: number;
  last_data_refresh_time?: string | null;
}

export interface OrbitalPoint {
  epoch: string;
  altitude_estimate_km?: number | null;
  perigee_km?: number | null;
  apogee_km?: number | null;
  source_name: string;
}

export interface EvidenceLink {
  id: number;
  satellite_id?: number | null;
  launch_event_id?: number | null;
  reporting_period_start?: string | null;
  reporting_period_end?: string | null;
  claim_type: string;
  claim_text: string;
  fact_vs_inference: FactLabel;
  confidence_level: ConfidenceLevel;
}

export interface EvidenceDocument {
  id: number;
  title: string;
  source_name: string;
  source_url?: string | null;
  published_date?: string | null;
  document_type?: string | null;
  local_file_path?: string | null;
  summary?: string | null;
  reliability_rating: ReliabilityRating;
  notes?: string | null;
  evidence_links: EvidenceLink[];
}

export interface SatelliteDetail extends SatelliteListItem {
  orbital_elements: Array<OrbitalPoint & { id: number; mean_motion?: number | null }>;
  decay_events: Array<{
    id: number;
    decay_date: string;
    decay_precision: string;
    decay_source_name: string;
    decay_source_url?: string | null;
    decay_status: string;
    confidence_level: ConfidenceLevel;
    notes?: string | null;
  }>;
  launch_events: Array<{ id: number; mission_name: string; launch_date?: string | null }>;
  evidence_documents: EvidenceDocument[];
  inferred_categories: Array<{
    category: InferredCategory;
    rationale: string;
    confidence_level: ConfidenceLevel;
    created_from_rules_version: string;
    created_at?: string | null;
  }>;
}

export interface TimelineEvent {
  id: string;
  date: string;
  type: string;
  title: string;
  description?: string | null;
  source_name?: string | null;
  fact_vs_inference?: FactLabel | null;
}

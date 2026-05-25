from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import ConfidenceLevel, FactLabel, InferredCategoryValue, ReliabilityRating


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SatelliteBase(BaseModel):
    norad_cat_id: int
    object_name: str
    starlink_name: str | None = None
    international_designator: str | None = None
    launch_date: date | None = None
    decay_date: date | None = None
    object_type: str | None = None
    operational_status: str | None = None
    generation_or_variant: str | None = None
    launch_group: str | None = None
    source_priority_status: str | None = None


class InferredCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: InferredCategoryValue
    rationale: str
    confidence_level: ConfidenceLevel
    created_from_rules_version: str
    created_at: datetime | None = None


class SatelliteListItem(SatelliteBase):
    id: int
    latest_altitude_estimate_km: float | None = None
    inferred_category: InferredCategoryValue | None = None
    inferred_confidence: ConfidenceLevel | None = None
    sources_count: int = 0
    has_direct_source: bool = False
    has_inference_only: bool = False
    missing_explanation: bool = False


class PaginatedSatellites(BaseModel):
    items: list[SatelliteListItem]
    total: int
    page: int
    page_size: int


class OrbitalElementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    epoch: datetime
    mean_motion: float | None = None
    eccentricity: float | None = None
    inclination: float | None = None
    raan: float | None = None
    arg_perigee: float | None = None
    mean_anomaly: float | None = None
    bstar: float | None = None
    semimajor_axis_km: float | None = None
    perigee_km: float | None = None
    apogee_km: float | None = None
    altitude_estimate_km: float | None = None
    raw_tle_line_1: str | None = None
    raw_tle_line_2: str | None = None
    raw_json: dict[str, Any] | None = None
    source_name: str
    source_url: str | None = None
    fetched_at: datetime | None = None


class DecayEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    decay_date: date
    decay_precision: str
    decay_source_name: str
    decay_source_url: str | None = None
    decay_status: str
    confidence_level: ConfidenceLevel
    notes: str | None = None


class LaunchEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mission_name: str
    launch_date: date | None = None
    launch_vehicle: str | None = None
    launch_site: str | None = None
    source_name: str | None = None
    source_url: str | None = None


class EvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    satellite_id: int | None = None
    launch_event_id: int | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    claim_type: str
    claim_text: str
    fact_vs_inference: FactLabel
    confidence_level: ConfidenceLevel


class EvidenceDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_name: str
    source_url: str | None = None
    published_date: date | None = None
    document_type: str | None = None
    local_file_path: str | None = None
    summary: str | None = None
    reliability_rating: ReliabilityRating
    notes: str | None = None
    evidence_links: list[EvidenceLinkRead] = Field(default_factory=list)


class EvidenceDocumentCreate(BaseModel):
    title: str
    source_name: str
    source_url: str | None = None
    published_date: date | None = None
    document_type: str | None = None
    local_file_path: str | None = None
    summary: str | None = None
    reliability_rating: ReliabilityRating
    notes: str | None = None


class EvidenceLinkCreate(BaseModel):
    evidence_document_id: int
    satellite_norad_cat_id: int | None = None
    launch_event_id: int | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    claim_type: str
    claim_text: str
    fact_vs_inference: FactLabel
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN


class SatelliteDetail(SatelliteBase):
    id: int
    orbital_elements: list[OrbitalElementRead] = Field(default_factory=list)
    decay_events: list[DecayEventRead] = Field(default_factory=list)
    launch_events: list[LaunchEventRead] = Field(default_factory=list)
    evidence_documents: list[EvidenceDocumentRead] = Field(default_factory=list)
    inferred_categories: list[InferredCategoryRead] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    total_satellites: int
    active_count: int
    decayed_reentered_count: int
    decayed_after_2024_11_05_count: int
    decayed_dec_2024_through_may_2025_count: int
    satellites_missing_decay_reason: int
    satellites_with_inferred_category_only: int
    last_data_refresh_time: datetime | None = None


class TimelineEvent(BaseModel):
    id: str
    date: date
    type: str
    title: str
    description: str | None = None
    source_name: str | None = None
    fact_vs_inference: FactLabel | None = None


class IngestResult(BaseModel):
    source: str
    fetched: int
    created: int
    updated: int
    skipped: int = 0
    warnings: list[str] = Field(default_factory=list)


class CsvImportPreview(BaseModel):
    accepted_columns: list[str]
    missing_recommended_columns: list[str]
    preview_rows: list[dict[str, str | None]]
    row_count: int


class CsvImportResult(BaseModel):
    row_count: int
    created: int
    updated: int
    warnings: list[str] = Field(default_factory=list)

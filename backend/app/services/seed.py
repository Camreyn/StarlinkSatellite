from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConfidenceLevel, FactLabel, ReliabilityRating, Satellite
from app.services.inference import refresh_all_inferences
from app.services.upsert import (
    create_evidence_document,
    create_evidence_link,
    link_satellite_to_launch,
    upsert_decay_event,
    upsert_launch_event,
    upsert_orbital_element,
    upsert_satellite,
)


def seed_database(db: Session) -> None:
    if db.scalar(select(Satellite).limit(1)) is not None:
        return

    sat_active, _ = upsert_satellite(
        db,
        norad_cat_id=70001,
        object_name="STARLINK-SAMPLE-ACTIVE",
        starlink_name="STARLINK-SAMPLE-ACTIVE",
        international_designator="2024-001A",
        launch_date=date(2024, 1, 2),
        object_type="PAYLOAD",
        operational_status="ACTIVE",
        generation_or_variant="V2 Mini",
        launch_group="Sample Group 1",
        source_priority_status="seed sample",
    )
    upsert_orbital_element(
        db,
        satellite=sat_active,
        epoch=datetime(2026, 5, 1, 12, 0, 0),
        source_name="Seed sample GP",
        source_url="sample_data/seed_satellites.csv",
        mean_motion=15.25,
        eccentricity=0.00012,
        inclination=53.2,
        raan=10.1,
        arg_perigee=80.0,
        mean_anomaly=250.0,
        bstar=0.00001,
        raw_json={"sample": True},
    )

    sat_decay, _ = upsert_satellite(
        db,
        norad_cat_id=70002,
        object_name="STARLINK-SAMPLE-DECAYED",
        starlink_name="STARLINK-SAMPLE-DECAYED",
        international_designator="2023-155A",
        launch_date=date(2023, 10, 10),
        decay_date=date(2024, 12, 8),
        object_type="PAYLOAD",
        operational_status="DECAYED",
        generation_or_variant="V2 Mini",
        launch_group="Sample Group 2",
        source_priority_status="seed sample SATCAT",
    )
    upsert_orbital_element(
        db,
        satellite=sat_decay,
        epoch=datetime(2024, 12, 1, 12, 0, 0),
        source_name="Seed sample TLE",
        source_url="sample_data/seed_satellites.csv",
        mean_motion=16.1,
        eccentricity=0.002,
        inclination=53.0,
        raan=120.0,
        arg_perigee=90.0,
        mean_anomaly=260.0,
        bstar=0.001,
        raw_tle_line_1="1 70002U 23155A   24336.50000000  .00000000  00000+0  10000-3 0  9991",
        raw_tle_line_2="2 70002  53.0000 120.0000 0020000  90.0000 260.0000 16.10000000    01",
    )
    upsert_decay_event(
        db,
        satellite=sat_decay,
        decay_date=date(2024, 12, 8),
        decay_source_name="Seed sample catalog",
        decay_source_url="sample_data/seed_satellites.csv",
        notes="Sample record: decay date only, no internal cause asserted.",
    )

    sat_v1, _ = upsert_satellite(
        db,
        norad_cat_id=70003,
        object_name="STARLINK-SAMPLE-V1-DECAYED",
        starlink_name="STARLINK-SAMPLE-V1-DECAYED",
        international_designator="2020-025A",
        launch_date=date(2020, 4, 22),
        decay_date=date(2025, 2, 14),
        object_type="PAYLOAD",
        operational_status="DECAYED",
        generation_or_variant="V1.0",
        launch_group="Sample Older V1",
        source_priority_status="seed sample SATCAT",
    )
    upsert_decay_event(
        db,
        satellite=sat_v1,
        decay_date=date(2025, 2, 14),
        decay_source_name="Seed sample catalog",
        decay_source_url="sample_data/seed_satellites.csv",
        notes="Sample V1 decay record. Retirement category is inferential unless sourced.",
    )

    launch = upsert_launch_event(
        db,
        mission_name="Sample Starlink Mission",
        launch_date=date(2024, 1, 2),
        launch_site="Sample launch site",
        source_name="Seed sample",
        source_url="sample_data/seed_satellites.csv",
    )
    link_satellite_to_launch(db, sat_active, launch)
    link_satellite_to_launch(db, sat_decay, launch)

    doc = create_evidence_document(
        db,
        title="Sample public catalog evidence",
        source_name="Seed sample catalog",
        source_url="sample_data/seed_satellites.csv",
        published_date=date(2026, 5, 24),
        document_type="sample CSV",
        summary="Synthetic sample records used to demonstrate app behavior and labels.",
        reliability_rating=ReliabilityRating.USER_MANUAL_NOTE,
        notes="Not real satellite data.",
    )
    create_evidence_link(
        db,
        evidence_document_id=doc.id,
        satellite_id=sat_decay.id,
        claim_type="decay",
        claim_text="Sample catalog row states a decay date of 2024-12-08 for STARLINK-SAMPLE-DECAYED.",
        fact_vs_inference=FactLabel.FACT,
        confidence_level=ConfidenceLevel.HIGH,
    )
    aggregate = create_evidence_document(
        db,
        title="Sample aggregate reporting-period note",
        source_name="User manual note",
        published_date=date(2025, 6, 1),
        document_type="manual note",
        summary="Demonstrates aggregate explanation handling for a reporting period.",
        reliability_rating=ReliabilityRating.USER_MANUAL_NOTE,
        notes="Example only; do not treat as SpaceX/FCC evidence.",
    )
    create_evidence_link(
        db,
        evidence_document_id=aggregate.id,
        reporting_period_start=date(2024, 12, 1),
        reporting_period_end=date(2025, 5, 31),
        claim_type="aggregate_deorbit_context",
        claim_text=(
            "Sample aggregate context for a reporting period. This is linked to the period, "
            "not asserted as the cause for each satellite."
        ),
        fact_vs_inference=FactLabel.AGGREGATE_EXPLANATION,
        confidence_level=ConfidenceLevel.LOW,
    )

    refresh_all_inferences(db)
    db.commit()

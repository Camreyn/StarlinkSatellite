from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import (
    ConfidenceLevel,
    DecayEvent,
    EvidenceDocument,
    EvidenceLink,
    FactLabel,
    LaunchEvent,
    OrbitalElement,
    ReliabilityRating,
    Satellite,
    SatelliteLaunchMembership,
)
from app.services.orbital_math import derive_orbit_values


def get_satellite_by_norad(db: Session, norad_cat_id: int) -> Satellite | None:
    return db.scalar(select(Satellite).where(Satellite.norad_cat_id == norad_cat_id))


def upsert_satellite(
    db: Session,
    *,
    norad_cat_id: int,
    object_name: str,
    starlink_name: str | None = None,
    international_designator: str | None = None,
    launch_date: date | None = None,
    decay_date: date | None = None,
    object_type: str | None = None,
    operational_status: str | None = None,
    generation_or_variant: str | None = None,
    launch_group: str | None = None,
    source_priority_status: str | None = None,
) -> tuple[Satellite, bool]:
    satellite = get_satellite_by_norad(db, norad_cat_id)
    created = satellite is None
    if satellite is None:
        satellite = Satellite(norad_cat_id=norad_cat_id, object_name=object_name)
        db.add(satellite)

    satellite.object_name = object_name or satellite.object_name
    satellite.starlink_name = (
        starlink_name if starlink_name is not None else satellite.starlink_name
    )
    satellite.international_designator = (
        international_designator
        if international_designator is not None
        else satellite.international_designator
    )
    satellite.launch_date = launch_date if launch_date is not None else satellite.launch_date
    satellite.decay_date = decay_date if decay_date is not None else satellite.decay_date
    satellite.object_type = object_type if object_type is not None else satellite.object_type
    satellite.operational_status = (
        operational_status if operational_status is not None else satellite.operational_status
    )
    satellite.generation_or_variant = (
        generation_or_variant
        if generation_or_variant is not None
        else satellite.generation_or_variant
    )
    satellite.launch_group = launch_group if launch_group is not None else satellite.launch_group
    satellite.source_priority_status = (
        source_priority_status
        if source_priority_status is not None
        else satellite.source_priority_status
    )
    db.flush()
    return satellite, created


def upsert_orbital_element(
    db: Session,
    *,
    satellite: Satellite,
    epoch: datetime,
    source_name: str,
    source_url: str | None,
    mean_motion: float | None,
    eccentricity: float | None,
    inclination: float | None,
    raan: float | None,
    arg_perigee: float | None,
    mean_anomaly: float | None,
    bstar: float | None,
    raw_json: dict[str, Any] | None = None,
    raw_tle_line_1: str | None = None,
    raw_tle_line_2: str | None = None,
) -> tuple[OrbitalElement, bool]:
    existing = db.scalar(
        select(OrbitalElement).where(
            OrbitalElement.satellite_id == satellite.id,
            OrbitalElement.epoch == epoch,
            OrbitalElement.source_name == source_name,
        )
    )
    created = existing is None
    element = existing or OrbitalElement(
        satellite_id=satellite.id, epoch=epoch, source_name=source_name
    )
    derived = derive_orbit_values(mean_motion, eccentricity)
    element.source_url = source_url
    element.mean_motion = mean_motion
    element.eccentricity = eccentricity
    element.inclination = inclination
    element.raan = raan
    element.arg_perigee = arg_perigee
    element.mean_anomaly = mean_anomaly
    element.bstar = bstar
    element.semimajor_axis_km = derived.semimajor_axis_km
    element.perigee_km = derived.perigee_km
    element.apogee_km = derived.apogee_km
    element.altitude_estimate_km = derived.altitude_estimate_km
    element.raw_json = raw_json
    element.raw_tle_line_1 = raw_tle_line_1
    element.raw_tle_line_2 = raw_tle_line_2
    if created:
        db.add(element)
    db.flush()
    return element, created


def upsert_decay_event(
    db: Session,
    *,
    satellite: Satellite,
    decay_date: date,
    decay_source_name: str,
    decay_source_url: str | None,
    decay_precision: str = "DAY",
    decay_status: str = "REENTERED",
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH,
    notes: str | None = None,
) -> tuple[DecayEvent, bool]:
    existing = db.scalar(
        select(DecayEvent).where(
            DecayEvent.satellite_id == satellite.id,
            DecayEvent.decay_date == decay_date,
            DecayEvent.decay_source_name == decay_source_name,
        )
    )
    created = existing is None
    event = existing or DecayEvent(
        satellite_id=satellite.id,
        decay_date=decay_date,
        decay_source_name=decay_source_name,
    )
    event.decay_precision = decay_precision
    event.decay_source_url = decay_source_url
    event.decay_status = decay_status
    event.confidence_level = confidence_level
    event.notes = notes
    if created:
        db.add(event)
    satellite.decay_date = decay_date
    db.flush()
    return event, created


def upsert_launch_event(
    db: Session,
    *,
    mission_name: str,
    launch_date: date | None,
    launch_vehicle: str | None = "Falcon 9",
    launch_site: str | None = None,
    source_name: str | None = None,
    source_url: str | None = None,
) -> LaunchEvent:
    event = db.scalar(select(LaunchEvent).where(LaunchEvent.mission_name == mission_name))
    if event is None:
        event = LaunchEvent(mission_name=mission_name)
        db.add(event)
    event.launch_date = launch_date or event.launch_date
    event.launch_vehicle = launch_vehicle or event.launch_vehicle
    event.launch_site = launch_site or event.launch_site
    event.source_name = source_name or event.source_name
    event.source_url = source_url or event.source_url
    db.flush()
    return event


def link_satellite_to_launch(db: Session, satellite: Satellite, launch_event: LaunchEvent) -> None:
    exists = db.scalar(
        select(SatelliteLaunchMembership).where(
            SatelliteLaunchMembership.satellite_id == satellite.id,
            SatelliteLaunchMembership.launch_event_id == launch_event.id,
        )
    )
    if exists is None:
        db.add(
            SatelliteLaunchMembership(
                satellite_id=satellite.id,
                launch_event_id=launch_event.id,
            )
        )
        db.flush()


def latest_orbital_element_subquery() -> Select[tuple[int, datetime]]:
    return select(
        OrbitalElement.satellite_id,
        OrbitalElement.epoch,
    )


def create_evidence_document(
    db: Session,
    *,
    title: str,
    source_name: str,
    reliability_rating: ReliabilityRating,
    source_url: str | None = None,
    published_date: date | None = None,
    document_type: str | None = None,
    local_file_path: str | None = None,
    summary: str | None = None,
    notes: str | None = None,
) -> EvidenceDocument:
    document = EvidenceDocument(
        title=title,
        source_name=source_name,
        source_url=source_url,
        published_date=published_date,
        document_type=document_type,
        local_file_path=local_file_path,
        summary=summary,
        reliability_rating=reliability_rating,
        notes=notes,
    )
    db.add(document)
    db.flush()
    return document


def create_evidence_link(
    db: Session,
    *,
    evidence_document_id: int,
    claim_type: str,
    claim_text: str,
    fact_vs_inference: FactLabel,
    confidence_level: ConfidenceLevel,
    satellite_id: int | None = None,
    launch_event_id: int | None = None,
    reporting_period_start: date | None = None,
    reporting_period_end: date | None = None,
) -> EvidenceLink:
    link = EvidenceLink(
        evidence_document_id=evidence_document_id,
        satellite_id=satellite_id,
        launch_event_id=launch_event_id,
        reporting_period_start=reporting_period_start,
        reporting_period_end=reporting_period_end,
        claim_type=claim_type,
        claim_text=claim_text,
        fact_vs_inference=fact_vs_inference,
        confidence_level=confidence_level,
    )
    db.add(link)
    db.flush()
    return link

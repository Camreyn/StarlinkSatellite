from __future__ import annotations

import logging
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestion.parsers import parse_gp_json, parse_satcat_csv, parse_tle_text
from app.models import ConfidenceLevel
from app.schemas.api import IngestResult
from app.services.inference import refresh_inference_for_satellite
from app.services.upsert import upsert_decay_event, upsert_orbital_element, upsert_satellite

logger = logging.getLogger(__name__)


def _starlink_name(object_name: str) -> str | None:
    return object_name.strip() if "STARLINK" in object_name.upper() else None


async def ingest_celestrak_active_starlink(db: Session) -> IngestResult:
    settings = get_settings()
    created = updated = 0
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(settings.celestrak_starlink_gp_url)
        response.raise_for_status()
        records = parse_gp_json(response.json())

    for record in records:
        satellite, was_created = upsert_satellite(
            db,
            norad_cat_id=record.norad_cat_id,
            object_name=record.object_name,
            starlink_name=_starlink_name(record.object_name),
            operational_status="ACTIVE",
            source_priority_status="CelesTrak GP active group",
        )
        _, element_created = upsert_orbital_element(
            db,
            satellite=satellite,
            epoch=record.epoch,
            source_name="CelesTrak GP",
            source_url=settings.celestrak_starlink_gp_url,
            mean_motion=record.mean_motion,
            eccentricity=record.eccentricity,
            inclination=record.inclination,
            raan=record.raan,
            arg_perigee=record.arg_perigee,
            mean_anomaly=record.mean_anomaly,
            bstar=record.bstar,
            raw_json=record.raw_json,
        )
        refresh_inference_for_satellite(db, satellite)
        created += int(was_created or element_created)
        updated += int(not was_created and not element_created)
    db.commit()
    return IngestResult(
        source="CelesTrak GP active Starlink",
        fetched=len(records),
        created=created,
        updated=updated,
    )


async def ingest_celestrak_active_starlink_tle(db: Session) -> IngestResult:
    settings = get_settings()
    created = updated = 0
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(settings.celestrak_starlink_tle_url)
        response.raise_for_status()
        records = parse_tle_text(response.text)
    for record in records:
        satellite, was_created = upsert_satellite(
            db,
            norad_cat_id=record.norad_cat_id,
            object_name=record.object_name,
            starlink_name=_starlink_name(record.object_name),
            operational_status="ACTIVE",
            source_priority_status="CelesTrak TLE active group",
        )
        _, element_created = upsert_orbital_element(
            db,
            satellite=satellite,
            epoch=record.epoch,
            source_name="CelesTrak TLE",
            source_url=settings.celestrak_starlink_tle_url,
            mean_motion=record.mean_motion,
            eccentricity=record.eccentricity,
            inclination=record.inclination,
            raan=record.raan,
            arg_perigee=record.arg_perigee,
            mean_anomaly=record.mean_anomaly,
            bstar=record.bstar,
            raw_tle_line_1=record.line1,
            raw_tle_line_2=record.line2,
        )
        refresh_inference_for_satellite(db, satellite)
        created += int(was_created or element_created)
        updated += int(not was_created and not element_created)
    db.commit()
    return IngestResult(
        source="CelesTrak TLE active Starlink",
        fetched=len(records),
        created=created,
        updated=updated,
    )


async def ingest_celestrak_satcat(db: Session) -> IngestResult:
    settings = get_settings()
    created = updated = decay_events = 0
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(settings.celestrak_satcat_url)
        response.raise_for_status()
        records = parse_satcat_csv(response.text)
    for record in records:
        satellite, was_created = upsert_satellite(
            db,
            norad_cat_id=record.norad_cat_id,
            object_name=record.object_name or f"STARLINK-{record.norad_cat_id}",
            starlink_name=record.object_name,
            international_designator=record.international_designator,
            launch_date=record.launch_date,
            decay_date=record.decay_date,
            object_type=record.object_type,
            operational_status=record.operational_status,
            source_priority_status="CelesTrak SATCAT",
        )
        if record.decay_date:
            _, decay_created = upsert_decay_event(
                db,
                satellite=satellite,
                decay_date=record.decay_date,
                decay_source_name="CelesTrak SATCAT",
                decay_source_url=settings.celestrak_satcat_url,
                confidence_level=ConfidenceLevel.HIGH,
                notes=(
                    "A public catalog gives this decay/reentry date. It supports the timing of "
                    "reentry, but it does not disclose the satellite-specific internal reason."
                ),
            )
            decay_events += int(decay_created)
        refresh_inference_for_satellite(db, satellite)
        created += int(was_created)
        updated += int(not was_created)
    db.commit()
    logger.info("CelesTrak SATCAT ingest completed at %s", datetime.utcnow().isoformat())
    return IngestResult(
        source="CelesTrak SATCAT",
        fetched=len(records),
        created=created + decay_events,
        updated=updated,
    )

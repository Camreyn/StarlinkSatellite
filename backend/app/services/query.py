from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.models import EvidenceLink, FactLabel, InferredCategory, OrbitalElement, Satellite
from app.schemas.api import SatelliteListItem


def satellite_to_list_item(db: Session, satellite: Satellite) -> SatelliteListItem:
    latest = db.scalar(
        select(OrbitalElement)
        .where(OrbitalElement.satellite_id == satellite.id)
        .order_by(OrbitalElement.epoch.desc())
        .limit(1)
    )
    inferred = db.scalar(
        select(InferredCategory)
        .where(InferredCategory.satellite_id == satellite.id)
        .order_by(InferredCategory.created_at.desc())
        .limit(1)
    )
    source_count = (
        db.scalar(
            select(func.count(EvidenceLink.id)).where(EvidenceLink.satellite_id == satellite.id)
        )
        or 0
    )
    direct_count = (
        db.scalar(
            select(func.count(EvidenceLink.id)).where(
                EvidenceLink.satellite_id == satellite.id,
                EvidenceLink.fact_vs_inference == FactLabel.FACT,
            )
        )
        or 0
    )
    inference_count = (
        db.scalar(
            select(func.count(EvidenceLink.id)).where(
                EvidenceLink.satellite_id == satellite.id,
                EvidenceLink.fact_vs_inference == FactLabel.INFERENCE,
            )
        )
        or 0
    )
    missing_explanation = bool(satellite.decay_date and source_count == 0)
    return SatelliteListItem(
        id=satellite.id,
        norad_cat_id=satellite.norad_cat_id,
        object_name=satellite.object_name,
        starlink_name=satellite.starlink_name,
        international_designator=satellite.international_designator,
        launch_date=satellite.launch_date,
        decay_date=satellite.decay_date,
        object_type=satellite.object_type,
        operational_status=satellite.operational_status,
        generation_or_variant=satellite.generation_or_variant,
        launch_group=satellite.launch_group,
        source_priority_status=satellite.source_priority_status,
        latest_altitude_estimate_km=latest.altitude_estimate_km if latest else None,
        inferred_category=inferred.category if inferred else None,
        inferred_confidence=inferred.confidence_level if inferred else None,
        sources_count=source_count,
        has_direct_source=direct_count > 0,
        has_inference_only=inference_count > 0 and direct_count == 0,
        missing_explanation=missing_explanation,
    )


def build_satellite_query(
    *,
    q: str | None = None,
    status: str | None = None,
    launch_date_from: date | None = None,
    launch_date_to: date | None = None,
    decay_date_from: date | None = None,
    decay_date_to: date | None = None,
    decayed_after: date | None = None,
    launch_group: str | None = None,
    generation: str | None = None,
) -> Select[tuple[Satellite]]:
    filters = []
    if q:
        like = f"%{q}%"
        q_filters: list[ColumnElement[bool]] = [
            Satellite.object_name.ilike(like),
            Satellite.starlink_name.ilike(like),
            Satellite.international_designator.ilike(like),
        ]
        if q.isdigit():
            q_filters.append(Satellite.norad_cat_id == int(q))
        filters.append(or_(*q_filters))
    if status:
        filters.append(Satellite.operational_status == status)
    if launch_date_from:
        filters.append(Satellite.launch_date >= launch_date_from)
    if launch_date_to:
        filters.append(Satellite.launch_date <= launch_date_to)
    if decay_date_from:
        filters.append(Satellite.decay_date >= decay_date_from)
    if decay_date_to:
        filters.append(Satellite.decay_date <= decay_date_to)
    if decayed_after:
        filters.append(Satellite.decay_date > decayed_after)
    if launch_group:
        filters.append(Satellite.launch_group == launch_group)
    if generation:
        filters.append(Satellite.generation_or_variant == generation)
    query = select(Satellite)
    if filters:
        query = query.where(and_(*filters))
    return query

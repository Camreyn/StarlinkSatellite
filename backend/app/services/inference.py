from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    ConfidenceLevel,
    EvidenceLink,
    FactLabel,
    InferredCategory,
    InferredCategoryValue,
    OrbitalElement,
    Satellite,
)

RULES_VERSION = "2026-05-24.v1"
OPERATIONAL_ALTITUDE_FLOOR_KM = 500.0


@dataclass(frozen=True)
class InferenceResult:
    category: InferredCategoryValue
    rationale: str
    confidence_level: ConfidenceLevel


def classify_satellite(db: Session, satellite: Satellite) -> InferenceResult:
    direct_decay_source = db.scalar(
        select(EvidenceLink).where(
            EvidenceLink.satellite_id == satellite.id,
            EvidenceLink.fact_vs_inference == FactLabel.FACT,
            EvidenceLink.claim_type.in_(["decay", "reentry", "status"]),
        )
    )
    latest_elements = db.scalars(
        select(OrbitalElement)
        .where(OrbitalElement.satellite_id == satellite.id)
        .order_by(OrbitalElement.epoch.desc())
        .limit(20)
    ).all()
    max_altitude = max(
        [
            element.altitude_estimate_km
            for element in latest_elements
            if element.altitude_estimate_km is not None
        ],
        default=None,
    )

    if satellite.decay_date:
        if direct_decay_source is not None:
            return InferenceResult(
                InferredCategoryValue.DECAYED_REENTERED,
                "A direct source record states a decay/reentry/status fact for this satellite.",
                ConfidenceLevel.HIGH,
            )
        if max_altitude is not None and max_altitude < OPERATIONAL_ALTITUDE_FLOOR_KM:
            return InferenceResult(
                InferredCategoryValue.POSSIBLE_FAILED_BEFORE_OPERATIONAL_ORBIT,
                (
                    "Decay date is present and stored orbital history never exceeds the configured "
                    f"{OPERATIONAL_ALTITUDE_FLOOR_KM:.0f} km operational-altitude screen. This is an "
                    "inference, not a disclosed internal cause."
                ),
                ConfidenceLevel.MEDIUM,
            )
        if satellite.generation_or_variant and "V1" in satellite.generation_or_variant.upper():
            return InferenceResult(
                InferredCategoryValue.POSSIBLE_OLDER_V1_RETIREMENT,
                (
                    "The satellite is labeled as an older V1-era object and has a decay date. "
                    "Any link to retirement planning remains inferential unless a source names this satellite."
                ),
                ConfidenceLevel.LOW,
            )
        return InferenceResult(
            InferredCategoryValue.DECAYED_REENTERED,
            "A decay date is present in catalog-style data. This is a lifecycle status, not a cause.",
            ConfidenceLevel.HIGH,
        )

    status = (satellite.operational_status or "").upper()
    if "ACTIVE" in status or "OPERATIONAL" in status:
        return InferenceResult(
            InferredCategoryValue.ACTIVE_ORBIT,
            "Operational status indicates active/on-orbit service in the stored source data.",
            ConfidenceLevel.MEDIUM,
        )

    return InferenceResult(
        InferredCategoryValue.UNKNOWN,
        "Stored public sources do not provide enough information to classify lifecycle state beyond unknown.",
        ConfidenceLevel.UNKNOWN,
    )


def refresh_inference_for_satellite(db: Session, satellite: Satellite) -> InferredCategory:
    result = classify_satellite(db, satellite)
    db.execute(delete(InferredCategory).where(InferredCategory.satellite_id == satellite.id))
    inferred = InferredCategory(
        satellite_id=satellite.id,
        category=result.category,
        rationale=result.rationale,
        confidence_level=result.confidence_level,
        created_from_rules_version=RULES_VERSION,
    )
    db.add(inferred)
    db.flush()
    return inferred


def refresh_all_inferences(db: Session) -> int:
    count = 0
    for satellite in db.scalars(select(Satellite)).all():
        refresh_inference_for_satellite(db, satellite)
        count += 1
    return count


def reporting_period_for_decay(decay_date: date) -> tuple[date, date]:
    year = decay_date.year
    if date(year, 6, 1) <= decay_date <= date(year, 11, 30):
        return date(year, 6, 1), date(year, 11, 30)
    if decay_date.month == 12:
        return date(year, 12, 1), date(year + 1, 5, 31)
    return date(year - 1, 12, 1), date(year, 5, 31)

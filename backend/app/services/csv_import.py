from __future__ import annotations

import csv
from datetime import date
from io import StringIO

from sqlalchemy.orm import Session

from app.models import ConfidenceLevel
from app.schemas.api import CsvImportPreview, CsvImportResult
from app.services.inference import refresh_inference_for_satellite
from app.services.upsert import upsert_decay_event, upsert_satellite

SUPPORTED_COLUMNS = {
    "norad_cat_id",
    "object_name",
    "starlink_name",
    "international_designator",
    "launch_date",
    "decay_date",
    "object_type",
    "operational_status",
    "generation_or_variant",
    "launch_group",
    "source_name",
    "source_url",
    "notes",
}
RECOMMENDED_COLUMNS = {"norad_cat_id", "object_name", "source_name"}


def _date_or_none(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value.strip()[:10])


def preview_manual_csv(text: str) -> CsvImportPreview:
    reader = csv.DictReader(StringIO(text))
    rows = list(reader)
    columns = set(reader.fieldnames or [])
    return CsvImportPreview(
        accepted_columns=sorted(columns & SUPPORTED_COLUMNS),
        missing_recommended_columns=sorted(RECOMMENDED_COLUMNS - columns),
        preview_rows=[{key: row.get(key) for key in sorted(columns)} for row in rows[:20]],
        row_count=len(rows),
    )


def import_manual_csv(db: Session, text: str) -> CsvImportResult:
    reader = csv.DictReader(StringIO(text))
    created = updated = 0
    warnings: list[str] = []
    for index, row in enumerate(reader, start=2):
        try:
            norad = int(row["norad_cat_id"])
        except (KeyError, TypeError, ValueError):
            warnings.append(f"Row {index}: missing or invalid norad_cat_id")
            continue
        satellite, was_created = upsert_satellite(
            db,
            norad_cat_id=norad,
            object_name=row.get("object_name") or row.get("starlink_name") or f"STARLINK-{norad}",
            starlink_name=row.get("starlink_name") or row.get("object_name"),
            international_designator=row.get("international_designator") or None,
            launch_date=_date_or_none(row.get("launch_date")),
            decay_date=_date_or_none(row.get("decay_date")),
            object_type=row.get("object_type") or None,
            operational_status=row.get("operational_status") or None,
            generation_or_variant=row.get("generation_or_variant") or None,
            launch_group=row.get("launch_group") or None,
            source_priority_status=row.get("source_name") or "manual CSV",
        )
        if row.get("decay_date"):
            upsert_decay_event(
                db,
                satellite=satellite,
                decay_date=_date_or_none(row.get("decay_date")),  # type: ignore[arg-type]
                decay_source_name=row.get("source_name") or "manual CSV",
                decay_source_url=row.get("source_url") or None,
                confidence_level=ConfidenceLevel.MEDIUM,
                notes=row.get("notes") or "Manual import; review supporting evidence.",
            )
        refresh_inference_for_satellite(db, satellite)
        created += int(was_created)
        updated += int(not was_created)
    db.commit()
    return CsvImportResult(
        row_count=created + updated, created=created, updated=updated, warnings=warnings
    )

from __future__ import annotations

import csv
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Satellite
from app.services.query import satellite_to_list_item


def export_satellites_csv(db: Session) -> str:
    output = StringIO()
    fieldnames = [
        "norad_cat_id",
        "object_name",
        "international_designator",
        "launch_date",
        "decay_date",
        "operational_status",
        "launch_group",
        "generation_or_variant",
        "latest_altitude_estimate_km",
        "inferred_category",
        "inferred_confidence",
        "sources_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    satellites = db.scalars(select(Satellite).order_by(Satellite.norad_cat_id)).all()
    for satellite in satellites:
        item = satellite_to_list_item(db, satellite)
        writer.writerow({field: getattr(item, field) for field in fieldnames})
    return output.getvalue()


def export_markdown_report(db: Session) -> str:
    satellites = db.scalars(
        select(Satellite)
        .options(
            selectinload(Satellite.evidence_links),
            selectinload(Satellite.inferred_categories),
            selectinload(Satellite.decay_events),
        )
        .order_by(Satellite.decay_date.desc().nullslast(), Satellite.norad_cat_id)
    ).all()
    lines = [
        "# Starlink Lifecycle Research Report",
        "",
        "> Public satellite-tracking data can usually show which satellite reentered and when. "
        "It generally does not provide a definitive public per-satellite internal reason for deorbit. "
        "This report distinguishes sourced facts from computed values and inferences.",
        "",
        "| NORAD | Name | Launch | Decay | Category | Label | Confidence | Sources |",
        "|---:|---|---|---|---|---|---|---:|",
    ]
    for satellite in satellites:
        category = satellite.inferred_categories[0] if satellite.inferred_categories else None
        labels = sorted({link.fact_vs_inference.value for link in satellite.evidence_links})
        lines.append(
            "| {norad} | {name} | {launch} | {decay} | {category} | {label} | {confidence} | {sources} |".format(
                norad=satellite.norad_cat_id,
                name=satellite.object_name.replace("|", "\\|"),
                launch=satellite.launch_date or "",
                decay=satellite.decay_date or "",
                category=category.category.value if category else "",
                label=", ".join(labels) if labels else "INFERENCE" if category else "",
                confidence=category.confidence_level.value if category else "",
                sources=len(satellite.evidence_links),
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `FACT` means a stored source directly supports the claim.",
            "- `AGGREGATE_EXPLANATION` means a source discusses a group or period, not a proven cause for each satellite.",
            "- `COMPUTED` values are derived from stored orbital elements.",
            "- `INFERENCE` values are rule-generated and are not a direct disclosed internal cause.",
        ]
    )
    return "\n".join(lines) + "\n"

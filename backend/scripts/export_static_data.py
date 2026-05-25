from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.routes import timeline
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.ingestion.celestrak import ingest_celestrak_active_starlink, ingest_celestrak_satcat
from app.models import (
    EvidenceDocument,
    EvidenceLink,
    InferredCategory,
    OrbitalElement,
    Satellite,
    SatelliteLaunchMembership,
)
from app.schemas.api import DashboardSummary, EvidenceDocumentRead, SatelliteDetail
from app.services.export import export_markdown_report, export_satellites_csv
from app.services.query import satellite_to_list_item


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


async def ingest_public_data() -> None:
    with SessionLocal() as db:
        init_db(db, seed=False)
        await ingest_celestrak_active_starlink(db)
        await ingest_celestrak_satcat(db)


def build_dashboard_summary(db) -> DashboardSummary:
    total = db.scalar(select(func.count(Satellite.id))) or 0
    active_ids = (
        select(OrbitalElement.satellite_id)
        .join(Satellite, Satellite.id == OrbitalElement.satellite_id)
        .where(Satellite.decay_date.is_(None))
        .distinct()
        .subquery()
    )
    active = db.scalar(select(func.count()).select_from(active_ids)) or 0
    decayed = db.scalar(select(func.count(Satellite.id)).where(Satellite.decay_date.is_not(None))) or 0
    post_election = db.scalar(
        select(func.count(Satellite.id)).where(Satellite.decay_date > date(2024, 11, 5))
    ) or 0
    reporting = (
        db.scalar(
            select(func.count(Satellite.id)).where(
                Satellite.decay_date >= date(2024, 12, 1),
                Satellite.decay_date <= date(2025, 5, 31),
            )
        )
        or 0
    )
    linked_fact_ids = select(EvidenceLink.satellite_id).where(
        EvidenceLink.satellite_id.is_not(None),
        EvidenceLink.fact_vs_inference.in_(["FACT", "AGGREGATE_EXPLANATION"]),
    )
    missing_reason = (
        db.scalar(
            select(func.count(Satellite.id)).where(
                Satellite.decay_date.is_not(None),
                Satellite.id.not_in(linked_fact_ids),
            )
        )
        or 0
    )
    inferred_only = (
        db.scalar(
            select(func.count(Satellite.id))
            .join(InferredCategory)
            .where(Satellite.id.not_in(linked_fact_ids))
        )
        or 0
    )
    latest_refresh = db.scalar(select(func.max(OrbitalElement.fetched_at)))
    return DashboardSummary(
        total_satellites=total,
        active_count=active,
        decayed_reentered_count=decayed,
        decayed_after_2024_11_05_count=post_election,
        decayed_dec_2024_through_may_2025_count=reporting,
        satellites_missing_decay_reason=missing_reason,
        satellites_with_inferred_category_only=inferred_only,
        last_data_refresh_time=latest_refresh,
    )


def satellite_detail(db, satellite: Satellite) -> SatelliteDetail:
    evidence_documents = []
    seen: set[int] = set()
    for link in satellite.evidence_links:
        if link.evidence_document and link.evidence_document_id not in seen:
            evidence_documents.append(link.evidence_document)
            seen.add(link.evidence_document_id)
    return SatelliteDetail(
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
        orbital_elements=sorted(satellite.orbital_elements, key=lambda item: item.epoch),
        decay_events=satellite.decay_events,
        launch_events=[membership.launch_event for membership in satellite.launch_memberships],
        evidence_documents=evidence_documents,
        inferred_categories=satellite.inferred_categories,
    )


def export_static_data(output_dir: Path) -> None:
    with SessionLocal() as db:
        init_db(db, seed=False)
        satellites = db.scalars(select(Satellite).order_by(Satellite.norad_cat_id)).all()
        write_json(
            output_dir / "dashboard-summary.json",
            build_dashboard_summary(db).model_dump(mode="json"),
        )
        write_json(
            output_dir / "satellites.json",
            [satellite_to_list_item(db, satellite).model_dump(mode="json") for satellite in satellites],
        )
        full_satellites = db.scalars(
            select(Satellite)
            .options(
                selectinload(Satellite.orbital_elements),
                selectinload(Satellite.decay_events),
                selectinload(Satellite.inferred_categories),
                selectinload(Satellite.launch_memberships).selectinload(
                    SatelliteLaunchMembership.launch_event
                ),
                selectinload(Satellite.evidence_links).selectinload(EvidenceLink.evidence_document),
            )
            .order_by(Satellite.norad_cat_id)
        ).all()
        write_json(
            output_dir / "satellite-details.json",
            {
                str(satellite.norad_cat_id): satellite_detail(db, satellite).model_dump(mode="json")
                for satellite in full_satellites
            },
        )
        write_json(
            output_dir / "orbital-history.json",
            {
                str(satellite.norad_cat_id): [
                    {
                        "epoch": element.epoch.isoformat(),
                        "altitude_estimate_km": element.altitude_estimate_km,
                        "perigee_km": element.perigee_km,
                        "apogee_km": element.apogee_km,
                        "source_name": element.source_name,
                    }
                    for element in sorted(satellite.orbital_elements, key=lambda item: item.epoch)
                ]
                for satellite in full_satellites
            },
        )
        write_json(
            output_dir / "evidence.json",
            [
                EvidenceDocumentRead.model_validate(document).model_dump(mode="json")
                for document in db.scalars(
                    select(EvidenceDocument).options(selectinload(EvidenceDocument.evidence_links))
                ).all()
            ],
        )
        write_json(
            output_dir / "timeline.json",
            [event.model_dump(mode="json") for event in timeline(db)],
        )
        (output_dir / "satellites.csv").write_text(export_satellites_csv(db), encoding="utf-8")
        (output_dir / "report.md").write_text(export_markdown_report(db), encoding="utf-8")

        with (output_dir / "snapshot-summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
            writer.writeheader()
            summary = build_dashboard_summary(db).model_dump(mode="json")
            for key, value in summary.items():
                writer.writerow({"metric": key, "value": value})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true", help="Fetch fresh CelesTrak data first.")
    parser.add_argument(
        "--out",
        default="../frontend/public/static-data",
        help="Output directory for static JSON/CSV/Markdown assets.",
    )
    args = parser.parse_args()
    if args.ingest:
        asyncio.run(ingest_public_data())
    export_static_data(Path(args.out))


if __name__ == "__main__":
    main()

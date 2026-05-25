from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.ingestion.celestrak import ingest_celestrak_active_starlink, ingest_celestrak_satcat
from app.ingestion.planet4589 import ingest_planet4589_starlink_stats
from app.ingestion.spacetrack import ingest_spacetrack_data
from app.models import (
    EvidenceDocument,
    EvidenceLink,
    FactLabel,
    InferredCategory,
    LaunchEvent,
    OrbitalElement,
    Satellite,
    SatelliteLaunchMembership,
)
from app.schemas.api import (
    CsvImportPreview,
    CsvImportResult,
    DashboardSummary,
    EvidenceDocumentCreate,
    EvidenceDocumentRead,
    EvidenceLinkCreate,
    EvidenceLinkRead,
    IngestResult,
    PaginatedSatellites,
    SatelliteDetail,
    TimelineEvent,
)
from app.services.csv_import import import_manual_csv, preview_manual_csv
from app.services.export import export_markdown_report, export_satellites_csv
from app.services.inference import refresh_all_inferences
from app.services.query import build_satellite_query, satellite_to_list_item
from app.services.upsert import (
    create_evidence_document,
    create_evidence_link,
    get_satellite_by_norad,
)

router = APIRouter(prefix="/api")

POST_ELECTION_DATE = date(2024, 11, 5)
REPORTING_DEC_2024_START = date(2024, 12, 1)
REPORTING_MAY_2025_END = date(2025, 5, 31)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/satellites", response_model=PaginatedSatellites)
def list_satellites(
    db: Session = Depends(get_db),
    q: str | None = None,
    status: str | None = None,
    launch_date_from: date | None = None,
    launch_date_to: date | None = None,
    decay_date_from: date | None = None,
    decay_date_to: date | None = None,
    decayed_after: date | None = None,
    launch_group: str | None = None,
    generation: str | None = None,
    inferred_category: str | None = None,
    fact_vs_inference: FactLabel | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=250),
    sort: str = "norad_cat_id:asc",
) -> PaginatedSatellites:
    query = build_satellite_query(
        q=q,
        status=status,
        launch_date_from=launch_date_from,
        launch_date_to=launch_date_to,
        decay_date_from=decay_date_from,
        decay_date_to=decay_date_to,
        decayed_after=decayed_after,
        launch_group=launch_group,
        generation=generation,
    )
    if inferred_category:
        query = query.join(InferredCategory).where(InferredCategory.category == inferred_category)
    if fact_vs_inference:
        query = query.join(EvidenceLink).where(EvidenceLink.fact_vs_inference == fact_vs_inference)

    sort_field, _, sort_dir = sort.partition(":")
    sort_column = getattr(Satellite, sort_field, Satellite.norad_cat_id)
    query = query.order_by(sort_column.desc() if sort_dir == "desc" else sort_column.asc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    satellites = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return PaginatedSatellites(
        items=[satellite_to_list_item(db, satellite) for satellite in satellites],
        total=total,
        page=page,
        page_size=page_size,
    )


def _satellite_detail_or_404(db: Session, norad_cat_id: int) -> Satellite:
    satellite = db.scalar(
        select(Satellite)
        .where(Satellite.norad_cat_id == norad_cat_id)
        .options(
            selectinload(Satellite.orbital_elements),
            selectinload(Satellite.decay_events),
            selectinload(Satellite.inferred_categories),
            selectinload(Satellite.launch_memberships).selectinload(
                SatelliteLaunchMembership.launch_event
            ),
            selectinload(Satellite.evidence_links)
            .selectinload(EvidenceLink.evidence_document)
            .selectinload(EvidenceDocument.evidence_links),
        )
    )
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return satellite


@router.get("/satellites/{norad_cat_id}", response_model=SatelliteDetail)
def get_satellite(norad_cat_id: int, db: Session = Depends(get_db)) -> SatelliteDetail:
    satellite = _satellite_detail_or_404(db, norad_cat_id)
    evidence_documents = []
    seen: set[int] = set()
    for link in satellite.evidence_links:
        if link.evidence_document_id not in seen:
            evidence_documents.append(link.evidence_document)
            seen.add(link.evidence_document_id)
    launch_events = [membership.launch_event for membership in satellite.launch_memberships]
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
        launch_events=launch_events,
        evidence_documents=evidence_documents,
        inferred_categories=satellite.inferred_categories,
    )


@router.get("/satellites/{norad_cat_id}/orbital-history")
def get_orbital_history(
    norad_cat_id: int, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    satellite = get_satellite_by_norad(db, norad_cat_id)
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    elements = db.scalars(
        select(OrbitalElement)
        .where(OrbitalElement.satellite_id == satellite.id)
        .order_by(OrbitalElement.epoch)
    ).all()
    return [
        {
            "epoch": element.epoch,
            "altitude_estimate_km": element.altitude_estimate_km,
            "perigee_km": element.perigee_km,
            "apogee_km": element.apogee_km,
            "source_name": element.source_name,
        }
        for element in elements
    ]


@router.get("/satellites/{norad_cat_id}/evidence", response_model=list[EvidenceDocumentRead])
def get_satellite_evidence(
    norad_cat_id: int, db: Session = Depends(get_db)
) -> list[EvidenceDocument]:
    satellite = get_satellite_by_norad(db, norad_cat_id)
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return list(
        db.scalars(
            select(EvidenceDocument)
            .join(EvidenceLink)
            .where(EvidenceLink.satellite_id == satellite.id)
            .options(selectinload(EvidenceDocument.evidence_links))
        )
        .unique()
        .all()
    )


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    total = db.scalar(select(func.count(Satellite.id))) or 0
    active_orbital_satellite_ids = (
        select(OrbitalElement.satellite_id)
        .join(Satellite, Satellite.id == OrbitalElement.satellite_id)
        .where(Satellite.decay_date.is_(None))
        .distinct()
        .subquery()
    )
    active = db.scalar(select(func.count()).select_from(active_orbital_satellite_ids)) or 0
    decayed = (
        db.scalar(select(func.count(Satellite.id)).where(Satellite.decay_date.is_not(None))) or 0
    )
    post_election = (
        db.scalar(select(func.count(Satellite.id)).where(Satellite.decay_date > POST_ELECTION_DATE))
        or 0
    )
    reporting = (
        db.scalar(
            select(func.count(Satellite.id)).where(
                Satellite.decay_date >= REPORTING_DEC_2024_START,
                Satellite.decay_date <= REPORTING_MAY_2025_END,
            )
        )
        or 0
    )
    linked_fact_satellite_ids = select(EvidenceLink.satellite_id).where(
        EvidenceLink.satellite_id.is_not(None),
        EvidenceLink.fact_vs_inference.in_([FactLabel.FACT, FactLabel.AGGREGATE_EXPLANATION]),
    )
    missing_reason = (
        db.scalar(
            select(func.count(Satellite.id)).where(
                Satellite.decay_date.is_not(None),
                Satellite.id.not_in(linked_fact_satellite_ids),
            )
        )
        or 0
    )
    inferred_only = (
        db.scalar(
            select(func.count(Satellite.id))
            .join(InferredCategory)
            .where(Satellite.id.not_in(linked_fact_satellite_ids))
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


@router.get("/timeline", response_model=list[TimelineEvent])
def timeline(db: Session = Depends(get_db)) -> list[TimelineEvent]:
    events: list[TimelineEvent] = [
        TimelineEvent(
            id="marker-election-2024",
            date=POST_ELECTION_DATE,
            type="marker",
            title="U.S. election",
            description="Custom marker: November 5, 2024",
        ),
        TimelineEvent(
            id="marker-reporting-dec-2024",
            date=REPORTING_DEC_2024_START,
            type="marker",
            title="FCC reporting period start",
            description="Custom marker: December 1, 2024",
        ),
    ]
    for launch in db.scalars(select(LaunchEvent).where(LaunchEvent.launch_date.is_not(None))).all():
        events.append(
            TimelineEvent(
                id=f"launch-{launch.id}",
                date=launch.launch_date,
                type="launch",
                title=launch.mission_name,
                source_name=launch.source_name,
                fact_vs_inference=FactLabel.FACT,
            )
        )
    for sat in db.scalars(select(Satellite).where(Satellite.decay_date.is_not(None))).all():
        events.append(
            TimelineEvent(
                id=f"decay-{sat.norad_cat_id}",
                date=sat.decay_date,
                type="decay",
                title=f"{sat.object_name} decay/reentry",
                description=(
                    "A public catalog lists this satellite as having decayed or reentered on this "
                    "date. That tells us when it came down; it does not tell us SpaceX's internal "
                    "reason for deorbiting it."
                ),
                source_name=sat.source_priority_status,
                fact_vs_inference=FactLabel.FACT,
            )
        )
    for doc in db.scalars(
        select(EvidenceDocument).where(EvidenceDocument.published_date.is_not(None))
    ).all():
        events.append(
            TimelineEvent(
                id=f"evidence-{doc.id}",
                date=doc.published_date,
                type="evidence",
                title=doc.title,
                source_name=doc.source_name,
            )
        )
    return sorted(events, key=lambda event: event.date)


@router.post("/ingest/celestrak/starlink", response_model=IngestResult)
async def ingest_starlink(db: Session = Depends(get_db)) -> IngestResult:
    return await ingest_celestrak_active_starlink(db)


@router.post("/ingest/celestrak/satcat", response_model=IngestResult)
async def ingest_satcat(db: Session = Depends(get_db)) -> IngestResult:
    return await ingest_celestrak_satcat(db)


@router.post("/ingest/spacetrack", response_model=IngestResult)
async def ingest_spacetrack(db: Session = Depends(get_db)) -> IngestResult:
    return await ingest_spacetrack_data(db)


@router.post("/ingest/planet4589", response_model=IngestResult)
async def ingest_planet4589(db: Session = Depends(get_db)) -> IngestResult:
    return await ingest_planet4589_starlink_stats(db)


@router.post("/import/csv/preview", response_model=CsvImportPreview)
async def import_csv_preview(file: UploadFile = File(...)) -> CsvImportPreview:
    content = (await file.read()).decode("utf-8-sig")
    return preview_manual_csv(content)


@router.post("/import/csv", response_model=CsvImportResult)
async def import_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> CsvImportResult:
    content = (await file.read()).decode("utf-8-sig")
    return import_manual_csv(db, content)


@router.get("/evidence", response_model=list[EvidenceDocumentRead])
def list_evidence(db: Session = Depends(get_db)) -> list[EvidenceDocument]:
    return list(
        db.scalars(
            select(EvidenceDocument)
            .options(selectinload(EvidenceDocument.evidence_links))
            .order_by(
                EvidenceDocument.published_date.desc().nullslast(), EvidenceDocument.id.desc()
            )
        ).all()
    )


@router.post("/evidence", response_model=EvidenceDocumentRead)
def add_evidence(
    payload: EvidenceDocumentCreate, db: Session = Depends(get_db)
) -> EvidenceDocument:
    doc = create_evidence_document(db, **payload.model_dump())
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/evidence/links", response_model=EvidenceLinkRead)
def add_evidence_link(payload: EvidenceLinkCreate, db: Session = Depends(get_db)) -> EvidenceLink:
    satellite_id = None
    if payload.satellite_norad_cat_id is not None:
        satellite = get_satellite_by_norad(db, payload.satellite_norad_cat_id)
        if satellite is None:
            raise HTTPException(status_code=404, detail="Satellite not found")
        satellite_id = satellite.id
    link = create_evidence_link(
        db,
        evidence_document_id=payload.evidence_document_id,
        satellite_id=satellite_id,
        launch_event_id=payload.launch_event_id,
        reporting_period_start=payload.reporting_period_start,
        reporting_period_end=payload.reporting_period_end,
        claim_type=payload.claim_type,
        claim_text=payload.claim_text,
        fact_vs_inference=payload.fact_vs_inference,
        confidence_level=payload.confidence_level,
    )
    db.commit()
    db.refresh(link)
    refresh_all_inferences(db)
    db.commit()
    return link


@router.delete("/evidence/{document_id}", status_code=204)
def delete_evidence(document_id: int, db: Session = Depends(get_db)) -> Response:
    db.execute(delete(EvidenceDocument).where(EvidenceDocument.id == document_id))
    db.commit()
    return Response(status_code=204)


@router.get("/export/satellites.csv")
def export_csv(db: Session = Depends(get_db)) -> Response:
    return Response(
        content=export_satellites_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="starlink_satellites.csv"'},
    )


@router.get("/export/report.md", response_class=PlainTextResponse)
def export_report(db: Session = Depends(get_db)) -> str:
    return export_markdown_report(db)

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InferredCategory, InferredCategoryValue, Satellite
from app.services.csv_import import import_manual_csv
from app.services.export import export_markdown_report, export_satellites_csv
from app.services.inference import refresh_inference_for_satellite
from app.services.query import build_satellite_query
from app.services.upsert import upsert_decay_event, upsert_orbital_element, upsert_satellite


def test_satellite_upsert_logic(db: Session) -> None:
    sat, created = upsert_satellite(db, norad_cat_id=1, object_name="STARLINK-1")
    assert created is True
    sat2, created2 = upsert_satellite(
        db, norad_cat_id=1, object_name="STARLINK-1B", operational_status="ACTIVE"
    )
    assert created2 is False
    assert sat.id == sat2.id
    assert sat2.object_name == "STARLINK-1B"
    assert sat2.operational_status == "ACTIVE"


def test_decay_date_filtering_and_post_election(db: Session) -> None:
    sat, _ = upsert_satellite(
        db, norad_cat_id=2, object_name="STARLINK-2", decay_date=date(2024, 12, 8)
    )
    upsert_decay_event(
        db,
        satellite=sat,
        decay_date=date(2024, 12, 8),
        decay_source_name="test",
        decay_source_url=None,
    )
    upsert_satellite(db, norad_cat_id=3, object_name="STARLINK-3", decay_date=date(2024, 10, 1))
    query = build_satellite_query(decayed_after=date(2024, 11, 5))
    rows = db.scalars(query).all()
    assert [row.norad_cat_id for row in rows] == [2]


def test_reporting_period_filter_december_through_may(db: Session) -> None:
    upsert_satellite(db, norad_cat_id=4, object_name="STARLINK-4", decay_date=date(2025, 5, 31))
    upsert_satellite(db, norad_cat_id=5, object_name="STARLINK-5", decay_date=date(2025, 6, 1))
    query = build_satellite_query(
        decay_date_from=date(2024, 12, 1), decay_date_to=date(2025, 5, 31)
    )
    assert [row.norad_cat_id for row in db.scalars(query).all()] == [4]


def test_inference_rules_do_not_mark_inferred_causes_as_facts(db: Session) -> None:
    sat, _ = upsert_satellite(
        db,
        norad_cat_id=6,
        object_name="STARLINK-6",
        decay_date=date(2025, 2, 1),
        generation_or_variant="V1.0",
    )
    inferred = refresh_inference_for_satellite(db, sat)
    assert inferred.category == InferredCategoryValue.POSSIBLE_OLDER_V1_RETIREMENT
    assert (
        db.scalar(select(InferredCategory).where(InferredCategory.satellite_id == sat.id))
        is not None
    )


def test_orbital_computation_from_mean_motion(db: Session) -> None:
    sat, _ = upsert_satellite(db, norad_cat_id=7, object_name="STARLINK-7")
    element, _ = upsert_orbital_element(
        db,
        satellite=sat,
        epoch=datetime(2024, 1, 1),
        source_name="test",
        source_url=None,
        mean_motion=15.1,
        eccentricity=0.0001,
        inclination=53.0,
        raan=0,
        arg_perigee=0,
        mean_anomaly=0,
        bstar=None,
    )
    assert element.altitude_estimate_km is not None
    assert element.altitude_estimate_km > 300


def test_csv_export_and_markdown_report_export(db: Session) -> None:
    sat, _ = upsert_satellite(
        db, norad_cat_id=8, object_name="STARLINK-8", decay_date=date(2024, 12, 9)
    )
    refresh_inference_for_satellite(db, sat)
    csv_text = export_satellites_csv(db)
    report = export_markdown_report(db)
    assert "STARLINK-8" in csv_text
    assert "FACT" in report or "INFERENCE" in report
    assert "not a direct disclosed internal cause" in report


def test_manual_csv_import(db: Session) -> None:
    result = import_manual_csv(
        db,
        "norad_cat_id,object_name,decay_date,source_name\n9,STARLINK-9,2024-12-10,manual\n",
    )
    assert result.created == 1
    assert db.scalar(select(Satellite).where(Satellite.norad_cat_id == 9)) is not None

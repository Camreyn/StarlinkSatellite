from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FactLabel(StrEnum):
    FACT = "FACT"
    AGGREGATE_EXPLANATION = "AGGREGATE_EXPLANATION"
    COMPUTED = "COMPUTED"
    INFERENCE = "INFERENCE"


class ReliabilityRating(StrEnum):
    PRIMARY_REGULATORY = "PRIMARY_REGULATORY"
    PRIMARY_OPERATOR = "PRIMARY_OPERATOR"
    OFFICIAL_CATALOG = "OFFICIAL_CATALOG"
    EXPERT_TRACKER = "EXPERT_TRACKER"
    INDUSTRY_MEDIA = "INDUSTRY_MEDIA"
    USER_MANUAL_NOTE = "USER_MANUAL_NOTE"


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class InferredCategoryValue(StrEnum):
    ACTIVE_ORBIT = "ACTIVE_ORBIT"
    DECAYED_REENTERED = "DECAYED_REENTERED"
    EARLY_DEORBIT = "EARLY_DEORBIT"
    POSSIBLE_FAILED_BEFORE_OPERATIONAL_ORBIT = "POSSIBLE_FAILED_BEFORE_OPERATIONAL_ORBIT"
    POSSIBLE_PLANNED_RETIREMENT = "POSSIBLE_PLANNED_RETIREMENT"
    POSSIBLE_OLDER_V1_RETIREMENT = "POSSIBLE_OLDER_V1_RETIREMENT"
    UNKNOWN = "UNKNOWN"


class Satellite(Base):
    __tablename__ = "satellites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    norad_cat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    object_name: Mapped[str] = mapped_column(String(255), index=True)
    starlink_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    international_designator: Mapped[str | None] = mapped_column(String(64), nullable=True)
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    decay_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    object_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operational_status: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    generation_or_variant: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    launch_group: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_priority_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    orbital_elements: Mapped[list["OrbitalElement"]] = relationship(
        back_populates="satellite", cascade="all, delete-orphan"
    )
    decay_events: Mapped[list["DecayEvent"]] = relationship(
        back_populates="satellite", cascade="all, delete-orphan"
    )
    launch_memberships: Mapped[list["SatelliteLaunchMembership"]] = relationship(
        back_populates="satellite", cascade="all, delete-orphan"
    )
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(back_populates="satellite")
    inferred_categories: Mapped[list["InferredCategory"]] = relationship(
        back_populates="satellite", cascade="all, delete-orphan"
    )


class OrbitalElement(Base):
    __tablename__ = "orbital_elements"
    __table_args__ = (
        UniqueConstraint("satellite_id", "epoch", "source_name", name="uq_orbital_epoch_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[int] = mapped_column(ForeignKey("satellites.id"), index=True)
    epoch: Mapped[datetime] = mapped_column(DateTime, index=True)
    mean_motion: Mapped[float | None] = mapped_column(Float, nullable=True)
    eccentricity: Mapped[float | None] = mapped_column(Float, nullable=True)
    inclination: Mapped[float | None] = mapped_column(Float, nullable=True)
    raan: Mapped[float | None] = mapped_column(Float, nullable=True)
    arg_perigee: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_anomaly: Mapped[float | None] = mapped_column(Float, nullable=True)
    bstar: Mapped[float | None] = mapped_column(Float, nullable=True)
    semimajor_axis_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    perigee_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    apogee_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_estimate_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_tle_line_1: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_tle_line_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source_name: Mapped[str] = mapped_column(String(128), index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    satellite: Mapped[Satellite] = relationship(back_populates="orbital_elements")


class DecayEvent(Base):
    __tablename__ = "decay_events"
    __table_args__ = (
        UniqueConstraint("satellite_id", "decay_date", "decay_source_name", name="uq_decay_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[int] = mapped_column(ForeignKey("satellites.id"), index=True)
    decay_date: Mapped[date] = mapped_column(Date, index=True)
    decay_precision: Mapped[str] = mapped_column(String(64), default="DAY")
    decay_source_name: Mapped[str] = mapped_column(String(128))
    decay_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    decay_status: Mapped[str] = mapped_column(String(128), default="REENTERED")
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel), default=ConfidenceLevel.HIGH
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    satellite: Mapped[Satellite] = relationship(back_populates="decay_events")


class LaunchEvent(Base):
    __tablename__ = "launch_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mission_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    launch_vehicle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    launch_site: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    satellite_memberships: Mapped[list["SatelliteLaunchMembership"]] = relationship(
        back_populates="launch_event", cascade="all, delete-orphan"
    )
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(back_populates="launch_event")


class SatelliteLaunchMembership(Base):
    __tablename__ = "satellite_launch_membership"
    __table_args__ = (
        UniqueConstraint("satellite_id", "launch_event_id", name="uq_satellite_launch"),
    )

    satellite_id: Mapped[int] = mapped_column(ForeignKey("satellites.id"), primary_key=True)
    launch_event_id: Mapped[int] = mapped_column(ForeignKey("launch_events.id"), primary_key=True)

    satellite: Mapped[Satellite] = relationship(back_populates="launch_memberships")
    launch_event: Mapped[LaunchEvent] = relationship(back_populates="satellite_memberships")


class EvidenceDocument(Base):
    __tablename__ = "evidence_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    document_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    local_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reliability_rating: Mapped[ReliabilityRating] = mapped_column(Enum(ReliabilityRating))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence_links: Mapped[list["EvidenceLink"]] = relationship(
        back_populates="evidence_document", cascade="all, delete-orphan"
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_document_id: Mapped[int] = mapped_column(ForeignKey("evidence_documents.id"))
    satellite_id: Mapped[int | None] = mapped_column(ForeignKey("satellites.id"), nullable=True)
    launch_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("launch_events.id"), nullable=True
    )
    reporting_period_start: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    reporting_period_end: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    claim_type: Mapped[str] = mapped_column(String(128), index=True)
    claim_text: Mapped[str] = mapped_column(Text)
    fact_vs_inference: Mapped[FactLabel] = mapped_column(Enum(FactLabel), index=True)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel), default=ConfidenceLevel.UNKNOWN
    )

    evidence_document: Mapped[EvidenceDocument] = relationship(back_populates="evidence_links")
    satellite: Mapped[Satellite | None] = relationship(back_populates="evidence_links")
    launch_event: Mapped[LaunchEvent | None] = relationship(back_populates="evidence_links")


class InferredCategory(Base):
    __tablename__ = "inferred_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[int] = mapped_column(ForeignKey("satellites.id"), index=True)
    category: Mapped[InferredCategoryValue] = mapped_column(Enum(InferredCategoryValue), index=True)
    rationale: Mapped[str] = mapped_column(Text)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel), default=ConfidenceLevel.UNKNOWN
    )
    created_from_rules_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    satellite: Mapped[Satellite] = relationship(back_populates="inferred_categories")

from __future__ import annotations

import re

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ConfidenceLevel, FactLabel, ReliabilityRating
from app.schemas.api import IngestResult
from app.services.upsert import create_evidence_document, create_evidence_link


async def ingest_planet4589_starlink_stats(db: Session) -> IngestResult:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(settings.planet4589_starlink_stats_url)
        response.raise_for_status()
        text = response.text

    title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Jonathan McDowell Starlink statistics"
    document = create_evidence_document(
        db,
        title=title,
        source_name="Jonathan McDowell / planet4589",
        source_url=settings.planet4589_starlink_stats_url,
        document_type="expert tracker web page",
        summary=(
            "Independent expert tracker page for Starlink statistics. Use as cross-checking evidence; "
            "page format may require manual extraction for per-satellite fields."
        ),
        reliability_rating=ReliabilityRating.EXPERT_TRACKER,
        notes="Imported page metadata; per-row parsing should be reviewed before field-level upserts.",
    )
    create_evidence_link(
        db,
        evidence_document_id=document.id,
        claim_type="source_reference",
        claim_text="Planet4589 page is available as an expert tracker reference for Starlink status cross-checking.",
        fact_vs_inference=FactLabel.FACT,
        confidence_level=ConfidenceLevel.HIGH,
    )
    db.commit()
    return IngestResult(source="planet4589 Starlink stats", fetched=1, created=1, updated=0)

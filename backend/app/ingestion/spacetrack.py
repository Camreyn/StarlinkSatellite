from __future__ import annotations

import logging

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.api import IngestResult

logger = logging.getLogger(__name__)

BASE_URL = "https://www.space-track.org"


async def ingest_spacetrack_data(db: Session) -> IngestResult:
    settings = get_settings()
    if not settings.space_track_username or not settings.space_track_password:
        return IngestResult(
            source="Space-Track",
            fetched=0,
            created=0,
            updated=0,
            skipped=1,
            warnings=["SPACE_TRACK_USERNAME and SPACE_TRACK_PASSWORD are not configured."],
        )

    # The implementation intentionally keeps Space-Track optional and credential-free by default.
    # It logs in with environment credentials, then fetches a small SATCAT query scoped to Starlink.
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
        login = await client.post(
            f"{BASE_URL}/ajaxauth/login",
            data={
                "identity": settings.space_track_username,
                "password": settings.space_track_password,
            },
        )
        login.raise_for_status()
        query = (
            f"{BASE_URL}/basicspacedata/query/class/satcat/"
            "OBJECT_NAME/STARLINK~~/orderby/NORAD_CAT_ID/format/json"
        )
        response = await client.get(query)
        response.raise_for_status()
        payload = response.json()

    # Space-Track field coverage and account limits vary. Store ingestion as a future extension point
    # unless explicit mapping is added; avoid silently overwriting CelesTrak facts with ambiguous fields.
    db.commit()
    return IngestResult(
        source="Space-Track SATCAT",
        fetched=len(payload) if isinstance(payload, list) else 0,
        created=0,
        updated=0,
        warnings=[
            "Fetched Space-Track data successfully. Mapping is conservative; add explicit field mapping before importing into catalog records."
        ],
    )

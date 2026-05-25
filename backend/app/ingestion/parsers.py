from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from typing import Any


@dataclass(frozen=True)
class GpRecord:
    norad_cat_id: int
    object_name: str
    epoch: datetime
    mean_motion: float | None
    eccentricity: float | None
    inclination: float | None
    raan: float | None
    arg_perigee: float | None
    mean_anomaly: float | None
    bstar: float | None
    raw_json: dict[str, Any]


@dataclass(frozen=True)
class TleRecord:
    norad_cat_id: int
    object_name: str
    epoch: datetime
    mean_motion: float | None
    eccentricity: float | None
    inclination: float | None
    raan: float | None
    arg_perigee: float | None
    mean_anomaly: float | None
    bstar: float | None
    line1: str
    line2: str


@dataclass(frozen=True)
class SatcatRecord:
    norad_cat_id: int
    object_name: str | None
    international_designator: str | None
    launch_date: date | None
    decay_date: date | None
    object_type: str | None
    operational_status: str | None


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        raise ValueError("Missing datetime value")
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _date_or_none(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return date.fromisoformat(value[:10])


def parse_gp_json(payload: list[dict[str, Any]]) -> list[GpRecord]:
    records: list[GpRecord] = []
    for item in payload:
        norad_value = item.get("NORAD_CAT_ID") or item.get("OBJECT_ID") or item.get("CATNR")
        if norad_value is None:
            continue
        object_name = str(item.get("OBJECT_NAME") or item.get("OBJECT_NAME_1") or "").strip()
        if "STARLINK" not in object_name.upper():
            continue
        records.append(
            GpRecord(
                norad_cat_id=int(norad_value),
                object_name=object_name,
                epoch=_parse_datetime(str(item.get("EPOCH"))),
                mean_motion=_float_or_none(item.get("MEAN_MOTION")),
                eccentricity=_float_or_none(item.get("ECCENTRICITY")),
                inclination=_float_or_none(item.get("INCLINATION")),
                raan=_float_or_none(item.get("RA_OF_ASC_NODE")),
                arg_perigee=_float_or_none(item.get("ARG_OF_PERICENTER")),
                mean_anomaly=_float_or_none(item.get("MEAN_ANOMALY")),
                bstar=_float_or_none(item.get("BSTAR")),
                raw_json=item,
            )
        )
    return records


def _parse_tle_epoch(line1: str) -> datetime:
    epoch_year = int(line1[18:20])
    epoch_day = float(line1[20:32])
    year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
    start = datetime(year, 1, 1)
    return start + timedelta(days=epoch_day - 1.0)


def _parse_tle_bstar(line1: str) -> float | None:
    raw = line1[53:61].strip()
    if not raw:
        return None
    mantissa = raw[:5]
    exponent = raw[5:]
    try:
        return float(f"{mantissa[0]}.{mantissa[1:]}e{exponent}")
    except (ValueError, IndexError):
        return None


def parse_tle_text(text: str) -> list[TleRecord]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    records: list[TleRecord] = []
    index = 0
    while index + 2 < len(lines):
        name, line1, line2 = lines[index], lines[index + 1], lines[index + 2]
        index += 3
        if not line1.startswith("1 ") or not line2.startswith("2 "):
            continue
        if "STARLINK" not in name.upper():
            continue
        eccentricity_text = line2[26:33].strip()
        records.append(
            TleRecord(
                norad_cat_id=int(line1[2:7]),
                object_name=name.strip(),
                epoch=_parse_tle_epoch(line1),
                mean_motion=_float_or_none(line2[52:63].strip()),
                eccentricity=float(f"0.{eccentricity_text}") if eccentricity_text else None,
                inclination=_float_or_none(line2[8:16].strip()),
                raan=_float_or_none(line2[17:25].strip()),
                arg_perigee=_float_or_none(line2[34:42].strip()),
                mean_anomaly=_float_or_none(line2[43:51].strip()),
                bstar=_parse_tle_bstar(line1),
                line1=line1,
                line2=line2,
            )
        )
    return records


def parse_satcat_csv(text: str) -> list[SatcatRecord]:
    reader = csv.DictReader(StringIO(text))
    records: list[SatcatRecord] = []
    for row in reader:
        name = row.get("OBJECT_NAME") or row.get("SATNAME") or row.get("OBJECT NAME")
        if not name or "STARLINK" not in name.upper():
            continue
        norad = row.get("NORAD_CAT_ID") or row.get("CATNR") or row.get("NORAD")
        if not norad:
            continue
        records.append(
            SatcatRecord(
                norad_cat_id=int(norad),
                object_name=name.strip(),
                international_designator=(
                    row.get("OBJECT_ID")
                    or row.get("INTLDES")
                    or row.get("INTERNATIONAL_DESIGNATOR")
                ),
                launch_date=_date_or_none(row.get("LAUNCH_DATE") or row.get("LAUNCH")),
                decay_date=_date_or_none(row.get("DECAY_DATE") or row.get("DECAY")),
                object_type=row.get("OBJECT_TYPE") or row.get("TYPE"),
                operational_status=row.get("OPS_STATUS_CODE") or row.get("STATUS"),
            )
        )
    return records

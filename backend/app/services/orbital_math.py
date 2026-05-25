from __future__ import annotations

from dataclasses import dataclass

EARTH_MU_KM3_S2 = 398600.4418
EARTH_RADIUS_KM = 6378.137
SECONDS_PER_DAY = 86400.0
TWO_PI = 6.283185307179586


@dataclass(frozen=True)
class OrbitDerivedValues:
    semimajor_axis_km: float | None
    perigee_km: float | None
    apogee_km: float | None
    altitude_estimate_km: float | None


def derive_orbit_values(
    mean_motion_rev_per_day: float | None, eccentricity: float | None
) -> OrbitDerivedValues:
    if not mean_motion_rev_per_day or mean_motion_rev_per_day <= 0:
        return OrbitDerivedValues(None, None, None, None)

    eccentricity = eccentricity or 0.0
    mean_motion_rad_s = mean_motion_rev_per_day * TWO_PI / SECONDS_PER_DAY
    semimajor_axis_km = (EARTH_MU_KM3_S2 / (mean_motion_rad_s**2)) ** (1.0 / 3.0)
    perigee_km = semimajor_axis_km * (1.0 - eccentricity) - EARTH_RADIUS_KM
    apogee_km = semimajor_axis_km * (1.0 + eccentricity) - EARTH_RADIUS_KM
    altitude_estimate_km = (perigee_km + apogee_km) / 2.0
    return OrbitDerivedValues(
        semimajor_axis_km=round(semimajor_axis_km, 3),
        perigee_km=round(perigee_km, 3),
        apogee_km=round(apogee_km, 3),
        altitude_estimate_km=round(altitude_estimate_km, 3),
    )

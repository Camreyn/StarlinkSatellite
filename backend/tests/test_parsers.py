from app.ingestion.parsers import parse_gp_json, parse_tle_text


def test_celestrak_parser_with_sample_gp_json() -> None:
    records = parse_gp_json(
        [
            {
                "OBJECT_NAME": "STARLINK-1000",
                "NORAD_CAT_ID": 44713,
                "EPOCH": "2024-12-10T12:00:00.000000",
                "MEAN_MOTION": 15.1,
                "ECCENTRICITY": 0.0001,
                "INCLINATION": 53.0,
                "RA_OF_ASC_NODE": 12.0,
                "ARG_OF_PERICENTER": 90.0,
                "MEAN_ANOMALY": 270.0,
                "BSTAR": 0.00001,
            }
        ]
    )
    assert len(records) == 1
    assert records[0].norad_cat_id == 44713
    assert records[0].object_name == "STARLINK-1000"


def test_tle_parser_with_sample_tle() -> None:
    text = """STARLINK-1000
1 44713U 19074A   24345.50000000  .00001234  00000+0  10270-3 0  9991
2 44713  53.0000 120.0000 0001000  90.0000 270.0000 15.10000000    01
"""
    records = parse_tle_text(text)
    assert len(records) == 1
    assert records[0].norad_cat_id == 44713
    assert records[0].eccentricity == 0.0001
    assert records[0].mean_motion == 15.1

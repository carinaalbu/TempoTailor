from app.services.pace_service import pace_to_bpm, parse_pace_string


def test_pace_to_bpm():
    assert pace_to_bpm(5.5) == 165  # 5:30 min/km
    assert pace_to_bpm(4.0) == 180
    assert pace_to_bpm(7.0) == 150
    assert pace_to_bpm(10.0) == 150  # clamped
    assert pace_to_bpm(3.0) == 180  # clamped


def test_parse_pace_string():
    assert parse_pace_string("5:30") == 5.5
    assert parse_pace_string("5.5") == 5.5
    assert parse_pace_string("6") == 6.0
    assert parse_pace_string("invalid") is None

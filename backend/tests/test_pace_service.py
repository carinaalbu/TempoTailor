from app.services.pace_service import pace_to_bpm, parse_pace_string


def test_pace_to_bpm():
    # 12 min/km -> 60 (walking), 8 -> 120 (jogging), 4 -> 180 (running)
    assert pace_to_bpm(12.0) == 60
    assert pace_to_bpm(10.0) == 90
    assert pace_to_bpm(8.0) == 120
    assert pace_to_bpm(6.0) == 150
    assert pace_to_bpm(4.0) == 180
    assert pace_to_bpm(5.5) == 158  # 5:30 min/km
    assert pace_to_bpm(3.0) == 180  # clamped


def test_parse_pace_string():
    assert parse_pace_string("5:30") == 5.5
    assert parse_pace_string("5.5") == 5.5
    assert parse_pace_string("6") == 6.0
    assert parse_pace_string("invalid") is None

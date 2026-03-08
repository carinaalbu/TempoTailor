"""Tests for Deezer harmonic entrainment BPM logic."""

import pytest

from app.services.deezer_service import (
    calculate_harmonic_bpm_ranges,
    _bpm_in_any_harmonic_range,
    _bpm_near_base,
    _closest_harmonic_distance,
    _deduplicate_tracks,
    _is_seed_artist,
)


def test_calculate_harmonic_bpm_ranges():
    """Base 160 -> base 152-168, half 72-88, double 312-328 (±8)."""
    ranges = calculate_harmonic_bpm_ranges(160)
    assert ranges["base"].min_bpm == 152
    assert ranges["base"].max_bpm == 168
    assert ranges["half_time"].min_bpm == 72
    assert ranges["half_time"].max_bpm == 88
    assert ranges["double_time"].min_bpm == 312
    assert ranges["double_time"].max_bpm == 328


def test_calculate_harmonic_bpm_ranges_custom_variance():
    ranges = calculate_harmonic_bpm_ranges(100, variance=5)
    assert ranges["base"].min_bpm == 95
    assert ranges["base"].max_bpm == 105
    assert ranges["half_time"].min_bpm == 45
    assert ranges["half_time"].max_bpm == 55
    assert ranges["double_time"].min_bpm == 195
    assert ranges["double_time"].max_bpm == 205


def test_bpm_in_any_harmonic_range():
    ranges = calculate_harmonic_bpm_ranges(160)  # ±8: 152-168, 72-88, 312-328
    assert _bpm_in_any_harmonic_range(160.0, ranges) is True
    assert _bpm_in_any_harmonic_range(80.0, ranges) is True
    assert _bpm_in_any_harmonic_range(320.0, ranges) is True
    assert _bpm_in_any_harmonic_range(90.0, ranges) is False
    assert _bpm_in_any_harmonic_range(200.0, ranges) is False


def test_is_seed_artist():
    assert _is_seed_artist("Daft Punk", ["Daft Punk"]) is True
    assert _is_seed_artist("Daft Punk", ["daft punk"]) is True
    assert _is_seed_artist("The Weeknd", ["Weeknd"]) is True
    assert _is_seed_artist("Unknown", ["Daft Punk"]) is False
    assert _is_seed_artist("Daft Punk", []) is False


def test_bpm_near_base():
    assert _bpm_near_base(160.0, 160) is True
    assert _bpm_near_base(168.0, 160) is True   # within ±10 (168 is 8 away)
    assert _bpm_near_base(150.0, 160) is True   # within ±10
    assert _bpm_near_base(175.0, 160) is False  # outside ±10


def test_closest_harmonic_distance():
    assert _closest_harmonic_distance(160.0, 160) == 0.0
    assert _closest_harmonic_distance(80.0, 160) == 0.0
    assert _closest_harmonic_distance(320.0, 160) == 0.0
    assert _closest_harmonic_distance(165.0, 160) == 5.0
    assert _closest_harmonic_distance(85.0, 160) == 5.0  # 85 vs 80


def test_deduplicate_tracks_by_id():
    tracks = [
        {"id": 1, "title": "A"},
        {"id": 2, "title": "B"},
        {"id": 1, "title": "A again"},
    ]
    deduped = _deduplicate_tracks(tracks)
    assert len(deduped) == 2
    assert deduped[0]["id"] == 1
    assert deduped[1]["id"] == 2


def test_deduplicate_tracks_by_isrc():
    tracks = [
        {"id": 1, "isrc": "USXXX111"},
        {"id": 2, "isrc": "USXXX111"},  # same ISRC, different id
    ]
    deduped = _deduplicate_tracks(tracks)
    assert len(deduped) == 1

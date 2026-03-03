"""Convert target running pace (min/km) to BPM target for music cadence."""

MIN_BPM = 150
MAX_BPM = 180


def pace_to_bpm(pace_min_per_km: float) -> int:
    """
    Convert target pace (e.g. 5.5 for 5:30 min/km) to BPM.
    Faster pace -> higher cadence. Clamped to 150-180 BPM.
    """
    if pace_min_per_km <= 0:
        return MAX_BPM
    # Empirical: 4 min/km -> 180, 7 min/km -> 150
    bpm = round(180 - (pace_min_per_km - 4.0) * 10)
    return max(MIN_BPM, min(MAX_BPM, bpm))


def parse_pace_string(pace_str: str) -> float | None:
    """Parse '5:30' or '5.5' into minutes per km."""
    pace_str = pace_str.strip()
    if ":" in pace_str:
        parts = pace_str.split(":")
        if len(parts) != 2:
            return None
        try:
            mins = int(parts[0])
            secs = int(parts[1])
            return mins + secs / 60.0
        except ValueError:
            return None
    try:
        return float(pace_str)
    except ValueError:
        return None

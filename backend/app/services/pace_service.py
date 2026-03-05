"""Convert target pace (min/km) to BPM for music cadence.

Pace spans walking (12 min/km) through running (4 min/km):
- 12 min/km -> 60 BPM (walking)
- 10 min/km -> 90 BPM (brisk walk)
- 8 min/km -> 120 BPM (jogging)
- 6 min/km -> 150 BPM (running)
- 4 min/km -> 180 BPM (fast run)
"""

MIN_BPM = 60
MAX_BPM = 180
PACE_MIN = 4
PACE_MAX = 12


def pace_to_bpm(pace_min_per_km: float) -> int:
    """
    Convert target pace (min/km) to BPM.
    Walking (12) -> 60 BPM, jogging (8) -> 120 BPM, running (4) -> 180 BPM.
    """
    if pace_min_per_km <= 0:
        return MAX_BPM
    # Linear: 12 min/km -> 60, 4 min/km -> 180
    bpm = round(60 + (PACE_MAX - pace_min_per_km) * (MAX_BPM - MIN_BPM) / (PACE_MAX - PACE_MIN))
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

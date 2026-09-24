"""Media/Wawa line geometry and live train-position tracking.

Combines the SEPTA TrainView feed (per-train GPS) with a baked-in station
chain so the display can show *where* an incoming train actually is, rather
than only when it is scheduled.

Station coordinates come from SEPTA's get_locations.php rail_stations feed;
they are baked in so the display has no extra runtime dependency.
"""

import math
import requests

TRAINVIEW_URL = "https://www3.septa.org/api/TrainView/index.php"

# Media/Wawa line, ordered north (Center City) -> south (Wawa).
# (canonical name, short label for the strip, lat, lon)
LINE = [
    ("Temple University",  "TEM", 39.9813889, -75.1494444),
    ("Jefferson Station",  "JEF", 39.9525000, -75.1580556),
    ("Suburban Station",   "SUB", 39.9538889, -75.1677778),
    ("30th Street Station","30TH", 39.9566667, -75.1816667),
    ("Penn Medicine Station", "PENN", 39.9480556, -75.1902778),
    ("49th Street",        "49TH", 39.9436111, -75.2166667),
    ("Angora",             "ANG", 39.9447222, -75.2386111),
    ("Fernwood-Yeadon",    "FRN", 39.9397222, -75.2558333),
    ("Lansdowne",          "LAN", 39.9375000, -75.2708333),
    ("Gladstone",          "GLA", 39.9327778, -75.2822222),
    ("Clifton-Aldan",      "CLF", 39.9266667, -75.2902778),
    ("Primos",             "PRI", 39.9216667, -75.2983333),
    ("Secane",             "SEC", 39.9158333, -75.3097222),
    ("Morton-Rutledge",    "MOR", 39.9077778, -75.3288889),
    ("Swarthmore",         "SWAT", 39.9022222, -75.3508333),
    ("Wallingford",        "WAL", 39.9036111, -75.3719444),
    ("Moylan-Rose Valley", "MRV", 39.9061111, -75.3886111),
    ("Media",              "MED", 39.9144444, -75.3950000),
    ("Elwyn",              "ELW", 39.9075000, -75.4116667),
    ("Wawa",               "WAW", 39.8886000, -75.4550000),
]

SWAT_IDX = [s[0] for s in LINE].index("Swarthmore")

# TrainView / Arrivals spell some stops differently than the locations feed.
ALIASES = {
    "Market East": "Jefferson Station",
    "Jefferson": "Jefferson Station",
    "Temple U": "Temple University",
    "University City": "Penn Medicine Station",
    "30th Street Sta": "30th Street Station",
    "Gray 30th Street": "30th Street Station",
    "30th Street Gray": "30th Street Station",
    "30th St": "30th Street Station",
    "Suburban": "Suburban Station",
    "49th St": "49th Street",
    "Moylan Rose Valley": "Moylan-Rose Valley",
    "Morton": "Morton-Rutledge",
    "Clifton Aldan": "Clifton-Aldan",
}

_INDEX = {name: i for i, (name, _, _, _) in enumerate(LINE)}


def station_index(name):
    """Index of a stop on the line, tolerating SEPTA's naming variants."""
    if not name:
        return None
    name = name.strip()
    name = ALIASES.get(name, name)
    if name in _INDEX:
        return _INDEX[name]
    # Fall back to a loose match ("Media" vs "Media Station" etc).
    low = name.lower()
    for canonical, i in _INDEX.items():
        if canonical.lower().startswith(low) or low.startswith(canonical.lower()):
            return i
    return None


def _meters(lat1, lon1, lat2, lon2):
    """Equirectangular approximation. Plenty accurate over a 30 km line."""
    mean_lat = math.radians((lat1 + lat2) / 2)
    dx = math.radians(lon2 - lon1) * math.cos(mean_lat) * 6371000
    dy = math.radians(lat2 - lat1) * 6371000
    return math.hypot(dx, dy)


def _project_onto_segment(lat, lon, i, j):
    """Fraction (0..1) of the way from station i to station j, plus offset in m."""
    _, _, alat, alon = LINE[i]
    _, _, blat, blon = LINE[j]
    mean_lat = math.radians((alat + blat) / 2)
    scale = math.cos(mean_lat)
    ax, ay = alon * scale, alat
    bx, by = blon * scale, blat
    px, py = lon * scale, lat
    vx, vy = bx - ax, by - ay
    denom = vx * vx + vy * vy
    if denom == 0:
        return 0.0, 0.0
    t = ((px - ax) * vx + (py - ay) * vy) / denom
    t_clamped = max(0.0, min(1.0, t))
    # Perpendicular distance, for a sanity check on whether the fix is sane.
    cx, cy = ax + vx * t_clamped, ay + vy * t_clamped
    off = _meters(py, cx / scale, cy, px / scale) if scale else 0.0
    return t_clamped, off


def locate_train(tv):
    """Turn one TrainView record into a fractional position along LINE.

    Returns a float index (14.5 == halfway between Swarthmore and Wallingford)
    or None if the train cannot be placed on the Media/Wawa chain.
    """
    cur = station_index(tv.get("currentstop"))
    nxt = station_index(tv.get("nextstop"))

    try:
        lat = float(tv["lat"])
        lon = float(tv["lon"])
    except (KeyError, TypeError, ValueError):
        lat = lon = None

    # Best case: both endpoints known and adjacent-ish, interpolate with GPS.
    if cur is not None and nxt is not None and cur != nxt and lat is not None:
        t, _ = _project_onto_segment(lat, lon, cur, nxt)
        return cur + (nxt - cur) * t

    # Only one endpoint known: snap to it.
    if cur is not None:
        return float(cur)
    if nxt is not None:
        return float(nxt)

    # No usable stop names: fall back to nearest-segment search on GPS alone.
    if lat is None:
        return None
    best = None
    for i in range(len(LINE) - 1):
        t, off = _project_onto_segment(lat, lon, i, i + 1)
        if best is None or off < best[0]:
            best = (off, i + t)
    # A train on another line can sit far from this one; reject those.
    if best and best[0] < 1500:
        return best[1]
    return None


def fetch_trainview(timeout=10):
    """All active regional-rail trains, keyed by train number (string)."""
    try:
        data = requests.get(TRAINVIEW_URL, timeout=timeout).json()
    except Exception as e:
        print(f"TrainView error: {e}")
        return {}
    out = {}
    for tv in data:
        num = str(tv.get("trainno") or "").strip()
        if num:
            out[num] = tv
    return out


def track_train(train_id, trainview, direction=None):
    """Live position info for one train id, or None if it isn't rolling yet.

    Returns dict with:
      pos       float index along LINE
      stops_away integer stations still to go before Swarthmore
      departed  True once it has passed Swarthmore, so stops_away is 0
      current   name of the stop it most recently left / is at
      next      name of the stop it is heading for
      late      minutes late per the GPS feed
    """
    tv = trainview.get(str(train_id))
    if not tv:
        return None
    pos = locate_train(tv)
    if pos is None:
        return None

    # Distance to Swarthmore signed by travel: a Center City train runs down
    # the indices and a Media/Wawa one runs up them, so the sign says whether
    # Swarthmore is still ahead. Unsigned, a train pulling away from the
    # platform counted its stops back up again as though it were approaching.
    if direction == "N":
        to_swat = pos - SWAT_IDX
    elif direction == "S":
        to_swat = SWAT_IDX - pos
    else:
        to_swat = abs(pos - SWAT_IDX)
    departed = to_swat < -1e-9
    stops_away = 0 if departed else int(math.ceil(to_swat - 1e-9))
    try:
        late = int(tv.get("late") or 0)
    except (TypeError, ValueError):
        late = 0
    # Same 999 sentinel as the Arrivals feed: absence of status, not a delay.
    late_unknown = late >= 999
    if late_unknown:
        late = 0

    return {
        "pos": pos,
        "stops_away": stops_away,
        "departed": departed,
        "current": tv.get("currentstop") or "",
        "next": tv.get("nextstop") or "",
        "late": late,
        "late_unknown": late_unknown,
        "dest": tv.get("dest") or "",
        "at_swat": not departed and stops_away == 0,
    }


def strip_window(direction, span=6):
    """Indices of the stations to draw on the progress strip.

    Always ends at Swarthmore, and looks back up the line in the direction the
    train is coming from: north for a Center City train, south for a Wawa one.
    """
    if direction == "N":          # train arrives from the Wawa/Media end
        idxs = list(range(SWAT_IDX + span - 1, SWAT_IDX - 1, -1))
    else:                          # train arrives from Center City
        idxs = list(range(SWAT_IDX - span + 1, SWAT_IDX + 1))
    return [i for i in idxs if 0 <= i < len(LINE)]


def journey_start_index(origin_name, direction):
    """Where the train's run meets the Media/Wawa line.

    A run that started off this line (a southbound train out of Norristown,
    say) joins at the Center City end, so it is treated as entering the line
    there rather than being dropped.
    """
    idx = station_index(origin_name)
    if idx is not None:
        return idx
    return 0 if direction == "S" else len(LINE) - 1


# The strip is a fixed map of the line rather than a per-train window: the
# same stretch is drawn whoever is coming, so the picture on the platform does
# not rearrange itself between trains.
PENN_IDX = _INDEX["Penn Medicine Station"]
MAP_START = PENN_IDX
MAP_END = len(LINE) - 1          # Wawa


def map_fraction(pos):
    """Where a line position sits on the fixed strip: 0.0 Penn Med, 1.0 Wawa."""
    span = MAP_END - MAP_START
    if span == 0:
        return 0.0
    return max(0.0, min(1.0, (pos - MAP_START) / span))


def map_stops():
    """Indices of every stop drawn on the fixed strip, Penn Med to Wawa."""
    return list(range(MAP_START, MAP_END + 1))


def journey_fraction(pos, origin_name, direction):
    """How far the train has come: 0.0 at its origin, 1.0 at Swarthmore.

    Measured over the stretch of the run that lies on the Media/Wawa line;
    for a train joining from another line that is the portion from Temple.
    """
    start = journey_start_index(origin_name, direction)
    span = SWAT_IDX - start
    if span == 0:
        return 1.0
    return max(0.0, min(1.0, (pos - start) / span))

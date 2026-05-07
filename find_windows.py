#!/usr/bin/env python3
"""
find_windows.py — John Clawford's Availability Scanner
Reads busy_blocks.json and finds:
  - Thu/Fri/Sat evenings where EVERYONE is free after 5:30 PM
  - Weekends with no all-day events for anyone

Usage: python3 find_windows.py
Input:  busy_blocks.json (from fetch_calendars.py)
Output: windows.json
"""

import json
from datetime import datetime, timedelta, timezone, time
from pathlib import Path
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────

# Your local timezone (change if needed)
# Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
LOCAL_TZ = ZoneInfo("America/Chicago")  # Hoover, AL is Central Time

# Evening window: 5:30 PM to midnight
EVENING_START = time(17, 30)
EVENING_END = time(23, 59)

# Days to check for evenings (0=Mon, 3=Thu, 4=Fri, 5=Sat)
EVENING_DAYS = {3: "Thursday", 4: "Friday", 5: "Saturday"}

# How many weeks ahead to scan
WEEKS_AHEAD = 6

# Minimum % of friends free to call it "open" (1.0 = everyone, 0.8 = 80%)
QUORUM = 1.0


def load_busy_blocks() -> tuple[list[dict], list[str], str]:
    """Load events from busy_blocks.json."""
    path = Path("busy_blocks.json")
    if not path.exists():
        raise FileNotFoundError("busy_blocks.json not found — run fetch_calendars.py first")
    data = json.loads(path.read_text())
    events = data.get("events", [])
    generated_at = data.get("generated_at", "unknown")
    # Get unique friend names
    friends = sorted(set(e["person"] for e in events)) if events else []
    return events, friends, generated_at


def is_busy_during(events: list[dict], person: str, check_start: datetime, check_end: datetime) -> bool:
    """Check if a specific person has any event overlapping the check window."""
    for e in events:
        if e["person"] != person:
            continue
        try:
            ev_start = datetime.fromisoformat(e["start"]).astimezone(LOCAL_TZ)
            ev_end = datetime.fromisoformat(e["end"]).astimezone(LOCAL_TZ)
        except (ValueError, KeyError):
            continue
        # Overlap check
        if ev_start < check_end and ev_end > check_start:
            return True
    return False


def has_all_day_event(events: list[dict], person: str, date: datetime) -> bool:
    """Check if a person has an all-day event on a given date."""
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=23, minute=59, second=59)
    for e in events:
        if e["person"] != person:
            continue
        if not e.get("all_day", False):
            continue
        try:
            ev_start = datetime.fromisoformat(e["start"]).astimezone(LOCAL_TZ)
            ev_end = datetime.fromisoformat(e["end"]).astimezone(LOCAL_TZ)
        except (ValueError, KeyError):
            continue
        if ev_start <= day_end and ev_end >= day_start:
            return True
    return False


def find_open_evenings(events: list[dict], friends: list[str]) -> list[dict]:
    """Find Thu/Fri/Sat evenings where everyone (or quorum) is free after 5:30 PM."""
    open_evenings = []
    now = datetime.now(LOCAL_TZ)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(WEEKS_AHEAD * 7):
        check_date = today + timedelta(days=day_offset)
        weekday = check_date.weekday()

        if weekday not in EVENING_DAYS:
            continue

        # Build the 5:30 PM - midnight window for this date
        window_start = check_date.replace(
            hour=EVENING_START.hour,
            minute=EVENING_START.minute,
            second=0,
        )
        window_end = check_date.replace(
            hour=EVENING_END.hour,
            minute=EVENING_END.minute,
            second=0,
        )

        # Skip if already past
        if window_start < now:
            continue

        busy_friends = [f for f in friends if is_busy_during(events, f, window_start, window_end)]
        free_friends = [f for f in friends if f not in busy_friends]
        free_ratio = len(free_friends) / len(friends) if friends else 0

        if free_ratio >= QUORUM:
            open_evenings.append({
                "date": check_date.strftime("%Y-%m-%d"),
                "day_name": EVENING_DAYS[weekday],
                "display": check_date.strftime("%A, %B %-d"),
                "type": "evening",
                "window": "5:30 PM onwards",
                "free_count": len(free_friends),
                "total_count": len(friends),
                "free_friends": free_friends,
                "busy_friends": busy_friends,
            })

    return open_evenings


def find_free_weekends(events: list[dict], friends: list[str]) -> list[dict]:
    """Find weekends with no all-day events for anyone."""
    free_weekends = []
    now = datetime.now(LOCAL_TZ)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Find upcoming Saturdays
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7

    for week in range(WEEKS_AHEAD):
        saturday = today + timedelta(days=days_until_saturday + (week * 7))
        sunday = saturday + timedelta(days=1)

        if saturday < today:
            continue

        sat_busy = {f for f in friends if has_all_day_event(events, f, saturday)}
        sun_busy = {f for f in friends if has_all_day_event(events, f, sunday)}
        all_busy = sat_busy | sun_busy
        all_free = [f for f in friends if f not in all_busy]

        free_ratio = len(all_free) / len(friends) if friends else 0

        free_weekends.append({
            "saturday": saturday.strftime("%Y-%m-%d"),
            "sunday": sunday.strftime("%Y-%m-%d"),
            "display": f"{saturday.strftime('%B %-d')} – {sunday.strftime('%-d')}",
            "type": "weekend",
            "saturday_busy": sorted(sat_busy),
            "sunday_busy": sorted(sun_busy),
            "all_free": sorted(all_free),
            "all_busy": sorted(all_busy),
            "fully_open": len(all_busy) == 0,
            "free_ratio": round(free_ratio, 2),
        })

    return free_weekends


def main():
    print("🦞 John Clawford — Availability Scanner")
    print("=" * 40)

    try:
        events, friends, generated_at = load_busy_blocks()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    if not friends:
        print("⚠️  No friends found in busy_blocks.json — add calendar URLs to fetch_calendars.py")
        return

    print(f"📋 Scanning calendars for: {', '.join(friends)}")
    print(f"🕐 Calendar data generated: {generated_at}")
    print()

    open_evenings = find_open_evenings(events, friends)
    free_weekends = find_free_weekends(events, friends)

    # Print summary
    print(f"🌙 Open evenings (Thu/Fri/Sat after 5:30 PM): {len(open_evenings)}")
    for e in open_evenings[:5]:
        print(f"   ✅ {e['display']} — {e['free_count']}/{e['total_count']} free")

    print(f"\n📅 Upcoming weekends: {len(free_weekends)}")
    for w in free_weekends[:4]:
        status = "✅ Fully open" if w["fully_open"] else f"⚠️  {len(w['all_busy'])} busy"
        print(f"   {status}: {w['display']}")

    # Save output
    output = {
        "generated_at": datetime.now(LOCAL_TZ).isoformat(),
        "friends": friends,
        "open_evenings": open_evenings,
        "weekends": free_weekends,
    }

    out_path = Path("windows.json")
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n✅ Saved → {out_path}")
    print("   Next step: run generate_report.py")


if __name__ == "__main__":
    main()

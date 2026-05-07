#!/usr/bin/env python3
"""
fetch_calendars.py — John Clawford's Calendar Fetcher
Pulls iCal feeds from all friends and outputs a unified JSON of busy blocks.
Handles both Google Calendar iCal export URLs and raw .ics feeds (Apple, Outlook, etc.)

Usage: python3 fetch_calendars.py
Output: busy_blocks.json
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─────────────────────────────────────────────
# FRIEND LIST — edit this to add/remove people
# Each friend needs:
#   name: display name
#   ical_url: their iCal feed URL (see README for how to get this)
#   share_details: False = busy/free only, True = show event titles
# ─────────────────────────────────────────────
FRIENDS = [
    {
        "name": "J.C.",
        "ical_url": "https://calendar.google.com/calendar/ical/YOUR_CALENDAR_ID/basic.ics",
        "share_details": True,
    },
    # Add friends below — they just send you their iCal URL
    # {
    #     "name": "Alex",
    #     "ical_url": "https://calendar.google.com/calendar/ical/ALEX_CALENDAR_ID/basic.ics",
    #     "share_details": False,
    # },
    # {
    #     "name": "Sam",
    #     "ical_url": "webcal://p01-caldav.icloud.com/published/2/APPLE_CALENDAR_URL",
    #     "share_details": False,
    # },
]

# How many weeks ahead to scan
WEEKS_AHEAD = 6


def parse_ical_datetime(value: str, tzinfo=None) -> datetime | None:
    """Parse iCal datetime strings into Python datetime objects."""
    value = value.strip()
    # All-day event: YYYYMMDD
    if len(value) == 8:
        try:
            dt = datetime.strptime(value, "%Y%m%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    # UTC datetime: YYYYMMDDTHHMMSSz
    if value.endswith("Z"):
        try:
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    # Local datetime: YYYYMMDDTHHMMSS
    if "T" in value:
        try:
            dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
            return dt.replace(tzinfo=timezone.utc)  # treat as UTC for simplicity
        except ValueError:
            return None
    return None


def fetch_ical(url: str) -> str | None:
    """Fetch raw iCal content from a URL. Handles webcal:// too."""
    url = url.replace("webcal://", "https://")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JohnClawford/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        print(f"  ⚠️  Could not fetch calendar: {e}")
        return None


def parse_events(ical_text: str, friend_name: str, show_details: bool) -> list[dict]:
    """Parse iCal text into a list of event dicts with start/end datetimes."""
    events = []
    lines = ical_text.replace("\r\n ", "").replace("\r\n\t", "").splitlines()

    in_event = False
    current = {}

    for line in lines:
        if line.strip() == "BEGIN:VEVENT":
            in_event = True
            current = {}
        elif line.strip() == "END:VEVENT":
            if in_event and "start" in current and "end" in current:
                events.append({
                    "person": friend_name,
                    "title": current.get("title", "Busy") if show_details else "Busy",
                    "start": current["start"].isoformat(),
                    "end": current["end"].isoformat(),
                    "all_day": current.get("all_day", False),
                })
            in_event = False
            current = {}
        elif in_event:
            if line.startswith("DTSTART"):
                val = line.split(":", 1)[-1] if ":" in line else ""
                dt = parse_ical_datetime(val)
                if dt:
                    current["start"] = dt
                    current["all_day"] = len(val.strip()) == 8
            elif line.startswith("DTEND"):
                val = line.split(":", 1)[-1] if ":" in line else ""
                dt = parse_ical_datetime(val)
                if dt:
                    current["end"] = dt
            elif line.startswith("SUMMARY"):
                current["title"] = line.split(":", 1)[-1].strip()

    return events


def filter_to_window(events: list[dict]) -> list[dict]:
    """Keep only events within our scan window (today → WEEKS_AHEAD weeks)."""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(weeks=WEEKS_AHEAD)
    filtered = []
    for e in events:
        try:
            start = datetime.fromisoformat(e["start"])
            if now <= start <= cutoff:
                filtered.append(e)
        except (ValueError, KeyError):
            continue
    return filtered


def main():
    print("🦞 John Clawford — Calendar Fetcher")
    print("=" * 40)

    all_events = []

    for friend in FRIENDS:
        name = friend["name"]
        url = friend["ical_url"]
        print(f"\n📅 Fetching {name}'s calendar...")

        if "YOUR_CALENDAR_ID" in url or not url:
            print(f"  ⚠️  No URL set for {name} — skipping")
            continue

        raw = fetch_ical(url)
        if not raw:
            print(f"  ❌ Failed to fetch {name}'s calendar")
            continue

        events = parse_events(raw, name, friend.get("share_details", False))
        events = filter_to_window(events)
        all_events.extend(events)
        print(f"  ✅ Found {len(events)} upcoming events")

    # Save to JSON
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scan_weeks_ahead": WEEKS_AHEAD,
        "friend_count": len(FRIENDS),
        "events": all_events,
    }

    out_path = Path("busy_blocks.json")
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n✅ Saved {len(all_events)} total events → {out_path}")
    print("   Next step: run find_windows.py")


if __name__ == "__main__":
    main()

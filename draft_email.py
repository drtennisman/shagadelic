#!/usr/bin/env python3
"""
draft_email.py — John Clawford's Email Drafter
Reads windows.json and prints a ready-to-send email for you to review.

Usage: python3 draft_email.py
Input:  windows.json (from find_windows.py)
Output: Prints email to terminal + saves email_draft.txt
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Chicago")

# ─────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────
CLAWFORD_EMAIL = "johnclawfordai@gmail.com"
REPORT_URL = "https://drtennisman.github.io/shagadelic"

# Your group email list — add everyone here
GROUP_EMAILS = [
    # "friend1@gmail.com",
    # "friend2@icloud.com",
    # etc.
]


def load_windows() -> dict:
    path = Path("windows.json")
    if not path.exists():
        raise FileNotFoundError("windows.json not found — run find_windows.py first")
    return json.loads(path.read_text())


def format_evenings(evenings: list[dict]) -> str:
    if not evenings:
        return "  • No fully open evenings found this stretch — everyone's surprisingly booked!\n"
    lines = []
    for e in evenings[:6]:
        lines.append(f"  • {e['display']} ({e['day_name']}) — {e['window']}")
    return "\n".join(lines)


def format_weekends(weekends: list[dict]) -> str:
    lines = []
    for w in weekends[:6]:
        if w["fully_open"]:
            status = "🟢 Wide open"
        elif w["free_ratio"] >= 0.7:
            status = f"🟡 Mostly free ({', '.join(w['all_busy'])} have something)"
        else:
            status = f"🔴 Looks busy"
        lines.append(f"  • {w['display']}: {status}")
    return "\n".join(lines) if lines else "  • No weekend data available."


def draft_email(data: dict) -> str:
    evenings = data.get("open_evenings", [])
    weekends = data.get("weekends", [])
    friends = data.get("friends", [])

    generated_raw = data.get("generated_at", "")
    try:
        gen_dt = datetime.fromisoformat(generated_raw).strftime("%B %-d")
    except Exception:
        gen_dt = "this week"

    evening_lines = format_evenings(evenings)
    weekend_lines = format_weekends(weekends)
    open_count = len(evenings)
    free_weekends = sum(1 for w in weekends if w["fully_open"])

    # Pick a subject line based on availability
    if open_count >= 4:
        subject = f"🕺 John Clawford says: we have WINDOWS — {open_count} of them"
    elif open_count >= 1:
        subject = f"📅 John Clawford's Weekly Report — {open_count} open evening(s) found"
    else:
        subject = "📅 John Clawford's Weekly Report — tight schedule this stretch"

    body = f"""Subject: {subject}
To: [GROUP — see GROUP_EMAILS in draft_email.py]
From: John Clawford <{CLAWFORD_EMAIL}>

Hey crew,

John Clawford here. I've been staring at {len(friends)} calendars all week so you don't have to.

Here's what I found:

━━━━━━━━━━━━━━━━━━━━━━━━━
🌙 OPEN EVENINGS (Thu/Fri/Sat after 5:30 PM)
━━━━━━━━━━━━━━━━━━━━━━━━━
{evening_lines}

━━━━━━━━━━━━━━━━━━━━━━━━━
📅 WEEKEND REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━
{weekend_lines}

━━━━━━━━━━━━━━━━━━━━━━━━━

See the full picture (and vote for your night) here:
👉 {REPORT_URL}

If you want to claim a night, just reply to this email with the date. 
First one to get 3+ replies wins the night and J.C. will make it happen.

Stay groovy,
John Clawford 🦞
Your AI Social Coordinator

---
Not on my calendar yet? Reply with your iCal link and I'll add you.
Want off this list? Reply "unsubscribe" and I'll remove you, no hard feelings.
"""
    return body


def main():
    print("🦞 John Clawford — Email Drafter")
    print("=" * 40)

    try:
        data = load_windows()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    draft = draft_email(data)

    # Print to terminal for review
    print("\n" + "=" * 50)
    print("DRAFT EMAIL — Review before sending:")
    print("=" * 50)
    print(draft)
    print("=" * 50)

    # Save to file
    out_path = Path("email_draft.txt")
    out_path.write_text(draft, encoding="utf-8")
    print(f"\n✅ Saved draft → {out_path}")
    print(f"\nNext steps:")
    print(f"  1. Review the draft above")
    print(f"  2. Push index.html to GitHub Pages")
    print(f"  3. Send from {CLAWFORD_EMAIL} via Gmail")


if __name__ == "__main__":
    main()

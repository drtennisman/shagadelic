#!/usr/bin/env python3
"""
generate_report.py — John Clawford's Report Generator
Reads windows.json and builds the shagadelic.github.io HTML report page.

Usage: python3 generate_report.py
Input:  windows.json (from find_windows.py)
Output: index.html  (push this to your GitHub Pages repo)
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Chicago")


def load_windows() -> dict:
    path = Path("windows.json")
    if not path.exists():
        raise FileNotFoundError("windows.json not found — run find_windows.py first")
    return json.loads(path.read_text())


def render_evening_cards(evenings: list[dict]) -> str:
    if not evenings:
        return '<p class="empty">No fully open evenings found in the next 6 weeks. Everyone\'s busy — must be a popular crew 😎</p>'

    cards = []
    for e in evenings[:8]:  # Show max 8
        busy_note = ""
        if e["busy_friends"]:
            busy_note = f'<span class="busy-note">({", ".join(e["busy_friends"])} busy)</span>'
        cards.append(f"""
        <div class="card evening-card">
          <div class="card-day">{e["day_name"]}</div>
          <div class="card-date">{e["display"]}</div>
          <div class="card-window">🕡 {e["window"]}</div>
          <div class="card-free">{e["free_count"]}/{e["total_count"]} people free {busy_note}</div>
        </div>""")
    return "\n".join(cards)


def render_weekend_rows(weekends: list[dict]) -> str:
    if not weekends:
        return '<p class="empty">No weekend data available.</p>'

    rows = []
    for w in weekends:
        if w["fully_open"]:
            status_class = "status-open"
            status_text = "🟢 Wide open"
            detail = "No all-day events for anyone"
        elif w["free_ratio"] >= 0.7:
            status_class = "status-mostly"
            status_text = "🟡 Mostly free"
            detail = f"{', '.join(w['all_busy'])} have something"
        else:
            status_class = "status-busy"
            status_text = "🔴 Busy weekend"
            detail = f"{len(w['all_busy'])} people have plans"

        rows.append(f"""
        <div class="weekend-row {status_class}">
          <div class="weekend-dates">{w["display"]}</div>
          <div class="weekend-status">{status_text}</div>
          <div class="weekend-detail">{detail}</div>
        </div>""")
    return "\n".join(rows)


def build_html(data: dict) -> str:
    generated_raw = data.get("generated_at", "")
    try:
        gen_dt = datetime.fromisoformat(generated_raw).strftime("%B %-d, %Y at %-I:%M %p CT")
    except Exception:
        gen_dt = generated_raw

    friends = data.get("friends", [])
    friend_count = len(friends)
    evenings = data.get("open_evenings", [])
    weekends = data.get("weekends", [])

    evening_cards = render_evening_cards(evenings)
    weekend_rows = render_weekend_rows(weekends)
    open_evening_count = len(evenings)
    open_weekend_count = sum(1 for w in weekends if w["fully_open"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Shagadelic Social — by John Clawford</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Boogaloo&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --groovy-orange: #FF6B35;
      --groovy-yellow: #FFD23F;
      --groovy-green: #06D6A0;
      --groovy-purple: #9B5DE5;
      --groovy-pink: #F15BB5;
      --dark: #1A1A2E;
      --card-bg: #16213E;
      --text: #E8E8F0;
      --muted: #8888A8;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: var(--dark);
      color: var(--text);
      font-family: 'DM Sans', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }}

    /* Groovy animated background */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background:
        radial-gradient(ellipse at 20% 20%, rgba(155,93,229,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(255,107,53,0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(6,214,160,0.08) 0%, transparent 60%);
      pointer-events: none;
      z-index: 0;
    }}

    .container {{
      position: relative;
      z-index: 1;
      max-width: 860px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }}

    /* Header */
    .header {{
      text-align: center;
      padding: 3rem 0 2.5rem;
    }}

    .logo {{
      font-size: 5rem;
      margin-bottom: 0.5rem;
      animation: wiggle 3s ease-in-out infinite;
      display: inline-block;
    }}

    @keyframes wiggle {{
      0%, 100% {{ transform: rotate(-3deg); }}
      50% {{ transform: rotate(3deg); }}
    }}

    .site-title {{
      font-family: 'Boogaloo', cursive;
      font-size: clamp(2.5rem, 6vw, 4rem);
      background: linear-gradient(135deg, var(--groovy-orange), var(--groovy-yellow), var(--groovy-pink));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      line-height: 1.1;
      margin-bottom: 0.5rem;
    }}

    .site-subtitle {{
      color: var(--muted);
      font-size: 1rem;
      letter-spacing: 0.05em;
    }}

    /* Stats bar */
    .stats-bar {{
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
      margin: 2rem 0;
    }}

    .stat-pill {{
      background: var(--card-bg);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 999px;
      padding: 0.5rem 1.25rem;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}

    .stat-pill strong {{
      color: var(--groovy-yellow);
      font-size: 1.1rem;
    }}

    /* Section headers */
    .section {{
      margin-top: 3rem;
    }}

    .section-title {{
      font-family: 'Boogaloo', cursive;
      font-size: 1.8rem;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .section-title.evenings {{ color: var(--groovy-orange); }}
    .section-title.weekends {{ color: var(--groovy-green); }}

    /* Evening cards */
    .evening-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
    }}

    .card {{
      background: var(--card-bg);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 16px;
      padding: 1.25rem;
      transition: transform 0.2s, border-color 0.2s;
    }}

    .card:hover {{
      transform: translateY(-3px);
      border-color: var(--groovy-orange);
    }}

    .card-day {{
      font-family: 'Boogaloo', cursive;
      font-size: 1rem;
      color: var(--groovy-orange);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 0.2rem;
    }}

    .card-date {{
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }}

    .card-window {{
      font-size: 0.85rem;
      color: var(--groovy-yellow);
      margin-bottom: 0.4rem;
    }}

    .card-free {{
      font-size: 0.8rem;
      color: var(--muted);
    }}

    .busy-note {{
      display: block;
      margin-top: 0.2rem;
      color: var(--groovy-pink);
      font-size: 0.75rem;
    }}

    /* Weekend rows */
    .weekend-list {{
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }}

    .weekend-row {{
      background: var(--card-bg);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 12px;
      padding: 1rem 1.25rem;
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 1rem;
      transition: border-color 0.2s;
    }}

    .weekend-row.status-open {{ border-left: 3px solid var(--groovy-green); }}
    .weekend-row.status-mostly {{ border-left: 3px solid var(--groovy-yellow); }}
    .weekend-row.status-busy {{ border-left: 3px solid var(--muted); }}

    .weekend-dates {{
      font-weight: 600;
      font-size: 1rem;
    }}

    .weekend-status {{
      font-size: 0.9rem;
      white-space: nowrap;
    }}

    .weekend-detail {{
      font-size: 0.8rem;
      color: var(--muted);
      text-align: right;
    }}

    /* Email CTA */
    .email-cta {{
      margin-top: 3rem;
      background: linear-gradient(135deg, rgba(155,93,229,0.2), rgba(255,107,53,0.15));
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 20px;
      padding: 2rem;
      text-align: center;
    }}

    .email-cta h3 {{
      font-family: 'Boogaloo', cursive;
      font-size: 1.6rem;
      color: var(--groovy-yellow);
      margin-bottom: 0.5rem;
    }}

    .email-cta p {{
      color: var(--muted);
      margin-bottom: 1rem;
      font-size: 0.95rem;
    }}

    .email-link {{
      display: inline-block;
      background: var(--groovy-orange);
      color: white;
      text-decoration: none;
      padding: 0.75rem 2rem;
      border-radius: 999px;
      font-weight: 600;
      font-size: 0.95rem;
      transition: opacity 0.2s, transform 0.2s;
    }}

    .email-link:hover {{
      opacity: 0.85;
      transform: scale(1.03);
    }}

    /* Footer */
    .footer {{
      margin-top: 3rem;
      text-align: center;
      font-size: 0.8rem;
      color: var(--muted);
      line-height: 1.8;
    }}

    .empty {{
      color: var(--muted);
      font-style: italic;
      padding: 1rem 0;
    }}

    @media (max-width: 600px) {{
      .weekend-row {{
        grid-template-columns: 1fr;
        gap: 0.4rem;
      }}
      .weekend-detail {{ text-align: left; }}
    }}
  </style>
</head>
<body>
  <div class="container">

    <div class="header">
      <div class="logo">🕺</div>
      <h1 class="site-title">Shagadelic Social</h1>
      <p class="site-subtitle">Your crew's window of opportunity — curated by John Clawford</p>
    </div>

    <div class="stats-bar">
      <div class="stat-pill">👥 <strong>{friend_count}</strong> people on radar</div>
      <div class="stat-pill">🌙 <strong>{open_evening_count}</strong> open evenings</div>
      <div class="stat-pill">📅 <strong>{open_weekend_count}</strong> fully free weekends</div>
    </div>

    <div class="section">
      <h2 class="section-title evenings">🌙 Open Evenings</h2>
      <p style="color:var(--muted); font-size:0.9rem; margin-bottom:1rem;">
        Thu / Fri / Sat after 5:30 PM — everyone's free
      </p>
      <div class="evening-grid">
        {evening_cards}
      </div>
    </div>

    <div class="section">
      <h2 class="section-title weekends">📅 Weekend Report</h2>
      <p style="color:var(--muted); font-size:0.9rem; margin-bottom:1rem;">
        No all-day events = fair game for something big
      </p>
      <div class="weekend-list">
        {weekend_rows}
      </div>
    </div>

    <div class="email-cta">
      <h3>Wanna claim a night? 🎳</h3>
      <p>Reply to John Clawford's email or reach out directly — he's always scheming.</p>
      <a class="email-link" href="mailto:johnclawfordai@gmail.com?subject=I'm in!">
        📧 Email John Clawford
      </a>
    </div>

    <div class="footer">
      <p>Last updated: {gen_dt}</p>
      <p style="margin-top:0.4rem;">This page is auto-generated by John Clawford 🦞 — your AI social coordinator</p>
      <p>He doesn't sleep. He just waits for everyone's calendars to align.</p>
    </div>

  </div>
</body>
</html>"""


def main():
    print("🦞 John Clawford — Report Generator")
    print("=" * 40)

    try:
        data = load_windows()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    html = build_html(data)

    out_path = Path("index.html")
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Generated → {out_path}")
    print("   Push this file to your shagadelic GitHub Pages repo")
    print("   Next step: run draft_email.py")


if __name__ == "__main__":
    main()

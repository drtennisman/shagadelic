# 🦞 John Clawford — Social Calendar Agent

**Shagadelic Social** — helps your crew actually hang out.

---

## What This Does

John Clawford scans everyone's calendars, finds open Thu/Fri/Sat evenings (after 5:30 PM) and free weekends, generates a shareable report page, and drafts a weekly email to the group with a voting mechanism.

---

## Setup (One Time)

### 1. Prerequisites
```bash
# Python 3.9+ required (check: python3 --version)
# No external packages needed — all standard library
```

### 2. Create the GitHub Pages repo
1. Go to github.com → New repository
2. Name it exactly: `shagadelic` (or whatever you picked)
3. Make it public
4. Go to Settings → Pages → Source: main branch / root
5. Your site will be at `https://[yourusername].github.io/shagadelic` 
   OR if the repo is named after your username: `https://shagadelic.github.io`

### 3. Clone the repo and add these files
```bash
git clone https://github.com/[yourusername]/shagadelic
cd shagadelic
# Copy all .py files and CLAUDE.md here
```

### 4. Add your friends' calendars to fetch_calendars.py

Open `fetch_calendars.py` and edit the `FRIENDS` list.

**Getting a Google Calendar iCal URL:**
1. Google Calendar → Settings → [Calendar name] → Integrate calendar
2. Copy the "Secret address in iCal format"
3. Paste as `ical_url` in the FRIENDS list

**Getting an Apple Calendar (iCloud) iCal URL:**
1. iCloud.com → Calendar → Share calendar (click the radio tower icon)
2. Enable "Public Calendar"
3. Copy the link — replace `webcal://` with `https://`

**Getting an Outlook iCal URL:**
1. Outlook → Settings → View all Outlook settings → Calendar → Shared calendars
2. "Publish a calendar" → Copy the ICS link

### 5. Create the Claude.ai Project
1. Claude.ai → Projects → New Project
2. Name it "John Clawford"
3. Upload CLAUDE.md as project knowledge
4. Connect Gmail MCP in project settings

---

## Weekly Usage

Open Claude.ai, go to the John Clawford project, and say:

```
run the weekly report
```

Clawford will:
1. Fetch all calendars
2. Find open windows
3. Generate the HTML page
4. Draft the email

You review and confirm before anything goes out.

---

## Adding a New Friend

1. Get their iCal URL (see formats above)
2. Add them to the `FRIENDS` list in `fetch_calendars.py`
3. That's it — they're on the radar next weekly run

---

## File Reference

| File | What it does |
|------|-------------|
| `fetch_calendars.py` | Pulls iCal feeds → `busy_blocks.json` |
| `find_windows.py` | Finds open evenings + weekends → `windows.json` |
| `generate_report.py` | Builds HTML report → `index.html` |
| `draft_email.py` | Drafts weekly email → `email_draft.txt` |
| `CLAUDE.md` | Clawford's identity + instructions |
| `index.html` | The shagadelic.github.io page (push to GitHub) |

---

## Changing the GitHub Pages URL later

1. Go to github.com → your repo → Settings → rename repo
2. Update `REPORT_URL` in `draft_email.py`
3. Update the URL in `generate_report.py` email CTA section
4. Update CLAUDE.md
5. Done — new link works immediately

---

*Stay groovy. 🦞*

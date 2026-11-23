# Setup & Operational Guide — Premium Animated GitHub Profile

This repository powers an automated, high-precision SVG portfolio engine for Krishanu Rastogi's GitHub Profile README.

---

## 1. Quick Start / Local Commands

### Prerequisites
- Python 3.10+
- Dependencies: `fonttools`, `brotli`

```powershell
# Install required Python packages
pip install fonttools brotli

# 1. Fetch real GitHub contributions & repository metadata
# (Uses public scrape fallback automatically if GH_TOKEN is not provided)
python fetch.py

# 2. Render all animated SVG cards & README.md
python render.py

# 3. Validate XML syntax of all generated cards
python validate_svgs.py

# 4. Render in static mode (no animations, for static audits or fallback verification)
$env:STATIC="1"; python render.py; Remove-Item env:\STATIC
```

---

## 2. Architecture & File Structure

```text
github-profile-svg/
├── .github/
│   └── workflows/
│       └── cards.yml          # Automated daily GitHub Action workflow
├── assets/
│   ├── font.ttf               # Space Grotesk font (subsetted into WOFF at render time)
│   └── portrait.png           # Profile photo embedded into hero.svg
├── cards/                     # Generated standalone SVG cards
│   ├── hero.svg               # Editorial hero with avatar, orbital rings & status beacon
│   ├── link-1.svg             # 01 / GITHUB navigation bento tile
│   ├── link-2.svg             # 02 / PORTFOLIO navigation bento tile
│   ├── link-3.svg             # 03 / PROJECTS navigation bento tile
│   ├── activity.svg           # 4 KPI metrics + 12-month contribution cadence bar chart
│   ├── repo-1.svg             # Featured Project 01 (TrustTrack)
│   ├── repo-2.svg             # Featured Project 02 (Aroven-Tech)
│   ├── graph.svg              # 365-day branded contribution calendar (53w x 7d)
│   └── closing.svg            # Signature quote & interactive CTA buttons
├── data/
│   └── contributions.json     # Normalized real telemetry & activity data
├── fetch.py                   # Dual-mode data fetching pipeline (GraphQL & public scrape)
├── profile.json               # Brand configuration, color tokens & project showcase
├── README.md                  # Main GitHub profile layout
├── render.py                  # High-precision SVG rendering & animation engine
├── validate_svgs.py           # Strict XML syntax & viewBox validator
└── SETUP.md                   # Documentation & operations guide
```

---

## 3. Brand Identity & Design System

The visual identity is modeled directly after Krishanu Rastogi's live portfolio:

- **Background Void**: `#050508`
- **Card Surface**: `#0C0C14` / Elevated `#12121E`
- **Subtle Borders**: `#1E1E2C` (with `#625FFF40` highlight rings)
- **Primary Accent**: `#625FFF` (Electric Purple-Indigo)
- **Secondary Accents**: `#7D87FF` (Periwinkle), `#AC4BFF` (Luminous Violet), `#54A2FF` (Cyan Blue)
- **Live Status Beacon**: `#00D294` (Pulsating Emerald Green)
- **Heatmap 5-Step Scale**: `#12121C` → `#231F4D` → `#3C328E` → `#5A4DF3` → `#7D72FF`
- **Typography**: Space Grotesk (subsetted into ~11 KB WOFF, base64-embedded directly into SVGs)

---

## 4. GitHub Actions Deployment

The automated workflow (`.github/workflows/cards.yml`) runs:
1. Daily on a schedule at `02:17 UTC`.
2. Manually via `workflow_dispatch`.

### Secrets Setup
To enable authenticated GraphQL queries (including private contributions, if desired):
1. Create a GitHub Personal Access Token (classic) with `read:user` permission.
2. Go to your repository **Settings → Secrets and variables → Actions**.
3. Create a secret named `PROFILE_TOKEN` and paste the token.
*(Note: If `PROFILE_TOKEN` is not set, `fetch.py` automatically falls back to fetching your public contribution calendar).*

### Permissions
Ensure Actions has read and write permissions:
1. Go to repository **Settings → Actions → General → Workflow permissions**.
2. Select **Read and write permissions**.
3. Check **Allow GitHub Actions to create and approve pull requests**.

---

## 5. Accessibility & Motion Compliance

- **Reduced Motion**: All cards include `@media (prefers-reduced-motion: reduce)` rules that automatically disable animations, transforms, and delays, rendering the 100% complete final state.
- **Static Mode**: Setting environment variable `STATIC=1` disables all keyframe definitions and outputs clean, static SVGs.

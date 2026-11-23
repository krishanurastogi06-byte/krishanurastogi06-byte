#!/usr/bin/env python3
"""
High-Precision SVG Card Rendering Engine for GitHub Profile README.
Implements Concept C (The Architect's Kinetic Studio) with:
- Portfolio-authentic dark purple-blue palette
- Space Grotesk font subsetting via FontTools
- Precision vector layouts, staggered keyframes, and reduced-motion/static modes
- Real GitHub contribution telemetry and curated project showcases
"""

import base64
import calendar
import datetime as dt
import html
import io
import json
import math
import os
import pathlib
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'cards'
OUT.mkdir(exist_ok=True)

# Load configuration and real contribution data
PROFILE_PATH = ROOT / 'profile.json'
CONTRIB_PATH = ROOT / 'data/contributions.json'

if not PROFILE_PATH.is_file():
    raise SystemExit("Missing profile.json configuration")

P = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
if CONTRIB_PATH.is_file():
    D = json.loads(CONTRIB_PATH.read_text(encoding='utf-8'))
else:
    D = {'days': [], 'total_contributions': 0, 'active_days': 0, 'current_streak': 0, 'longest_streak': 0, 'monthly': []}

STATIC = os.getenv('STATIC', '0').strip() == '1'

# Color Tokens
C = P.get('colors', {})
BG = C.get('background', '#050508')
PANEL = C.get('surface', '#0C0C14')
PANEL_ELEVATED = C.get('surface_elevated', '#12121E')
BORDER = C.get('border', '#1E1E2C')
BORDER_HIGHLIGHT = C.get('border_highlight', '#625FFF40')
FG = C.get('text', '#FFFFFF')
MUTED = C.get('text_muted', '#8A8A9B')
ACC = C.get('accent', '#625FFF')
ACC_LIGHT = C.get('accent_light', '#7D87FF')
ACC_GLOW = C.get('accent_glow', '#AC4BFF')
ACC_CYAN = C.get('accent_blue', '#54A2FF')
GREEN = C.get('status_green', '#00D294')

HEAT_COLORS = [
    C.get('heat0', '#12121C'),
    C.get('heat1', '#231F4D'),
    C.get('heat2', '#3C328E'),
    C.get('heat3', '#5A4DF3'),
    C.get('heat4', '#7D72FF')
]

# Typography & Font Subsetting
FONT_NAME = 'Space Grotesk'
FONT_FACE = ''
font_file = ROOT / P.get('font_file', 'assets/font.ttf')

if font_file.is_file():
    try:
        from fontTools.subset import Subsetter, Options
        from fontTools.ttLib import TTFont

        # Collect glyphs across all potential strings
        glyph_text = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,;:!?&/+()-#@•—↗→←*[]{}|"`~\'%'
        for k in ['name', 'tagline', 'role', 'status', 'location']:
            glyph_text += str(P.get(k, ''))
        for item in P.get('links', []) + P.get('pillars', []) + P.get('featured', []):
            glyph_text += ' '.join(str(v) for v in item.values())

        options = Options()
        options.flavor = 'woff'
        font = TTFont(str(font_file))
        subsetter = Subsetter(options=options)
        subsetter.populate(text=glyph_text)
        subsetter.subset(font)

        out_io = io.BytesIO()
        font.save(out_io)
        woff_b64 = base64.b64encode(out_io.getvalue()).decode('ascii')
        FONT_FACE = f"""@font-face {{
  font-family: '{FONT_NAME}';
  src: url(data:font/woff;base64,{woff_b64}) format('woff');
  font-weight: 300 800;
  font-style: normal;
  font-display: swap;
}}"""
        print(f"Font successfully subsetted and embedded ({len(woff_b64)} b64 chars).")
    except Exception as exc:
        print(f"Font subsetting failed ({exc}), falling back to system fonts.")


def e(val):
    """Escape XML characters."""
    return escape(str(val), {'"': '&quot;'})


def base_frame(w, h, content, delay=0.0, defs=''):
    """Generates standard SVG container with styling, responsive viewBox, and motion system."""
    motion_css = ""
    if not STATIC:
        motion_css = f"""
    .fade-up {{
      opacity: 0;
      animation: animFadeUp 0.75s cubic-bezier(0.16, 1, 0.3, 1) {delay:.2f}s forwards;
    }}
    .fade-in {{
      opacity: 0;
      animation: animFade 0.6s ease-out {delay:.2f}s forwards;
    }}
    .pulse-dot {{
      animation: animPulse 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      transform-origin: center;
    }}
    .bar-grow {{
      transform: scaleY(0);
      transform-origin: bottom;
      animation: animBarGrow 0.85s cubic-bezier(0.16, 1, 0.3, 1) {delay + 0.2:.2f}s forwards;
    }}
    .shimmer-line {{
      stroke-dasharray: 200 800;
      animation: animShimmer 6s linear infinite;
    }}
    @keyframes animFadeUp {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes animFade {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    @keyframes animPulse {{
      0%, 100% {{ transform: scale(1); opacity: 0.9; }}
      50% {{ transform: scale(1.4); opacity: 0.3; }}
    }}
    @keyframes animBarGrow {{
      from {{ transform: scaleY(0); }}
      to {{ transform: scaleY(1); }}
    }}
    @keyframes animShimmer {{
      from {{ stroke-dashoffset: 1000; }}
      to {{ stroke-dashoffset: 0; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation: none !important;
        transition: none !important;
      }}
      .fade-up, .fade-in {{ opacity: 1 !important; transform: none !important; }}
      .bar-grow {{ transform: scaleY(1) !important; }}
    }}
"""
    else:
        motion_css = """
    .fade-up, .fade-in { opacity: 1; transform: none; }
    .bar-grow { transform: scaleY(1); }
"""

    style = f"""<style>
    {FONT_FACE}
    text {{
      font-family: '{FONT_NAME}', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    .mono {{
      font-family: 'Geist Mono', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
    }}
    {motion_css}
  </style>"""

    # Shared gradient defs
    default_defs = f"""
    <linearGradient id="primaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{ACC}"/>
      <stop offset="100%" stop-color="{ACC_GLOW}"/>
    </linearGradient>
    <linearGradient id="accentLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{ACC}" stop-opacity="0.8"/>
      <stop offset="50%" stop-color="{ACC_CYAN}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{ACC_GLOW}" stop-opacity="0.2"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{PANEL_ELEVATED}" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="{PANEL}" stop-opacity="0.95"/>
    </linearGradient>
    <radialGradient id="heroGlow" cx="80%" cy="30%" r="50%">
      <stop offset="0%" stop-color="{ACC}" stop-opacity="0.16"/>
      <stop offset="60%" stop-color="{ACC_GLOW}" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="gridPattern" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="{BORDER}" stroke-width="0.5" stroke-opacity="0.35"/>
    </pattern>
    {defs}
"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Krishanu Rastogi Portfolio Card">
  <defs>{default_defs}</defs>
  {style}
  <rect width="{w}" height="{h}" rx="18" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="17.5" fill="url(#cardGrad)" stroke="{BORDER}" stroke-width="1"/>
  {content}
</svg>"""


def save(filename, w, h, content, delay=0.0, defs=''):
    """Save generated SVG file."""
    svg_code = base_frame(w, h, content, delay, defs)
    target = OUT / filename
    target.write_text(svg_code, encoding='utf-8')


# ==============================================================================
# SECTION 1 — HERO CARD (hero.svg)
# ==============================================================================
def render_hero():
    name = P.get('name', 'Krishanu Rastogi')
    tagline = P.get('tagline', 'Designing thoughtful interfaces. Building useful software.')
    role = P.get('role', 'UI/UX & Frontend Developer').upper()
    status = P.get('status', 'Available for opportunities & freelance')
    location = P.get('location', 'India · Remote')

    # Portrait image embedding
    avatar_markup = ""
    portrait_path = ROOT / P.get('portrait', 'assets/portrait.png')
    if portrait_path.is_file():
        mime = 'image/png' if portrait_path.suffix.lower() == '.png' else 'image/jpeg'
        b64_data = base64.b64encode(portrait_path.read_bytes()).decode('ascii')
        avatar_defs = """
        <clipPath id="avatarClip">
          <circle cx="855" cy="148" r="68"/>
        </clipPath>
        <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{ACC}"/>
          <stop offset="50%" stop-color="{ACC_CYAN}"/>
          <stop offset="100%" stop-color="{ACC_GLOW}"/>
        </linearGradient>
        """.replace('{ACC}', ACC).replace('{ACC_CYAN}', ACC_CYAN).replace('{ACC_GLOW}', ACC_GLOW)

        avatar_markup = f"""
        <!-- Background radial glow behind portrait -->
        <circle cx="855" cy="148" r="105" fill="{ACC}" opacity="0.12"/>
        <circle cx="855" cy="148" r="78" fill="none" stroke="{BORDER_HIGHLIGHT}" stroke-width="1.5" stroke-dasharray="4 4"/>
        <circle cx="855" cy="148" r="73" fill="none" stroke="url(#ringGrad)" stroke-width="2.5"/>
        <image x="787" y="80" width="136" height="136" href="data:{mime};base64,{b64_data}" clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid slice"/>
        <!-- Portrait status badge -->
        <rect x="805" y="226" width="100" height="22" rx="11" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1"/>
        <circle cx="817" cy="237" r="4" fill="{GREEN}"/>
        <text x="826" y="241" fill="{FG}" font-size="9" font-weight="600" class="mono" letter-spacing="0.5">ONLINE</text>
        """
    else:
        avatar_defs = ""
        avatar_markup = f"""
        <circle cx="855" cy="148" r="68" fill="{PANEL_ELEVATED}" stroke="{ACC}" stroke-width="2"/>
        <text x="855" y="156" fill="{ACC_LIGHT}" font-size="28" font-weight="700" text-anchor="middle">&lt;/&gt;</text>
        """

    content = f"""
  <!-- Subtle Grid Texture -->
  <rect x="0" y="0" width="1000" height="300" rx="18" fill="url(#gridPattern)" opacity="0.7"/>
  <rect x="0" y="0" width="1000" height="300" rx="18" fill="url(#heroGlow)"/>

  <!-- Top Accent Horizon Line -->
  <path d="M 0 0 L 1000 0" stroke="url(#accentLineGrad)" stroke-width="2.5"/>

  <!-- Header Metadata Row -->
  <g class="fade-up" style="animation-delay: 0.05s;">
    <!-- Active Status Beacon -->
    <rect x="42" y="32" width="295" height="26" rx="13" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1"/>
    <circle cx="56" cy="45" r="4" fill="{GREEN}"/>
    <circle cx="56" cy="45" r="7" fill="none" stroke="{GREEN}" stroke-width="1.5" class="pulse-dot" opacity="0.6"/>
    <text x="68" y="49" fill="{FG}" font-size="10" font-weight="600" class="mono" letter-spacing="0.8">{e(status.upper())}</text>

    <!-- Location & Discipline Badge -->
    <text x="730" y="49" fill="{MUTED}" font-size="10" font-weight="500" class="mono" letter-spacing="1">INDIA · UI/UX &amp; DEV</text>
  </g>

  <!-- Hero Identity Block -->
  <g class="fade-up" style="animation-delay: 0.15s;">
    <!-- Name -->
    <text x="40" y="118" fill="{FG}" font-size="52" font-weight="800" letter-spacing="-0.8">
      {e(name)}<tspan fill="{ACC}">.</tspan>
    </text>

    <!-- Tagline -->
    <text x="42" y="156" fill="{MUTED}" font-size="18" font-weight="400" letter-spacing="-0.2">
      {e(tagline)}
    </text>

    <!-- Role Pill -->
    <rect x="42" y="184" width="232" height="28" rx="6" fill="{ACC}" fill-opacity="0.12" stroke="{ACC}" stroke-opacity="0.4" stroke-width="1"/>
    <text x="54" y="202" fill="{ACC_LIGHT}" font-size="11" font-weight="700" class="mono" letter-spacing="1.2">{e(role)}</text>
  </g>

  <!-- Capability Taxonomy Pills -->
  <g class="fade-up" style="animation-delay: 0.28s;">
    <!-- Pill 1: UI/UX Design -->
    <g transform="translate(42, 234)">
      <rect width="180" height="34" rx="8" fill="{PANEL}" stroke="{BORDER}" stroke-width="1"/>
      <circle cx="16" cy="17" r="3" fill="{ACC}"/>
      <text x="28" y="21" fill="{FG}" font-size="11" font-weight="700">UI/UX DESIGN</text>
      <text x="116" y="21" fill="{MUTED}" font-size="10" font-weight="400">· Systems</text>
    </g>

    <!-- Pill 2: Frontend Dev -->
    <g transform="translate(232, 234)">
      <rect width="180" height="34" rx="8" fill="{PANEL}" stroke="{BORDER}" stroke-width="1"/>
      <circle cx="16" cy="17" r="3" fill="{ACC_CYAN}"/>
      <text x="28" y="21" fill="{FG}" font-size="11" font-weight="700">FRONTEND DEV</text>
      <text x="124" y="21" fill="{MUTED}" font-size="10" font-weight="400">· Next.js</text>
    </g>

    <!-- Pill 3: Motion Design -->
    <g transform="translate(422, 234)">
      <rect width="180" height="34" rx="8" fill="{PANEL}" stroke="{BORDER}" stroke-width="1"/>
      <circle cx="16" cy="17" r="3" fill="{ACC_GLOW}"/>
      <text x="28" y="21" fill="{FG}" font-size="11" font-weight="700">MOTION DESIGN</text>
      <text x="130" y="21" fill="{MUTED}" font-size="10" font-weight="400">· GSAP</text>
    </g>
  </g>

  <!-- Avatar & Orbital Composition -->
  <g class="fade-in" style="animation-delay: 0.35s;">
    {avatar_markup}
  </g>
"""
    save('hero.svg', 1000, 300, content, delay=0.0, defs=avatar_defs if portrait_path.is_file() else '')


# ==============================================================================
# SECTION 2 — THREE HORIZONTAL NAVIGATION TILES (link-1, link-2, link-3)
# ==============================================================================
def render_nav_tiles():
    links = P.get('links', [])[:3]
    colors_accent = [ACC, ACC_GLOW, ACC_CYAN]

    for i, item in enumerate(links):
        num = item.get('num', f"0{i+1}")
        label = item.get('label', 'LINK')
        sub = item.get('subtitle', '')
        accent = colors_accent[i % len(colors_accent)]

        content = f"""
  <!-- Subtle Top Glowing Accent Line -->
  <rect x="0" y="0" width="320" height="2" fill="{accent}" opacity="0.85"/>

  <g class="fade-up" style="animation-delay: {0.1 + i * 0.1:.2f}s;">
    <!-- Step / Index Pill -->
    <rect x="22" y="22" width="46" height="20" rx="5" fill="{accent}" fill-opacity="0.14" stroke="{accent}" stroke-opacity="0.3" stroke-width="1"/>
    <text x="45" y="36" fill="{accent}" font-size="10" font-weight="700" class="mono" text-anchor="middle">{e(num)}</text>

    <!-- Arrow Action Circle -->
    <circle cx="282" cy="32" r="14" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1"/>
    <text x="282" y="37" fill="{accent}" font-size="14" font-weight="700" text-anchor="middle">↗</text>

    <!-- Primary Tile Label -->
    <text x="22" y="74" fill="{FG}" font-size="19" font-weight="800" letter-spacing="0.8">
      {e(label.upper())}
    </text>

    <!-- Subtitle -->
    <text x="22" y="98" fill="{MUTED}" font-size="12" font-weight="400">
      {e(sub)}
    </text>
  </g>
"""
        save(f'link-{i+1}.svg', 320, 126, content, delay=0.1 + i * 0.1)


# ==============================================================================
# SECTION 3 — CONTRIBUTION ANALYTICS & ACTIVITY PULSE (activity.svg)
# ==============================================================================
def render_activity():
    total_contribs = D.get('total_contributions', 0)
    active_days = D.get('active_days', 0)
    current_streak = D.get('current_streak', 0)
    longest_streak = D.get('longest_streak', 0)
    peak_info = D.get('peak_day', {'date': '', 'count': 0})
    monthly = D.get('monthly', [])

    # Format peak date
    peak_date_str = peak_info.get('date', '')
    peak_count = peak_info.get('count', 0)
    if peak_date_str:
        try:
            p_dt = dt.datetime.strptime(peak_date_str, '%Y-%m-%d')
            peak_fmt = p_dt.strftime('%d %b %Y')
        except ValueError:
            peak_fmt = peak_date_str
    else:
        peak_fmt = '—'

    # If monthly data is missing or empty, build trailing 12 months with 0
    if not monthly:
        now = dt.date.today()
        monthly = []
        for i in range(11, -1, -1):
            m_date = (now.replace(day=1) - dt.timedelta(days=i * 30)).replace(day=1)
            monthly.append({'year_month': m_date.strftime('%Y-%m'), 'label': m_date.strftime('%b'), 'count': 0})

    max_val = max([m.get('count', 0) for m in monthly] + [1])

    # Top KPI Metrics Cards (4 columns)
    kpis = [
        {'val': f"{total_contribs}", 'label': 'TOTAL CONTRIBUTIONS', 'sub': 'Past 365 Days', 'color': ACC},
        {'val': f"{active_days}", 'label': 'ACTIVE DAYS', 'sub': f"{round(active_days/365*100, 1) if active_days else 0}% of Year", 'color': ACC_CYAN},
        {'val': f"{current_streak}d", 'label': 'CURRENT STREAK', 'sub': f"Max: {longest_streak}d Record", 'color': ACC_LIGHT},
        {'val': f"{peak_count}", 'label': 'BUSIEST DAY', 'sub': peak_fmt, 'color': GREEN},
    ]

    kpi_cards = ""
    col_w = 216
    start_x = 38
    gap = 20
    for idx, kpi in enumerate(kpis):
        x = start_x + idx * (col_w + gap)
        kpi_cards += f"""
        <g transform="translate({x}, 82)">
          <rect width="{col_w}" height="90" rx="12" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1"/>
          <!-- Subtle top color accent -->
          <rect x="14" y="0" width="36" height="2" fill="{kpi['color']}" rx="1"/>
          <text x="18" y="42" fill="{FG}" font-size="30" font-weight="800" class="mono">{e(kpi['val'])}</text>
          <text x="18" y="62" fill="{MUTED}" font-size="10" font-weight="700" class="mono" letter-spacing="0.8">{e(kpi['label'])}</text>
          <text x="18" y="78" fill="{MUTED}" font-size="10" font-weight="400" opacity="0.7">{e(kpi['sub'])}</text>
        </g>
        """

    # Monthly Bar Chart Geometry
    chart_y_top = 224
    chart_base_y = 368
    chart_max_h = 110
    bar_w = 48
    bar_gap = 28
    chart_start_x = 52

    bars_markup = ""
    # Grid lines (20%, 50%, 100%)
    for frac in [0.25, 0.5, 0.75, 1.0]:
        gy = chart_base_y - chart_max_h * frac
        val_label = int(max_val * frac)
        bars_markup += f"""
        <line x1="{chart_start_x - 10}" y1="{gy}" x2="948" y2="{gy}" stroke="{BORDER}" stroke-dasharray="3 4" stroke-width="1" opacity="0.6"/>
        <text x="955" y="{gy + 4}" fill="{MUTED}" font-size="9" class="mono" opacity="0.6">{val_label}</text>
        """

    # Baseline axis
    bars_markup += f'<line x1="{chart_start_x - 10}" y1="{chart_base_y}" x2="948" y2="{chart_base_y}" stroke="{BORDER}" stroke-width="1.5"/>'

    for idx, m_data in enumerate(monthly[-12:]):
        val = m_data.get('count', 0)
        label = m_data.get('label', '')
        bx = chart_start_x + idx * (bar_w + bar_gap)
        bar_h = round((val / max_val) * chart_max_h) if max_val > 0 else 0
        bar_h = max(bar_h, 3) if val > 0 else 2
        by = chart_base_y - bar_h

        bar_fill = "url(#primaryGrad)" if val > 0 else PANEL_ELEVATED
        bar_opacity = "1" if val > 0 else "0.4"

        # Highlight peak month
        is_peak = (val == max_val and val > 0)
        peak_pill = ""
        if is_peak:
            peak_pill = f"""
            <rect x="{bx + bar_w//2 - 14}" y="{by - 20}" width="28" height="15" rx="4" fill="{ACC_LIGHT}" opacity="0.95"/>
            <text x="{bx + bar_w//2}" y="{by - 9}" fill="{BG}" font-size="9" font-weight="800" class="mono" text-anchor="middle">{val}</text>
            """
        elif val > 0:
            peak_pill = f"""
            <text x="{bx + bar_w//2}" y="{by - 7}" fill="{MUTED}" font-size="10" font-weight="600" class="mono" text-anchor="middle">{val}</text>
            """

        bars_markup += f"""
        <g>
          {peak_pill}
          <rect x="{bx}" y="{by}" width="{bar_w}" height="{bar_h}" rx="5" fill="{bar_fill}" opacity="{bar_opacity}" class="bar-grow"/>
          <text x="{bx + bar_w//2}" y="{chart_base_y + 22}" fill="{FG if val > 0 else MUTED}" font-size="11" font-weight="{600 if val > 0 else 400}" class="mono" text-anchor="middle">{e(label)}</text>
        </g>
        """

    content = f"""
  <!-- Section Title Header -->
  <g class="fade-up" style="animation-delay: 0.05s;">
    <rect x="42" y="32" width="6" height="20" rx="3" fill="{ACC}"/>
    <text x="56" y="47" fill="{FG}" font-size="16" font-weight="800" letter-spacing="1">CONTRIBUTION TELEMETRY &amp; ACTIVITY PULSE</text>
    <text x="815" y="46" fill="{MUTED}" font-size="11" font-weight="600" class="mono" letter-spacing="1">REAL-TIME DATA</text>
  </g>

  <!-- 4 KPI Metrics -->
  <g class="fade-up" style="animation-delay: 0.15s;">
    {kpi_cards}
  </g>

  <!-- Monthly Cadence Chart -->
  <g class="fade-up" style="animation-delay: 0.25s;">
    {bars_markup}
  </g>
"""
    save('activity.svg', 1000, 420, content, delay=0.1)


# ==============================================================================
# SECTION 4 — FEATURED PROJECTS CARDS (repo-1.svg, repo-2.svg)
# ==============================================================================
def render_featured_projects():
    featured = P.get('featured', [])
    repo_meta_lookup = {r.get('name'): r for r in D.get('repositories', [])}

    for idx, item in enumerate(featured):
        repo_name = item.get('name', 'Project')
        tagline = item.get('tagline', '')
        desc = item.get('description', '')
        lang = item.get('language', 'JavaScript')
        tags = item.get('tags', ['Web App', 'React'])
        url = item.get('url', f"https://github.com/krishanurastogi06-byte/{repo_name}")
        demo = item.get('demo', '')

        # Enrich with live stars & forks if present in fetched metadata
        if repo_name in repo_meta_lookup:
            meta = repo_meta_lookup[repo_name]
            stars = meta.get('stars', item.get('stars', 0))
            forks = meta.get('forks', item.get('forks', 0))
            if not desc and meta.get('description'):
                desc = meta['description']
        else:
            stars = item.get('stars', 0)
            forks = item.get('forks', 0)

        # Tags pills markup
        tags_markup = ""
        tag_x = 42
        for t in tags[:4]:
            t_len = len(t) * 7.5 + 20
            tags_markup += f"""
            <rect x="{tag_x}" y="152" width="{t_len}" height="24" rx="6" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1"/>
            <text x="{tag_x + t_len/2}" y="167" fill="{MUTED}" font-size="10" font-weight="600" class="mono" text-anchor="middle">{e(t.upper())}</text>
            """
            tag_x += t_len + 8

        accent_color = ACC if idx == 0 else ACC_CYAN

        content = f"""
  <!-- Left Accent Vertical Pillar -->
  <rect x="0" y="0" width="3" height="206" fill="{accent_color}" opacity="0.9"/>

  <g class="fade-up" style="animation-delay: {0.1 + idx * 0.15:.2f}s;">
    <!-- Top Index & Category Badge -->
    <rect x="42" y="28" width="138" height="22" rx="6" fill="{accent_color}" fill-opacity="0.12" stroke="{accent_color}" stroke-opacity="0.3" stroke-width="1"/>
    <text x="52" y="43" fill="{accent_color}" font-size="10" font-weight="700" class="mono" letter-spacing="1">FEATURED PROJECT / {idx+1:02d}</text>

    <!-- Star & Fork Metrics Pill -->
    <rect x="790" y="28" width="168" height="26" rx="8" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1"/>
    <!-- Star Icon -->
    <text x="806" y="45" fill="#FACC15" font-size="12">★</text>
    <text x="822" y="45" fill="{FG}" font-size="11" font-weight="600" class="mono">{stars}</text>
    <!-- Fork Icon -->
    <text x="856" y="45" fill="{ACC_LIGHT}" font-size="12">⑂</text>
    <text x="872" y="45" fill="{FG}" font-size="11" font-weight="600" class="mono">{forks}</text>
    <!-- Arrow Link Icon -->
    <circle cx="936" cy="41" r="10" fill="{accent_color}" fill-opacity="0.2"/>
    <text x="936" y="45" fill="{accent_color}" font-size="11" font-weight="800" text-anchor="middle">↗</text>

    <!-- Project Title & Tagline -->
    <text x="42" y="84" fill="{FG}" font-size="28" font-weight="800" letter-spacing="-0.3">
      {e(repo_name)}
      <tspan fill="{MUTED}" font-size="15" font-weight="400" dx="14">— {e(tagline)}</tspan>
    </text>

    <!-- Project Description -->
    <text x="42" y="118" fill="{MUTED}" font-size="13" font-weight="400">
      {e(desc[:115])}{'...' if len(desc) > 115 else ''}
    </text>

    <!-- Tech Stack Tags -->
    {tags_markup}

    <!-- Language Dot & Indicator -->
    <circle cx="900" cy="164" r="4" fill="{accent_color}"/>
    <text x="912" y="168" fill="{FG}" font-size="11" font-weight="600" class="mono">{e(lang)}</text>
  </g>
"""
        save(f'repo-{idx+1}.svg', 1000, 206, content, delay=0.1 + idx * 0.15)


# ==============================================================================
# SECTION 5 — 365-DAY CONTRIBUTION HEATMAP (graph.svg)
# ==============================================================================
def render_heatmap():
    days_data = D.get('days', [])
    total_contribs = D.get('total_contributions', 0)

    # Convert days list to dictionary mapping YYYY-MM-DD to count
    counts = {d['date']: int(d.get('count', 0)) for d in days_data}

    # Generate 365 calendar days ending today or last data date
    if days_data:
        last_date = dt.date.fromisoformat(days_data[-1]['date'])
    else:
        last_date = dt.date.today()

    start_date = last_date - dt.timedelta(days=364)
    # Align to previous Sunday
    sunday = start_date - dt.timedelta(days=(start_date.weekday() + 1) % 7)

    calendar_days = [start_date + dt.timedelta(days=i) for i in range(365)]

    cell_size = 12
    cell_gap = 4.2
    grid_x0 = 54
    grid_y0 = 84

    # Calculate month header positions
    month_headers = []
    seen_months = set()
    for day in calendar_days:
        ym = day.strftime('%Y-%m')
        if ym not in seen_months and day.day <= 7:
            seen_months.add(ym)
            week_idx = (day - sunday).days // 7
            mx = grid_x0 + week_idx * (cell_size + cell_gap)
            month_headers.append((mx, day.strftime('%b')))

    # Render month labels
    month_markup = ""
    for mx, mlabel in month_headers:
        month_markup += f'<text x="{mx}" y="{grid_y0 - 12}" fill="{MUTED}" font-size="10" font-weight="600" class="mono">{mlabel}</text>'

    # Render weekday labels (Mon, Wed, Fri)
    weekday_markup = ""
    for dow, wlabel in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        wy = grid_y0 + dow * (cell_size + cell_gap) + 9
        weekday_markup += f'<text x="{grid_x0 - 20}" y="{wy}" fill="{MUTED}" font-size="9" font-weight="500" class="mono">{wlabel}</text>'

    # Render 53 weeks x 7 days
    cells_markup = ""
    for day in calendar_days:
        week_idx = (day - sunday).days // 7
        dow = (day.weekday() + 1) % 7  # 0=Sunday, 6=Saturday
        count = counts.get(day.isoformat(), 0)

        # Intensity scale: 0 to 4
        if count == 0:
            level = 0
        elif count <= 3:
            level = 1
        elif count <= 6:
            level = 2
        elif count <= 10:
            level = 3
        else:
            level = 4

        cell_color = HEAT_COLORS[level]
        cx = grid_x0 + week_idx * (cell_size + cell_gap)
        cy = grid_y0 + dow * (cell_size + cell_gap)

        # Add tooltip for browser inspection
        cells_markup += f"""
        <rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{cell_color}">
          <title>{day.isoformat()}: {count} contribution{'s' if count != 1 else ''}</title>
        </rect>
        """

    # Legend at bottom
    legend_markup = f'<text x="740" y="246" fill="{MUTED}" font-size="10" font-weight="500" class="mono">Less</text>'
    for idx, col in enumerate(HEAT_COLORS):
        lx = 772 + idx * (cell_size + 4)
        legend_markup += f'<rect x="{lx}" y="236" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{col}"/>'
    legend_markup += f'<text x="{772 + 5 * (cell_size + 4) + 4}" y="246" fill="{MUTED}" font-size="10" font-weight="500" class="mono">More</text>'

    content = f"""
  <!-- Section Title -->
  <g class="fade-up" style="animation-delay: 0.05s;">
    <rect x="42" y="30" width="6" height="20" rx="3" fill="{ACC_LIGHT}"/>
    <text x="56" y="45" fill="{FG}" font-size="16" font-weight="800" letter-spacing="1">CONTRIBUTION CALENDAR · 365 DAYS</text>
    <text x="740" y="44" fill="{MUTED}" font-size="11" font-weight="600" class="mono" letter-spacing="0.8">ENGINEERING CONSISTENCY</text>
  </g>

  <!-- Heatmap Canvas -->
  <g class="fade-up" style="animation-delay: 0.15s;">
    {month_markup}
    {weekday_markup}
    {cells_markup}
  </g>

  <!-- Footer Summary & Legend -->
  <g class="fade-up" style="animation-delay: 0.25s;">
    <circle cx="52" cy="242" r="3" fill="{ACC}"/>
    <text x="62" y="246" fill="{FG}" font-size="12" font-weight="600" class="mono">
      {total_contribs} contributions <tspan fill="{MUTED}" font-weight="400">recorded across the past year</tspan>
    </text>
    {legend_markup}
  </g>
"""
    save('graph.svg', 1000, 276, content, delay=0.15)


# ==============================================================================
# SECTION 6 — CLOSING IDENTITY SECTION (closing.svg)
# ==============================================================================
def render_closing():
    statement = P.get('tagline', 'Designing thoughtful interfaces. Building useful software.')
    socials = P.get('socials', {})
    portfolio_url = socials.get('portfolio', 'https://krishanu-rastogi-portfolio.vercel.app/')
    linkedin_url = socials.get('linkedin', 'https://www.linkedin.com/in/krishanu-rastogi-')

    content = f"""
  <!-- Center Ambient Radial Glow -->
  <radialGradient id="closingGlow" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{ACC}" stop-opacity="0.12"/>
    <stop offset="80%" stop-color="{BG}" stop-opacity="0"/>
  </radialGradient>
  <rect width="1000" height="190" rx="18" fill="url(#closingGlow)"/>

  <!-- Top Accent Horizon Line -->
  <path d="M 100 0 L 900 0" stroke="url(#accentLineGrad)" stroke-width="1.5"/>

  <g class="fade-up" style="animation-delay: 0.1s;">
    <!-- Large Centered Signature Tagline -->
    <text x="500" y="66" fill="{FG}" font-size="24" font-weight="800" text-anchor="middle" letter-spacing="-0.3">
      &#8220;{e(statement)}&#8221;
    </text>

    <!-- Sub-statement -->
    <text x="500" y="96" fill="{MUTED}" font-size="13" font-weight="400" text-anchor="middle">
      Open for collaborations, frontend design engineering, and full-stack challenges.
    </text>

    <!-- CTA Buttons Row -->
    <g transform="translate(300, 122)">
      <!-- CTA 1: Portfolio -->
      <g>
        <rect width="190" height="38" rx="19" fill="{ACC}" fill-opacity="0.18" stroke="{ACC}" stroke-width="1.2"/>
        <text x="95" y="24" fill="{FG}" font-size="12" font-weight="700" text-anchor="middle" letter-spacing="0.5">
          VISIT PORTFOLIO <tspan fill="{ACC_LIGHT}">↗</tspan>
        </text>
      </g>

      <!-- CTA 2: Let's Connect -->
      <g transform="translate(210, 0)">
        <rect width="190" height="38" rx="19" fill="{PANEL_ELEVATED}" stroke="{BORDER}" stroke-width="1.2"/>
        <text x="95" y="24" fill="{MUTED}" font-size="12" font-weight="700" text-anchor="middle" letter-spacing="0.5">
          LET&apos;S CONNECT <tspan fill="{ACC_CYAN}">✉</tspan>
        </text>
      </g>
    </g>
  </g>
"""
    save('closing.svg', 1000, 190, content, delay=0.1)


# ==============================================================================
# README.MD BUILDER
# ==============================================================================
def render_readme():
    links = P.get('links', [])
    gh_link = links[0]['url'] if len(links) > 0 else "https://github.com/krishanurastogi06-byte"
    portfolio_link = links[1]['url'] if len(links) > 1 else "https://krishanu-rastogi-portfolio.vercel.app/"
    projects_link = links[2]['url'] if len(links) > 2 else "https://github.com/krishanurastogi06-byte?tab=repositories"

    featured = P.get('featured', [])
    repo_sections = []
    for idx, repo in enumerate(featured):
        repo_url = repo.get('url', f"https://github.com/krishanurastogi06-byte/{repo['name']}")
        repo_name = repo.get('name', f"Project {idx+1}")
        repo_sections.append(
            f'<a href="{html.escape(repo_url, quote=True)}"><img src="cards/repo-{idx+1}.svg" alt="{html.escape(repo_name, quote=True)}" width="100%" /></a>'
        )
    repos_markdown = '\n\n'.join(repo_sections)

    # Crucial GFM layout: 3 navigation tiles on a SINGLE line inside <p align="center"> so GFM never stacks them!
    nav_tiles_html = (
        f'<p align="center">'
        f'<a href="{html.escape(gh_link, quote=True)}"><img src="cards/link-1.svg" alt="01 GitHub" width="32.5%" /></a> '
        f'<a href="{html.escape(portfolio_link, quote=True)}"><img src="cards/link-2.svg" alt="02 Portfolio" width="32.5%" /></a> '
        f'<a href="{html.escape(projects_link, quote=True)}"><img src="cards/link-3.svg" alt="03 Projects" width="32.5%" /></a>'
        f'</p>'
    )

    readme_content = f"""<div align="center">

<!-- Hero Header Card -->
<img src="cards/hero.svg" alt="Krishanu Rastogi — UI/UX &amp; Frontend Developer" width="100%" />

<!-- Three Horizontal Navigation Tiles -->
{nav_tiles_html}

<!-- Activity & Contribution Pulse -->
<img src="cards/activity.svg" alt="Engineering Activity and Telemetry Pulse" width="100%" />

<!-- Featured Engineering Projects -->
{repos_markdown}

<!-- 365-Day Contribution Heatmap -->
<img src="cards/graph.svg" alt="365-Day Contribution Heatmap" width="100%" />

<!-- Closing Identity Signature -->
<a href="{html.escape(portfolio_link, quote=True)}"><img src="cards/closing.svg" alt="Designing thoughtful interfaces. Building useful software." width="100%" /></a>

</div>
"""
    (ROOT / 'README.md').write_text(readme_content, encoding='utf-8')
    print("README.md successfully updated with responsive layout.")


def main():
    print(f"=== Rendering SVG Cards (STATIC={STATIC}) ===")
    render_hero()
    render_nav_tiles()
    render_activity()
    render_featured_projects()
    render_heatmap()
    render_closing()
    render_readme()
    cards = list(OUT.glob('*.svg'))
    print(f"Successfully generated {len(cards)} SVG cards in {OUT}:")
    for c in sorted(cards):
        print(f"  - {c.name} ({c.stat().st_size:,} bytes)")


if __name__ == '__main__':
    main()

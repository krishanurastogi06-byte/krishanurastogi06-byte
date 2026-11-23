# Setup

1. Copy these files to the public `krishanurastogi06-byte/krishanurastogi06-byte` profile repository.
2. Replace the placeholder colours and typography in `profile.json` with the actual website's design tokens. The website URL was not supplied and its styling could not be verified. The portfolio tile currently links to GitHub deliberately rather than inventing a URL.
3. Put a licensed local TTF/OTF font in `assets/font.ttf` (or change `font_file`). Optional portrait goes in `assets/portrait.png`. The renderer embeds both assets into the SVG itself. Font subsetting requires `pyftsubset` from `fonttools`.
4. Populate `featured` in `profile.json` with real repository objects: `name`, `description`, `language`, `url`. No repositories are invented.
5. Add an Actions secret `PROFILE_TOKEN` with read access to your profile contribution data (classic token: `read:user`; private contributions require appropriate access). GitHub's default `GITHUB_TOKEN` may not have access to another repository's user contributions; use the explicit secret.
6. Enable Actions write permission for the profile repo. The workflow fetches data, renders cards, and commits generated files every day. Scheduled workflows run on the default branch and can be delayed.
7. Local preview: `pip install fonttools brotli`; `STATIC=1 python render.py` (Windows PowerShell: `$env:STATIC='1'; python render.py`). Preview `cards/*.svg` in a browser or screenshot. Run `python render.py` without STATIC before publishing to restore animations.

**Rendering limitations:** GitHub sanitizes README HTML and external image contexts vary. Inline CSS animations/SMIL in SVG files may be suppressed in some GitHub rendering surfaces; verify on the live profile. Reduced-motion CSS disables CSS animations. No JS, external stylesheets, remote fonts or remote SVG assets are required. Image links belong in README `<a>` wrappers. The three tiles use `width="32.5%"` each.

**Analytics definitions:** 365-day UTC lookback; current streak is consecutive active days ending today or yesterday; active days are days with nonzero contributions; busiest day is the highest daily contribution count. GitHub contribution counts are GitHub's calendar values, not commit-only counts. Public profile data may omit private activity depending on token/account settings.

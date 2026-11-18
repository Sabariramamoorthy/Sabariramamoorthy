#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: "Three Shifts" — matched to Sabarimani's Senior Full Stack AI Engineer
resume and CloudShift work. Cool paper surface, deep ink, teal for agents,
steel blue for systems, copper for shipping. Instrument Serif + Geist.

Every card is a standalone SVG shown through <img>, so it can only use what
GitHub allows there: inline CSS animations, SMIL and fonts embedded as data
URIs (no JS, no external requests).

Live numbers come from data/contributions.json (fetch_contributions.py).
Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.

STATIC=1 shows every animation at its end state for screenshots.
"""
import base64
import datetime
import json
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")

# ---- brand tokens (cool paper + CloudShift-adjacent, not purple-on-white) ----
PAPER = "#f2f4f7"
PAPER_DEEP = "#d9dee8"
INK = "#0b1220"
INK_SOFT = "#2a3344"
MUTED = "#6b7380"
RULE = "#d5dae3"
SYSTEMS = "#1d4ed8"   # enterprise platforms
AGENTS = "#0f766e"    # RAG / MCP / LLM
SHIP = "#b45309"      # products that shipped
W = 880

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


GAP = 12
BOTTOM = 12
COL = W / 3


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC"):
        css += (
            ".r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro{animation:none!important;"
            "opacity:1!important;transform:none!important}.sh,.rg{display:none}"
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" '
        f'viewBox="0 0 {w:.3f} {h}" role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title><style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines)
    )


# ---- 1 · hero -----------------------------------------------------------------
def hero():
    h = 420
    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="700" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{AGENTS}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-700 0;700 0;700 0"
      keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="52" width="10" height="10" rx="2" fill="{AGENTS}"/>
  <text x="70" y="61" font-family="{MONO}" font-size="14" letter-spacing="1.2" fill="{MUTED}">SENIOR FULL STACK AI ENGINEER · BENGALURU</text>
</g>
<text class="r" {d(0.15)} x="40" y="175" font-family="{SERIF}" font-size="96" letter-spacing="-2.2" fill="{INK}">Sabarimani</text>
<text class="r" {d(0.3)} x="40" y="275" font-family="{SERIF}" font-style="italic" font-size="96" letter-spacing="-2.2" fill="url(#shine)">Ramamoorthi</text>
<g class="r" {d(0.55)}>
  {text_lines(48, 322, [
      "I modernize enterprise .NET systems and build RAG,",
      "agentic workflows, and LLM apps that ship."
  ], 28, f'font-family="{SANS}" font-size="20" fill="{INK_SOFT}"')}
</g>
<g class="f" {d(0.85)}>
  <text x="48" y="396" font-family="{MONO}" font-size="15" fill="{INK}">Palo Alto Networks via Spire</text>
  <text class="nu" x="292" y="396" font-family="{MONO}" font-size="15" fill="{AGENTS}">&#8599;</text>
</g>
"""
    write(
        "hero.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            "Sabarimani Ramamoorthi. Senior Full Stack AI Engineer. "
            "I modernize enterprise .NET systems and build RAG, agentic workflows, and LLM apps that ship.",
        ),
    )


# ---- 2 · world tiles ----------------------------------------------------------
TILE_W, TILE_H = 880 / 3 - 8, 240


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    m = re.match(r"([\d.]+)(.*)", num)
    val, suf = float(m.group(1)), m.group(2)
    dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    if os.environ.get("STATIC"):
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else f"{val * e:.{dec}f}{suf}"
        on = begin + dur * i / frames
        off = (
            ""
            if i == frames
            else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        )
        out.append(
            f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(txt)}{tail}'
            f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>'
        )
    return "".join(out)


def tile(name, label, color, on, num, word, blurb, delay, pos):
    lines = wrap(blurb, 30)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{168 + i * 22}" font-family="{SANS}" '
        f'font-size="15" fill="{on}" opacity=".92">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="68" width="{TILE_W}" height="72"/></clipPath>
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{color}"/>
    <circle class="rg" {d(delay + 0.5)} cx="{TILE_W - 40}" cy="{TILE_H - 40}" r="60" fill="none" stroke="{on}" stroke-opacity=".5" stroke-width="2"/>
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
  </g>
  <text class="sl" {d(delay + 0.35)} x="24" y="42" font-family="{MONO}" font-size="14" letter-spacing="1.4" fill="{on}">{label}</text>
  <g class="ai" {d(delay + 0.5)}><text class="n" style="animation-delay:{delay + 1.3:.2f}s" x="248" y="42" font-family="{MONO}" font-size="16" fill="{on}">&#8594;</text></g>
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.45)}>
    {count_up(num, word, 22, 126, f'font-family="{SERIF}" font-size="52" fill="{on}"', delay + 0.45)}
  </g></g>
  {blurb_svg}
</g>
"""
    write(
        f"{name}.svg",
        svg(
            TILE_W,
            TILE_H,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"{label}: {num} {word}. {blurb}",
            left=4 * pos,
            right=8 - 4 * pos,
        ),
    )


# ---- 3 · activity -------------------------------------------------------------
def activity(data):
    h = 380
    monthly = data["monthly"][-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 330, 160, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / max(len(monthly), 1)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = AGENTS if is_best else ("#c5cbd6" if partial else INK)
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 24}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 12}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="13" fill="{AGENTS}">{m["total"]:,}</text>'
            )
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "current streak, and the longest" if cs >= ls else f"current streak, longest {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic">days</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="#8e8e93"> / {total_days}</tspan>', "days with a commit"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 118 + i * 98
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="640" y="{y}" font-family="{SERIF}" font-size="46" fill="{INK}">{big}</text>'
            f'<text x="640" y="{y + 26}" font-family="{SANS}" font-size="14" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="640" y="{y + 48}" width="200" height="1" fill="{RULE}"/>')
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="14" letter-spacing="1.2" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="36" y="120" font-family="{SERIF}" font-size="58" fill="{INK}">{data["total_contributions"]:,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write(
        "activity.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f'{data["total_contributions"]:,} contributions in the last year, {cs}-day streak',
        ),
    )


# ---- 4 · repo cards -----------------------------------------------------------
REPO_W, REPO_H = 880 / 3 - 8, 200
REPOS = [
    (
        "cloudshift-plane-mcp",
        "MCP server for Plane CE: workspace tools and deterministic CloudShift team reports.",
        "Python",
        AGENTS,
        "Sabariramamoorthy/cloudshift-plane-mcp",
    ),
    (
        "cppas-report",
        "CPPAS personality report generator: scoring, A4 PDF, Cloudinary upload.",
        "Python",
        SYSTEMS,
        "Sabariramamoorthy/cppas-report",
    ),
    (
        "WA-AKG",
        "Self-hosted WhatsApp gateway and dashboard: sessions, schedules, webhooks.",
        "TypeScript",
        SHIP,
        "Sabariramamoorthy/WA-AKG",
    ),
]


def repo_card(i, name, desc, lang, color, stars):
    delay = 4.6 + i * 0.12
    meta = f"{lang}  ·  ★ {stars}" if stars else f"{lang}  ·  live"
    body = f"""
<rect width="{REPO_W}" height="{REPO_H}" rx="14" fill="{PAPER}"/>
<g class="r" {d(delay)}>
  <rect x="24" y="34" width="10" height="10" rx="2" fill="{color}"/>
  <text x="44" y="44" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {text_lines(24, 80, wrap(desc, 30), 24, f'font-family="{SANS}" font-size="15" fill="{INK_SOFT}"')}
  <text x="24" y="{REPO_H - 28}" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(meta)}</text>
</g>
"""
    write(
        f"repo-{name}.svg",
        svg(
            REPO_W,
            REPO_H,
            body,
            ["sans", "sans-b", "mono"],
            f"{name}: {desc}",
            left=4 * i,
            right=8 - 4 * i,
        ),
    )


def section_title(text, italic, theme):
    fg = "#e6edf3" if theme == "dark" else INK
    body = (
        f'<text class="r" {d(4.4)} x="2" y="54" font-family="{SERIF}" font-size="40" fill="{fg}">'
        f'{escape(text)} <tspan font-style="italic">{escape(italic)}</tspan></text>'
    )
    write(f"title-coding-{theme}.svg", svg(W, 72, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0))


# ---- 5 · contribution graph (teal) --------------------------------------------
TEAL = [PAPER_DEEP, "#b7e4de", "#7dccc2", "#3fa99d", AGENTS, "#0a5c56"]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5


def heatmap(data):
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
    cell, step, gx, gy = 13, 15.5, 36, 100
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        delay = 1.0 + col * 0.03 + row * 0.02
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{TEAL[level_for(c)]}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )
    ncols = (len(days) + lead + 6) // 7
    right = min(W - 40, gx + ncols * step - 3)
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 18}" font-family="{MONO}" font-size="12" fill="{MUTED}">{m}</text>'
        for col, m in months
        if col < ncols - 10
    )
    legend_x = right - len(TEAL) * 15
    legend = "".join(
        f'<rect x="{legend_x + i * 15}" y="{gy + 7 * step + 6}" width="12" height="12" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(TEAL)
    )
    h = gy + 7 * step + 48
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="r" {d(0.8)} x="40" y="66" font-family="{SERIF}" font-size="40" fill="{INK}">Every day, <tspan font-style="italic" fill="{AGENTS}">in teal</tspan></text>
<text class="f" {d(0.8)} x="{right}" y="64" text-anchor="end" font-family="{MONO}" font-size="13" letter-spacing="1.2" fill="{MUTED}">REFRESHED DAILY</text>
{''.join(cells)}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 17}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">less</text>
{legend}
<text x="{legend_x + len(TEAL) * 15 + 2}" y="{gy + 7 * step + 17}" font-family="{MONO}" font-size="12" fill="{MUTED}">more</text></g>
"""
    write(
        "heatmap.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "mono"],
            f'Contribution graph: {data["total_contributions"]:,} contributions in the last year',
        ),
    )


def repo_stars():
    stars = {}
    try:
        import requests

        for name, _desc, _lang, _color, full in REPOS:
            r = requests.get(f"https://api.github.com/repos/{full}", timeout=10)
            if r.ok:
                stars[name] = r.json().get("stargazers_count", 0)
    except Exception as e:
        print(f"stars unavailable: {e}")
    return stars


if __name__ == "__main__":
    data = json.load(open(DATA, encoding="utf-8"))
    hero()
    tile(
        "systems",
        "SYSTEMS",
        SYSTEMS,
        "#ffffff",
        "7",
        "years",
        ".NET, React and Azure — enterprise apps, APIs and modernization.",
        3.1,
        0,
    )
    tile(
        "agents",
        "AGENTS",
        AGENTS,
        "#ffffff",
        "6",
        "stacks",
        "RAG, Copilot Studio, MCP, Groq, OpenRouter and LLM APIs.",
        3.35,
        1,
    )
    tile(
        "ship",
        "SHIP",
        SHIP,
        "#ffffff",
        "5",
        "products",
        "Auth, CPPAS, RepairFlow, GeeCee and Plane MCP — live.",
        3.6,
        2,
    )
    activity(data)
    stars = repo_stars()
    for i, (name, desc, lang, color, _full) in enumerate(REPOS):
        repo_card(i, name, desc, lang, color, stars.get(name, 0))
    section_title("What I'm", "building", "dark")
    section_title("What I'm", "building", "light")
    heatmap(data)

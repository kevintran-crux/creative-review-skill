"""One-shot creative report build kit, v3.

build(spec) turns tagged live ads from one platform (spec['platform']) into the five-page A4 report Kevin signed off on 2026-10-22 (the Natural Retreats
mock): what your ads sell, how many you run, what competitors do that you don't, how often you launch, and what Crux
does. It returns one self-contained HTML string. Every number is computed here from the ad rows and the benchmark file.
Authored text uses {placeholders} for numbers; a digit typed by hand is refused. A refused build lists every problem at
once (precheck(spec) returns the same list without building).

Spec (dict):
  as_of        "2026-10-21"
  platform     "META" (default) | "TIKTOK" | "GOOGLE" | "LINKEDIN": the one platform every count on the report comes from
  live_rule    what live means on that platform, for the footer ("seen in the last 7 days"); required off Meta
  rep          "Kevin Tran"
  rep_email    "kevin.tran@getcrux.ai"
  calendly     "https://calendly.com/atharva-getcrux/30min"   the booking button on page 5
  brand        {"name", "accent": "#56755E", "logo": url | path | inline SVG markup, "logo_missing": "sources tried"}
  brands       [{"name", "short", "kind", "market", "dropped", "dropped_why", "ads": [row, ...]}, ...]   first entry is the brand
               (b0), then competitors on the same platform; "short" = the name a marketer says, used on the pages ("Western Governors",
               "Purdue Global"; default name; a long name wraps and can push a page past A4); "dropped" = live ads set aside, "dropped_why" = what they were, in the
               reader's words ("homeowner and realtor ads")
               row: {"ad_id", "platform" (optional; must equal spec platform), "start_date" (optional), "end_date" (when the source shows one), "format": image|video|carousel,
                     "reason_to_buy", "audience", "landing_page_url" (optional), "image": url|path}
               reason_to_buy and audience go on every live ad of every brand
  compare      the one competitor pages 1, 2, 3 and 5 set beside the brand: a name in brands[1:]
  merge        {"tag": "same reason tag"}                  reason_to_buy tags that name one reason
  focus        {"audience": the audience tag most of the brand's ads carry, "phrase": "a mountain getaway",
                "short": "A mountain trip", "other": "Another trip"}
  named        [audience tags that name who the trip is for ("families and groups", "long stay travelers")]
  named_phrase "families, groups or longer stays"           the same tags, in the reader's words
  named_one    "a family, a group or a longer stay"         the same tags, one guest each
  buyer        "guest"                                      optional, one word for who the ads are aimed at ("guest", "sender",
               "student", "patient"); the pages print it as "new-guest ads" and "one per guest". Default "guest"
  one_home     {"tag": the reason_to_buy tag of the ads that each show one product, "unit": "home"}
  guests       [{"who": "families", "one": "a family", "title": "For a family ski week", "hook": "Ski all day..."}] x 3
  p1_ad        ad_id of one of the brand's own live ads, shown on page 1
  p3_ads       [{"ad_id", "brand", "for": "Built for a mountain trip", "alt": "what the picture shows"}] x 4
  text         {"p1": {"answer", "caption", "alt", "works", "pitfall", "try", "reasons_note"},
                "p3": {"answer", "opportunity"}, "p5": {"answer"}}
  benchmark    optional dict from load_benchmark(); fetched when absent
Authored text never uses spend, cost or budget words, "rivals", em dashes, "winner" or "works", and says "you", never the
brand's own name.
"""
import base64
import collections
import datetime as dt
import html as H
import io
import json
import math
import re
import statistics
import string
import types
import unicodedata
import urllib.parse
import urllib.request

INK, GREY, LIGHT = "#070707", "#B9B6B0", "#E6E3DE"
PAPER, DARK = "#F7F5F0", "#101418"

MIN_RIVAL_ADS = 20
SMALL_SAMPLE_MIN = 5  # a competitor's live ads in a directional report (spec sample: "directional")
SAMPLES = ("standard", "directional")
MIN_LAUNCHES = 5  # launches in the window a directional report needs before it prints a competitor's weeks to launch

PLATFORMS = {
    "META":     {"name": "Meta",     "library": "Meta Ad Library",                "bench": "FACEBOOK"},
    "TIKTOK":   {"name": "TikTok",   "library": "TikTok Ad Library",              "bench": "TIKTOK"},
    "GOOGLE":   {"name": "Google",   "library": "Google Ads Transparency Center", "bench": "GOOGLE"},
    "LINKEDIN": {"name": "LinkedIn", "library": "LinkedIn Ad Library",            "bench": "LINKEDIN"},
}
BENCH_DROP_BELOW = 10    # Kevin 10/23 default: no spend benchmark under 10 USD accounts with spend
BENCH_CAVEAT_BELOW = 85  # a caveat line when the platform has fewer accounts than the Meta benchmark

CHECK_CAP = 3  # check builds a run makes on its own: the first, then Stage 7 fixes at most twice (K37)

# words that only say go on: never a fix round's rep_asked (K40, P38). UMass Global passed rep_asked="continue" on
# 10/21, so the kit took builds 2 and 3 for a rep's round with no cap
GO_ON = {"continue", "go", "on", "ahead", "keep", "going", "carry", "proceed", "resume", "finish", "yes", "ok", "okay",
         "please", "the", "review", "report", "run", "it", "and", "now", "with", "up"}

BENCH_URL = "https://assets.aws.getcrux.ai/copilot-convo-artifacts/debug-reports/ad-spend-vs-active-ads-2026-09-08.html"

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/140 Safari/537.36"}

# ------------------------------------------------------------------ data
def _get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def load_benchmark(url=BENCH_URL, platform="META"):
    """Benchmark of USD accounts on one platform with spend and at least one live ad. No names kept. "none" = too few
    accounts to show (under BENCH_DROP_BELOW); "caveat" = fewer than the Meta benchmark's BENCH_CAVEAT_BELOW."""
    rows = json.loads(re.search(r"ROWS\s*=\s*(\[.*?\]);", _get(url, 60).decode(), re.S).group(1))
    v = [r for r in rows if r["platform"] == PLATFORMS[platform]["bench"] and r["currency"] == "USD"
         and (r["spend_30d"] or 0) > 0 and (r["active_ads"] or 0) > 0]
    x = [math.log10(r["spend_30d"]) for r in v]
    y = [math.log10(r["active_ads"]) for r in v]
    fit = {"slope": 0.0, "intercept": statistics.mean(y) if y else 0.0}
    if len(v) >= 2 and len(set(x)) >= 2:
        mx, my = statistics.mean(x), statistics.mean(y)
        slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)
        fit = {"slope": slope, "intercept": my - slope * mx}
    window = re.search(r"window:\s*(\d+ \w+ \d{4}) to (\d+ \w+ \d{4})", _get(url, 60).decode())
    return {"accounts": len(v), "window": f"{window.group(1)} to {window.group(2)}" if window else "30 days",
            "points": sorted([round(r["spend_30d"]), r["active_ads"]] for r in v), "fit": fit,
            "none": len(v) < BENCH_DROP_BELOW, "caveat": len(v) < BENCH_CAVEAT_BELOW}

def connected_names(url=BENCH_URL):
    """Org and account names connected to Crux. A rival matching one is replaced; never print the list."""
    rows = json.loads(re.search(r"ROWS\s*=\s*(\[.*?\]);", _get(url, 60).decode(), re.S).group(1))
    return {n.lower() for r in rows for n in (r.get("org_name"), r.get("name")) if n}

def is_connected(brand, names):
    pat = re.compile(r"\b" + re.escape(brand.lower()) + r"\b")
    return any(pat.search(n) for n in names)

def _img_bytes(src):
    if not src:
        return None
    if isinstance(src, (bytes, bytearray)):
        return bytes(src)
    if src.startswith("data:"):
        return base64.b64decode(src.split(",", 1)[1])
    if src.startswith("http"):
        try:
            return _get(src)
        except Exception:
            return None
    try:
        return open(src, "rb").read()
    except OSError:
        return None

def _gray(data):
    if not data:
        return None
    try:
        from PIL import Image
        return list(Image.open(io.BytesIO(data)).convert("L").resize((32, 32)).getdata())
    except Exception:
        return None

def _blank(data):
    """A thumbnail with nothing to see: it failed to load, or is one flat colour (Capital's beige video frame and
    Trade Republic's white one printed as empty tiles, 2026-10-10)."""
    g = _gray(data)
    return not g or statistics.pstdev(g) < 6

def window_start(as_of):
    """First of the 90 days that {since90}, days90 and every launch chart cover. Each chart once picked its own start
    (73 days back, or the first launch day), so a page said "since July 13" beside a chart from August (2026-10-14)."""
    return as_of - dt.timedelta(days=89)

def ended(a, as_of):
    """An ad listed as active that had ended by as_of: an end_date before it, or status "inactive". The public feed
    marked 10 Disruptive, 17 Logical Position and 8 Hawke Media ads active past their end dates, and the page
    counted them as live (2026-10-10)."""
    end = a.get("end_date")
    return str(a.get("status", "")).lower() == "inactive" or bool(end) and dt.date.fromisoformat(str(end)[:10]) < as_of

# ------------------------------------------------------------------ text
def plural(n, word):
    """"1 launch day", "5 launch days". Every count the kit prints with its noun goes through here: each string once had
    its own rule, and "1 launch days" and "1 carousels" came back after one was fixed (2026-10-14)."""
    return f"{n} {word}" if n == 1 else f"{n} {word}s"

def missing(v):
    """A value that would print as no count: None, NaN, blank, or "N/A" and its kin (K38, P34). The original skill showed
    "N/A" launch velocity for a brand with 124 live ads (Hunter, 2026-10-21)."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return True
    return isinstance(v, str) and re.fullmatch(r"\s*(?:n/?a|none|nan|null|undefined|-|\u2014)?\s*", v, re.I) is not None

# Our own analysis terms, which a cold reader does not use: every 10/9 re-engagement review needed a fix round for
# "diversity score" or "variety score" in a deck or a step (Bridgestone's "visual-mix score is 17" before them).
# Quotes from the brand's own ads are exempt, and so are "credit score" and a no_meta note's "too few ads to score".
JARGON = [r"(?<!credit )(?<!to )\bscor(?:e|es|ed|ing)\b", r"\bdiversity\b", r"\bvariety\b", r"\bconcentration\b"]

# A period with no dates: "40 recent days", "the review window", "the recent quarter" (every round-2 review, 10/9);
# "the last ninety-day window" (Tiendanube), "the observed window" (Solaire), "over the same window" (TalkRemit),
# "currently opens" (Reliance), 10/9 to 10/10.
# "right now" in a headline and a take (Metro Vein, Edelson and TalkRemit, 2026-10-16 ablation test).
PERIOD = [r"\brecent(?:ly)?\b", r"\bcurrently\b", r"\b(?:review|observed|sample|sampled|study|data|time|launch|[\w]+-day) window\b",
          r"\b(?:the|this|that)(?: (?:last|past|same|full|whole))? window\b", r"\bright now\b", r"\bat the moment\b",
          r"\bas of now\b"]

# A note meant for the rep, which belongs in the copilot's reply: "Confirm ad status in Meta before sharing"
# (Disruptive), "not a verified US-targeting comparison" (Pvolve), "an inspected live furnace ad" (Reliance), 10/10.
# "verified" alone stays: ads sell on it ("verified-battery offer").
REP = [r"\bverify\b", r"\bunverified\b", r"\bnot (?:an? )?verified\b", r"\b(?:was|were|been|be|not yet) verified\b",
       r"\binspected\b", r"\bbefore (?:sharing|sending|forwarding|you send|it goes out)\b"]

# Our own outreach and line-up words: "Promised in the outreach", "ADP remains listed as promised" (Employment Hero,
# 10/9). "Message" and "competitor" are the buyers' words (2026-10-09 buyer-language read of Atharva's calls).
INTERNAL = [r"\bpromis(?:e|es|ed|ing)\b", r"\boutreach\b", r"\bnamed by\b", r"\bthe lead\b(?![- ](?:form|magnet|gen))",
            r"\brivals?\b"]

             # written before 2026-10-17, turn it off
GENERIC = {"centers", "center", "inc", "co", "company", "group", "us", "usa", "uk", "app", "llc", "ltd", "the"}

def _sentences(t):
    return [x for x in re.split(r"(?<=[.!?:;])\s+", t.strip()) if re.search(r"[A-Za-z0-9]", x)]

def reading_grade(t):
    """Automated Readability Index, the formula the Hemingway editor uses, on plain text."""
    words = re.findall(r"[A-Za-z0-9$%'\u2019+]+", t)
    if not words:
        return 0.0
    chars = sum(len(re.sub(r"[^A-Za-z0-9]", "", w)) for w in words)
    return round(4.71 * chars / len(words) + 0.5 * len(words) / max(1, len(_sentences(t))) - 21.43, 1)

def own_names(name):
    """The brand's name as a reader would see it written: "Metro Vein Centers", "Metro Vein"."""
    words = name.replace("\u2019", "'").split()
    out = {name}
    while len(words) > 1 and words[-1].lower().strip(".,") in GENERIC:
        words = words[:-1]
        out.add(" ".join(words))
    return sorted((n for n in out if len(n) >= 3), key=len, reverse=True)

def _is_svg(b):
    if b[:4] in (b"\x89PNG", b"RIFF", b"GIF8") or b[:2] == b"\xff\xd8":
        return False
    return b"<svg" in b[:4096].lower()

def _flat(im):
    # transparent pixels go white, not black, when an image loses its alpha
    from PIL import Image
    im = im.convert("RGBA")
    bg = Image.new("RGB", im.size, "white")
    bg.paste(im, mask=im.getchannel("A"))
    return bg

def _data_uri(src, max_side=640):
    if isinstance(src, str) and src.lstrip().startswith("<"):
        src = src.encode()
    b = _img_bytes(src)
    if not b:
        return None
    if _is_svg(b):
        return "data:image/svg+xml;base64," + base64.b64encode(b).decode()
    try:
        from PIL import Image
        im = _flat(Image.open(io.BytesIO(b)))
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=84)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

def _page(url):
    url = url if url.startswith("http") else "https://" + url
    return url, _get(url, 20).decode("utf-8", "ignore")

def logo_candidates(url):
    """Logo sources on the brand's own site, in the order to try them: the image in the home link or the
    header, the site's structured-data logo, then og:image and the apple-touch icon, which are often a
    photo or a square mark and must be opened before use. Each is {"kind", "src", "aspect", "light"}; src
    is a URL or the inline SVG markup itself. Sources the kit cannot draw are left out."""
    try:
        base, page = _page(url)
    except Exception:
        return []
    host = urllib.parse.urlparse(base).netloc.removeprefix("www.")
    out = []

    def add(kind, src):
        src = H.unescape(src.strip())
        if not src.startswith(("<", "data:")):
            src = urllib.parse.urljoin(base, src)
        if src in [c["src"] for c in out]:
            return False
        try:
            r, lum = _logo(src)[1:]
        except Exception:
            return False
        out.append({"kind": kind, "src": src, "aspect": round(r, 2), "light": _contrast(lum, 1.0) < 3})
        return True

    for m in re.finditer(r'<a\b[^>]*\bhref=["\']([^"\']*)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        u = urllib.parse.urlparse(urllib.parse.urljoin(base, m.group(1)))
        if u.netloc.removeprefix("www.") != host or u.path not in ("", "/") or u.query:
            continue
        im = re.search(r'<img\b[^>]*?\bsrc=["\']([^"\']+)', m.group(2), re.I)
        sv = re.search(r"<svg\b.*?</svg>", m.group(2), re.S | re.I)
        if (im or sv) and add("header", im.group(1) if im and (not sv or im.start() < sv.start()) else sv.group(0)):
            break
    hd = re.search(r"<header\b.*?</header>", page, re.S | re.I)
    for t in re.findall(r"<img\b[^>]*>", hd.group(0) if hd else page[:len(page) // 3], re.I):
        s = re.search(r'\bsrc=["\']([^"\']+)', t)
        if s and re.search(r"logo|wordmark", t, re.I) and not re.search(r"icon|menu|hamburger", s.group(1), re.I):
            add("header", s.group(1))
    for s in re.findall(r'"logo"\s*:\s*(?:"([^"]+)"|\{[^}]*?"url"\s*:\s*"([^"]+)")', page):
        if s[0] or s[1]:
            add("schema", s[0] or s[1])
    for pat, kind in ((r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', "og:image"),
                      (r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', "og:image"),
                      (r'<link[^>]+rel=["\']apple-touch-icon[^"\']*["\'][^>]+href=["\']([^"\']+)', "apple-touch-icon"),
                      (r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']apple-touch-icon', "apple-touch-icon")):
        for s in re.findall(pat, page, re.I)[-1:]:
            add(kind, s)
    return out

def _lum(rgb):
    c = [((v / 255 + .055) / 1.055) ** 2.4 if v > 10 else v / 255 / 12.92 for v in rgb]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def _contrast(a, b):
    return (max(a, b) + .05) / (min(a, b) + .05)

def _hex(h):
    h = h.lstrip("#")
    h = "".join(x * 2 for x in h) if len(h) == 3 else h[:6]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _shade(h, against, target=4.5):
    """The accent with its hue kept, made darker (on white) or lighter (on the black panel) until text in it reads at
    `target`:1. Back Market's lime was 1.2 on white; Employment Hero's purple 2.9 and Tonies' red 3.6 on black (10/9)."""
    import colorsys
    rgb = _hex(h)
    hu, li, sa = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
    chroma = (1 - abs(2 * li - 1)) * sa
    bg = _lum(_hex(against))
    step = -.01 if bg > .5 else .01
    while _contrast(_lum(rgb), bg) < target and 0 <= li + step <= 1:
        li += step
        # darkening keeps the accent's strength: at its own saturation Metro Vein's coral #FD7B7B became #EB0404,
        # near-pure red, and now becomes #CA4848 (K20, 2026-10-15)
        s = min(sa, chroma / (1 - abs(2 * li - 1))) if step < 0 and 0 < li < 1 else sa
        rgb = tuple(round(v * 255) for v in colorsys.hls_to_rgb(hu, li, s))
    return "#%02X%02X%02X" % rgb

def _svg_colours(svg):
    named = {"white": (255, 255, 255), "#fff": (255, 255, 255), "black": (0, 0, 0), "currentcolor": (0, 0, 0)}
    out = []
    for v in re.findall(r"(?:fill|stroke|stop-color)\s*[:=]\s*[\"']?\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|[a-zA-Z]+)", svg):
        v = v.lower()
        if v.startswith("#") and len(v) in (4, 7, 9):
            out.append(_hex(v))
        elif v.startswith("rgb"):
            n = [float(x) for x in re.findall(r"[\d.]+", v)[:3]]
            if len(n) == 3:
                out.append(tuple(int(x) for x in n))
        elif v in named:
            out.append(named[v])
    return out or [(0, 0, 0)]

def _svg_lum(svg):
    """How light an SVG logo is, 0 to 1, for the tile decision. The darkest colour used to decide: TalkRemit's white wordmark
    carries a dark gradient, so it read as dark and printed white on a light page (v3 check, 2026-10-22). Now the paint
    decides: when light fills cover 40% or more of what the logo paints it reads as light; otherwise its darkest colour."""
    grads = {}
    for m in re.finditer(r"<(?:linearGradient|radialGradient)\b[^>]*\bid=[\"']([^\"']+)[\"'][^>]*>(.*?)</(?:linearGradient|radialGradient)>", svg, re.S):
        c = _svg_colours(m.group(2))
        grads[m.group(1)] = sum(_lum(x) for x in c) / len(c)
    light = total = 0.0
    for m in re.finditer(r"<(?:path|rect|circle|ellipse|polygon|polyline)\b([^>]*)>", svg):
        a = m.group(1)
        f = re.search(r"\bfill=[\"']([^\"']+)[\"']", a) or re.search(r"\bfill\s*:\s*([^;\"']+)", a)
        if not f or f.group(1).strip().lower() in ("none", "transparent"):
            continue
        v = f.group(1).strip()
        u = re.match(r"url\(\s*#([^)\s]+)\s*\)", v)
        lum = grads.get(u.group(1)) if u else _lum(_svg_colours(f'fill="{v}"')[0])
        if lum is None:
            continue
        total += len(a)
        light += len(a) * (lum > .6)
    if total and light / total >= .4:
        return 1.0
    return min(_lum(c) for c in _svg_colours(svg))


def _logo(src):
    """The header logo as (data URI, aspect, luminance of its darker part), or raises ValueError saying why."""
    if isinstance(src, str) and src.lstrip().startswith("<"):
        src = src.encode()
    b = _img_bytes(src)
    if not b:
        raise ValueError("brand.logo did not download or open; try the next source from logo_candidates()")
    if _is_svg(b):
        svg = b.decode("utf-8", "ignore")
        svg = svg[svg.lower().index("<svg"):]
        if re.search(r"<use\b[^>]*href=[\"'](?!#)", svg):
            raise ValueError("brand.logo is an SVG that points at an outside sprite file, so it draws nothing; "
                             "try the next source from logo_candidates()")
        if "xmlns=" not in svg[:svg.index(">")]:
            svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        vb = re.search(r"viewBox=[\"']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)", svg)
        wh = [re.search(rf"<svg\b[^>]*\b{k}=[\"']([\d.]+)(?:px)?[\"']", svg) for k in ("width", "height")]
        w, h = (float(vb.group(1)), float(vb.group(2))) if vb else \
            (float(wh[0].group(1)), float(wh[1].group(1))) if all(wh) else (4, 1)
        root = svg[:svg.index(">")]
        # a logo that paints its own background shows on any page
        lum = 0.0 if re.search(r"background(?:-color)?\s*:\s*(?:#|rgb)", root) else _svg_lum(svg)
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode(), w / h, lum
    try:
        from PIL import Image, ImageChops
        im = Image.open(io.BytesIO(b)).convert("RGBA")
    except Exception:
        raise ValueError("brand.logo is not an image the kit can read (SVG, PNG, JPEG, WebP or GIF)")
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:
        box = a.point(lambda v: 255 if v > 16 else 0).getbbox()
    else:
        rgb = im.convert("RGB")
        box = ImageChops.difference(rgb, Image.new("RGB", im.size, rgb.getpixel((0, 0)))).convert("L") \
            .point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box:
        raise ValueError("brand.logo is a blank image")
    im = im.crop(box)
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:
        px = sorted(_lum(p[:3]) for p in im.resize((64, max(1, round(64 * im.height / im.width)))).getdata()
                    if p[3] > 128)
        lum = px[len(px) // 4] if px else 1.0
    else:
        lum = 0.0
    im.thumbnail((720, 180))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.width / im.height, lum

def _fonts(tries=3):
    """The kit face, embedded. Without it the page falls back to Helvetica, which sets wider and can push text past
    the footer, so a failed download is retried and then flagged in report.brand."""
    for _ in range(tries):
        try:
            css = _get("https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700&display=swap").decode()
            faces = ""
            for blk in re.findall(r"/\* latin \*/\s*(@font-face\s*{[^}]+})", css):
                u = re.search(r"url\((https://[^)]+\.woff2)\)", blk).group(1)
                faces += blk.replace(u, "data:font/woff2;base64," + base64.b64encode(_get(u)).decode()) + "\n"
            if faces:
                return faces
        except Exception:
            pass
    return ""

def esc(t):
    return H.escape(t, quote=True)

def poss(name):
    """The possessive a reader expects: "MariBank Philippines'", not "MariBank Philippines's"."""
    return name + ("'" if name.endswith("s") else "'s")

def _visible(fragment):
    return " ".join(H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(style|script|title)[^>]*>.*?</\1>", " ", fragment,
                                                               flags=re.S))).split())

def check_words(doc, pats):
    """Banned words in the visible text and alt text. Trim a quoted ad rather than keep a hit."""
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", doc, flags=re.S)
    text = re.sub(r'src="data:[^"]*"', " ", text)
    text = re.sub(r'(?:alt|aria-label)="([^"]*)"', r" \1 ", text)
    text = H.unescape(re.sub(r"<[^>]+>", " ", text))
    return [(m.group(0), re.sub(r"\s+", " ", text[max(0, m.start() - 50):m.end() + 40]))
            for pat in pats for m in re.finditer(pat, text, flags=re.I)]

def check_slug(name):
    """"Metro Vein Centers" -> "metro-vein-centers", the brand as page 1 names it."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


BANNED3 = [r"\bleast\b", r"\b(weakest|worst|poorest|sharpest|strongest|best)\b", r"\b(lags?|lagging|trails?|falls? behind)\b",
           r"\b(advertises|looks|reads|acts) like\b", r"\bthan any (rival|other|competitor)s?\b", r"\bproven\b",
           r"\btop-performing\b", r"\buntested\b", r"\btoday\b", "\u2014", r"\bbuyers?\b", r"\brivals?\b"]
MAX_GRADE, MAX_WORDS = 6, 20

# The page style: tokens, then layout (the phase 2 mock's tokens.css and style block). Every colour, size and space comes
# from the tokens.
CSS = r"""
:root {
  --paper: #F7F5F0;
  --paper-2: #EFEBE3;
  --ink: #101418;
  --muted: #5B5E61;
  --rule: #D8D2C6;
  --accent: #B4451F;
  --brand: #56755E;          
  --brand-on-ink: #A9C4AE;
  --on-ink: #F7F5F0;
  --on-ink-muted: #B9BCC0;
  --bar: #C9C3B7;            
  --bar-dark: #8E877A;       
  --crux-orange: #FB7441;     
  --crux-navy: #13235F;       
  --crux-muted: #5A6075;      
  --crux-paper: #FFFFFF;
  --crux-grid: #F3F4F7;       
  --crux-line: #E3E5EC;
  --crux-radius: 12px;
  --crux-radius-sm: 8px;
  --font: 'Hanken Grotesk', Helvetica, Arial, sans-serif;
  --t-14: 14px;   
  --t-16: 16px;   
  --t-20: 20px;   
  --t-28: 28px;   
  --t-40: 40px;   
  --t-56: 56px;   
  --w-regular: 400;
  --w-semi: 600;
  --w-bold: 700;
  --lh-tight: 1.08;
  --lh-head: 1.18;
  --lh-body: 1.45;
  --track-head: -0.02em;
  --track-label: 0.06em;
  --s-4: 4px;
  --s-8: 8px;
  --s-16: 16px;
  --s-24: 24px;
  --s-40: 40px;
  --s-64: 64px;
  --radius: 0;
  --radius-button: 2px;
  --hairline: 1px;
  --page-w: 794px;           
  --page-h: 1123px;
  --measure: 62ch;
}
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0; background: var(--paper-2); color: var(--ink);
    font: var(--w-regular) var(--t-16)/var(--lh-body) var(--font);
    font-variant-numeric: lining-nums tabular-nums;
  }
  ::selection { background: var(--ink); color: var(--paper); }
  img { display: block; max-width: 100%; height: auto; }
  p { margin: 0; }
  h1, h2, h3 { margin: 0; font-weight: var(--w-bold); letter-spacing: var(--track-head); line-height: var(--lh-head); text-wrap: balance; }
  .page {
    width: min(100%, var(--page-w)); min-height: var(--page-h); margin: 0 auto var(--s-40);
    background: var(--paper); padding: var(--s-40) var(--s-64);
    display: flex; flex-direction: column; gap: var(--s-40);
  }
  .page > footer { margin-top: auto; }
  footer span:last-child { white-space: nowrap; }
  .p1, .p2, .p3 { gap: var(--s-24); }
  .run { display: flex; align-items: center; justify-content: space-between; gap: var(--s-16); }
  .brand { display: flex; align-items: center; gap: var(--s-8); font-weight: var(--w-bold); font-size: var(--t-16); }
  .brand-mark { width: 32px; height: 32px; background: var(--brand); padding: var(--s-4); }
  .run .when { font-size: var(--t-14); color: var(--muted); }
  .page h1 { font-size: var(--t-40); }
  .p1 h1 { font-size: var(--t-40); }
  .lede { font-size: var(--t-20); max-width: var(--measure); }
  .answer { font-size: var(--t-28); font-weight: var(--w-bold); line-height: var(--lh-head); letter-spacing: var(--track-head); max-width: 30ch; }
  .p2 .answer, .p3 .answer, .p4 .answer, .pv .answer { max-width: none; }
  .bench-wrap { overflow-x: auto; }
  .bench { display: block; width: 100%; min-width: 520px; height: auto; }
  .nums .lab { font-size: var(--t-20); font-weight: var(--w-bold); line-height: var(--lh-head); letter-spacing: -0.01em; margin-bottom: var(--s-8); }
  .nums.n3 { grid-template-columns: 1fr 1fr 1fr; }
  .nums.n1 { grid-template-columns: 1fr; }
  .lwrap { overflow-x: auto; }
  .lines { display: block; width: 100%; height: auto; min-width: 520px; }
  .pv { gap: var(--s-24); }
  .nums.n2 { grid-template-columns: 1fr 1fr; grid-template-rows: auto auto; row-gap: 0; }
  .nums.n2 > div { display: grid; grid-row: span 2; grid-template-rows: subgrid; align-items: start; }
  .bars .val { font-size: var(--t-28); font-weight: var(--w-bold); color: var(--ink); line-height: 1; }
  .bars .val small { font-size: var(--t-14); font-weight: var(--w-regular); color: var(--muted); }
  .small { font-size: var(--t-14); color: var(--muted); }
  .bold-line { font-size: var(--t-20); font-weight: var(--w-bold); color: var(--accent); max-width: var(--measure); }
  .says { font-size: var(--t-20); font-weight: var(--w-semi); line-height: var(--lh-head); max-width: var(--measure); }
  .catch { font-weight: var(--w-semi); max-width: var(--measure); }
  .hbars { display: grid; grid-template-columns: max-content 1fr max-content; gap: var(--s-8) var(--s-16); align-items: center; }
  .hbars .hn { font-weight: var(--w-semi); }
  .hbars .you { color: var(--brand); }
  .hbars .hv { font-size: var(--t-20); font-weight: var(--w-bold); }
  .hbars .ht { display: flex; height: 24px; border-left: 2px solid var(--muted); }
  .hbars .ht i { display: block; height: 100%; }
  .hbars .ht i.y { background: var(--brand); }
  .hbars .ht i.new { border: 2px dashed var(--brand); border-left: 0; }
  .hbars .ht i.v { background: var(--bar); }
  .hb h2 { font-size: var(--t-20); margin-bottom: var(--s-8); }
  .hb .small { margin-top: var(--s-8); }
  .p6 { gap: var(--s-24); }
  .deck6 { background-color: var(--crux-paper); background-image: linear-gradient(var(--crux-grid) 1px, transparent 1px), linear-gradient(90deg, var(--crux-grid) 1px, transparent 1px); background-size: 24px 24px; }
  .deck6 h1, .deck6 .answer { color: var(--crux-navy); }
  .dk { display: flex; flex-direction: column; gap: var(--s-24); color: var(--crux-navy); }
  .dhead { font-size: var(--t-28); line-height: var(--lh-head); }
  .dhead em { font-style: normal; color: var(--crux-orange); }
  .fd { display: grid; grid-template-columns: 170px max-content 190px 1fr; gap: var(--s-16); align-items: center; }
  .fd figure { margin: 0; }
  .fd figure img { border-radius: var(--crux-radius-sm); border: var(--hairline) solid var(--crux-line); background: var(--crux-paper); }
  .fd figcaption { font-size: var(--t-14); color: var(--crux-muted); margin-top: var(--s-4); text-align: center; }
  .fd-you { display: flex; flex-direction: column; gap: var(--s-8); padding-left: var(--s-16); border-left: 2px solid var(--crux-orange); }
  .fd-you .fd-h { font-weight: var(--w-bold); }
  .fd-you img { border-radius: var(--crux-radius-sm); }
  .fd-you em { font-style: normal; font-weight: var(--w-bold); color: var(--crux-orange); }
  .flow { display: grid; grid-template-columns: 160px max-content 1fr; gap: var(--s-16); align-items: center; }
  .flow img { border-radius: var(--crux-radius-sm); }
  .flow figcaption { color: var(--crux-muted); font-size: var(--t-14); margin-top: var(--s-4); }
  .arr { font-size: var(--t-40); color: var(--crux-orange); }
  .guests { display: flex; flex-direction: column; gap: var(--s-8); }
  .guests p { border: 1.5px solid var(--crux-orange); border-radius: var(--crux-radius-sm); padding: var(--s-8) var(--s-16); font-weight: var(--w-semi); background: var(--crux-paper); }
  .sboxes { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-16); }
  .sbox { border: 1.5px solid var(--crux-orange); border-radius: var(--crux-radius); padding: var(--s-16); text-align: center; background: var(--crux-paper); }
  .sbox .sl { font-size: var(--t-14); color: var(--crux-muted); font-weight: var(--w-semi); }
  .sbox .sn { font-size: var(--t-28); font-weight: var(--w-bold); color: var(--crux-orange); line-height: 1.15; margin: 2px 0; }
  .sbox .ss { font-size: var(--t-14); line-height: 1.3; }
  .trust { background: var(--crux-paper); border: var(--hairline) solid var(--crux-line); border-radius: var(--crux-radius-sm); padding: var(--s-8) var(--s-16); display: flex; align-items: center; gap: var(--s-16); }
  .trust p { color: var(--ink); font-weight: var(--w-bold); font-size: var(--t-14); white-space: nowrap; }
  .logos { display: flex; flex-wrap: wrap; gap: var(--s-8) var(--s-24); align-items: center; }
  .logos img { height: 18px; width: auto; }
  .cask { margin-top: auto; display: flex; justify-content: space-between; align-items: center; gap: var(--s-24); background: var(--crux-navy); color: var(--on-ink); padding: var(--s-24); border-radius: var(--crux-radius); }
  .cask h2 { font-size: var(--t-28); }
  .cask p { color: var(--on-ink-muted); margin-top: var(--s-4); }
  .cbtn { background: var(--crux-orange); color: var(--ink); font-weight: var(--w-bold); padding: var(--s-16) var(--s-24); text-decoration: none; white-space: nowrap; border-radius: var(--crux-radius-sm); }
  .cbtn:focus-visible { outline: 2px solid var(--on-ink); outline-offset: 3px; }
  .sum { display: grid; grid-template-columns: 0.8fr 1.5fr 1fr; gap: var(--s-24); }
  .sum .cell { border-top: 2px solid var(--ink); padding-top: var(--s-8); }
  .sum .sn { font-size: var(--t-40); font-weight: var(--w-bold); line-height: var(--lh-tight); letter-spacing: var(--track-head); }
  .sum .sn .op { color: var(--muted); font-weight: var(--w-regular); margin-right: var(--s-8); }
  .sum .you .sn { color: var(--brand); }
  .sum .sl { color: var(--muted); margin-top: var(--s-4); }
  .wk { display: grid; grid-template-columns: max-content 1fr max-content; gap: var(--s-16); align-items: center; }
  .wk .hn, .wk .hv { color: var(--brand); font-weight: var(--w-bold); }
  .wk .hv { font-size: var(--t-20); }
  .wstrip { display: flex; gap: 2px; height: 20px; }
  .wstrip i { flex: 1; background: var(--brand); }
  footer { border-top: var(--hairline) solid var(--rule); padding-top: var(--s-8);
    display: flex; justify-content: space-between; gap: var(--s-16); font-size: var(--t-14); color: var(--muted); }
  .ph { border: 2px dashed var(--muted); color: var(--muted); font-size: var(--t-14); padding: var(--s-16);
    display: flex; flex-direction: column; justify-content: center; gap: var(--s-4); }
  .ph b { color: var(--ink); font-weight: var(--w-semi); }
  .p1-top { display: grid; grid-template-columns: 1fr 1.15fr; gap: var(--s-16) var(--s-24); align-items: start; }
  .p1-top .head { grid-column: 1 / -1; }
  .head { display: flex; flex-direction: column; gap: var(--s-16); }
  figure { margin: 0; }
  figcaption { margin-top: var(--s-8); font-size: var(--t-14); color: var(--muted); }
  .box { background: var(--ink); color: var(--on-ink); padding: var(--s-24) var(--s-40) var(--s-24);
    display: flex; flex-direction: column; gap: var(--s-16); }
  .box .finding { font-size: var(--t-28); font-weight: var(--w-bold); line-height: var(--lh-head); letter-spacing: var(--track-head); max-width: 34ch; }
  .box .finding em { font-style: normal; color: var(--brand-on-ink); }
  .box p { max-width: var(--measure); }
  .box .try { font-weight: var(--w-semi); max-width: none; }
  .rows3 { display: grid; grid-template-columns: max-content 1fr; gap: var(--s-8) var(--s-24); margin: 0; }
  .rows3 dt { font-size: var(--t-14); color: var(--on-ink-muted); letter-spacing: var(--track-label); text-transform: uppercase; padding-top: 2px; }
  .rows3 dd { margin: 0; font-weight: var(--w-semi); }
  .rows3 .tl { color: var(--brand-on-ink); font-weight: var(--w-bold); }
  .strip { display: flex; gap: 3px; height: 28px; }
  .strip i { flex: 1; border: var(--hairline) solid var(--on-ink-muted); }
  .strip i.on { background: var(--brand-on-ink); border-color: var(--brand-on-ink); }
  .strip-key { font-size: var(--t-14); color: var(--on-ink-muted); display: flex; gap: var(--s-16); flex-wrap: wrap; }
  .strip-key span::before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: var(--s-8);
    border: var(--hairline) solid var(--on-ink-muted); vertical-align: -1px; }
  .strip-key span.on::before { background: var(--brand-on-ink); border-color: var(--brand-on-ink); }
  .nums { display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: var(--s-24); }
  .nums > div { border-top: 2px solid var(--ink); padding-top: var(--s-16); }
  .nums .n { font-size: var(--t-40); font-weight: var(--w-bold); line-height: var(--lh-tight); letter-spacing: var(--track-head); }
  .nums .n small { display: block; margin-top: var(--s-8); font-size: var(--t-16); font-weight: var(--w-regular); color: var(--muted); letter-spacing: 0; line-height: var(--lh-body); }
  .nums.vs { grid-template-columns: 0.9fr 1.1fr 1.1fr; }
  .nums.vs .lab { margin: 0; font-size: var(--t-20); font-weight: var(--w-bold); line-height: var(--lh-head); letter-spacing: -0.01em; }
  .nums.vs .pair { display: flex; gap: var(--s-24); margin-top: var(--s-8); align-items: flex-end; }
  .nums.vs .pair b { display: block; font-size: var(--t-40); line-height: 1; letter-spacing: var(--track-head); }
  .nums.vs .you b { color: var(--brand); }
  .nums.vs .them b { color: var(--muted); font-weight: var(--w-semi); }
  .nums.vs .them { border-left: var(--hairline) solid var(--bar-dark); padding-left: var(--s-24); }
  .nums.vs .pair span { font-size: var(--t-14); color: var(--muted); }
  .nums.vs .you span { color: var(--ink); font-weight: var(--w-semi); }
  .nums.vs .say { margin-top: var(--s-8); color: var(--muted); }
  .chart { display: flex; flex-direction: column; gap: var(--s-8); }
  .chart h2 { font-size: var(--t-20); }
  .bars { display: grid; grid-template-columns: max-content 1fr max-content; gap: var(--s-8) var(--s-16); align-items: center; margin-top: var(--s-8); }
  .bars .name { font-weight: var(--w-semi); }
  .bars .track { height: 24px; position: relative; border-left: 2px solid var(--muted); }
  .bars .fill { position: absolute; inset: 0 auto 0 0; background: var(--bar); }
  .bars .zero { display: none; }
  .bars .you { color: var(--brand); font-weight: var(--w-bold); }
  .bars .you + .track { border-left-color: var(--brand); }
  .bars .you ~ .val.you-val { color: var(--brand); font-weight: var(--w-bold); }
  .ads { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--s-16); align-items: start; }
  .ad .who { font-size: var(--t-14); font-weight: var(--w-bold); letter-spacing: var(--track-label); text-transform: uppercase; margin-bottom: var(--s-4); }
  .ad .who.you { color: var(--brand); }
  .ad .for { font-size: var(--t-14); color: var(--muted); margin-top: var(--s-8); }
  .ad img { border: var(--hairline) solid var(--rule); }
  .hooks h2 { font-size: var(--t-20); margin-bottom: var(--s-8); }
  .hk3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-16); }
  .hk3 > div { border-top: 2px solid var(--ink); padding-top: var(--s-8); }
  .hk3 .hg { font-weight: var(--w-bold); }
  .hk3 .hh { color: var(--muted); margin-top: var(--s-4); }
  .rows { display: flex; flex-direction: column; gap: var(--s-16); }
  .row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--s-16); align-items: start;
    border-top: var(--hairline) solid var(--rule); padding-top: var(--s-16); }
  .row h2 { font-size: var(--t-20); margin-bottom: var(--s-8); }
  .row .hook { font-weight: var(--w-semi); margin-top: var(--s-8); }
  .row .src { font-size: var(--t-14); color: var(--muted); margin-top: var(--s-8); }
  .row .ph { aspect-ratio: var(--ar); }
  .p4 { gap: var(--s-16); }
  .proof { display: grid; grid-template-columns: max-content 1fr; gap: var(--s-8) var(--s-24); align-items: baseline;
    border-top: 2px solid var(--ink); padding-top: var(--s-16); }
  .proof .n { font-size: var(--t-56); font-weight: var(--w-bold); line-height: var(--lh-tight); letter-spacing: var(--track-head); }
  .proof p { font-size: var(--t-20); max-width: 34ch; }
  .proof .claim, .proof .ph-tag { grid-column: 1 / -1; max-width: none; }
  .proof .claim { font-size: var(--t-16); }
  .proof .ph-tag { font-size: var(--t-14); padding: var(--s-4) var(--s-8); }
  .proof p.names { grid-column: 1 / -1; color: var(--muted); font-size: var(--t-16); max-width: none; }
  .p4.sep { gap: var(--s-24); }
  .grp { display: flex; flex-direction: column; gap: var(--s-16); border-top: 2px solid var(--ink); padding-top: var(--s-16); }
  .grp .chart { gap: var(--s-8); }
  .rings { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-24); }
  .ring { margin: 0; display: flex; align-items: center; gap: var(--s-16); }
  .ring svg { width: 112px; height: 112px; flex: none; }
  .ring figcaption { font-size: var(--t-16); font-weight: var(--w-semi); }
  @media (max-width: 640px) { .rings { grid-template-columns: 1fr; } }
  .insight { min-height: 0; }
  .close { display: flex; flex-direction: column; gap: var(--s-16); align-items: flex-start; }
  .button { display: inline-block; background: var(--accent); color: var(--on-ink); font-weight: var(--w-bold); font-size: var(--t-16);
    padding: var(--s-16) var(--s-24); border-radius: var(--radius-button); text-decoration: none; }
  .button:focus-visible { outline: 2px solid var(--ink); outline-offset: 3px; }
  .rep { display: flex; align-items: center; gap: var(--s-8); font-size: var(--t-14); }
  .rep .face { width: 40px; height: 40px; border-radius: 50%; background: var(--paper-2); border: var(--hairline) solid var(--rule);
    display: grid; place-items: center; font-weight: var(--w-bold); font-size: var(--t-14); }
  .method { font-size: var(--t-14); color: var(--muted); max-width: var(--measure); }
  @media (max-width: 640px) {
    .page { padding: var(--s-24) var(--s-16); min-height: 0; gap: var(--s-24); margin-bottom: var(--s-16); }
    .p1 h1 { font-size: var(--t-28); }
    .answer { font-size: var(--t-20); }
    .nums.n2 { grid-template-columns: 1fr; grid-template-rows: none; row-gap: var(--s-16); }
    .nums.n2 > div { display: block; grid-row: auto; }
    .bars .val { font-size: var(--t-20); }
    .run { flex-wrap: wrap; gap: var(--s-4) var(--s-16); }
    .page h1 { font-size: var(--t-28); }
    .lede { font-size: var(--t-16); }
    .p1-top { grid-template-columns: 1fr; }
    .box { padding: var(--s-24) var(--s-16); }
    .box .finding { font-size: var(--t-20); }
    .strip { gap: 2px; height: 20px; }
    .nums { grid-template-columns: 1fr; gap: var(--s-16); }
    .sum { grid-template-columns: 1fr; gap: var(--s-16); }
    .nums.vs { grid-template-columns: 1fr; }
    .wstrip { gap: 1px; height: 16px; }
    .sboxes, .flow, .fd, .hk3 { grid-template-columns: 1fr; }
    .fd-you { padding-left: 0; border-left: 0; }
    .arr { transform: rotate(90deg); justify-self: start; }
    .cask { flex-direction: column; align-items: stretch; }
    .cbtn { text-align: center; }
    .ads { grid-template-columns: 1fr 1fr; }
    .row { grid-template-columns: 1fr 1fr; }
    .row .say { grid-column: 1 / -1; }
    .proof .n { font-size: var(--t-40); }
    .proof p { font-size: var(--t-16); }
    .button { display: block; width: 100%; text-align: center; }
    footer { flex-direction: column; gap: var(--s-4); }
  }
  @media print {
    body { background: none; }
    .page { margin: 0; break-after: page; }
  }
  @page { size: A4; margin: 0; }
  .brand-mark { background: none; padding: 0; }
  .brand-mark[style] { padding: var(--s-4); }
  .brand-logo { height: 32px; width: auto; max-width: 200px; }
  .brand-logo[style] { padding: var(--s-4); }
  .fbar { height: 28px; border: var(--hairline) solid var(--on-ink-muted); }
  .fbar i { display: block; height: 100%; background: var(--brand-on-ink); }
  .p1-top figure img { width: auto; max-width: 100%; max-height: 260px; }
  .ads .ad img { width: auto; max-width: 100%; max-height: 240px; }
  .fd-you img { width: auto; max-width: 100%; max-height: 150px; }
  .page.tight { padding-top: var(--s-24); padding-bottom: var(--s-24); gap: var(--s-16); }
  .page.tight .p1-top figure img { max-height: 200px; }
  .page.tight .ads .ad img { max-height: 170px; }
  .page.tight .fd-you img { max-height: 110px; }
  .page.tight .box { padding-top: var(--s-16); padding-bottom: var(--s-16); gap: var(--s-8); }
  .page.tight .head { gap: var(--s-8); }
  .page.tighter h1 { font-size: 32px; }
  .page.tighter .answer { font-size: var(--t-20); }
  .page.tighter .says { font-size: var(--t-16); }
  .page.tighter .p1-top figure img { max-height: 150px; }
  .page.tighter .ads .ad img { max-height: 130px; }
"""

# A page whose text runs long (a long competitor name, a tall ad) is tightened a step at a time until it fits A4: spacing first,
# then type. The kit cannot measure where there is no browser, so the page measures itself.
FIT_JS = ("<script>(function(){function fit(){document.querySelectorAll('section.page').forEach(function(p){"
          "p.classList.remove('tight','tighter');if(window.innerWidth<641)return;"
          "if(p.offsetHeight>%d){p.classList.add('tight');if(p.offsetHeight>%d)p.classList.add('tighter');}});}"
          "fit();if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);"
          "window.addEventListener('load',fit);window.addEventListener('resize',fit);})();</script>" % (1123, 1123))

try:
    STATIC
except NameError:
    from v3_static import STATIC  # noqa: F401 (make_skill_v3.py puts v3_static.py above the kit instead)



# ------------------------------------------------------------------ v3 constants and counts
# The 90 days the launch counts cover run 12 whole weeks and 6 days, 12.9 weeks: 32 ads in them is 2.5 a week, Vrbo's 163 is
# 12.6 (the mock Kevin signed off on 10/22)
WEEKS = 12.9
PAGE_H = 1123  # A4 at 96 dpi: a page that grows past it spills onto a sixth page
SIDE = {"p1": 900, "p3": 640, "thumb": 360}  # longest side of each ad picture, in px
MAX_LINEUP = 700  # live ads the copilot can tag in one run; past it the kit refuses (v2 capped tagging at 600)
GUESTS = 3
SPEND_WORDS = [r"\bcosts?\b", r"\bcost(?:ing|-per|ly)\b", r"\bspend(?:s|ing)?\b", r"\bspent\b", r"\bbudgets?\b",
               r"\b(?:CPA|CPC|CPM|CPL|CAC|ROAS|ROI)s?\b", r"\breturn on (?:ad )?spend\b", r"\bmoney\b"]
# performance words in text we write for the brand; the kit's own page 5 says "winning" about Crux's method
PERFORM = [r"\bwork(?:s|ed)?\b", r"\bwin(?:s|ning|ner|ners)?\b", r"\bproven\b", r"\bbest\b", r"\btop-performing\b",
           r"\bgrow(?:s|th)?\b", r"\bboost\w*\b", r"\bconvert\w*\b", r"\btired\b", r"\bstale\b", r"\bfatigue\w*\b"]
HINTS = {"jargon": "an analysis word; write the count the reader would say",
         "period": "a period with no dates; name it with {since} (\"since July 24\") or drop it",
         "rep": "a note for the rep, not the reader; put it in your reply",
         "internal": "our own word; write \"competitors\", never \"rivals\", and never say who named a brand",
         "spend": "public ads show no spend or results, so the text never names a cost, spend, budget or money",
         "perform": "a performance word; public ads show what ran, not how it did"}
READER_FIELDS = {"p1": ("answer", "caption", "works", "pitfall", "try", "reasons_note"), "p3": ("answer", "opportunity"),
                 "p5": ("answer",)}


def to_tag(spec):
    """The ads to tag, as {brand name: set of ad_ids}: every live ad of every brand. A line-up past MAX_LINEUP live ads is
    refused when the report is built, so pick competitors with fewer ads."""
    as_of = dt.date.fromisoformat(spec["as_of"])
    return {b["name"]: {a["ad_id"] for a in b["ads"] if not ended(a, as_of)} for b in spec["brands"]}


def _day(s):
    return dt.date.fromisoformat(str(s)[:10])


def month_day(d):
    return f"{d.strftime('%B')} {d.day}"


def long_date(d):
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def in_n(k, n):
    """A share in the words a marketer says: "1 in 5", "7 in 10", "none", "almost all"."""
    s = k / n
    if k == 0:
        return "none"
    if s >= .95:
        return "almost all"
    if s < .35:
        return f"1 in {max(2, round(1 / s))}"
    return f"{round(s * 10)} in 10"


def _pkey(spec):
    return str(spec.get("platform") or "META").upper()


def metrics(spec):
    as_of = dt.date.fromisoformat(spec["as_of"])
    start = window_start(as_of)
    days = (as_of - start).days + 1
    merge = spec.get("merge", {})
    named = set(spec.get("named") or [])
    focus = (spec.get("focus") or {}).get("audience")
    one = (spec.get("one_home") or {}).get("tag")
    out = []
    total = 0
    for i, b in enumerate(spec["brands"]):
        ads = [dict(a, format=str(a["format"]).lower()) for a in b["ads"] if not ended(a, as_of)]
        if not ads:
            raise ValueError(f"{b['name']} has no live guest ads on {PLATFORMS[_pkey(spec)]['name']}: " + (
                "take the brand's next platform (Stage 1 step 2b), else stop and tell the rep" if not i else "drop it from brands"))
        total += len(ads)
        bare = [a for a in ads if not a.get("reason_to_buy") or not a.get("audience")]
        if bare:
            raise ValueError(f"{b['name']}: {len(bare)} of its {len(ads)} live ads have no reason_to_buy or audience; "
                             "tag every live ad")
        starts = [_day(a["start_date"]) for a in ads if a.get("start_date")]
        daily = [0] * days
        for s in starts:
            if 0 <= (s - start).days < days:
                daily[(s - start).days] += 1
        weekly = [sum(daily[k * 7:k * 7 + 7]) for k in range(math.ceil(days / 7))]
        n_new = sum(daily)
        peak = max(weekly)
        reasons = {merge.get(a["reason_to_buy"], a["reason_to_buy"]) for a in ads}
        auds = collections.Counter(a["audience"] for a in ads)
        reas = collections.Counter(merge.get(a["reason_to_buy"], a["reason_to_buy"]) for a in ads)
        out.append(types.SimpleNamespace(
            name=b["name"], short=(b.get("short") or b["name"]).strip(), kind=b.get("kind", ""), market=str(b.get("market") or "").strip(), ads=ads, live=len(ads),
            past_end=len(b["ads"]) - len(ads), dropped=dropped_count(b),
            dropped_why=(b.get("dropped_why") or "").strip().rstrip("."),
            reasons=len(reasons), reason_counts=reas, audience_counts=auds,
            named=sum(n for t, n in auds.items() if t in named),
            focus_n=auds.get(focus, 0) if focus else None, one_n=reas.get(merge.get(one, one), 0) if one else None,
            n_new=n_new, no_start=len(ads) - len(starts), daily=daily, weekly=weekly, peak=peak, peak_week=weekly.index(peak),
            pace=round(n_new / WEEKS, 1), last30=sum(1 for s in starts if 0 <= (as_of - s).days <= 30),
            oldest=(as_of - min(starts)).days if starts else 0, formats=collections.Counter(a["format"] for a in ads)))
    if total > MAX_LINEUP:
        raise ValueError(f"the line-up holds {total} live ads, past the {MAX_LINEUP} one run can tag: replace the competitor "
                         "with the most ads by one with fewer, and tell the rep")
    return out


def dropped_count(b):
    n = b.get("dropped", 0)
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError(f"{b['name']}: dropped is {n!r}; give the number of live ads set aside as a whole number, 0 when "
                         "none were")
    return n


# ------------------------------------------------------------------ text
class _Count(string.Formatter):
    def get_field(self, name, args, kwargs):
        v = super().get_field(name, args, kwargs)
        if missing(v[0]) and name.split(".")[-1] not in ("kind", "dropped_why", "market"):
            raise ValueError(f"{{{name}}} would print {v[0]!r}: a count the page shows is never blank, None or N/A")
        return v

    def format_field(self, v, spec):
        if isinstance(v, int) and re.fullmatch(r"[a-z][a-z ]+", spec or ""):
            return plural(v, spec)
        return super().format_field(v, spec)


class _Fill(dict):
    def __missing__(self, k):
        raise KeyError(f"unknown placeholder {{{k}}}")


def fill(text, ctx):
    return _Count().vformat(text, (), _Fill(ctx)) if text else ""


def join_and(items, oxford=False):
    items = list(items)
    if len(items) < 3:
        return " and ".join(items)
    return ", ".join(items[:-1]) + (", and " if oxford else " and ") + items[-1]


def lint(spec):
    """Digits typed by hand in authored text, as (field, digits, text). Each must come from a placeholder instead."""
    found = []

    def scan(where, t):
        if isinstance(t, str):
            bare = re.sub(r"\{[^{}]*\}", "", t)
            bare = re.sub(r'"[^"]*"', "", bare)
            for m in re.finditer(r"\d[\d,.:%]*", bare):
                found.append((where, m.group(0), t[:80]))
        elif isinstance(t, dict):
            for k, v in t.items():
                if k != "ad_id":
                    scan(f"{where}.{k}", v)
        elif isinstance(t, list):
            for i, v in enumerate(t):
                scan(f"{where}[{i}]", v)
    for key in ("text", "guests", "p3_ads", "focus", "named_phrase", "named_one", "one_home"):
        scan(key, spec.get(key))
    return [f for f in found if not f[0].endswith(".unit") and not f[0].endswith(".tag")]


def check_authored(spec):
    """Words the reader should never see in authored text, as (field, word, text, hint)."""
    found = []
    groups = [("jargon", JARGON), ("period", PERIOD), ("internal", INTERNAL), ("rep", REP), ("spend", SPEND_WORDS),
              ("perform", PERFORM)]

    def scan(where, t, gs):
        if isinstance(t, str):
            bare = re.sub(r'"[^"]*"|“[^”]*”', "", re.sub(r"\{[^{}]*\}", "", t))
            for kind, pats in gs:
                for pat in pats:
                    for m in re.finditer(pat, bare, re.I):
                        found.append((where, m.group(0), t[:80], HINTS[kind]))
            if "—" in bare or "–" in bare:
                found.append((where, "a dash", t[:80], "write a comma or a full stop; the report has no em or en dashes"))
        elif isinstance(t, dict):
            for k, v in t.items():
                if k not in ("ad_id", "brand", "tag", "audience", "unit"):
                    scan(f"{where}.{k}", v, gs)
        elif isinstance(t, list):
            for i, v in enumerate(t):
                scan(f"{where}[{i}]", v, gs)
    for key in ("text", "named_phrase", "named_one"):
        scan(key, spec.get(key), groups)
    # hooks, titles, labels and alt text are ad copy and captions: the same words, jargon aside
    for key in ("guests", "p3_ads", "focus"):
        scan(key, spec.get(key), [g for g in groups if g[0] in ("spend", "perform", "internal")])
    return found


def _ctx_names(r):
    return [m.name for m in r.M]


def check_plain(spec, r):
    """Reader text that names the brand instead of saying "you", has a sentence over MAX_WORDS words, or reads above
    grade MAX_GRADE, as (where, problem, text)."""
    found, pages = [], {}
    own = own_names(r.M[0].name)
    names = _ctx_names(r)
    for page, fields in READER_FIELDS.items():
        v = (spec.get("text") or {}).get(page) or {}
        for k in fields:
            if not v.get(k) or k == "alt":
                continue
            t = r.t(page, k)
            bare = re.sub(r'"[^"]*"|“[^”]*”', " ", t)
            rest = bare
            for n in sorted(names[1:], key=len, reverse=True):
                rest = rest.replace(n, " ")
            for n in own:
                if re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", rest):
                    found.append((f"text.{page}.{k}", f"names the brand ({n!r}); talk to the reader: \"your {{b0.live}} "
                                  "live ads\"", t))
                    break
            plain = bare
            for n in sorted(names, key=len, reverse=True):
                plain = plain.replace(n, "Brand")
            for x in _sentences(plain):
                n = len(re.findall(r"[A-Za-z0-9$%'’+]+", x))
                if n > MAX_WORDS:
                    found.append((f"text.{page}.{k}", f"a sentence of {n} words; keep each under {MAX_WORDS + 1}", x))
            pages.setdefault(page, []).append(plain if plain.rstrip()[-1:] in ".?!" else plain + ".")
    for page, parts in sorted(pages.items()):
        g = reading_grade(" ".join(parts))
        if g >= MAX_GRADE + 0.5:
            found.append((page, f"reads at grade {g}; keep each page at grade {MAX_GRADE} or lower: shorter sentences, "
                                "shorter words", " ".join(parts)[:120]))
    return found


# ------------------------------------------------------------------ charts
def bench_svg(B, live, pname="Meta"):
    """Page 2's chart: live ads against monthly spend on one platform for the benchmark accounts, the trend, and the brand's own
    live-ad count as a dashed line (its spend is private)."""
    x0, x1, top, base = 52, 560, 26, 206
    ymax = 3000
    X = lambda sp: x0 + (x1 - x0) * (math.log10(max(sp, 1000)) - 3) / 4
    Y = lambda n: base - (base - top) * math.sqrt(min(n, ymax)) / math.sqrt(ymax)
    F = lambda sp: 10 ** (B["fit"]["intercept"] + B["fit"]["slope"] * math.log10(sp))
    g = [f'<title id="bench-title">Live ads against monthly {pname} spend, {B["accounts"]} Crux accounts</title>',
         f'<desc id="bench-desc">Each dot is one {pname} ad account on Crux. Brands that spend more run more live ads; the dashed '
         f'line is your {live}.</desc>']
    for t in (0, 50, 100, 250, 500, 1000, 3000):
        g.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke="var(--rule)"/>'
                 f'<text x="{x0 - 8}" y="{Y(t) + 4:.1f}" font-size="12" fill="var(--muted)" text-anchor="end">'
                 f'{t if t < 1000 else f"{t // 1000}K"}</text>')
    for sp, lab in ((1e3, "$1K"), (1e4, "$10K"), (1e5, "$100K"), (1e6, "$1M"), (1e7, "$10M")):
        g.append(f'<text x="{X(sp):.1f}" y="{base + 18}" font-size="12" fill="var(--muted)" text-anchor="middle">{lab}</text>')
    for sp, n in B["points"]:
        g.append(f'<circle cx="{X(sp):.1f}" cy="{Y(n):.1f}" r="4" fill="var(--bar)" stroke="var(--muted)" stroke-width=".8"/>')
    trend = " ".join(f"{X(10 ** lx):.1f},{Y(F(10 ** lx)):.1f}" for lx in [3 + k * 0.05 for k in range(81)])
    g.append(f'<polyline points="{trend}" fill="none" stroke="var(--ink)" stroke-width="2.5"/>'
             f'<line x1="{x0}" y1="{Y(live):.1f}" x2="{x1}" y2="{Y(live):.1f}" stroke="var(--brand)" stroke-width="2" '
             f'stroke-dasharray="6 4"/>'
             f'<text x="{x1 + 8}" y="{Y(live) + 4:.1f}" font-size="13" font-weight="700" fill="var(--brand)">You: {live}</text>'
             f'<text x="{x1 + 8}" y="{Y(F(1e7)) + 4:.1f}" font-size="13" font-weight="700" fill="var(--ink)">Typical</text>'
             f'<text x="{(x0 + x1) / 2}" y="{base + 36}" font-size="12" fill="var(--muted)" text-anchor="middle">What each '
             f'brand spends on {pname} in a month</text>'
             f'<text x="{x0 + 6}" y="{top - 12}" font-size="12" fill="var(--muted)">live ads (dots: brands on Crux)</text>')
    return (f'<div class="bench-wrap"><svg class="bench" viewBox="0 0 640 {base + 44}" role="img" '
            f'aria-labelledby="bench-title bench-desc">{"".join(g)}</svg></div>')


def speed_svg(start, as_of, you, them):
    """Page 4's chart: running totals of live ads launched since the window began, the brand against one competitor."""
    n = (as_of - start).days + 1
    cum = lambda c: [sum(c[:i + 1]) for i in range(n)]
    cy, cv = cum(you.daily), cum(them.daily)
    W, Hh, L, T, B = 666, 200, 40, 16, 30
    R = min(230, max(110, int(9.2 * len(f"{them.short} {cv[-1]}")) + 14))
    top = max(cy[-1], cv[-1], 1) * 1.07
    step = next(s for s in (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000) if top / s <= 4.5)
    X = lambda i: L + i / (n - 1) * (W - L - R)
    Y = lambda v: T + (1 - v / top) * (Hh - T - B)

    def path(c):
        pts, prev = [], 0
        for i, v in enumerate(c):
            pts += [f"{X(i):.1f},{Y(prev):.1f}", f"{X(i):.1f},{Y(v):.1f}"]
            prev = v
        return " ".join(pts)
    grid = "".join(f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--rule)"/>'
                   f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="12" fill="var(--muted)">{v}</text>'
                   for v in range(0, int(top) + 1, step))
    ticks = [start, start + dt.timedelta(days=28), start + dt.timedelta(days=56), as_of]
    xt = "".join(f'<text x="{X((d - start).days):.1f}" y="{Hh - 8}" text-anchor="middle" font-size="12" '
                 f'fill="var(--muted)">{d.strftime("%b")} {d.day}</text>' for d in ticks)
    bi = them.peak_week * 7
    be = min(bi + 6, n - 1)
    ann = ""
    if them.peak >= 8 and them.peak >= 3 * max(you.peak, 1):
        ann = (f'<line x1="{X(bi + 3):.1f}" x2="{X(bi + 3):.1f}" y1="{Y(cv[be]) + 4:.1f}" y2="{Y(cv[bi]) - 4:.1f}" '
               f'stroke="var(--muted)" stroke-dasharray="3 3"/>'
               f'<text x="{X(bi + 3) - 8:.1f}" y="{Y((cv[bi] + cv[be]) / 2):.1f}" text-anchor="end" font-size="13" '
               f'fill="var(--ink)" font-weight="600">{them.peak} in one week</text>')
    yv, yy = Y(cv[-1]), Y(cy[-1])
    if abs(yv - yy) < 18:
        yv, yy = (yv - 9, yy + 9) if yv <= yy else (yv + 9, yy - 9)
    label = lambda y, cls, t: f'<text x="{W - R + 8}" y="{y + 5:.1f}" font-size="15" font-weight="700" fill="{cls}">{esc(t)}</text>'
    return (f'<svg class="lines" viewBox="0 0 {W} {Hh}" role="img" aria-label="Live ads added since {month_day(start)}: you '
            f'{cy[-1]}, {esc(them.short)} {cv[-1]}">{grid}{xt}'
            f'<polyline points="{path(cv)}" fill="none" stroke="var(--bar-dark)" stroke-width="3"/>'
            f'<polyline points="{path(cy)}" fill="none" stroke="var(--brand)" stroke-width="3"/>{ann}'
            f'{label(yv, "var(--muted)", f"{them.short} {cv[-1]}")}{label(yy, "var(--brand)", f"You {cy[-1]}")}</svg>')


def ring_fig(n, k, label, arc_col):
    r, c, s = 54, 70, 22
    circ = 2 * math.pi * r
    arc = (f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{arc_col}" stroke-width="{s}" '
           f'stroke-dasharray="{circ * k / n:.1f} {circ:.1f}" transform="rotate(-90 {c} {c})"/>') if k else ""
    return (f'<figure class="ring"><svg viewBox="0 0 140 140" role="img" aria-label="{esc(label)}"><circle cx="{c}" cy="{c}" '
            f'r="{r}" fill="none" stroke="var(--bar)" stroke-width="{s}"/>{arc}'
            f'<text x="{c}" y="{c + 2}" text-anchor="middle" font-size="30" font-weight="700" fill="var(--ink)">{k}</text>'
            f'<text x="{c}" y="{c + 20}" text-anchor="middle" font-size="13" fill="var(--muted)">of {n}</text></svg>'
            f'<figcaption>{esc(label)}</figcaption></figure>')


# ------------------------------------------------------------------ the report
def _px(uri):
    from PIL import Image
    return Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).size


class Report:
    def __init__(self, spec):
        self.s = spec
        self.raw_accent = spec["brand"].get("accent") or "#F66135"
        self.A, self.A_INK = _shade(self.raw_accent, PAPER), _shade(self.raw_accent, DARK)
        self.as_of = dt.date.fromisoformat(spec["as_of"])
        self.start = window_start(self.as_of)
        self.pk = _pkey(spec)
        self.directional = spec.get("sample") == "directional"
        if self.pk not in PLATFORMS:
            raise ValueError(f"platform {spec.get('platform')!r} must be one of {', '.join(PLATFORMS)}")
        self.P = PLATFORMS[self.pk]
        self.M = metrics(spec)
        self.B = dict(spec.get("benchmark") or load_benchmark(platform=self.pk))
        self.B.setdefault("none", self.B["accounts"] < BENCH_DROP_BELOW)
        self.B.setdefault("caveat", self.B["accounts"] < BENCH_CAVEAT_BELOW)
        self.guess = max(self.M[1:], key=lambda m: m.live) if len(self.M) > 1 else None
        self.c = next((m for m in self.M[1:] if m.name == spec.get("compare")), None)
        self.brand = self._brand()
        self.uri = {}
        self.ctx = self._ctx()

    # placeholders available to authored text
    def _ctx(self):
        b0, c = self.M[0], self.c or self.guess
        ctx = {"as_of": long_date(self.as_of), "since": f"since {month_day(self.start)}", "brand": b0.name, "b0": b0, "c": c,
               "rep": self.s.get("rep", "")}
        for i, m in enumerate(self.M):
            ctx[f"b{i}"] = m
        pts = self.B["points"]
        n = [a for sp, a in pts if sp >= 1e5]
        if self.B["none"]:
            n = []
        ctx["t100"] = types.SimpleNamespace(n=len(n), median=int(statistics.median(n) + .5) if n else 0, label="$100K+")
        guests = len(self.s.get("guests") or []) or GUESTS
        new = guests * (b0.one_n or 0)
        ctx.update(new_ads=new, total_ads=b0.live + new, bench_n=self.B["accounts"], platform=self.P["name"])
        return ctx

    def t(self, page, key):
        """Authored text with its placeholders filled."""
        return fill(((self.s.get("text") or {}).get(page) or {}).get(key, ""), self.ctx)

    def _brand(self):
        b, out = self.s["brand"], {"logo": None, "tile": None, "flags": [], "accent": self.A, "accent_ink": self.A_INK}
        if self.A.upper() != self.raw_accent.upper():
            out["flags"].append(f"accent {self.raw_accent} darkened to {self.A} so it reads on the paper")
        self.logo = None
        if b.get("logo"):
            uri, r, lum = _logo(b["logo"])
            self.logo = (uri, r)
            out.update(logo=uri[5:uri.index(";")], aspect=round(r, 2))
            if _contrast(lum, 1.0) < 3:
                out["tile"] = self.raw_accent if _contrast(lum, _lum(_hex(self.raw_accent))) >= 3 else INK
                out["flags"].append(f"light logo set on a {out['tile']} tile so it shows on the page")
            if r < 1.5:
                out["flags"].append("square mark: the brand name is set beside it")
        elif b.get("logo_missing"):
            out["flags"].append(f"no logo: the header prints the brand name (tried: {b['logo_missing']})")
        else:
            out["flags"].append("no logo yet")
        return out

    def problems(self):
        """Every reason the report cannot be built from this spec, one message each (a rebuild fixes them all)."""
        s, out = self.s, []
        M, b0, c = self.M, self.M[0], self.c
        for k in ("rep", "rep_email", "calendly", "compare", "p1_ad", "named_phrase", "named_one"):
            if not s.get(k):
                out.append(f"spec needs {k}")
        if not s["brand"].get("name"):
            out.append("spec needs brand.name")
        if not any(m.name == s.get("compare") for m in M[1:]):
            out.append(f"compare {s.get('compare')!r} must be the name of a competitor in brands[1:]: "
                       f"{', '.join(m.name for m in M[1:]) or 'none given'}")
        if self.pk != "META" and not (s.get("live_rule") or "").strip():
            out.append(f"spec needs live_rule on {self.P['name']}: what live means there, in the footer's words "
                       "(e.g. \"seen in the last 7 days\")")
        for b in s["brands"]:
            odd = collections.Counter(str(a["platform"]).upper() for a in b["ads"]
                                      if a.get("platform") and str(a["platform"]).upper() != self.pk)
            for x, k in odd.items():
                out.append(f"{b['name']}: {k} ads are from {PLATFORMS.get(x, {'name': x})['name']}, not {self.P['name']}: "
                           "count one platform per report")
        if s.get("sample") not in (None, *SAMPLES):
            out.append(f"sample {s['sample']!r} must be one of {', '.join(map(repr, SAMPLES))}, or left out")
        floor = SMALL_SAMPLE_MIN if self.directional else MIN_RIVAL_ADS
        for m in M[1:]:
            if m.live < floor:
                out.append(f"{m.name} has {m.live} live guest ads after set-asides and ended ads; a competitor on "
                           f"{self.P['name']} needs at least {floor}" + (" even in a directional report" if self.directional else "")
                           + ". Replace it")
        for m in M:
            if not m.market:
                out.append(f"{m.name} needs a market, as the line-up's Market column says it")
        f = s.get("focus") or {}
        for k in ("audience", "phrase", "short", "other"):
            if not f.get(k):
                out.append(f"focus needs {k}")
        if f.get("audience") and not b0.focus_n:
            out.append(f"focus.audience {f['audience']!r} is on none of your live ads; its tags: "
                       + ", ".join(f"{t!r} ({n})" for t, n in b0.audience_counts.most_common(4)))
        if not s.get("named"):
            out.append("spec needs named: the audience tags that name who the trip is for")
        else:
            allt = {t for m in M for t in m.audience_counts}
            gone = [t for t in s["named"] if t not in allt]
            if gone:
                out.append(f"named tags on no live ad of any brand: {gone}")
        if c and s.get("named") and not c.named:
            out.append(f"{c.name} has no live ad tagged with a named audience, so page 3 has no gap to show: pick another "
                       "compare or other named tags")
        oh = s.get("one_home") or {}
        if not oh.get("tag") or not oh.get("unit"):
            out.append("spec needs one_home: {\"tag\": reason_to_buy tag of the ads that each show one product, \"unit\": "
                       "\"home\"}")
        elif not b0.one_n:
            out.append(f"one_home.tag {oh['tag']!r} is on none of your live ads; its reasons: "
                       + ", ".join(f"{t!r} ({n})" for t, n in b0.reason_counts.most_common(4)))
        g = s.get("guests") or []
        if len(g) != GUESTS:
            out.append(f"guests needs exactly {GUESTS} entries, one per kind of guest the report suggests testing")
        for i, x in enumerate(g):
            for k in ("who", "one", "title", "hook"):
                if not (x or {}).get(k):
                    out.append(f"guests[{i}] needs {k}")
        if b0.pace == 0:
            out.append(f"you launched no ads {self.ctx['since']}, so pages 1 and 4 cannot show a pace: stop and tell the rep")
        if c and c.pace == 0:
            out.append(f"{c.name} launched no ads {self.ctx['since']}: pick another compare")
        rows = {m.name: {str(a["ad_id"]): a for a in m.ads} for m in M}
        if s.get("p1_ad") and str(s["p1_ad"]) not in rows[b0.name]:
            out.append(f"p1_ad {s['p1_ad']} is not one of your live ads")
        p3 = s.get("p3_ads") or []
        if len(p3) != 4:
            out.append("p3_ads needs exactly 4 ads: one of yours, then competitors' ads built for a named guest")
        for i, x in enumerate(p3):
            if x.get("brand") not in rows or str(x.get("ad_id")) not in rows.get(x.get("brand"), {}):
                out.append(f"p3_ads[{i}]: ad {x.get('ad_id')} is not a live ad of {x.get('brand')!r}")
            for k in ("for", "alt"):
                if not x.get(k):
                    out.append(f"p3_ads[{i}] needs {k}")
        if p3 and p3[0].get("brand") != b0.name:
            out.append("p3_ads[0] must be one of your own live ads")
        for page, fields in READER_FIELDS.items():
            for k in fields:
                if not ((s.get("text") or {}).get(page) or {}).get(k):
                    out.append(f"text.{page}.{k} is empty")
        for w, d, t in lint(s):
            out.append(f"digits typed by hand in {w}: {d!r} in {t!r}; use a placeholder ({{b0.live}}, {{c.live}}, ...)")
        return out

    def summary(self):
        """The counts the copilot writes against, before it writes the text."""
        b0, M, B = self.M[0], self.M, self.ctx
        lines = [f"as of {long_date(self.as_of)}; launch counts {B['since']}; benchmark {self.B['accounts']} accounts, "
                 f"brands at $100K+ a month typically run {B['t100'].median} live ads ({B['t100'].n} brands)"]
        if self.pk != "META" or self.B["caveat"]:
            lines.insert(0, f"platform: {self.P['name']}; benchmark: {self.B['accounts']} accounts, "
                            + ("none" if self.B["none"] else "caveat" if self.B["caveat"] else "full"))
        for i, m in enumerate(M):
            top = ", ".join(f"{t!r} {n}" for t, n in m.audience_counts.most_common(4))
            rs = ", ".join(f"{t!r} {n}" for t, n in m.reason_counts.most_common(4))
            lines.append(f"b{i} {m.name}: {m.live} live ads, {m.reasons} reasons, {m.n_new} launched {B['since']} "
                         f"({m.pace:g} a week, busiest week {m.peak}), {m.last30} in the last 30 days, set aside {m.dropped}"
                         f"\n    audiences: {top}\n    reasons: {rs}")
        g = self.guess
        if g:
            lines.append(f"compare (the competitor with the most live ads): {g.name}; its named-audience ads, once `named` is "
                         f"set: {g.named}")
        return "\n".join(lines)

    # ---------------------------------------------------------------- html
    def img(self, row, alt, side=720, cls=""):
        """An ad's picture inline, with its size."""
        src = row.get("image")
        data = _img_bytes(src)
        if not data or _blank(data):
            raise ValueError(f"the picture of ad {row['ad_id']} did not load or is blank; pick another ad")
        uri = _data_uri(data, side)
        if not uri:
            raise ValueError(f"the picture of ad {row['ad_id']} is not an image the kit can read; pick another ad")
        w, h = _px(uri)
        return f'<img{cls} src="{uri}" width="{w}" height="{h}" alt="{esc(alt)}">'

    def run(self):
        b0 = self.M[0]
        name = esc(b0.name)
        if self.logo:
            uri, r = self.logo
            tile = self.brand["tile"]
            style = f' style="background:{tile}"' if tile else ""
            if r < 1.5:
                mark = f'<img class="brand-mark"{style} src="{uri}" alt="">{name}'
            else:
                mark = f'<img class="brand-logo"{style} src="{uri}" alt="{name}">'
        else:
            mark = name
        return (f'<div class="run"><div class="brand">{mark}</div>'
                f'<div class="when">From Crux, {long_date(self.as_of)}</div></div>')

    def small_note(self):
        """The footer line that labels a directional report, on the pages that set the compare competitor beside the brand."""
        if not self.directional:
            return ""
        return f" Small sample: {esc(self.c.short)} has {plural(self.c.live, 'live ad')} in this line, so read this as a direction."

    def foot(self, n, left):
        return f'<footer><span>{left}</span><span>Prepared by Crux · {n} / 5</span></footer>'

    def _focus_strip(self):
        b0, f = self.M[0], self.s["focus"]
        if b0.live <= 80:
            marks = '<i class="on"></i>' * b0.focus_n + "<i></i>" * (b0.live - b0.focus_n)
            kind = f'<div class="strip" role="img" aria-label="{b0.live} marks, one per live ad. {b0.focus_n} are filled: {esc(f["short"].lower())}.">{marks}</div>'
        else:
            kind = (f'<div class="fbar" role="img" aria-label="{b0.focus_n} of {b0.live} live ads: {esc(f["short"].lower())}.">'
                    f'<i style="width:{100 * b0.focus_n / b0.live:.1f}%"></i></div>')
        return kind + (f'<div class="strip-key"><span class="on">{esc(f["short"])}</span><span>{esc(f["other"])}</span></div>')

    def p1_foot(self):
        rule = (self.s.get("live_rule") or "").strip()
        live = f", live = {esc(rule)}" if rule else ""
        out = f"{self.P['library']}{live}, {long_date(self.as_of)}. We count ads, not money spent."
        if self.pk == "GOOGLE":
            out += " Image and video ads only."
        elif self.pk == "LINKEDIN":
            out += f" Pulled from LinkedIn's ad library on {long_date(self.as_of)}."
        return out + self.small_note()

    def page1(self):
        b0, c, s = self.M[0], self.c, self.s
        f = s["focus"]
        pace = lambda m: f"{m.pace:g}"
        lede = f"Your {b0.live} live {self.P['name']} ads, next to {join_and([poss(m.short) for m in self.M[1:]])}."
        ad = next(a for a in b0.ads if str(a["ad_id"]) == str(s["p1_ad"]))
        photo = self.img(ad, self.t("p1", "alt"), SIDE["p1"])
        return f'''<section class="page p1" data-page="1">
  {self.run()}
  <div class="p1-top">
    <div class="head"><h1>What do your {self.P["name"]} ads sell?</h1>
    <p class="answer">{esc(self.t("p1", "answer"))}</p></div>
    <p class="lede">{esc(lede)}</p>
    <figure>
      {photo}
      <figcaption>{esc(self.t("p1", "caption"))}</figcaption>
    </figure>
  </div>
  <div class="box">
    <p class="finding"><em>{b0.focus_n} of your {b0.live}</em> live ads sell {esc(f["phrase"])}.</p>
    {self._focus_strip()}
    <dl class="rows3"><dt>Works</dt><dd>{esc(self.t("p1", "works"))}</dd><dt>Pitfall</dt><dd>{esc(self.t("p1", "pitfall"))}</dd><dt>Try</dt><dd class="tl">{esc(self.t("p1", "try"))}</dd></dl>
  </div>
  <div class="nums vs">
    <div><p class="lab">How many you run.</p><div class="pair"><p class="you"><b>{b0.live}</b><span>You</span></p><p class="them"><b>{c.live}</b><span>{esc(c.short)}</span></p></div><p class="say">Live ads running now.</p></div>
    <div><p class="lab">How varied they are.</p><div class="pair"><p class="you"><b>{b0.reasons}</b><span>You</span></p><p class="them"><b>{c.reasons}</b><span>{esc(c.short)}</span></p></div><p class="say">{esc(self.t("p1", "reasons_note"))}</p></div>
    <div><p class="lab">How often you launch.</p><div class="pair"><p class="you"><b>{b0.n_new}</b><span>You, of {b0.live}</span></p><p class="them"><b>{c.n_new}</b><span>{esc(c.short)}, of {c.live}</span></p></div><p class="say">New since {month_day(self.start)}, about {pace(b0)} a week.</p></div>
  </div>
  {self.foot(1, self.p1_foot())}
</section>'''

    def page2(self):
        b0, c, s = self.M[0], self.c, self.s
        t100, new, total = self.ctx["t100"], self.ctx["new_ads"], self.ctx["total_ads"]
        unit = s["one_home"]["unit"]
        buyer = esc(s.get("buyer") or "guest")
        Pn, B = self.P["name"], self.B
        show_t = bool(t100.n)
        base = max(b0.live, t100.median, total, c.live)
        w = lambda v: f"{100 * v / base:.1f}%"
        ones = join_and([x["one"] for x in s["guests"]], oxford=True)
        typ = f"typical brand at $100K+ a month {t100.median}; " if show_t else ""
        label = f"Live ads: you now {b0.live}; {typ}you with {new} new-{buyer} ads {total}; {c.short} {c.live}."
        bars = f'<p class="hn you">You now</p><div class="ht"><i class="y" style="width:{w(b0.live)}"></i></div><p class="hv you">{b0.live}</p>'
        if show_t:
            bars += f'<p class="hn">Typical at $100K+</p><div class="ht"><i class="v" style="width:{w(t100.median)}"></i></div><p class="hv">{t100.median}</p>'
        bars += (f'<p class="hn you">You with new-{buyer} ads</p><div class="ht"><i class="y" style="width:{w(b0.live)}"></i><i class="new" style="width:{w(new)}"></i></div><p class="hv you">{total}</p>'
                 f'<p class="hn">{esc(c.short)}</p><div class="ht"><i class="v" style="width:{w(c.live)}"></i></div><p class="hv">{c.live}</p>')
        if B["none"]:
            answer = f"{b0.live} live ads. We can't see your spend, and Crux has too few {Pn} accounts to show what a brand at your spend runs."
            chart = ""
            says = f"Ads for new {buyer}s would take you from {b0.live} to {total}."
            foot = (f"No spend benchmark: Crux has {B['accounts']} {Pn} {'account' if B['accounts'] == 1 else 'accounts'} that pay in US dollars, "
                    "too few to show. We count ads, not money spent.")
        else:
            end = dt.datetime.strptime(B["window"].split(" to ")[1], "%d %b %Y").date()
            answer = (f"{b0.live} live ads. We can't see your spend, but brands at $100K+ a month typically run {t100.median}."
                      if show_t else f"{b0.live} live ads. We can't see your spend.")
            caveat = ""
            if B["caveat"]:
                caveat = (f'\n    <p class="small">Based on {B["accounts"]} {Pn} accounts on Crux that pay in US dollars, {esc(B["window"])}. '
                          'A small sample, a guide only.</p>')
            chart = f'''<div class="chart">
    <h2>Live ads at {B["accounts"]} brands on Crux, by what each spends on {Pn} in a month</h2>
    {bench_svg(B, b0.live, Pn)}
    <p class="small">Each dot is one brand. Your spend is private, so you show as a line. A guide, not a target.</p>{caveat}
  </div>
  '''
            says = f"Bigger budgets run more ads. Ads for new {buyer}s would take you from {b0.live} to {total}."
            foot = f"{B['accounts']} {Pn} ad accounts on Crux that pay in US dollars, 30 days to {long_date(end)}. We count ads, not money spent."
        typical = ""
        if show_t:
            typical = (" Typical: the middle brand on Crux at that spend." if not B["caveat"]
                       else f" Typical: the middle of {t100.n} {Pn} {'account' if t100.n == 1 else 'accounts'} at $100K+ a month.")
        return f'''<section class="page pv" data-page="2">
  {self.run()}
  <div class="head"><h1>How many ads do you run?</h1>
  <p class="answer">{answer}</p></div>
  {chart}<p class="says">{says}</p>
  <div class="chart hb">
    <h2>Live ads</h2>
    <div class="hbars" role="img" aria-label="{esc(label)}">{bars}</div>
  </div>
  <p class="small">The {new} new ads: {esc(ones)} version of your {b0.one_n} ads that each show one {esc(unit)}.{typical}</p>
  {self.foot(2, foot)}
</section>'''

    def page3(self):
        b0, c, s = self.M[0], self.c, self.s
        rivals = sorted(self.M[1:], key=lambda m: (-m.named / m.live, m.name))
        rows = [("You", b0, True)] + [(m.short, m, False) for m in rivals]
        label = ", ".join(f"{('Your ads' if y else m.short)} {m.named} of {m.live}" for _, m, y in rows)
        bars = ""
        for name, m, you in rows:
            share = 100 * m.named / m.live
            val = f"{m.named} <small>of your {m.live} live ads</small>" if you else f"{m.named} <small>of {esc(poss(m.short))} {m.live}</small>"
            track = '<span class="zero"></span>' if not m.named else f'<span class="fill" style="width:{share:.1f}%"></span>'
            bars += (f'<span class="name{" you" if you else ""}">{esc(name)}</span><span class="track">{track}</span>'
                     f'<span class="val{" you-val you" if you else ""}">{val}</span>')
        mine = "none" if not b0.named else str(b0.named)
        says = f"{c.short} built {c.named} of its live ads for {s['named_phrase']}. You built {mine}."
        rows_by = {m.name: {str(a["ad_id"]): a for a in m.ads} for m in self.M}
        shorts = {m.name: m.short for m in self.M}
        ads = ""
        for x in s["p3_ads"]:
            you = x["brand"] == b0.name
            row = rows_by[x["brand"]][str(x["ad_id"])]
            ads += (f'<div class="ad"><p class="who{" you" if you else ""}">{"Your ad" if you else esc(shorts[x["brand"]])}</p>'
                    f'{self.img(row, x["alt"], SIDE["p3"])}<p class="for">{esc(x["for"])}</p></div>')
        hooks = "".join(f'<div><p class="hg">{esc(g["title"])}</p><p class="hh">&ldquo;{esc(g["hook"])}&rdquo;</p></div>'
                        for g in s["guests"])
        buyer = esc(s.get("buyer") or "guest")
        left = "Who an ad is built for comes from its words and picture."
        if b0.dropped:
            left += f" We left out {b0.dropped} of your ads for {esc(b0.dropped_why)}."
        left += self.small_note()
        return f'''<section class="page p2" data-page="3">
  {self.run()}
  <div class="head"><h1>What do competitors do that you don't?</h1>
  <p class="answer">{esc(self.t("p3", "answer"))}</p></div>
  <div class="chart">
    <h2>Live ads built for {esc(s["named_one"])}</h2>
    <div class="bars" role="img" aria-label="Ads built for {esc(s["named_phrase"])}: {esc(label)}.">{bars}</div>
  </div>
  <p class="says">{esc(says)}</p>
  <p class="bold-line">{esc(self.t("p3", "opportunity"))}</p>
  <div class="ads">{ads}</div>
  <div class="hooks"><h2>Three hooks to test, one per {buyer}</h2><div class="hk3">{hooks}</div></div>
  {self.foot(3, left)}
</section>'''

    def p4_foot(self):
        n = self.M[0].no_start + self.c.no_start
        out = "Only ads still running are counted. Public ads show no spend or sales."
        if n:
            out += f" {n} live ads show no start date and are not in the pace."
        return out + self.small_note()

    def page4(self):
        b0, c, s = self.M[0], self.c, self.s
        new = self.ctx["new_ads"]
        unit = s["one_home"]["unit"]
        wy, wc = round(new / b0.pace), round(new / c.pace)
        few = self.directional and c.n_new < MIN_LAUNCHES
        base = wy if few else max(wy, wc)
        who = join_and([g["who"] for g in s["guests"]])
        since = f"{month_day(self.start)}"
        if c.peak >= 8 and c.peak >= 3 * max(b0.peak, 1):
            answer = f"About {b0.pace:g} new ads a week. {c.short} launched {c.peak} ads in one week."
        else:
            answer = f"About {b0.pace:g} new ads a week. {c.short} launched about {c.pace:g} a week."
        bars = f'<p class="hn you">You, {b0.pace:g} a week</p><div class="ht"><i class="y" style="width:{100 * wy / base:.1f}%"></i></div><p class="hv you">{plural(wy, "week")}</p>'
        if few:
            bars += f'<p class="small" style="grid-column:1/-1">{esc(c.short)} launched {plural(c.n_new, "ad")} since {since}, too few to compare.</p>'
            wlabel = f"Weeks to launch {new} new ads: you {wy}; {esc(c.short)} launched too few ads to compare."
        else:
            bars += f'<p class="hn">{esc(c.short)}, {c.pace:g} a week</p><div class="ht"><i class="v" style="width:{100 * wc / base:.1f}%"></i></div><p class="hv">{plural(wc, "week")}</p>'
            wlabel = f"Weeks to launch {new} new ads: you {wy}, {esc(c.short)} {wc}."
        cap = lambda m, who: f"{who} live ads: {m} went up in the last 30 days"
        rings = (ring_fig(b0.live, b0.last30, cap(b0.last30, "Your"), "var(--brand)")
                 + ring_fig(c.live, c.last30, cap(c.last30, poss(c.short)), "var(--bar-dark)"))
        mine = in_n(b0.last30, b0.live)
        theirs = in_n(c.last30, c.live)
        if mine == "none":
            first = "None of your live ads is under a month old."
        elif mine == "almost all":
            first = "Almost all of your live ads are under a month old."
        else:
            first = f"About {mine} of your live ads is under a month old."
        second = f"{c.short} has none." if theirs == "none" else f"{poss(c.short)} is {theirs}."
        return f'''<section class="page p4 sep" data-page="4">
  {self.run()}
  <div class="head"><h1>How often do you launch new ads?</h1>
  <p class="answer">{esc(answer)}</p></div>
  <div class="grp">
  <div class="chart">
    <h2>Live ads launched since {since}, you against {esc(c.short)}</h2>
    <div class="lwrap">{speed_svg(self.start, self.as_of, b0, c)}</div>
  </div>
  <p class="says">Since {since}, you launched {b0.n_new} new ads. {esc(c.short)} launched {c.n_new}.</p>
  </div>
  <div class="grp">
  <p class="says">One ad each for {esc(who)} on your {b0.one_n} {esc(unit)} ads is {new} ads. At your pace, that is {plural(wy, "week")}.</p>
  <div class="chart hb"><h2>Weeks to launch {new} new ads</h2><div class="hbars" role="img" aria-label="{wlabel}">{bars}</div></div>
  </div>
  <div class="grp">
  <div class="chart rg"><h2>How many live ads went up in the last 30 days?</h2><div class="rings">{rings}</div><p class="says">{esc(first)} {esc(second)}</p></div>
  </div>
  {self.foot(4, self.p4_foot())}
</section>'''

    def page5(self):
        b0, s = self.M[0], self.s
        ad = next(a for a in b0.ads if str(a["ad_id"]) == str(s["p1_ad"]))
        thumb = self.img(ad, f"One of your {s['one_home']['unit']} ads", SIDE["thumb"])
        guests = join_and([f"<em>{esc(g['who'])}</em>" for g in s["guests"]])

        def st(k, alt, cap=None):
            u, w, h = STATIC[k]
            return f'<img src="{u}" width="{w}" height="{h}" alt="{esc(alt)}">'
        logos = "".join(f'<img src="{STATIC["logo-" + k][0]}" alt="{n}">' for k, n in
                        (("cloaked", "Cloaked"), ("rocketmoney", "Rocket Money"), ("sofi", "SoFi"), ("noom", "Noom"),
                         ("ag1", "AG1"), ("wise", "Wise"), ("lifelock", "LifeLock"), ("gen", "Gen")))
        return f'''<section class="page p6 deck6" data-page="5">
  {self.run()}
  <div class="head"><h1>What would Crux do for you?</h1>
  <p class="answer">{esc(self.t("p5", "answer"))}</p></div>
  <div class="dk">
    <h2 class="dhead">Crux makes <em>new ads inspired by your winning ads</em>.</h2>
    <div class="fd"><figure>{st("rm-in", "Rocket Money's app photos")}<figcaption>Rocket Money's app photos</figcaption></figure><span class="arr" aria-hidden="true">&rarr;</span><figure>{st("rm-out", "Four new Rocket Money ads made by Crux")}<figcaption>New ads Crux made from them</figcaption></figure><div class="fd-you"><p class="fd-h">For you, the same move.</p>{thumb}<p>Your {esc(s["one_home"]["unit"])} photos, made into ads for {guests}.</p></div></div>
    <div class="sboxes"><div class="sbox"><p class="sl">Creatives tested</p><p class="sn">600 to 800</p><p class="ss">new ads a month at Cloaked, a privacy app</p></div><div class="sbox"><p class="sl">Purchases from AI ads</p><p class="sn">Nearly half</p><p class="ss">of Cloaked's Meta purchases</p></div><div class="sbox"><p class="sl">AI ads launched</p><p class="sn">20,000+</p><p class="ss">with Crux in just 3 months</p></div></div>
    <div class="trust"><p>Trusted by</p><div class="logos">{logos}</div></div>
  </div>
  <div class="cask"><div><h2>Talk to the founders.</h2><p>Plan your first tests with Crux's founders.</p></div><a class="cbtn" href="{esc(s["calendly"])}">Book a time with Atharva &rarr;</a></div>
  {self.foot(5, f"Questions? Reply to {esc(s['rep'])}, {esc(s['rep_email'])}. Figures from Crux customers.")}
</section>'''

    def html(self):
        fonts = _fonts()
        self.brand["fonts"] = bool(fonts)
        if not fonts:
            self.brand["flags"].append("the kit font did not download, so the page uses Helvetica; build again before you "
                                       "check the pages")
        name = esc(self.M[0].name)
        css = (CSS + f"\n:root{{--brand:{self.A};--brand-on-ink:{self.A_INK}}}")
        return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                f'<title>{name} {self.P['name']} ads report</title>\n<style>\n{fonts}{css}\n</style>\n</head>\n<body>\n'
                + "\n".join(p() for p in (self.page1, self.page2, self.page3, self.page4, self.page5))
                + "\n" + FIT_JS + "\n</body>\n</html>\n")


# ------------------------------------------------------------------ checks
def measure(doc, notes=None):
    """What runs past its page once the report is laid out in Chromium, as a list of problems; None when no browser runs
    here."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            try:
                pg = b.new_page(viewport={"width": 900, "height": 1200})
                pg.set_content(doc, wait_until="networkidle")
                pg.wait_for_timeout(300)
                heights = pg.evaluate("[...document.querySelectorAll('section.page')].map(p => Math.round(p.getBoundingClientRect().height))")
                broken = pg.evaluate("[...document.images].filter(i => !i.naturalWidth).length")
                pg.set_viewport_size({"width": 375, "height": 800})
                pg.wait_for_timeout(200)
                wide = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            finally:
                b.close()
    except Exception:
        return None
    out = [f"page {i}: {h} px tall, {PAGE_H} allowed: shorten that page's text" for i, h in enumerate(heights, 1) if h > PAGE_H]
    if len(heights) != 5:
        out.append(f"{len(heights)} pages, not 5")
    if broken:
        out.append(f"{broken} image(s) do not load; pick other ads")
    if wide > 1:
        out.append(f"the page scrolls sideways by {wide} px on a 375 px phone")
    return out


def _check(spec):
    """Everything build() checks, every problem at once. Returns (problems, html, report, fit)."""
    out = []
    words = check_authored(spec)
    if words:
        out.append("words the reader should not see in the text:\n"
                   + "\n".join(f"  {w}: {k!r}: {t}\n    {h}" for w, k, t, h in words))
    try:
        r = Report(spec)
    except (ValueError, KeyError) as e:
        return out + [str(e)], None, None, None
    out += r.problems()
    if out:
        return out, None, r, None
    try:
        plain = check_plain(spec, r)
    except (ValueError, KeyError) as e:
        return out + [str(e)], None, r, None
    if plain:
        out.append("text a fifth grader could not follow, or that names the brand instead of saying you:\n"
                   + "\n".join(f"  {w}: {k}: {t[:120]}" for w, k, t in plain))
    try:
        doc = r.html()
    except (ValueError, KeyError) as e:
        return out + [str(e)], None, r, None
    hits = check_words(doc, BANNED3)
    if hits:
        out.append("banned words on the page:\n" + "\n".join(f"  {w!r}: ...{c}..." for w, c in hits))
    bad = re.findall(r"\b(?:None(?! of)|nan|N/A|undefined)\b", _visible(re.sub(r'src="data:[^"]*"', "", doc)))
    if bad:
        out.append(f"the page prints {sorted(set(bad))}: a count is missing")
    fit = measure(doc)
    if fit:
        out.append("the pages do not fit:\n" + "\n".join(f"  {x}" for x in fit))
    return out, doc, r, fit


def precheck(spec):
    """Every problem build() would refuse, as a list of messages; empty when the spec builds."""
    return _check(spec)[0]


def build(spec):
    """Return (html, report). Raises ValueError listing every problem precheck() finds."""
    out, doc, r, fit = _check(spec)
    if out:
        raise ValueError(out[0] if len(out) == 1 else f"{len(out)} problems; fix them all before the next build:\n\n"
                         + "\n\n".join(out))
    if fit is None:
        r.brand["flags"].append("page fit not measured: no browser here, so say in your reply that the page fit is "
                                "unchecked; the rep's check build is measured")
    return doc, r


def next_step(report, name, n, rep_round):
    if rep_round:
        return (f"{name} saved: a fix round the rep asked for. Run Stage 7 on it now; fix any defect you find and build "
                "again with the same rep_asked.")
    if n < CHECK_CAP:
        return (f"{name} saved: check build {n} of {CHECK_CAP}. Run Stage 7 on it now, then print(after_check(report, "
                "[each defect])). Fix every defect you find in the spec and build again; never reply with a defect while "
                "a build is left.")
    return (f"{name} saved: check build {n} of {CHECK_CAP}, the last. Run Stage 7 on it, then print(after_check("
            "report, [each defect])); build no more, and name in your reply each defect it still has.")


def save_check(html, report, open_artifact, rep_asked=None):
    """Write html as the chat's next <brand-slug>-check-N.html and return the name. A fourth check build is refused
    unless the rep asked for this fix round: rep_asked holds the rep's words."""
    rep_round = bool((rep_asked or "").strip())
    if rep_round and set(re.findall(r"[a-z]+", rep_asked.lower())) <= GO_ON:
        raise ValueError(f"rep_asked {rep_asked.strip()!r} is not a fix round: it only says go on, so this build is one "
                         f"of the run's {CHECK_CAP}. Call save_check(html, report, open_artifact) without rep_asked; pass "
                         "rep_asked only with the rep's own words asking for a change")
    slug = check_slug(report.M[0].name)
    for n in range(1, 100):
        name = f"{slug}-check-{n}.html"
        try:
            open_artifact(name, "rb").read()
        except Exception:
            if n > CHECK_CAP and not (rep_asked or "").strip():
                raise ValueError(f"{name} would be check build {n}: this chat already holds {slug}-check-1.html to "
                                 f"{slug}-check-{n - 1}.html, and a run makes at most {CHECK_CAP} check builds. Stop "
                                 "building: reply with the newest check build and name in the reply each defect still on "
                                 "it. Build again only for a fix round the rep asks for, with save_check(html, report, "
                                 "open_artifact, rep_asked=\"<the rep's words>\")")
            try:
                with open_artifact(name, "x") as f:
                    f.write(html)
            except FileExistsError:
                continue
            report.check = (name, n, rep_round)
            print(next_step(report, name, n, rep_round))
            return name
    raise ValueError(f"open_artifact opens {slug}-check-1.html to -check-99.html: pass the chat's own open_artifact")


def after_check(report, defects=()):
    """What to do once Stage 7 has looked at the newest check build: with a defect and a build left, build again in this
    turn; otherwise reply."""
    if not getattr(report, "check", None):
        raise ValueError("after_check needs the report of a build saved with save_check(html, report, open_artifact)")
    name, n, rep_round = report.check
    defects = [str(d).strip() for d in ([defects] if isinstance(defects, str) else defects or []) if str(d).strip()]
    if not defects:
        return f"Stage 7 found no defect on {name}: reply now as Stage 8 says, with {name}."
    listed = "; ".join(defects)
    if rep_round or n < CHECK_CAP:
        left = "this is the rep's fix round" if rep_round else f"build {n + 1} of {CHECK_CAP} is left"
        return (f"Not done: {name} has {plural(len(defects), 'defect')} and {left}. Fix each in the spec and "
                f"build again now, in this turn; do not reply until it is built and checked. To fix: {listed}")
    return f"No build left: reply now as Stage 8 says, with {name}, and name each defect it still has: {listed}"

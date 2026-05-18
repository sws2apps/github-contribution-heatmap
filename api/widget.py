"""
widget.py — SVG heatmap widget renderer.

Exposes a single Flask Blueprint (`widget_bp`) with the `/api/heatmap` route.
Two render variants are supported:
  - render_map_only        compact world-map card
  - render_map_with_list   map + top-countries leaderboard sidebar
"""

import logging
import math
import os

from flask import Blueprint, request, Response
from lxml import etree

from utils import get_all_contributors, resolve_country_code
from data import COUNTRY_NAMES

logger = logging.getLogger(__name__)

widget_bp = Blueprint("widget", __name__)

# Allowed query-parameter values (reject anything outside these)
_VALID_THEMES = {"light", "dark"}
_VALID_VARIANTS = {"map", "list"}

def get_color(count, max_count):
    """Returns an interpolated blue shade from light to dark blue."""
    if count == 0:
        return "#ffffff"
    
    if max_count > 1:
        intensity = math.log(count) / math.log(max_count) if count > 1 else 0
    else:
        intensity = 0
    
    start_r, start_g, start_b = 147, 197, 253
    end_r, end_g, end_b = 30, 64, 175
    
    r = int(start_r + (end_r - start_r) * intensity)
    g = int(start_g + (end_g - start_g) * intensity)
    b = int(start_b + (end_b - start_b) * intensity)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def get_color_dark(count, max_count):
    """Returns an interpolated blue shade for dark mode (Nice Dark)."""
    if count == 0:
        return "#1e293b"
    
    if max_count > 1:
        intensity = math.log(count) / math.log(max_count) if count > 1 else 0
    else:
        intensity = 0
    
    # Using GitHub-inspired dark blue shades
    start_r, start_g, start_b = 31, 111, 235 # #1f6feb
    end_r, end_g, end_b = 88, 166, 255   # #58a6ff
    
    r = int(start_r + (end_r - start_r) * intensity)
    g = int(start_g + (end_g - start_g) * intensity)
    b = int(start_b + (end_b - start_b) * intensity)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def get_country_name(code):
    """Get full country name from manual mapping or ISO code."""
    code_upper = code.upper()
    return COUNTRY_NAMES.get(code_upper, code_upper)


def load_map_svg():
    """Load and parse the SirLisko map SVG."""
    svg_path = os.path.join(os.path.dirname(__file__), 'static', 'sirlisko-world-map.svg')
    parser = etree.XMLParser(remove_blank_text=True)
    orig_tree = etree.parse(svg_path, parser)
    return orig_tree.getroot()


def clone_elements(source, target, is_outline, country_counts, max_count, color_fn=get_color, empty_fill='#ffffff'):
    """Clone SVG elements with heatmap coloring."""
    if not isinstance(source.tag, str): return
    if source.tag.endswith('}title') or source.tag.endswith('}desc'): return
    
    tag = source.tag.split('}', 1)[1] if '}' in source.tag else source.tag
    new_node = etree.SubElement(target, tag)
    
    for k, v in source.attrib.items():
        if k not in ['fill', 'style', 'class', 'stroke', 'transform']: new_node.set(k, v)
    
    if 'transform' in source.attrib:
        new_node.set('transform', source.attrib['transform'])
        
    node_id = source.get('id', '').lower()
    if not node_id:
        node_id = source.get('data-id', '').lower()
    
    clean_id = node_id.lstrip('_')
    
    if tag in ['path', 'polygon', 'circle', 'rect']:
        if is_outline:
            new_node.set('class', 'country-outline')
        else:
            new_node.set('class', 'country-fill')
            found_code = None
            if len(clean_id) == 2: found_code = clean_id
            elif len(clean_id) > 2:
                parts = clean_id.split()
                for p in parts:
                    if len(p) == 2:
                        found_code = p
                        break
            
            if found_code:
                count = country_counts.get(found_code, 0)
                new_node.set('fill', color_fn(count, max_count))
            else:
                new_node.set('fill', empty_fill)
    
    for child in source:
        clone_elements(child, new_node, is_outline, country_counts, max_count, color_fn, empty_fill)


def render_map_only(country_counts, theme='light'):
    """Render map-only variant (compact)."""
    max_count = max(country_counts.values()) if country_counts else 1
    total_countries = len(country_counts)
    is_dark = theme == 'dark'

    card_w = 920
    card_h = 620
    
    final_svg = etree.Element("svg",
        width="100%",
        viewBox=f"0 0 {card_w} {card_h}",
        style=f"max-width:{card_w}px",
        version="1.1",
        xmlns="http://www.w3.org/2000/svg"
    )
    
    # --- CSS: single clean stylesheet, no media queries ---
    # Font sizes are in viewBox units; the SVG scales uniformly so they stay
    # proportional at every rendered width without any JS or media queries.
    title_color  = "#f8fafc" if is_dark else "#0f172a"
    card_color   = "#0f172a" if is_dark else "#f1f5f9"
    badge_bg     = "#3b82f6" if is_dark else "#bfdbfe"
    badge_fg     = "#ffffff" if is_dark else "#1e40af"
    divider_clr  = "#334155" if is_dark else "#cbd5e1"
    outline_clr  = "#334155"
    outline_op   = "1" if is_dark else "0.8"

    style_elem = etree.SubElement(final_svg, "style")
    style_elem.text = f"""
        @import url('https://rsms.me/inter/inter.css');
        svg, text {{ -webkit-text-size-adjust: none; text-size-adjust: none; }}
        .card    {{ fill: {card_color}; }}
        .title   {{ font-family: 'Inter', sans-serif; font-size: 32px; font-weight: 600; fill: {title_color}; }}
        .badge-bg  {{ fill: {badge_bg}; }}
        .badge-text {{ font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 700;
                      fill: {badge_fg}; letter-spacing: 0.06em;
                      text-anchor: middle; dominant-baseline: middle; }}
        .divider {{ stroke: {divider_clr}; stroke-width: 1; }}
        .country-fill    {{ stroke: none; }}
        .country-outline {{ fill: none; stroke: {outline_clr}; stroke-width: 0.4;
                           stroke-linejoin: round; pointer-events: none; opacity: {outline_op}; }}
    """

    etree.SubElement(final_svg, "rect", x="0", y="0",
                     width=str(card_w), height=str(card_h), rx="10",
                     attrib={"class": "card"})
    etree.SubElement(final_svg, "text", x="40", y="60",
                     attrib={"class": "title"}).text = "Contributors heatmap"

    # Single badge — sized in viewBox units, always proportional
    badge_val = f"{total_countries} COUNTRY" if total_countries == 1 else f"{total_countries} COUNTRIES"
    text_len  = len(badge_val)
    badge_h   = 36
    badge_w   = max(190, text_len * 16)
    badge_x   = card_w - badge_w - 40
    badge_y   = 34
    etree.SubElement(final_svg, "rect",
                     x=str(badge_x), y=str(badge_y),
                     width=str(badge_w), height=str(badge_h),
                     rx=str(badge_h / 2),
                     attrib={"class": "badge-bg"})
    etree.SubElement(final_svg, "text",
                     x=str(badge_x + badge_w / 2),
                     y=str(badge_y + badge_h / 2 + 1),
                     attrib={"class": "badge-text"}).text = badge_val

    etree.SubElement(final_svg, "line",
                     x1="40", y1="90", x2=str(card_w - 40), y2="90",
                     attrib={"class": "divider"})

    orig_root = load_map_svg()
    vb_str = orig_root.get("viewBox")
    if not vb_str and 'width' in orig_root.attrib and 'height' in orig_root.attrib:
         vb_str = f"0 0 {orig_root.attrib['width']} {orig_root.attrib['height']}"
    if vb_str:
        vb = vb_str.replace(',', ' ').split()
        ox, oy, ow, oh = float(vb[0]), float(vb[1]), float(vb[2]), float(vb[3])
    else:
        ox, oy, ow, oh = 0, 0, 1000, 500

    target_w = card_w - 80
    target_h = card_h - 150
    scale = min(target_w / ow, target_h / oh)
    tx = 40 + (target_w - ow * scale) / 2 - ox * scale
    ty = 130 + (target_h - oh * scale) / 2 - oy * scale

    color_fn = get_color_dark if is_dark else get_color
    empty_fill = '#1e293b' if is_dark else '#ffffff'
    
    fills_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, fills_container, False, country_counts, max_count, color_fn, empty_fill)
    
    outlines_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, outlines_container, True, country_counts, max_count, color_fn, empty_fill)

    return etree.tostring(final_svg, pretty_print=True, xml_declaration=True, encoding="utf-8")


def render_map_with_list(country_counts: dict, theme: str = "light") -> bytes:
    """Render map with country list variant."""
    max_count = max(country_counts.values()) if country_counts else 1
    total_countries = len(country_counts)
    is_dark = theme == "dark"

    card_w = 1200
    card_h = 620
    map_area_w = 800
    list_area_x = map_area_w + 30
    
    final_svg = etree.Element("svg",
        width="100%",
        viewBox=f"0 0 {card_w} {card_h}",
        style=f"max-width:{card_w}px",
        version="1.1",
        xmlns="http://www.w3.org/2000/svg"
    )
    
    # --- CSS: single stylesheet, no media queries ---
    title_color  = "#f8fafc" if is_dark else "#0f172a"
    card_color   = "#0f172a" if is_dark else "#f1f5f9"
    badge_bg     = "#3b82f6" if is_dark else "#bfdbfe"
    badge_fg     = "#ffffff" if is_dark else "#1e40af"
    divider_clr  = "#334155" if is_dark else "#cbd5e1"
    list_lbl_clr = "#94a3b8" if is_dark else "#64748b"
    cname_clr    = "#f8fafc" if is_dark else "#334155"
    ccount_clr   = "#60a5fa" if is_dark else "#1e40af"
    outline_clr  = "#334155"
    outline_op   = "1" if is_dark else "0.8"

    style_elem.text = f"""
        @import url('https://rsms.me/inter/inter.css');
        svg, text {{ -webkit-text-size-adjust: none; text-size-adjust: none; }}
        .card         {{ fill: {card_color}; }}
        .title        {{ font-family: 'Inter', sans-serif; font-size: 34px; font-weight: 600; fill: {title_color}; }}
        .badge-bg     {{ fill: {badge_bg}; }}
        .badge-text   {{ font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 700;
                        fill: {badge_fg}; letter-spacing: 0.06em;
                        text-anchor: middle; dominant-baseline: middle; }}
        .divider      {{ stroke: {divider_clr}; stroke-width: 1; }}
        .list-divider {{ stroke: {divider_clr}; stroke-width: 1; }}
        .country-fill    {{ stroke: none; }}
        .country-outline {{ fill: none; stroke: {outline_clr}; stroke-width: 0.4;
                           stroke-linejoin: round; pointer-events: none; opacity: {outline_op}; }}
        .list-title   {{ font-family: 'Inter', sans-serif; font-size: 24px; font-weight: 600; fill: {list_lbl_clr}; }}
        .country-name {{ font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 500; fill: {cname_clr}; }}
        .country-count{{ font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 700; fill: {ccount_clr}; }}
    """

    etree.SubElement(final_svg, "rect", x="0", y="0",
                     width=str(card_w), height=str(card_h), rx="10",
                     attrib={"class": "card"})
    etree.SubElement(final_svg, "text", x="40", y="60",
                     attrib={"class": "title"}).text = "Contributors heatmap"

    # Single badge — sized in viewBox units, always proportional at any scale
    badge_val = f"{total_countries} COUNTRY" if total_countries == 1 else f"{total_countries} COUNTRIES"
    text_len  = len(badge_val)
    badge_h   = 36
    badge_w   = max(210, text_len * 16)
    badge_x   = map_area_w - badge_w
    badge_y   = 34
    etree.SubElement(final_svg, "rect",
                     x=str(badge_x), y=str(badge_y),
                     width=str(badge_w), height=str(badge_h),
                     rx=str(badge_h / 2),
                     attrib={"class": "badge-bg"})
    etree.SubElement(final_svg, "text",
                     x=str(badge_x + badge_w / 2),
                     y=str(badge_y + badge_h / 2 + 1),
                     attrib={"class": "badge-text"}).text = badge_val

    etree.SubElement(final_svg, "line",
                     x1="40", y1="90", x2=str(map_area_w), y2="90",
                     attrib={"class": "divider"})

    # Vertical divider between map and list
    etree.SubElement(final_svg, "line", x1=str(map_area_w + 20), y1="40", x2=str(map_area_w + 20), y2=str(card_h - 40), attrib={"class": "list-divider"})

    # Load and render map (smaller area)
    orig_root = load_map_svg()
    vb_str = orig_root.get("viewBox")
    if not vb_str and 'width' in orig_root.attrib and 'height' in orig_root.attrib:
         vb_str = f"0 0 {orig_root.attrib['width']} {orig_root.attrib['height']}"
    if vb_str:
        vb = vb_str.replace(',', ' ').split()
        ox, oy, ow, oh = float(vb[0]), float(vb[1]), float(vb[2]), float(vb[3])
    else:
        ox, oy, ow, oh = 0, 0, 1000, 500

    target_w = map_area_w - 80
    target_h = card_h - 150
    scale = min(target_w / ow, target_h / oh)
    tx = 40 + (target_w - ow * scale) / 2 - ox * scale
    ty = 130 + (target_h - oh * scale) / 2 - oy * scale

    color_fn = get_color_dark if is_dark else get_color
    empty_fill = '#1e293b' if is_dark else '#ffffff'
    
    fills_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, fills_container, False, country_counts, max_count, color_fn, empty_fill)
    
    outlines_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, outlines_container, True, country_counts, max_count, color_fn, empty_fill)

    list_x = list_area_x + 15
    list_w = card_w - list_x - 40
    
    # Fixed label "TOP COUNTRIES" (no count)
    etree.SubElement(final_svg, "text", x=str(list_x), y="60", attrib={"class": "list-title"}).text = "TOP COUNTRIES"
    etree.SubElement(final_svg, "line", x1=str(list_area_x), y1="90", x2=str(card_w - 40), y2="90", attrib={"class": "divider"})

    # Sort countries by count (descending) and take top 10
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    max_display = min(10, len(sorted_countries))
    
    # Calculate spacing based on number of countries
    list_start_y = 120
    list_end_y = card_h - 40
    available_height = list_end_y - list_start_y
    
    if max_display >= 5:
        # 5+ countries: fill the height evenly
        row_spacing = available_height / max_display if max_display > 1 else available_height
    else:
        # 4 or less: use airy gaps (60px spacing)
        row_spacing = 60
    
    bar_max_width = 80
    
    for i, (code, count) in enumerate(sorted_countries[:max_display]):
        y = list_start_y + i * row_spacing + row_spacing * 0.5  # Center text in each row space
        country_name = get_country_name(code)
        
        # No truncation - show full country names
        
        # Country name
        etree.SubElement(final_svg, "text", x=str(list_x), y=str(y + 4), attrib={"class": "country-name"}).text = country_name
        
        # Count number (far right)
        count_x = card_w - 40
        etree.SubElement(final_svg, "text", 
            x=str(count_x), y=str(y + 4), 
            attrib={"class": "country-count", "text-anchor": "end"}).text = str(count)
        
        bar_width = (count / max_count) * bar_max_width
        bar_x = count_x - 32 - bar_width
        etree.SubElement(final_svg, "rect", 
            x=str(bar_x), y=str(y - 14), 
            width=str(bar_width), height="22",
            rx="4",
            fill=color_fn(count, max_count),
            attrib={"class": "country-bar"})

    # Show remaining count if more than 10
    if len(sorted_countries) > max_display:
        remaining = len(sorted_countries) - max_display
        y = list_start_y + max_display * row_spacing + row_spacing * 0.5
        etree.SubElement(final_svg, "text", x=str(list_x), y=str(y + 4), attrib={"class": "list-title"}).text = f"+{remaining} more countries"

    return etree.tostring(final_svg, pretty_print=True, xml_declaration=True, encoding="utf-8")


@widget_bp.route("/api/heatmap")
def heatmap() -> Response:
    """
    Render and return an SVG heatmap for a GitHub repository.

    Query parameters
    ----------------
    repo     : str  – GitHub repository slug (``owner/name``). Required.
    variant  : str  – ``list`` (default) or ``map``.
    theme    : str  – ``light`` (default) or ``dark``.
    refresh  : str  – Pass ``1`` to bypass the 24-hour cache.
    """
    repo = request.args.get("repo", "").strip()
    variant = request.args.get("variant", "list").strip().lower()
    theme = request.args.get("theme", "light").strip().lower()
    force_refresh = request.args.get("refresh") == "1"

    # --- Input validation ---
    if not repo:
        return Response("Missing required parameter: repo", status=400)
    if "/" not in repo or len(repo.split("/")) != 2:
        return Response("Invalid repo format. Expected: owner/name", status=400)
    if variant not in _VALID_VARIANTS:
        variant = "list"
    if theme not in _VALID_THEMES:
        theme = "light"

    try:
        contributors = get_all_contributors(repo, force_refresh=force_refresh)

        country_counts: dict[str, int] = {}
        for user in contributors:
            code = resolve_country_code(user["location"])
            if code:
                country_counts[code] = country_counts.get(code, 0) + 1

        if variant == "list":
            svg_output = render_map_with_list(country_counts, theme)
        else:
            svg_output = render_map_only(country_counts, theme)

        return Response(
            svg_output,
            mimetype="image/svg+xml",
            # Cache at Vercel Edge for 24h (86400s), then serve stale while fetching fresh data
            headers={"Cache-Control": "public, max-age=14400, s-maxage=86400, stale-while-revalidate=86400"},
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error rendering heatmap for %s", repo)
        return Response(f"Internal server error: {exc}", status=500)

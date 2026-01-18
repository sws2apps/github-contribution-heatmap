"""
Embeddable Heatmap Widget
This module contains the production widget endpoint.
"""
from flask import Blueprint, request, Response
import os
import math
from lxml import etree
from utils import get_all_contributors, resolve_country_code
from data import COUNTRY_NAMES

widget_bp = Blueprint('widget', __name__)

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
    """Returns an interpolated blue shade for dark mode (GitHub-inspired "really dark")."""
    if count == 0:
        return "#161b22"
    
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
        width=str(card_w), 
        height=str(card_h), 
        viewBox=f"0 0 {card_w} {card_h}",
        version="1.1",
        xmlns="http://www.w3.org/2000/svg"
    )
    
    if is_dark:
        style_elem = etree.SubElement(final_svg, "style")
        style_elem.text = """
            @import url('https://rsms.me/inter/inter.css');
            .card { fill: #0d1117; rx: 10; }
            .title { font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 600; fill: #c9d1d9; }
            .badge-bg { fill: #1f6feb; }
            .badge-text { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600; fill: #ffffff; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .badge-text-mobile { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; fill: #ffffff; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .divider { stroke: #30363d; stroke-width: 1; }
            .country-fill { stroke: none; }
            .country-outline { fill: none; stroke: #30363d; stroke-width: 0.5; stroke-linejoin: round; pointer-events: none; }
            .badge-desktop { display: block; }
            .badge-mobile { display: none; }
            
            @media (max-width: 600px) {
                .title { font-size: 32px; }
                .badge-desktop { display: none; }
                .badge-mobile { display: block; }
            }
        """
    else:
        style_elem = etree.SubElement(final_svg, "style")
        style_elem.text = """
            @import url('https://rsms.me/inter/inter.css');
            .card { fill: #f1f5f9; rx: 10; }
            .title { font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 600; fill: #0f172a; }
            .badge-bg { fill: #bfdbfe; }
            .badge-text { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600; fill: #1e40af; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .badge-text-mobile { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; fill: #1e40af; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .divider { stroke: #cbd5e1; stroke-width: 1; }
            .country-fill { stroke: none; }
            .country-outline { fill: none; stroke: #334155; stroke-width: 0.4; stroke-linejoin: round; pointer-events: none; opacity: 0.8; }
            .badge-desktop { display: block; }
            .badge-mobile { display: none; }
            
            @media (max-width: 600px) {
                .title { font-size: 32px; }
                .badge-desktop { display: none; }
                .badge-mobile { display: block; }
            }
        """

    etree.SubElement(final_svg, "rect", x="0", y="0", width=str(card_w), height=str(card_h), rx="10", attrib={"class": "card"})
    etree.SubElement(final_svg, "text", x="40", y="60", attrib={"class": "title"}).text = "Contributors heatmap"
    
    # Singular/plural logic for badge text
    badge_val = f"{total_countries} COUNTRY" if total_countries == 1 else f"{total_countries} COUNTRIES"
    
    # Desktop badge (normal size)
    text_length = len(badge_val)
    badge_w_desktop = max(120, text_length * 8.5)
    badge_h_desktop = 22
    badge_x_desktop = card_w - badge_w_desktop - 40
    badge_y_desktop = 43
    
    desktop_group = etree.SubElement(final_svg, "g", attrib={"class": "badge-desktop"})
    etree.SubElement(desktop_group, "rect", x=str(badge_x_desktop), y=str(badge_y_desktop), 
                     width=str(badge_w_desktop), height=str(badge_h_desktop), 
                     rx=str(badge_h_desktop/2), attrib={"class": "badge-bg"})
    etree.SubElement(desktop_group, "text", x=str(badge_x_desktop + badge_w_desktop/2), 
                     y=str(badge_y_desktop + badge_h_desktop/2 + 1), 
                     attrib={"class": "badge-text"}).text = badge_val
    
    # Mobile badge (larger size)
    badge_w_mobile = max(180, text_length * 13)  # Larger for mobile
    badge_h_mobile = 36  # Taller for mobile
    badge_x_mobile = card_w - badge_w_mobile - 40
    badge_y_mobile = 36
    
    mobile_group = etree.SubElement(final_svg, "g", attrib={"class": "badge-mobile"})
    etree.SubElement(mobile_group, "rect", x=str(badge_x_mobile), y=str(badge_y_mobile), 
                     width=str(badge_w_mobile), height=str(badge_h_mobile), 
                     rx=str(badge_h_mobile/2), attrib={"class": "badge-bg"})
    etree.SubElement(mobile_group, "text", x=str(badge_x_mobile + badge_w_mobile/2), 
                     y=str(badge_y_mobile + badge_h_mobile/2 + 1), 
                     attrib={"class": "badge-text-mobile"}).text = badge_val
    
    etree.SubElement(final_svg, "line", x1="40", y1="90", x2=str(card_w-40), y2="90", attrib={"class": "divider"})

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
    empty_fill = '#161b22' if is_dark else '#ffffff'
    
    fills_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, fills_container, False, country_counts, max_count, color_fn, empty_fill)
    
    outlines_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, outlines_container, True, country_counts, max_count, color_fn, empty_fill)

    return etree.tostring(final_svg, pretty_print=True, xml_declaration=True, encoding="utf-8")


def render_map_with_list(country_counts, theme='light'):
    """Render map with country list variant."""
    max_count = max(country_counts.values()) if country_counts else 1
    total_countries = len(country_counts)
    total_contributors = sum(country_counts.values())
    is_dark = theme == 'dark'

    card_w = 1200
    card_h = 620
    map_area_w = 800
    list_area_x = map_area_w + 30
    
    final_svg = etree.Element("svg", 
        width=str(card_w), 
        height=str(card_h), 
        viewBox=f"0 0 {card_w} {card_h}",
        version="1.1",
        xmlns="http://www.w3.org/2000/svg"
    )
    
    if is_dark:
        style_elem = etree.SubElement(final_svg, "style")
        style_elem.text = """
            @import url('https://rsms.me/inter/inter.css');
            .card { fill: #0d1117; rx: 10; }
            .title { font-family: 'Inter', sans-serif; font-size: 28px; font-weight: 600; fill: #c9d1d9; }
            .badge-bg { fill: #1f6feb; }
            .badge-text { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; fill: #ffffff; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .badge-text-mobile { font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 600; fill: #ffffff; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .divider { stroke: #30363d; stroke-width: 1; }
            .country-fill { stroke: none; }
            .country-outline { fill: none; stroke: #30363d; stroke-width: 0.5; stroke-linejoin: round; pointer-events: none; }
            .list-title { font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600; fill: #8b949e; }
            .country-name { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 500; fill: #c9d1d9; }
            .country-count { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 700; fill: #58a6ff; }
            .list-divider { stroke: #30363d; stroke-width: 1; }
            .badge-desktop { display: block; }
            .badge-mobile { display: none; }
            
            @media (max-width: 600px) {
                .title { font-size: 40px; }
                .badge-desktop { display: none; }
                .badge-mobile { display: block; }
                .list-title { font-size: 24px; }
                .country-name, .country-count { font-size: 24px; }
            }
        """
    else:
        style_elem = etree.SubElement(final_svg, "style")
        style_elem.text = """
            @import url('https://rsms.me/inter/inter.css');
            .card { fill: #f1f5f9; rx: 10; }
            .title { font-family: 'Inter', sans-serif; font-size: 28px; font-weight: 600; fill: #0f172a; }
            .badge-bg { fill: #bfdbfe; }
            .badge-text { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; fill: #1e40af; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .badge-text-mobile { font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 600; fill: #1e40af; letter-spacing: 0.05em; text-anchor: middle; dominant-baseline: middle; }
            .divider { stroke: #cbd5e1; stroke-width: 1; }
            .country-fill { stroke: none; }
            .country-outline { fill: none; stroke: #334155; stroke-width: 0.4; stroke-linejoin: round; pointer-events: none; opacity: 0.8; }
            .list-title { font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600; fill: #64748b; }
            .country-name { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 500; fill: #334155; }
            .country-count { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 700; fill: #1e40af; }
            .list-divider { stroke: #cbd5e1; stroke-width: 1; }
            .badge-desktop { display: block; }
            .badge-mobile { display: none; }

            @media (max-width: 600px) {
                .title { font-size: 40px; }
                .badge-desktop { display: none; }
                .badge-mobile { display: block; }
                .list-title { font-size: 24px; }
                .country-name, .country-count { font-size: 24px; }
            }
        """

    etree.SubElement(final_svg, "rect", x="0", y="0", width=str(card_w), height=str(card_h), rx="10", attrib={"class": "card"})
    
    # Header
    etree.SubElement(final_svg, "text", x="40", y="60", attrib={"class": "title"}).text = "Contributors heatmap"
    # Singular/plural logic for badge text
    badge_val = f"{total_countries} COUNTRY" if total_countries == 1 else f"{total_countries} COUNTRIES"
    
    # Desktop badge (normal size)
    text_length = len(badge_val)
    badge_w_desktop = max(145, text_length * 10)
    badge_h_desktop = 26
    badge_x_desktop = map_area_w - badge_w_desktop
    badge_y_desktop = 41
    
    desktop_group = etree.SubElement(final_svg, "g", attrib={"class": "badge-desktop"})
    etree.SubElement(desktop_group, "rect", x=str(badge_x_desktop), y=str(badge_y_desktop), 
                     width=str(badge_w_desktop), height=str(badge_h_desktop), 
                     rx=str(badge_h_desktop/2), attrib={"class": "badge-bg"})
    etree.SubElement(desktop_group, "text", x=str(badge_x_desktop + badge_w_desktop/2), 
                     y=str(badge_y_desktop + badge_h_desktop/2 + 1), 
                     attrib={"class": "badge-text"}).text = badge_val
    
    # Mobile badge (larger size)
    badge_w_mobile = max(220, text_length * 15)  # Larger for mobile
    badge_h_mobile = 44  # Taller for mobile
    badge_x_mobile = map_area_w - badge_w_mobile
    badge_y_mobile = 34
    
    mobile_group = etree.SubElement(final_svg, "g", attrib={"class": "badge-mobile"})
    etree.SubElement(mobile_group, "rect", x=str(badge_x_mobile), y=str(badge_y_mobile), 
                     width=str(badge_w_mobile), height=str(badge_h_mobile), 
                     rx=str(badge_h_mobile/2), attrib={"class": "badge-bg"})
    etree.SubElement(mobile_group, "text", x=str(badge_x_mobile + badge_w_mobile/2), 
                     y=str(badge_y_mobile + badge_h_mobile/2 + 1), 
                     attrib={"class": "badge-text-mobile"}).text = badge_val
    
    etree.SubElement(final_svg, "line", x1="40", y1="90", x2=str(map_area_w), y2="90", attrib={"class": "divider"})

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
    empty_fill = '#161b22' if is_dark else '#ffffff'
    
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
        bar_x = count_x - 28 - bar_width
        etree.SubElement(final_svg, "rect", 
            x=str(bar_x), y=str(y - 12), 
            width=str(bar_width), height="18",
            rx="4",
            fill=color_fn(count, max_count),
            attrib={"class": "country-bar"})

    # Show remaining count if more than 12
    if len(sorted_countries) > max_display:
        remaining = len(sorted_countries) - max_display
        y = start_y + max_display * row_height
        etree.SubElement(final_svg, "text", x=str(list_x), y=str(y + 4), attrib={"class": "list-title"}).text = f"+{remaining} more countries"

    return etree.tostring(final_svg, pretty_print=True, xml_declaration=True, encoding="utf-8")


@widget_bp.route('/api/heatmap')
def heatmap():
    """
    Embeddable heatmap widget endpoint.
    
    Query params:
        repo: GitHub repo (owner/name)
        variant: 'list' (default) or 'map'
        theme: 'light' (default) or 'dark'
        refresh: '1' to force refresh cache
    """
    repo = request.args.get('repo', 'sws2apps/organized-app')
    variant = request.args.get('variant', 'list')
    theme = request.args.get('theme', 'light')
    force_refresh = request.args.get('refresh') == '1'
    
    try:
        contributors = get_all_contributors(repo, force_refresh=force_refresh)
        
        country_counts = {}
        for user in contributors:
            code = resolve_country_code(user['location'])
            if code:
                country_counts[code] = country_counts.get(code, 0) + 1
        
        if variant == 'list':
            svg_output = render_map_with_list(country_counts, theme)
        else:
            svg_output = render_map_only(country_counts, theme)
            
        return Response(svg_output, mimetype='image/svg+xml', headers={'Cache-Control': 'no-cache, max-age=0'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(f"Internal Error: {e}", status=500)

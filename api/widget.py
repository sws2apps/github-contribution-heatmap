"""
Embeddable Heatmap Widget
This module contains the production widget endpoint.
"""
from flask import Blueprint, request, Response
import os
import math
from lxml import etree
from utils import get_all_contributors, resolve_country_code

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


COUNTRY_NAMES = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AI": "Anguilla", "AM": "Armenia", 
    "AW": "Aruba", "AT": "Austria", "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados", 
    "BY": "Belarus", "BE": "Belgium", "BZ": "Belize", "BJ": "Benin", "BM": "Bermuda", 
    "BT": "Bhutan", "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BW": "Botswana", 
    "BR": "Brazil", "VG": "British Virgin Islands", "BN": "Brunei Darussalam", "BG": "Bulgaria", 
    "BF": "Burkina Faso", "BI": "Burundi", "KH": "Cambodia", "CM": "Cameroon", 
    "CF": "Central African Republic", "TD": "Chad", "CO": "Colombia", "CR": "Costa Rica", 
    "HR": "Croatia", "CU": "Cuba", "CW": "Curaçao", "CZ": "Czech Republic", "CI": "Côte d'Ivoire", 
    "KP": "Dem. Rep. Korea", "CD": "Democratic Republic of the Congo", "DJ": "Djibouti", 
    "DM": "Dominica", "DO": "Dominican Republic", "EC": "Ecuador", "EG": "Egypt", 
    "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea", "EE": "Estonia", 
    "ET": "Ethiopia", "FI": "Finland", "GF": "French Guiana", "GA": "Gabon", "GE": "Georgia", 
    "DE": "Germany", "GH": "Ghana", "GL": "Greenland", "GD": "Grenada", "GU": "Guam", 
    "GT": "Guatemala", "GN": "Guinea", "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", 
    "HN": "Honduras", "HU": "Hungary", "IS": "Iceland", "IN": "India", "IR": "Iran", 
    "IQ": "Iraq", "IE": "Ireland", "IL": "Israel", "JM": "Jamaica", "JO": "Jordan", 
    "KZ": "Kazakhstan", "KE": "Kenya", "XK": "Kosovo", "KW": "Kuwait", "KG": "Kyrgyzstan", 
    "LA": "Lao PDR", "LV": "Latvia", "LB": "Lebanon", "LS": "Lesotho", "LR": "Liberia", 
    "LY": "Libya", "LT": "Lithuania", "LU": "Luxembourg", "MK": "Macedonia", "MG": "Madagascar", 
    "MW": "Malawi", "MV": "Maldives", "ML": "Mali", "MH": "Marshall Islands", "MQ": "Martinique", 
    "MR": "Mauritania", "YT": "Mayotte", "MX": "Mexico", "MD": "Moldova", "MN": "Mongolia", 
    "ME": "Montenegro", "MS": "Montserrat", "MA": "Morocco", "MZ": "Mozambique", "MM": "Myanmar", 
    "NA": "Namibia", "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands", "BQBO": "Netherlands", 
    "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "PK": "Pakistan", "PW": "Palau", 
    "PS": "Palestine", "PA": "Panama", "PY": "Paraguay", "PE": "Peru", "PL": "Poland", 
    "PT": "Portugal", "QA": "Qatar", "CG": "Republic of Congo", "KR": "Republic of Korea", 
    "RE": "Reunion", "RO": "Romania", "RW": "Rwanda", "BQSA": "Saba (Netherlands)", 
    "LC": "Saint Lucia", "VC": "Saint Vincent and the Grenadines", "BL": "Saint-Barthélemy", 
    "MF": "Saint-Martin", "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", 
    "SL": "Sierra Leone", "SX": "Sint Maarten", "SK": "Slovakia", "SI": "Slovenia", 
    "SO": "Somalia", "ZA": "South Africa", "SS": "South Sudan", "ES": "Spain", "LK": "Sri Lanka", 
    "BQSE": "St. Eustatius (Netherlands)", "SD": "Sudan", "SR": "Suriname", "SZ": "Swaziland", 
    "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan", "TJ": "Tajikistan", 
    "TZ": "Tanzania", "TH": "Thailand", "GM": "The Gambia", "TL": "Timor-Leste", "TG": "Togo", 
    "TN": "Tunisia", "TM": "Turkmenistan", "TV": "Tuvalu", "UG": "Uganda", "UA": "Ukraine", 
    "AE": "United Arab Emirates", "UY": "Uruguay", "UZ": "Uzbekistan", "VE": "Venezuela", 
    "VN": "Vietnam", "EH": "Western Sahara", "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe"
}

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


def clone_elements(source, target, is_outline, country_counts, max_count):
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
                new_node.set('fill', get_color(count, max_count))
            else:
                new_node.set('fill', '#ffffff')
    
    for child in source:
        clone_elements(child, new_node, is_outline, country_counts, max_count)


def render_map_only(country_counts):
    """Render map-only variant (compact)."""
    max_count = max(country_counts.values()) if country_counts else 1
    total_countries = len(country_counts)

    card_w = 920
    card_h = 620
    
    final_svg = etree.Element("svg", 
        width=str(card_w), 
        height=str(card_h), 
        viewBox=f"0 0 {card_w} {card_h}",
        version="1.1",
        xmlns="http://www.w3.org/2000/svg"
    )
    
    style_elem = etree.SubElement(final_svg, "style")
    style_elem.text = """
        @import url('https://rsms.me/inter/inter.css');
        .card { fill: #f9fafb; rx: 12; }
        .title { font-family: 'Inter', sans-serif; font-size: 32px; font-weight: 600; fill: #0f172a; }
        .badge-bg { fill: #dbeafe; rx: 16; }
        .badge-text { font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 800; fill: #1e40af; letter-spacing: 0.05em; }
        .divider { stroke: #e2e8f0; stroke-width: 1; }
        .country-fill { stroke: none; }
        .country-outline { fill: none; stroke: #334155; stroke-width: 0.6; stroke-linejoin: round; pointer-events: none; }
    """

    etree.SubElement(final_svg, "rect", x="0", y="0", width=str(card_w), height=str(card_h), attrib={"class": "card"})
    etree.SubElement(final_svg, "text", x="40", y="60", attrib={"class": "title"}).text = "Contribution map"
    
    badge_val = f"{total_countries} COUNTRIES"
    badge_w = 150
    badge_x = card_w - badge_w - 40
    etree.SubElement(final_svg, "rect", x=str(badge_x), y="35", width=str(badge_w), height="36", attrib={"class": "badge-bg"})
    etree.SubElement(final_svg, "text", x=str(badge_x + badge_w/2), y="58", attrib={"class": "badge-text", "text-anchor": "middle"}).text = badge_val
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

    fills_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, fills_container, False, country_counts, max_count)
    
    outlines_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, outlines_container, True, country_counts, max_count)

    return etree.tostring(final_svg, pretty_print=True, xml_declaration=True, encoding="utf-8")


def render_map_with_list(country_counts):
    """Render map with country list variant."""
    max_count = max(country_counts.values()) if country_counts else 1
    total_countries = len(country_counts)
    total_contributors = sum(country_counts.values())

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
    
    style_elem = etree.SubElement(final_svg, "style")
    style_elem.text = """
        @import url('https://rsms.me/inter/inter.css');
        .card { fill: #f9fafb; rx: 12; }
        .title { font-family: 'Inter', sans-serif; font-size: 32px; font-weight: 600; fill: #0f172a; }
        .badge-bg { fill: #dbeafe; rx: 16; }
        .badge-text { font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 800; fill: #1e40af; letter-spacing: 0.05em; }
        .divider { stroke: #e2e8f0; stroke-width: 1; }
        .country-fill { stroke: none; }
        .country-outline { fill: none; stroke: #334155; stroke-width: 0.6; stroke-linejoin: round; pointer-events: none; }
        .list-title { font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600; fill: #64748b; }
        .country-name { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 500; fill: #334155; }
        .country-count { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 700; fill: #1e40af; }
        .country-bar { rx: 4; }
        .list-divider { stroke: #e2e8f0; stroke-width: 1; }
    """

    # Card Background
    etree.SubElement(final_svg, "rect", x="0", y="0", width=str(card_w), height=str(card_h), attrib={"class": "card"})
    
    # Header
    etree.SubElement(final_svg, "text", x="40", y="60", attrib={"class": "title"}).text = "Contribution map"
    badge_val = f"{total_countries} COUNTRIES"
    badge_w = 150
    badge_x = map_area_w - badge_w
    etree.SubElement(final_svg, "rect", x=str(badge_x), y="35", width=str(badge_w), height="36", attrib={"class": "badge-bg"})
    etree.SubElement(final_svg, "text", x=str(badge_x + badge_w/2), y="58", attrib={"class": "badge-text", "text-anchor": "middle"}).text = badge_val
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

    fills_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, fills_container, False, country_counts, max_count)
    
    outlines_container = etree.SubElement(final_svg, "g", transform=f"translate({tx}, {ty}) scale({scale})")
    for child in orig_root: 
        clone_elements(child, outlines_container, True, country_counts, max_count)

    list_x = list_area_x + 15
    list_w = card_w - list_x - 40
    
    display_count = min(10, len(country_counts))
    etree.SubElement(final_svg, "text", x=str(list_x), y="60", attrib={"class": "list-title"}).text = f"TOP {display_count} COUNTRIES"
    etree.SubElement(final_svg, "line", x1=str(list_area_x), y1="90", x2=str(card_w - 40), y2="90", attrib={"class": "divider"})

    # Sort countries by count (descending)
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    
    max_display = min(10, len(sorted_countries))
    row_height = 38
    start_y = 120
    bar_max_width = 80
    
    for i, (code, count) in enumerate(sorted_countries[:max_display]):
        y = start_y + i * row_height
        country_name = get_country_name(code)
        
        # No truncation - show full country names
        
        # Country name
        etree.SubElement(final_svg, "text", x=str(list_x), y=str(y + 4), attrib={"class": "country-name"}).text = country_name
        
        # Count number (far right)
        count_x = card_w - 40
        etree.SubElement(final_svg, "text", 
            x=str(count_x), y=str(y + 4), 
            attrib={"class": "country-count", "text-anchor": "end"}).text = str(count)
        
        # Bar (grows right-to-left, ends before the count)
        bar_x = count_x - 28 - bar_width
        etree.SubElement(final_svg, "rect", 
            x=str(bar_x), y=str(y - 12), 
            width=str(bar_width), height="18",
            fill=get_color(count, max_count),
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
        variant: 'map' (default) or 'list' (map + country list)
        refresh: '1' to force refresh cache
    """
    repo = request.args.get('repo', 'sws2apps/organized-app')
    variant = request.args.get('variant', 'map')
    force_refresh = request.args.get('refresh') == '1'
    
    try:
        contributors = get_all_contributors(repo, force_refresh=force_refresh)
        
        country_counts = {}
        for user in contributors:
            code = resolve_country_code(user['location'])
            if code:
                country_counts[code] = country_counts.get(code, 0) + 1
        
        if variant == 'list':
            svg_output = render_map_with_list(country_counts)
        else:
            svg_output = render_map_only(country_counts)
            
        return Response(svg_output, mimetype='image/svg+xml', headers={'Cache-Control': 'no-cache, max-age=0'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(f"Internal Error: {e}", status=500)

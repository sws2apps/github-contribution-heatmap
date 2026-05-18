"""
utils.py — GitHub contributor fetching and location resolution.

Handles:
  - GitHub API pagination for contributor lists
  - Disk-backed caching (24-hour TTL) for API responses
  - Fuzzy location → ISO-3166-1 alpha-2 country code resolution
"""

import os
import json
import time
import logging
import requests
import pycountry

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Use /tmp for caching on Vercel (the only writable directory in serverless)
CACHE_DIR = "/tmp" if os.getenv("VERCEL") else "."
CACHE_FILE = os.path.join(CACHE_DIR, "repo_cache.json")
LOCATION_CACHE_FILE = os.path.join(CACHE_DIR, "user_locations.json")

CACHE_TTL_SECONDS = 86_400  # 24 hours


# ---------------------------------------------------------------------------
# Disk-backed JSON helpers
# ---------------------------------------------------------------------------

def load_json(filename: str) -> dict:
    """Load a JSON file from disk, returning an empty dict on any failure."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.warning("Could not load %s — starting fresh.", filename)
    return {}


def save_json(filename: str, data: dict) -> None:
    """Persist *data* as JSON to *filename*, silently failing in read-only envs."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        logger.warning("Could not save %s (read-only filesystem?).", filename)


# Module-level cache loaded once per cold-start
repo_cache: dict = load_json(CACHE_FILE)
user_locations: dict = load_json(LOCATION_CACHE_FILE)


# ---------------------------------------------------------------------------
# Location → country code resolution
# ---------------------------------------------------------------------------

# Comprehensive mapping of location strings to ISO 3166-1 alpha-2 codes.
# Sorted longest-first so substring matching favours the most specific entry.
COUNTRY_MAP = sorted([
    # NORTH AMERICA
    ("united states", "us"), ("usa", "us"), ("united states of america", "us"), ("washington d.c.", "us"),
    ("new york", "us"), ("los angeles", "us"), ("chicago", "us"), ("houston", "us"), ("phoenix", "us"), ("philadelphia", "us"),
    ("canada", "ca"), ("ottawa", "ca"), ("toronto", "ca"), ("montreal", "ca"), ("vancouver", "ca"), ("calgary", "ca"), ("edmonton", "ca"),
    ("mexico", "mx"), ("méxico", "mx"), ("mexico city", "mx"), ("guadalajara", "mx"), ("monterrey", "mx"), ("puebla", "mx"), ("tijuana", "mx"),
    ("cuba", "cu"), ("havana", "cu"), ("guatemala", "gt"), ("guatemala city", "gt"), ("haiti", "ht"), ("port-au-prince", "ht"),
    ("dominican republic", "do"), ("santo domingo", "do"), ("honduras", "hn"), ("tegucigalpa", "hn"), ("nicaragua", "ni"), ("managua", "ni"),
    ("el salvador", "sv"), ("san salvador", "sv"), ("costa rica", "cr"), ("san josé", "cr"), ("panama", "pa"), ("panama city", "pa"),
    ("jamaica", "jm"), ("kingston", "jm"), ("puerto rico", "pr"), ("san juan", "pr"),

    # EUROPE
    ("united kingdom", "gb"), ("uk", "gb"), ("great britain", "gb"), ("england", "gb"), ("scotland", "gb"), ("wales", "gb"), ("london", "gb"),
    ("birmingham", "gb"), ("manchester", "gb"), ("glasgow", "gb"), ("liverpool", "gb"), ("leeds", "gb"), ("sheffield", "gb"),
    ("germany", "de"), ("deutschland", "de"), ("berlin", "de"), ("hamburg", "de"), ("munich", "de"), ("cologne", "de"), ("frankfurt", "de"), ("stuttgart", "de"),
    ("france", "fr"), ("paris", "fr"), ("marseille", "fr"), ("lyon", "fr"), ("toulouse", "fr"), ("nice", "fr"), ("nantes", "fr"), ("strasbourg", "fr"),
    ("italy", "it"), ("italia", "it"), ("rome", "it"), ("milan", "it"), ("naples", "it"), ("turin", "it"), ("palermo", "it"), ("genoa", "it"), ("florence", "it"),
    ("spain", "es"), ("españa", "es"), ("madrid", "es"), ("barcelona", "es"), ("valencia", "es"), ("seville", "es"), ("zaragoza", "es"), ("malaga", "es"),
    ("ukraine", "ua"), ("україна", "ua"), ("kyiv", "ua"), ("kharkiv", "ua"), ("odesa", "ua"), ("dnipro", "ua"), ("donetsk", "ua"), ("lviv", "ua"),
    ("poland", "pl"), ("polska", "pl"), ("warsaw", "pl"), ("krakow", "pl"), ("lodz", "pl"), ("wroclaw", "pl"), ("poznan", "pl"), ("gdansk", "pl"),
    ("netherlands", "nl"), ("nederland", "nl"), ("amsterdam", "nl"), ("rotterdam", "nl"), ("the hague", "nl"), ("utrecht", "nl"), ("eindhoven", "nl"),
    ("belgium", "be"), ("belgië", "be"), ("belgique", "be"), ("brussels", "be"), ("antwerp", "be"), ("ghent", "be"), ("charleroi", "be"), ("liege", "be"),
    ("switzerland", "ch"), ("schweiz", "ch"), ("suisse", "ch"), ("svizzera", "ch"), ("bern", "ch"), ("zurich", "ch"), ("geneva", "ch"), ("basel", "ch"), ("lausanne", "ch"),
    ("austria", "at"), ("österreich", "at"), ("vienna", "at"), ("graz", "at"), ("linz", "at"), ("salzburg", "at"), ("innsbruck", "at"),
    ("sweden", "se"), ("sverige", "se"), ("stockholm", "se"), ("gothenburg", "se"), ("malmo", "se"), ("uppsala", "se"), ("vasteras", "se"),
    ("norway", "no"), ("norge", "no"), ("oslo", "no"), ("bergen", "no"), ("trondheim", "no"), ("stavanger", "no"), ("drammen", "no"),
    ("denmark", "dk"), ("danmark", "dk"), ("copenhagen", "dk"), ("aarhus", "dk"), ("odense", "dk"), ("aalborg", "dk"), ("esbjerg", "dk"),
    ("finland", "fi"), ("suomi", "fi"), ("helsinki", "fi"), ("espoo", "fi"), ("tampere", "fi"), ("vantaa", "fi"), ("oulu", "fi"), ("turku", "fi"),
    ("ireland", "ie"), ("dublin", "ie"), ("cork", "ie"), ("limerick", "ie"), ("galway", "ie"), ("waterford", "ie"),
    ("portugal", "pt"), ("lisbon", "pt"), ("porto", "pt"), ("braga", "pt"), ("funchal", "pt"), ("coimbra", "pt"),
    ("greece", "gr"), ("ελλάδα", "gr"), ("athens", "gr"), ("thessaloniki", "gr"), ("patras", "gr"), ("heraklion", "gr"), ("larissa", "gr"),
    ("czechia", "cz"), ("česko", "cz"), ("prague", "cz"), ("brno", "cz"), ("ostrava", "cz"), ("pilsen", "cz"), ("liberec", "cz"),
    ("hungary", "hu"), ("magyarország", "hu"), ("budapest", "hu"), ("debrecen", "hu"), ("szeged", "hu"), ("miskolc", "hu"), ("pecs", "hu"),
    ("romania", "ro"), ("românia", "ro"), ("bucharest", "ro"), ("cluj-napoca", "ro"), ("timisoara", "ro"), ("iasi", "ro"), ("constanta", "ro"),
    ("bulgaria", "bg"), ("българия", "bg"), ("sofia", "bg"), ("plovdiv", "bg"), ("varna", "bg"), ("croatia", "hr"), ("hrvatska", "hr"), ("zagreb", "hr"),
    ("serbia", "rs"), ("србија", "rs"), ("belgrade", "rs"), ("slovakia", "sk"), ("slovensko", "sk"), ("bratislava", "sk"),
    ("russia", "ru"), ("россия", "ru"), ("moscow", "ru"), ("saint petersburg", "ru"), ("novosibirsk", "ru"), ("yekaterinburg", "ru"), ("kazan", "ru"),

    # ASIA
    ("china", "cn"), ("中国", "cn"), ("beijing", "cn"), ("shanghai", "cn"), ("guangzhou", "cn"), ("shenzhen", "cn"), ("wuhan", "cn"), ("chengdu", "cn"),
    ("india", "in"), ("भारत", "in"), ("new delhi", "in"), ("mumbai", "in"), ("bangalore", "in"), ("hyderabad", "in"), ("ahmedabad", "in"), ("chennai", "in"),
    ("japan", "jp"), ("日本", "jp"), ("tokyo", "jp"), ("yokohama", "jp"), ("osaka", "jp"), ("nagoya", "jp"), ("sapporo", "jp"), ("fukuoka", "jp"),
    ("south korea", "kr"), ("대한민국", "kr"), ("seoul", "kr"), ("busan", "kr"), ("incheon", "kr"), ("daegu", "kr"), ("daejeon", "kr"), ("gwangju", "kr"),
    ("indonesia", "id"), ("jakarta", "id"), ("surabaya", "id"), ("medan", "id"), ("bandung", "id"), ("makassar", "id"), ("semarang", "id"),
    ("vietnam", "vn"), ("việt nam", "vn"), ("hanoi", "vn"), ("ho chi minh city", "vn"), ("da nang", "vn"), ("hai phong", "vn"), ("can tho", "vn"),
    ("philippines", "ph"), ("manila", "ph"), ("quezon city", "ph"), ("davao city", "ph"), ("cebu city", "ph"), ("zamboanga city", "ph"),
    ("thailand", "th"), ("ประเทศไทย", "th"), ("bangkok", "th"), ("nonthaburi", "th"), ("nakhon ratchasima", "th"), ("chiang mai", "th"), ("phuket", "th"),
    ("malaysia", "my"), ("kuala lumpur", "my"), ("george town", "my"), ("ipoh", "my"), ("shah alam", "my"), ("petaling jaya", "my"),
    ("pakistan", "pk"), ("islamabad", "pk"), ("karachi", "pk"), ("lahore", "pk"), ("faisalabad", "pk"), ("rawalpindi", "pk"),
    ("bangladesh", "bd"), ("dhaka", "bd"), ("chittagong", "bd"), ("khulna", "bd"), ("singapore", "sg"), ("taipei", "tw"), ("taiwan", "tw"),
    ("iran", "ir"), ("ایران", "ir"), ("tehran", "ir"), ("mashhad", "ir"), ("isfahan", "ir"), ("iraq", "iq"), ("baghdad", "iq"),
    ("saudi arabia", "sa"), ("العربية السعودية", "sa"), ("riyadh", "sa"), ("jeddah", "sa"), ("mecca", "sa"),
    ("turkey", "tr"), ("türkiye", "tr"), ("ankara", "tr"), ("istanbul", "tr"), ("izmir", "tr"), ("bursa", "tr"),
    ("israel", "il"), ("ישראל", "il"), ("jerusalem", "il"), ("tel aviv", "il"), ("haifa", "il"),
    ("united arab emirates", "ae"), ("dubai", "ae"), ("abu dhabi", "ae"), ("kazakhstan", "kz"), ("astana", "kz"), ("almaty", "kz"),

    # AFRICA
    ("nigeria", "ng"), ("abuja", "ng"), ("lagos", "ng"), ("kano", "ng"), ("ibadan", "ng"), ("kaduna", "ng"), ("port harcourt", "ng"),
    ("egypt", "eg"), ("مصر", "eg"), ("cairo", "eg"), ("alexandria", "eg"), ("giza", "eg"), ("shubra el kheima", "eg"), ("port said", "eg"),
    ("south africa", "za"), ("pretoria", "za"), ("johannesburg", "za"), ("cape town", "za"), ("durban", "za"), ("soweto", "za"), ("port elizabeth", "za"),
    ("ethiopia", "et"), ("addis ababa", "et"), ("gondar", "et"), ("mekele", "et"), ("adama", "et"), ("bahir dar", "et"),
    ("kenya", "ke"), ("nairobi", "ke"), ("mombasa", "ke"), ("nakuru", "ke"), ("kisumu", "ke"), ("eldoret", "ke"),
    ("morocco", "ma"), ("المغرب", "ma"), ("rabat", "ma"), ("casablanca", "ma"), ("fez", "ma"), ("tangier", "ma"), ("marrakesh", "ma"),
    ("algeria", "dz"), ("الجزائر", "dz"), ("algiers", "dz"), ("oran", "dz"), ("constantine", "dz"),
    ("ghana", "gh"), ("accra", "gh"), ("kumasi", "gh"), ("tamale", "gh"), ("ivory coast", "ci"), ("côte d'ivoire", "ci"), ("yamoussoukro", "ci"), ("abidjan", "ci"),
    ("uganda", "ug"), ("kampala", "ug"), ("sudan", "sd"), ("khartoum", "sd"), ("tanzania", "tz"), ("dodoma", "tz"), ("dar es salaam", "tz"),
    ("angola", "ao"), ("luanda", "ao"), ("mozambique", "mz"), ("maputo", "mz"), ("madagascar", "mg"), ("antananarivo", "mg"),
    ("cameroon", "cm"), ("yaoundé", "cm"), ("douala", "cm"), ("senegal", "sn"), ("dakar", "sn"), ("zimbabwe", "zw"), ("harare", "zw"),
    ("tunisia", "tn"), ("tunis", "tn"), ("libya", "ly"), ("tripoli", "ly"), ("mali", "ml"), ("bamako", "ml"), ("zambia", "zm"), ("lusaka", "zm"),

    # SOUTH AMERICA
    ("brazil", "br"), ("brasil", "br"), ("brasília", "br"), ("são paulo", "br"), ("rio de janeiro", "br"), ("salvador", "br"), ("fortaleza", "br"), ("belo horizonte", "br"),
    ("argentina", "ar"), ("buenos aires", "ar"), ("córdoba", "ar"), ("rosario", "ar"), ("mendoza", "ar"), ("la plata", "ar"),
    ("colombia", "co"), ("bogotá", "co"), ("medellín", "co"), ("cali", "co"), ("barranquilla", "co"), ("cartagena", "co"),
    ("peru", "pe"), ("perú", "pe"), ("lima", "pe"), ("arequipa", "pe"), ("trujillo", "pe"), ("chiclayo", "pe"),
    ("chile", "cl"), ("santiago", "cl"), ("valparaíso", "cl"), ("concepción", "cl"), ("antofagasta", "cl"),
    ("venezuela", "ve"), ("caracas", "ve"), ("maracaibo", "ve"), ("valencia", "ve"), ("ecuador", "ec"), ("quito", "ec"), ("guayaquil", "ec"),
    ("bolivia", "bo"), ("la paz", "bo"), ("sucre", "bo"), ("paraguay", "py"), ("asunción", "py"), ("uruguay", "uy"), ("montevideo", "uy"),

    # OCEANIA
    ("australia", "au"), ("canberra", "au"), ("sydney", "au"), ("melbourne", "au"), ("brisbane", "au"), ("perth", "au"), ("adelaide", "au"), ("gold coast", "au"),
    ("new zealand", "nz"), ("wellington", "nz"), ("auckland", "nz"), ("christchurch", "nz"), ("hamilton", "nz"), ("tauranga", "nz"),
    ("fiji", "fj"), ("suva", "fj"), ("papua new guinea", "pg"), ("port moresby", "pg"),
], key=lambda x: len(x[0]), reverse=True)

# Values that should never be resolved (noise / placeholder text)
LOCATION_BLOCKLIST = {
    "ci", "cd", "api", "bot", "n/a", "none", "unknown",
    "earth", "world", "internet", "remote",
}


def resolve_country_code(location: str | None) -> str | None:
    """
    Map a free-text location string to an ISO 3166-1 alpha-2 country code.

    Resolution order:
      1. Exact match in COUNTRY_MAP
      2. Substring match in COUNTRY_MAP  (e.g. "Espoo region, Finland" → "fi")
      3. Token-by-token check from end of string (country usually comes last)
      4. pycountry fuzzy search on full string as fallback

    Returns *None* if the location cannot be resolved or is in BLOCKLIST.
    """
    if not location:
        return None

    loc_lower = location.lower().strip()

    if loc_lower in LOCATION_BLOCKLIST:
        return None

    # 1. Exact match
    for key, code in COUNTRY_MAP:
        if key == loc_lower:
            return code

    # 2. Substring match
    for key, code in COUNTRY_MAP:
        if key in loc_lower:
            return code

    # 3. Token-by-token (reversed — country typically at the end)
    tokens = [p.strip() for p in loc_lower.replace(",", " ").split() if p.strip()]
    for token in reversed(tokens):
        for key, code in COUNTRY_MAP:
            if key == token:
                return code
        try:
            results = pycountry.countries.search_fuzzy(token)
            if results:
                return results[0].alpha_2.lower()
        except LookupError:
            pass

    # 4. Full-string pycountry fallback
    try:
        results = pycountry.countries.search_fuzzy(location)
        if results:
            return results[0].alpha_2.lower()
    except LookupError:
        for country in pycountry.countries:
            if country.name.lower() in loc_lower:
                return country.alpha_2.lower()

    return None


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------

def get_all_contributors(repo_name: str, force_refresh: bool = False) -> list[dict]:
    """
    Fetch all contributors for *repo_name*, including their profile locations.

    Results are cached to disk for CACHE_TTL_SECONDS (24 h). Pass
    ``force_refresh=True`` to bypass the cache and re-fetch from GitHub.

    Each returned dict has keys: ``login`` (str), ``location`` (str | None).
    """
    now = time.time()

    if (
        not force_refresh
        and repo_name in repo_cache
        and now - repo_cache[repo_name]["timestamp"] < CACHE_TTL_SECONDS
    ):
        return repo_cache[repo_name]["data"]

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # --- Paginate contributors endpoint ---
    contributors: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repo_name}/contributors"
            f"?per_page=100&page={page}"
        )
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning("GitHub contributors API returned %s for %s", resp.status_code, repo_name)
                break
            page_data = resp.json()
            if not page_data:
                break
            contributors.extend(page_data)
            if len(page_data) < 100:
                break
            page += 1
        except requests.RequestException as exc:
            logger.error("Error fetching contributors page %s: %s", page, exc)
            break

    # --- Resolve locations (with per-user cache) ---
    users_data: list[dict] = []
    for contributor in contributors:
        username = contributor["login"].lower()
        if username in user_locations:
            location = user_locations[username]
        else:
            location = None
            try:
                u_resp = requests.get(contributor["url"], headers=headers, timeout=10)
                if u_resp.status_code == 200:
                    location = u_resp.json().get("location")
            except requests.RequestException as exc:
                logger.warning("Could not fetch profile for %s: %s", username, exc)
            user_locations[username] = location

        users_data.append({"login": username, "location": location})

    save_json(LOCATION_CACHE_FILE, user_locations)
    repo_cache[repo_name] = {"timestamp": now, "data": users_data}
    save_json(CACHE_FILE, repo_cache)

    return users_data

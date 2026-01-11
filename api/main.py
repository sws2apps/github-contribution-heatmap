from flask import Flask
import os
import json
import time
import requests
import pycountry

app = Flask(__name__)

# === Configuration ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CACHE_FILE = "repo_cache.json"
LOCATION_CACHE_FILE = "user_locations.json"

# === Cache Helpers ===
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

repo_cache = load_json(CACHE_FILE)
user_locations = load_json(LOCATION_CACHE_FILE)

# === Country Resolution ===
# Order matters! Check longer/specific keys before shorter ones
# to avoid "uk" matching "ukraine"
COUNTRY_MAP = [
    ("united states", "us"),
    ("united kingdom", "gb"),
    ("ukraine", "ua"),  # Must be before "uk"
    ("usa", "us"),
    ("michigan", "us"),
    ("uk", "gb"),  # After "ukraine" to avoid conflict
    ("russia", "ru"),
    ("china", "cn"),
    ("germany", "de"),
    ("france", "fr"),
    ("italy", "it"),
    ("milan", "it"),
    ("japan", "jp"),
    ("osaka", "jp"),
    ("australia", "au"),
    ("nigeria", "ng"),
    ("madagascar", "mg"),
    ("antananarivo", "mg"),
    ("côte d'ivoire", "ci"),
    ("ivory coast", "ci"),
]

# Blocklist for non-location values that look like country codes
LOCATION_BLOCKLIST = {"ci", "cd", "api", "bot", "n/a", "none", "unknown", "earth", "world", "internet", "remote"}

def resolve_country_code(location):
    if not location: return None
    loc_lower = location.lower().strip()
    
    # Skip blocklisted values
    if loc_lower in LOCATION_BLOCKLIST:
        return None
    
    # Check manual map (ordered to check longer matches first)
    for key, code in COUNTRY_MAP:
        if key in loc_lower:
            return code

    try:
        results = pycountry.countries.search_fuzzy(location)
        if results:
            return results[0].alpha_2.lower()
    except:
        for country in pycountry.countries:
            if country.name.lower() in loc_lower:
                return country.alpha_2.lower()
    return None

# === Data Fetching ===
def get_all_contributors(repo_name, force_refresh=False):
    """Fetch all contributors by paginating through GitHub API."""
    now = time.time()
    if not force_refresh and repo_name in repo_cache and now - repo_cache[repo_name]["timestamp"] < 3600:
        return repo_cache[repo_name]["data"]

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    contributors = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo_name}/contributors?per_page=100&page={page}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        contributors.extend(data)
        if len(data) < 100:
            break
        page += 1

    users_data = []
    for c in contributors:
        username = c['login'].lower()
        if username in user_locations:
            location = user_locations[username]
        else:
            u_resp = requests.get(c['url'], headers=headers)
            location = None
            if u_resp.status_code == 200:
                location = u_resp.json().get("location")
                user_locations[username] = location
            else:
                user_locations[username] = None
        
        users_data.append({"login": username, "location": location})

    save_json(LOCATION_CACHE_FILE, user_locations)
    repo_cache[repo_name] = {"timestamp": now, "data": users_data}
    save_json(CACHE_FILE, repo_cache)
    
    return users_data


# === Register Blueprints ===
from widget import widget_bp

app.register_blueprint(widget_bp)


if __name__ == '__main__':
    app.run(port=5002, debug=True)

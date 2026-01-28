import os

import httpx

CONFIG_URL = "https://cdn.jsdelivr.net/gh/fedi-libs/.github@master/data/templates.json"

def fetch_templates() -> list[dict]:
    """Fetch the template list from a remote JSON file."""
    try:
        r = httpx.get(os.environ.get("APKIT_TEMPLATES", CONFIG_URL))
        r.raise_for_status()
        return r.json().get("templates", [])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch templates: {e}")
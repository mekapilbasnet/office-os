#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIP Design Core - BM25 search engine for Corporate Identity Program design guidelines
"""

import re
import sys
from pathlib import Path

# Shared helpers live one directory up (design/scripts/_common.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import load_csv as _load_csv  # noqa: E402
from _common import search as _search_domain  # noqa: E402
from _common import search_all as _search_all  # noqa: E402

# ============ CONFIGURATION ============
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "cip"
MAX_RESULTS = 3

CSV_CONFIG = {
    "deliverable": {
        "file": "deliverables.csv",
        "search_cols": ["Deliverable", "Category", "Keywords", "Description", "Mockup Context"],
        "output_cols": ["Deliverable", "Category", "Keywords", "Description", "Dimensions", "File Format", "Logo Placement", "Color Usage", "Typography Notes", "Mockup Context", "Best Practices", "Avoid"]
    },
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Name", "Category", "Keywords", "Description", "Mood"],
        "output_cols": ["Style Name", "Category", "Keywords", "Description", "Primary Colors", "Secondary Colors", "Typography", "Materials", "Finishes", "Mood", "Best For", "Avoid For"]
    },
    "industry": {
        "file": "industries.csv",
        "search_cols": ["Industry", "Keywords", "CIP Style", "Mood"],
        "output_cols": ["Industry", "Keywords", "CIP Style", "Primary Colors", "Secondary Colors", "Typography", "Key Deliverables", "Mood", "Best Practices", "Avoid"]
    },
    "mockup": {
        "file": "mockup-contexts.csv",
        "search_cols": ["Context Name", "Category", "Keywords", "Scene Description"],
        "output_cols": ["Context Name", "Category", "Keywords", "Scene Description", "Lighting", "Environment", "Props", "Camera Angle", "Background", "Style Notes", "Best For", "Prompt Modifiers"]
    }
}


# BM25, CSV loading and search live in ../_common.py (cached per file).


def detect_domain(query):
    """Auto-detect the most relevant domain from query"""
    query_lower = query.lower()

    domain_keywords = {
        "deliverable": ["card", "letterhead", "envelope", "folder", "shirt", "cap", "badge", "signage", "vehicle", "car", "van", "stationery", "uniform", "merchandise", "packaging", "banner", "booth"],
        "style": ["style", "minimal", "modern", "luxury", "vintage", "industrial", "elegant", "bold", "corporate", "organic", "playful"],
        "industry": ["tech", "finance", "legal", "healthcare", "hospitality", "food", "fashion", "retail", "construction", "logistics"],
        "mockup": ["mockup", "scene", "context", "photo", "shot", "lighting", "background", "studio", "lifestyle"]
    }

    scores = {domain: sum(1 for kw in keywords if kw in query_lower) for domain, keywords in domain_keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "deliverable"


def search(query, domain=None, max_results=MAX_RESULTS):
    """Main search function with auto-domain detection"""
    if domain is None:
        domain = detect_domain(query)
    if domain not in CSV_CONFIG:
        domain = "deliverable"
    return _search_domain(DATA_DIR, CSV_CONFIG, query, domain, max_results)


def search_all(query, max_results=2):
    """Search across all domains and combine results"""
    return _search_all(search, CSV_CONFIG, query, max_results)



_DELIVERABLE_SPLIT = re.compile(r"[,;/\n]+|\s+&\s+|\s+and\s+", re.IGNORECASE)


def _stem(word):
    """Very small plural normaliser: cards -> card, uniforms -> uniform."""
    word = word.lower()
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


# Adjectives that appear in many deliverable keyword lists; matching on them
# alone ("Premium stationery" -> Gift Box) produces confident wrong rows.
_GENERIC_WORDS = frozenset({
    "premium", "digital", "custom", "customized", "branded", "corporate",
    "office", "company", "professional", "modern", "luxury", "standard",
    "basic", "printed", "print", "branding", "brand", "quality", "new",
})

# Industry text wording -> deliverable-name wording (applied to stemmed words).
_DELIVERABLE_SYNONYMS = {"vehicle": "van"}


def _deliverable_text_stems(row):
    text = " ".join(str(row.get(k, "")) for k in ("Deliverable", "Keywords"))
    return {_stem(w) for w in re.findall(r"\w+", text.lower())}


def _exact_deliverable(stems):
    """Return the deliverable row whose name equals the given stemmed words."""
    for row in _load_csv(DATA_DIR / CSV_CONFIG["deliverable"]["file"]):
        name = [_stem(w) for w in re.findall(r"\w+", row.get("Deliverable", "").lower())]
        if name == list(stems):
            return {col: row.get(col, "") for col in CSV_CONFIG["deliverable"]["output_cols"] if col in row}
    return None


def parse_key_deliverables(text, limit=5):
    """Turn the free-text "Key Deliverables" cell into deliverable rows.

    The industries CSV stores things like "Business cards office signage
    digital templates vehicle" (no separators). Splitting on whitespace and
    searching each word returns wrong rows, so instead:

    1. split on commas / semicolons / slashes / "and" / "&" into phrases;
    2. inside each phrase, walk the words left to right and, at each position,
       prefer a run (up to 3 words) that exactly equals a known deliverable
       name ("Business cards" -> Business Card); otherwise a run (2 words,
       then 1) whose best BM25 match really contains every word of the run in
       its name or keywords;
    3. de-duplicate, keep order, cap at `limit`.
    """
    results = []
    seen = set()

    def add(row):
        name = row.get("Deliverable")
        if name not in seen:
            seen.add(name)
            results.append(row)

    for phrase in _DELIVERABLE_SPLIT.split(str(text or "")):
        words = [_DELIVERABLE_SYNONYMS.get(_stem(w), _stem(w)) for w in re.findall(r"\w+", phrase)]
        i = 0
        while i < len(words) and len(results) < limit:
            step = 0
            for n in (3, 2, 1):  # exact deliverable names first
                chunk = words[i:i + n]
                if len(chunk) == n:
                    row = _exact_deliverable(chunk)
                    if row:
                        add(row)
                        step = n
                        break
            if not step:
                for n in (2, 1):  # then keyword-backed fuzzy matches
                    chunk = words[i:i + n]
                    if len(chunk) < n:
                        continue
                    # Generic adjectives never justify a match on their own
                    specific = [w for w in chunk if w not in _GENERIC_WORDS]
                    if not specific:
                        step = n
                        break
                    found = search(" ".join(specific), "deliverable", 1).get("results") or []
                    if found and all(w in _deliverable_text_stems(found[0]) for w in specific):
                        add(found[0])
                        step = n
                        break
            i += step or 1
    return results[:limit]


def get_cip_brief(brand_name, industry_query, style_query=None):
    """Generate a comprehensive CIP brief for a brand"""
    # Search industry
    industry_results = search(industry_query, "industry", 1)
    industry = industry_results.get("results", [{}])[0] if industry_results.get("results") else {}

    # Search style (use industry style if not specified)
    style_query = style_query or industry.get("CIP Style", "corporate minimal")
    style_results = search(style_query, "style", 1)
    style = style_results.get("results", [{}])[0] if style_results.get("results") else {}

    # Get recommended deliverables for the industry
    deliverable_results = parse_key_deliverables(industry.get("Key Deliverables", ""))

    return {
        "brand_name": brand_name,
        "industry": industry,
        "style": style,
        "recommended_deliverables": deliverable_results,
        "color_system": {
            "primary": style.get("Primary Colors", industry.get("Primary Colors", "")),
            "secondary": style.get("Secondary Colors", industry.get("Secondary Colors", ""))
        },
        "typography": style.get("Typography", industry.get("Typography", "")),
        "materials": style.get("Materials", ""),
        "finishes": style.get("Finishes", "")
    }

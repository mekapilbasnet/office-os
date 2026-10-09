#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo Design Core - BM25 search engine for logo design guidelines
"""

import sys
from pathlib import Path

# Shared helpers live one directory up (design/scripts/_common.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import BM25, load_csv as _load_csv  # noqa: E402,F401
from _common import search_csv as _search_csv  # noqa: E402
from _common import search as _search_domain  # noqa: E402
from _common import search_all as _search_all  # noqa: E402

# ============ CONFIGURATION ============
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "logo"
MAX_RESULTS = 3

CSV_CONFIG = {
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Name", "Category", "Keywords", "Best For"],
        "output_cols": ["Style Name", "Category", "Keywords", "Primary Colors", "Secondary Colors", "Typography", "Effects", "Best For", "Avoid For", "Complexity", "Era"]
    },
    "color": {
        "file": "colors.csv",
        "search_cols": ["Palette Name", "Category", "Keywords", "Psychology", "Best For"],
        "output_cols": ["Palette Name", "Category", "Keywords", "Primary Hex", "Secondary Hex", "Accent Hex", "Background Hex", "Text Hex", "Psychology", "Best For", "Avoid For"]
    },
    "industry": {
        "file": "industries.csv",
        "search_cols": ["Industry", "Keywords", "Recommended Styles", "Mood"],
        "output_cols": ["Industry", "Keywords", "Recommended Styles", "Primary Colors", "Typography", "Common Symbols", "Mood", "Best Practices", "Avoid"]
    }
}


# BM25, CSV loading and search live in ../_common.py (cached per file).


def detect_domain(query):
    """Auto-detect the most relevant domain from query"""
    query_lower = query.lower()

    domain_keywords = {
        "style": ["style", "minimalist", "vintage", "modern", "retro", "geometric", "abstract", "emblem", "badge", "wordmark", "mascot", "luxury", "playful", "corporate"],
        "color": ["color", "palette", "hex", "#", "rgb", "blue", "red", "green", "gold", "warm", "cool", "vibrant", "pastel"],
        "industry": ["tech", "healthcare", "finance", "legal", "restaurant", "food", "fashion", "beauty", "education", "sports", "fitness", "real estate", "crypto", "gaming"]
    }

    scores = {domain: sum(1 for kw in keywords if kw in query_lower) for domain, keywords in domain_keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "style"


def search(query, domain=None, max_results=MAX_RESULTS):
    """Main search function with auto-domain detection"""
    if domain is None:
        domain = detect_domain(query)
    if domain not in CSV_CONFIG:
        domain = "style"
    return _search_domain(DATA_DIR, CSV_CONFIG, query, domain, max_results)


def search_all(query, max_results=2):
    """Search across all domains and combine results"""
    return _search_all(search, CSV_CONFIG, query, max_results)

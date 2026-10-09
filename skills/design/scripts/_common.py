#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared helpers for the design skill scripts (logo, cip, icon).

- load_env(): load a fixed allow-list of API keys from .env files
- BM25 + CSV search helpers used by logo/core.py and cip/core.py

Local patch (not in upstream): this module replaces code that was copy-pasted
into logo/core.py, cip/core.py and three generate.py files.
"""

import csv
import os
import re
from collections import defaultdict
from functools import lru_cache
from math import log
from pathlib import Path

# ============ ENVIRONMENT ============
# Only these variables are ever read from .env files. Anything else in those
# files is ignored, so unrelated secrets never leak into os.environ.
KNOWN_ENV_KEYS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ATLASCLOUD_API_KEY",
    "MUAPI_API_KEY",
)

# design/.env, ~/.claude/skills/.env, ~/.claude/.env (first one wins)
SKILL_DIR = Path(__file__).resolve().parent.parent


def env_file_paths():
    return [
        SKILL_DIR / ".env",
        Path.home() / ".claude" / "skills" / ".env",
        Path.home() / ".claude" / ".env",
    ]


def load_env(paths=None, keys=KNOWN_ENV_KEYS):
    """Load KNOWN_ENV_KEYS from .env files into os.environ.

    Existing environment variables are never overridden. Lines for any other
    key are skipped. Returns the list of keys that were set from files.
    """
    allowed = set(keys)
    loaded = []
    for env_path in (paths if paths is not None else env_file_paths()):
        try:
            if not env_path.exists():
                continue
            text = env_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            key, value = line.split("=", 1)
            key = key.strip()
            if key not in allowed or key in os.environ:
                continue
            os.environ[key] = value.strip().strip("\"'")
            loaded.append(key)
    return loaded


# ============ BM25 IMPLEMENTATION ============
class BM25:
    """BM25 ranking algorithm for text search"""

    MIN_TOKEN_LEN = 2

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0

    def tokenize(self, text):
        """Lowercase, split, remove punctuation, drop 1-char tokens.

        Two-character tokens ("ai", "ui", "3d") are kept on purpose.
        """
        text = re.sub(r"[^\w\s]", " ", str(text).lower())
        return [w for w in text.split() if len(w) >= self.MIN_TOKEN_LEN]

    def fit(self, documents):
        """Build BM25 index from documents"""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = (sum(self.doc_lengths) / self.N) or 1.0

        for doc in self.corpus:
            seen = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] += 1
                    seen.add(word)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.N - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query):
        """Score all documents against query"""
        query_tokens = self.tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0
            doc_len = self.doc_lengths[idx]
            term_freqs = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1

            for token in query_tokens:
                if token in self.idf:
                    tf = term_freqs[token]
                    idf = self.idf[token]
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (
                        1 - self.b + self.b * doc_len / self.avgdl
                    )
                    score += idf * numerator / denominator

            scores.append((idx, score))

        return sorted(scores, key=lambda x: x[1], reverse=True)


# ============ SEARCH FUNCTIONS ============
def _mtime(filepath):
    try:
        return os.stat(filepath).st_mtime_ns
    except OSError:
        return 0


@lru_cache(maxsize=64)
def _load_csv_cached(filepath, mtime):
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        return tuple(csv.DictReader(f))


def load_csv(filepath):
    """Load CSV rows (cached per file + modification time). Rows are shared:
    treat them as read-only."""
    return _load_csv_cached(str(filepath), _mtime(filepath))


@lru_cache(maxsize=64)
def _index_cached(filepath, mtime, search_cols):
    rows = _load_csv_cached(filepath, mtime)
    documents = [
        " ".join(str(row.get(col, "")) for col in search_cols) for row in rows
    ]
    bm25 = BM25()
    bm25.fit(documents)
    return bm25


def search_csv(filepath, search_cols, output_cols, query, max_results):
    """Search one CSV with BM25; the parsed rows and index are cached."""
    filepath = Path(filepath)
    if not filepath.exists():
        return []

    mtime = _mtime(filepath)
    rows = _load_csv_cached(str(filepath), mtime)
    bm25 = _index_cached(str(filepath), mtime, tuple(search_cols))
    ranked = bm25.score(query)

    results = []
    for idx, score in ranked[:max_results]:
        if score > 0:
            row = rows[idx]
            results.append({col: row.get(col, "") for col in output_cols if col in row})
    return results


def search(data_dir, csv_config, query, domain, max_results):
    """Domain search over a CSV_CONFIG mapping."""
    config = csv_config[domain]
    filepath = Path(data_dir) / config["file"]
    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}

    results = search_csv(
        filepath, config["search_cols"], config["output_cols"], query, max_results
    )
    return {
        "domain": domain,
        "query": query,
        "file": config["file"],
        "count": len(results),
        "results": results,
    }


def search_all(search_fn, csv_config, query, max_results=2):
    """Search every domain with `search_fn(query, domain, max_results)`."""
    all_results = {}
    for domain in csv_config.keys():
        result = search_fn(query, domain, max_results)
        if result.get("results"):
            all_results[domain] = result["results"]
    return all_results

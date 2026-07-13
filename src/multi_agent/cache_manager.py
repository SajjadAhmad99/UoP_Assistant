"""
Semantic Cache for UoP Multi-Agent Responses.

Changes vs original:
- Uses shared embeddings singleton (no more independent model load)
- Adds 7-day TTL eviction (README §5: prevent outdated memory entries)
- On save: removes ALL existing entries for the same query before inserting (README §5)
- Keeps a maximum of 200 most-recent entries
"""
import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from .embeddings_singleton import get_embeddings_model

CACHE_FILE = os.path.join(os.path.dirname(__file__), "data", "response_cache.json")
MAX_CACHE_SIZE = 200
MAX_AGE_DAYS   = 7  # Evict entries older than this (README §5: prevent stale memory)


class ResponseCache:
    """
    Semantic Cache for Agent Responses.
    Stores successful answers and retrieves them when the live site is down.
    """

    def __init__(self):
        self._ensure_cache_exists()
        # Embeddings loaded via shared singleton — no duplicate model load

    # ── Private helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _ensure_cache_exists():
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        if not os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    @staticmethod
    def _load_cache() -> List[Dict[str, Any]]:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ResponseCache] Error loading cache: {e}")
            return []

    @staticmethod
    def _save_cache(data: List[Dict[str, Any]]):
        try:
            if len(data) > MAX_CACHE_SIZE:
                data = data[-MAX_CACHE_SIZE:]
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ResponseCache] Error saving cache: {e}")

    @staticmethod
    def _is_fresh(entry: Dict[str, Any]) -> bool:
        """Return True if the entry is within MAX_AGE_DAYS."""
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", ""))
            return (datetime.now() - ts) < timedelta(days=MAX_AGE_DAYS)
        except Exception:
            return True  # Unknown age — keep it

    # ── Public API ─────────────────────────────────────────────────────────────
    def save(self, query: str, answer: str, agent_name: str):
        """
        Save a successful response.
        Removes ALL previous entries for the same query before inserting (no duplicates).
        """
        try:
            model = get_embeddings_model()
            cache = self._load_cache()
            embedding = model.embed_query(query)

            # README §5: Delete OLD cached response for the SAME query
            cache = [e for e in cache if e.get("query", "").lower() != query.lower()]

            entry = {
                "query":      query,
                "embedding":  embedding,
                "answer":     answer,
                "agent_name": agent_name,
                "timestamp":  datetime.now().isoformat(),
                "hit_count":  0,
            }
            cache.append(entry)
            self._save_cache(cache)
            print(f"[ResponseCache] Saved response for: '{query}'")
        except Exception as e:
            print(f"[ResponseCache] Failed to save entry: {e}")

    def search(self, query: str, threshold: float = 0.70) -> Optional[Dict[str, Any]]:
        """
        Search for a semantically similar cached response.
        Returns best matching fresh entry if similarity >= threshold.
        Evicts stale (>7-day) entries automatically.
        """
        try:
            model = get_embeddings_model()
            cache = self._load_cache()
            if not cache:
                return None

            # Evict stale entries (README §5)
            fresh_cache = [e for e in cache if self._is_fresh(e)]
            if len(fresh_cache) < len(cache):
                evicted = len(cache) - len(fresh_cache)
                print(f"[ResponseCache] Evicted {evicted} stale entries (>{MAX_AGE_DAYS} days old).")
                self._save_cache(fresh_cache)
                cache = fresh_cache

            if not cache:
                return None

            query_emb = np.array(model.embed_query(query))
            best_match = None
            max_sim = -1.0

            for entry in cache:
                cached_emb = np.array(entry["embedding"])
                norm = np.linalg.norm(query_emb) * np.linalg.norm(cached_emb)
                if norm == 0:
                    continue
                sim = float(np.dot(query_emb, cached_emb) / norm)
                if sim > max_sim:
                    max_sim = sim
                    best_match = entry

            print(f"[ResponseCache] Best semantic match score: {max_sim:.3f}")
            if max_sim >= threshold and best_match is not None:
                best_match["hit_count"] = best_match.get("hit_count", 0) + 1
                self._save_cache(cache)
                return best_match
        except Exception as e:
            print(f"[ResponseCache] Search failed: {e}")

        return None

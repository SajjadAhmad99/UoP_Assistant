"""
Debug Metrics & System Evaluation Module
Tracks retrieval quality, hallucination risk, source reliability,
and provides structured debug output for developer testing.
"""
from __future__ import annotations

import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class RetrievalSource:
    """Metadata for a single retrieved source."""
    source_name: str = ""
    url: str = ""
    timestamp: str = ""
    reliability: str = "UNKNOWN"       # HIGH / MEDIUM / LOW / UNKNOWN
    status_code: int = 0
    latency_ms: float = 0.0
    content_length: int = 0
    success: bool = False


@dataclass
class QueryMetrics:
    """
    Captures all debug/telemetry data for a single query execution.
    Populated progressively as the system processes the query.
    """
    # ── Query Info ────────────────────────────────────────────────────────
    query: str = ""
    query_timestamp: str = ""
    intent_categories: List[str] = field(default_factory=list)

    # ── Retrieval Metrics ────────────────────────────────────────────────
    retrieved_sources: List[RetrievalSource] = field(default_factory=list)
    retrieved_docs_count: int = 0
    top_similarity_score: float = 0.0
    retrieval_status: str = "PENDING"  # SUCCESS / PARTIAL / FAILED / PENDING
    failed_sources: int = 0
    duplicate_chunks_removed: int = 0

    # ── Performance ──────────────────────────────────────────────────────
    total_response_time_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    token_usage: int = 0

    # ── Quality Scores ───────────────────────────────────────────────────
    hallucination_risk: str = "UNKNOWN"  # LOW / MEDIUM / HIGH / CRITICAL
    hallucination_reason: str = ""
    grounding_score: float = 0.0         # 0.0 to 1.0
    source_reliability: str = "UNKNOWN"  # HIGH / MEDIUM / LOW
    confidence_score: float = 0.0        # 0.0 to 1.0

    # ── Cache Info ───────────────────────────────────────────────────────
    cache_hit: bool = False
    cache_similarity: float = 0.0

    # ── Self-Healing ─────────────────────────────────────────────────────
    fallback_triggered: bool = False
    fallback_source: str = ""            # "cache" / "rag_fallback" / "friendly_fallback"

    # ── Raw Debug ────────────────────────────────────────────────────────
    debug_logs: List[str] = field(default_factory=list)

    def add_source(self, source: RetrievalSource):
        """Register a retrieval source."""
        self.retrieved_sources.append(source)
        if source.success:
            self.retrieved_docs_count += 1
        else:
            self.failed_sources += 1

    def log(self, message: str):
        """Append a timestamped debug log entry."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.debug_logs.append(f"[{ts}] {message}")

    def finalize(self, response_text: str):
        """
        Compute derived scores after all retrieval and generation is complete.
        """
        total = len(self.retrieved_sources)
        successful = sum(1 for s in self.retrieved_sources if s.success)

        # Retrieval status
        if total == 0:
            self.retrieval_status = "FAILED"
        elif successful == total:
            self.retrieval_status = "SUCCESS"
        elif successful > 0:
            self.retrieval_status = "PARTIAL"
        else:
            self.retrieval_status = "FAILED"

        # Source reliability (aggregate)
        if successful == total and total > 0:
            self.source_reliability = "HIGH"
        elif successful > 0:
            self.source_reliability = "MEDIUM"
        else:
            self.source_reliability = "LOW"

        # Grounding score — ratio of tool-sourced content indicators
        grounding_markers = [
            "according to", "based on", "from the", "the website",
            "internal records", "the tool", "scraped", "retrieved",
            "source:", "http://", "https://", "www.uop.edu.pk"
        ]
        response_lower = response_text.lower()
        marker_hits = sum(1 for m in grounding_markers if m in response_lower)
        self.grounding_score = min(1.0, marker_hits / max(len(grounding_markers) * 0.4, 1))

        # Confidence score
        if self.retrieval_status == "SUCCESS" and self.hallucination_risk == "LOW":
            self.confidence_score = 0.90 + (self.grounding_score * 0.1)
        elif self.retrieval_status == "PARTIAL":
            self.confidence_score = 0.60 + (self.grounding_score * 0.2)
        elif self.cache_hit:
            self.confidence_score = 0.50 + (self.cache_similarity * 0.3)
        else:
            self.confidence_score = 0.30

        self.confidence_score = round(min(1.0, self.confidence_score), 2)
        self.grounding_score = round(self.grounding_score, 2)


class SystemEvaluator:
    """
    Evaluates system performance on 10 dimensions.
    Scores each dimension out of 10.
    """

    @staticmethod
    def evaluate(metrics: QueryMetrics, response_text: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}

        # 1. Retrieval Accuracy
        if metrics.retrieval_status == "SUCCESS":
            scores["retrieval_accuracy"] = 9.0
        elif metrics.retrieval_status == "PARTIAL":
            scores["retrieval_accuracy"] = 6.0
        else:
            scores["retrieval_accuracy"] = 2.0

        # 2. Relevance
        if len(response_text) > 50 and metrics.retrieval_status != "FAILED":
            scores["relevance"] = 8.0
        elif metrics.cache_hit:
            scores["relevance"] = 6.0
        else:
            scores["relevance"] = 3.0

        # 3. Freshness
        if metrics.retrieval_status == "SUCCESS" and not metrics.cache_hit:
            scores["freshness"] = 9.0
        elif metrics.cache_hit:
            scores["freshness"] = 5.0
        else:
            scores["freshness"] = 2.0

        # 4. Hallucination Rate (inverted — lower risk = higher score)
        risk_map = {"LOW": 9.0, "MEDIUM": 5.0, "HIGH": 2.0, "CRITICAL": 1.0, "UNKNOWN": 4.0}
        scores["hallucination_rate"] = risk_map.get(metrics.hallucination_risk, 4.0)

        # 5. Source Attribution
        scores["source_attribution"] = min(10.0, metrics.grounding_score * 10)

        # 6. Latency
        if metrics.total_response_time_ms < 5000:
            scores["latency"] = 9.0
        elif metrics.total_response_time_ms < 15000:
            scores["latency"] = 6.0
        elif metrics.total_response_time_ms < 30000:
            scores["latency"] = 4.0
        else:
            scores["latency"] = 2.0

        # 7. Context Understanding
        if metrics.retrieval_status in ("SUCCESS", "PARTIAL") and len(response_text) > 100:
            scores["context_understanding"] = 8.0
        else:
            scores["context_understanding"] = 4.0

        # 8. Multi-source Reasoning
        if len(metrics.intent_categories) > 1 and metrics.retrieval_status != "FAILED":
            scores["multi_source_reasoning"] = 8.0
        elif len(metrics.intent_categories) == 1 and metrics.retrieval_status == "SUCCESS":
            scores["multi_source_reasoning"] = 7.0
        else:
            scores["multi_source_reasoning"] = 3.0

        # 9. Duplicate Filtering
        if metrics.duplicate_chunks_removed > 0:
            scores["duplicate_filtering"] = 8.0
        else:
            scores["duplicate_filtering"] = 7.0  # No duplicates = clean

        # 10. Failure Handling
        if metrics.fallback_triggered and len(response_text) > 50:
            scores["failure_handling"] = 8.0  # Graceful fallback
        elif metrics.retrieval_status == "FAILED" and len(response_text) > 50:
            scores["failure_handling"] = 6.0  # Friendly error
        elif metrics.retrieval_status == "SUCCESS":
            scores["failure_handling"] = 9.0  # No failure needed
        else:
            scores["failure_handling"] = 3.0

        # Round all scores
        return {k: round(v, 1) for k, v in scores.items()}


def format_debug_output(metrics: QueryMetrics, evaluation: Dict[str, float]) -> str:
    """
    Render the full structured debug output block for the Streamlit debug panel.
    """
    lines = []

    # ── Retrieved Sources ────────────────────────────────────────────────
    lines.append("### 📡 Retrieved Sources")
    if metrics.retrieved_sources:
        for src in metrics.retrieved_sources:
            status = "✅" if src.success else "❌"
            lines.append(
                f"- {status} **{src.source_name}**\n"
                f"  - URL: `{src.url}`\n"
                f"  - Timestamp: {src.timestamp}\n"
                f"  - Reliability: **{src.reliability}**\n"
                f"  - Latency: {src.latency_ms:.0f}ms | Status: {src.status_code}"
            )
    else:
        lines.append("- No sources retrieved")

    # ── Confidence ───────────────────────────────────────────────────────
    lines.append(f"\n### 🎯 Confidence Score: **{metrics.confidence_score}**")

    # ── System Evaluation ────────────────────────────────────────────────
    lines.append("\n### 📊 System Evaluation")
    for key, score in evaluation.items():
        label = key.replace("_", " ").title()
        bar = "█" * int(score) + "░" * (10 - int(score))
        lines.append(f"- {label}: `{bar}` **{score}/10**")

    # ── Debug Logs ───────────────────────────────────────────────────────
    lines.append("\n### 🔍 Debug Logs")
    if metrics.debug_logs:
        for log_entry in metrics.debug_logs[-20:]:  # Last 20 entries
            lines.append(f"- `{log_entry}`")
    else:
        lines.append("- No debug logs recorded")

    return "\n".join(lines)


def format_developer_metrics(metrics: QueryMetrics, evaluation: Dict[str, float]) -> str:
    """
    Render the JSON developer testing metrics block.
    """
    dev_metrics = {
        "query": metrics.query,
        "timestamp": metrics.query_timestamp,
        "intents": metrics.intent_categories,
        "retrieved_docs": metrics.retrieved_docs_count,
        "top_similarity": metrics.top_similarity_score,
        "retrieval_status": metrics.retrieval_status,
        "response_time_ms": round(metrics.total_response_time_ms),
        "hallucination_risk": metrics.hallucination_risk,
        "hallucination_reason": metrics.hallucination_reason,
        "source_reliability": metrics.source_reliability,
        "grounding_score": metrics.grounding_score,
        "confidence_score": metrics.confidence_score,
        "duplicate_chunks_removed": metrics.duplicate_chunks_removed,
        "failed_sources": metrics.failed_sources,
        "cache_hit": metrics.cache_hit,
        "fallback_triggered": metrics.fallback_triggered,
        "fallback_source": metrics.fallback_source,
        "evaluation_scores": evaluation,
    }
    return json.dumps(dev_metrics, indent=2)

"""
UoP AI Assistant - Main Entry Point
Entry point for the University of Peshawar information assistant.
"""
from __future__ import annotations
import os
import sys
import io

# Fix UTF-8 encoding for console output if possible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

from dotenv import load_dotenv
load_dotenv()

import time
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter

from multi_agent.crew import multi_agent, classify_query
from multi_agent.cache_manager import ResponseCache
from multi_agent.debug_metrics import (
    QueryMetrics, RetrievalSource, SystemEvaluator,
    format_debug_output, format_developer_metrics
)

# Initialize semantic cache
response_cache = ResponseCache()

# Markers that indicate a real-time retrieval failure
FAILURE_MARKERS = [
    "temporarily unavailable",
    "site is down",
    "unable to access",
    "site is currently inaccessible",
    "try visiting the relevant page directly",
    "not found in the university documents",
    "SITE_UNAVAILABLE",
    "NO_DATA_FOUND"
]


def _detect_hallucination(text: str) -> Tuple[bool, str]:
    """
    Detect hallucinated output patterns.

    Returns:
        Tuple[bool, str]: (is_hallucinated, reason)
    """
    if not text or len(text.strip()) < 10:
        return True, "empty_response"

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Pattern 1: Repeated lines (dept agent repeating names)
    if len(lines) >= 10:
        counts = Counter(lines)
        most_common_line, repeat_count = counts.most_common(1)[0]
        if repeat_count > 8: # Increased from 5 to allow for larger legitimate lists
            # Check if it's a name pattern (not a legitimate repeated header)
            if any(word in most_common_line.lower() for word in ["dr.", "prof", "mr.", "ms."]):
                return True, "repeated_names"

    # Pattern 2: Long response with excessive Dr. names → department hallucination
    if len(text) > 3000:
        name_lines = [
            l for l in lines
            if (l.startswith("* Dr.") or l.startswith("- Dr.") or
                l.startswith("* Prof") or l.startswith("- Prof") or
                l.startswith("Dr.") or l.startswith("Prof."))
        ]
        if len(name_lines) > 20:
            return True, "excessive_faculty_names"

    # Pattern 3: News empty template — lines like "- **Title:**" with nothing after
    empty_field_patterns = [
        "- **Title:**", "- **Date:**", "- **URL:**",
        "**Title:**", "**Date:**", "**URL:**",
        "* **Title:**", "* **Date:**", "* **URL:**",
        "1. **Title:**", "2. **Title:**", "3. **Title:**",
    ]
    empty_field_lines = [
        l for l in lines
        if l in empty_field_patterns or (l.endswith(":") and len(l) < 15)
    ]
    if len(empty_field_lines) >= 3:
        return True, "empty_template_fields"

    # Pattern 4: Gibberish or placeholder text
    placeholder_patterns = [
        "[insert", "[date]", "[url]", "[title]",
        "placeholder", "todo", "tbd", "xxx",
    ]
    if any(p in text.lower() for p in placeholder_patterns):
        return True, "placeholder_text"

    # Pattern 5: Contradictory statements indicating confusion
    contradiction_markers = [
        "i don't have access", "i cannot access", "unable to access",
        "however, based on my knowledge", "from my training data",
    ]
    if any(m in text.lower() for m in contradiction_markers):
        # Only flag if combined with specific data (mixing admission of no access with claims)
        if any(kw in text.lower() for kw in ["fee", "pkR", "rupees", "semester"]):
            return True, "contradictory_statement"

    return False, "ok"


def _friendly_fallback(prompt: str, reason: str = "unknown") -> str:
    """
    Return a context-aware friendly fallback message as plain text.
    """
    p = prompt.lower()

    if any(kw in p for kw in ["news", "announcement", "scholarship", "tender", "job", "opening", "event", "notice"]):
        return (
            "I'm sorry, I couldn't find any verified news or announcements right now. "
            "The University website may be temporarily unavailable. "
            "You can try visiting http://www.uop.edu.pk/news/ directly, or ask me again in a few minutes."
        )
    elif any(kw in p for kw in ["department", "faculty", "program", "professor", "course", "institute", "teacher", "chairman", "hod"]):
        return (
            "I'm sorry, I couldn't retrieve verified department information right now. "
            "The University website may be temporarily unavailable. "
            "You can try visiting http://www.uop.edu.pk/departments/ directly, or ask me again in a few minutes."
        )
    else:
        return (
            "I'm sorry, I couldn't find verified information for your query right now. "
            "The University website may be temporarily unavailable. "
            "You can try visiting http://www.uop.edu.pk directly, or ask me again in a few minutes."
        )


def _is_uop_related(query: str) -> bool:
    """
    Fast check: is this query related to University of Peshawar?
    Uses keyword matching against ALL known UoP terms + a general university lexicon.
    Returns True if the query is likely UoP-related, False otherwise.
    """
    import re
    q = query.lower()

    # 1. Explicit UoP mentions
    if any(tag in q for tag in ["uop", "uop ", "university of peshawar", "peshawar university",
                                 "peshawar uni", "upesh"]):
        return True

    # 2. General university/academic terms (could be about any university, but
    #    since this system is ONLY for UoP, we accept these)
    university_terms = {
        "university", "campus", "semester", "admission", "admissions",
        "fee", "fees", "tuition", "merit", "eligibility",
        "department", "departments", "faculty", "program", "programs",
        "programme", "programmes", "course", "courses",
        "professor", "professors", "lecturer", "teacher", "dean", "chairman", "hod",
        "vice chancellor", "vc", "registrar", "chancellor", "pro vice",
        "hostel", "hostels", "provost", "accommodation",
        "examination", "examinations", "exam", "exams", "result", "results",
        "date sheet", "datesheet",
        "news", "announcement", "tender", "scholarship", "notice",
        "student", "students", "library", "sports", "convocation",
        "oric", "qec", "das", "bic",
        "bs", "msc", "bsc", "ma", "mphil", "phd",
        "zoology", "botany", "chemistry", "physics", "mathematics",
        "computer science", "economics", "history", "english", "urdu",
        "pashto", "sociology", "psychology", "journalism", "law",
        "pharmacy", "geology", "statistics", "education", "islamiyat",
        "political science", "social work", "criminology",
        "statutory", "senate", "syndicate", "academic council",
        "genesis", "vision", "mission",
        "contact", "address", "email", "phone",
    }
    if any(re.search(rf"\b{re.escape(term)}\b", q) for term in university_terms):
        return True

    return False


def _is_greeting(query: str) -> bool:
    """
    Check if the query is a simple greeting, polite expression, or social expression.
    """
    import re
    q = re.sub(r'[^\w\s]', '', query.lower().strip())
    
    greeting_patterns = [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "how are you", "how are you doing", "whats up", "greetings",
        "thanks", "thank you", "thanks a lot", "thank you so much",
        "bye", "goodbye", "see you", "take care", "ok", "okay", "great",
        "awesome", "cool", "nice", "good", "thanks for the info",
        "thanks for the information", "thank you for the information",
        "thank you very much", "much appreciated", "i appreciate it",
        "alright", "sure", "yes", "no"
    ]
    
    if q in greeting_patterns:
        return True
        
    # Also catch very short phrases (1-3 words) that are purely conversational
    words = q.split()
    if len(words) <= 3:
        if any(g in q for g in ["hello", "hi", "hey", "thanks", "thank", "bye"]):
            return True
            
    return False

def _get_greeting_response(query: str) -> str:
    """
    Return a friendly plain text response for greetings and social expressions.
    """
    q = query.lower()
    if any(thx in q for thx in ["thank", "great", "awesome", "cool", "nice", "good", "ok", "okay", "alright"]):
        return "You are very welcome! Let me know if you need any further assistance with the University of Peshawar."
    elif any(bye in q for bye in ["bye", "see you", "take care"]):
        return "Goodbye! Have a great day!"
    elif "how are you" in q or "whats up" in q:
        return "I am doing well, thank you! How can I help you with the University of Peshawar today?"
    else:
        return "Hello! I am the University of Peshawar AI Assistant. How can I assist you today?"


# Standard friendly out-of-scope response
_OUT_OF_SCOPE_MSG = (
    "Thank you for your question!\n\n"
    "I'm the University of Peshawar AI Assistant, and I'm specifically designed "
    "to help with queries related to the University of Peshawar (UoP) only.\n\n"
    "Here are some things I can help you with:\n"
    "- Departments & Programs: faculties, courses, faculty members\n"
    "- News & Announcements: latest updates, tenders, scholarships\n"
    "- Fees & Admissions: fee structures, merit criteria, eligibility\n"
    "- Campus Life: hostels, sports, student resources\n"
    "- Examinations: results, date sheets, private exams\n"
    "- University Officials: Vice Chancellor, Registrar, statutory bodies\n\n"
    "Please ask me something about UoP and I'll be happy to assist!"
)


def _extract_clean_answer(text: str) -> str:
    """
    Extract only the actual user answer from the response.
    Handles both legacy 7-section format and new direct text format.
    """
    import re
    # Legacy format support: extract [Final Verified/Retrieved Answer] if present
    if "[Final Verified Answer]" in text or "[Final Retrieved Answer]" in text:
        pattern = r"\[Final (?:Verified|Retrieved) Answer\]\n(.*?)(?=\n\[|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    return text.strip()


def ask_uop(prompt: str, thread_id: str = "user_default") -> Tuple[str, Dict[str, Any]]:
    """
    Entry point for the UOP assistant.
    Routes query to the correct specialist via Python keyword classifier.

    Args:
        prompt: User's query string
        thread_id: Optional conversation thread identifier

    Returns:
        Tuple[str, Dict]: (response_text, metrics_dict)
            metrics_dict contains debug info, evaluation scores, and developer metrics.
            If debug is not applicable (greetings, out-of-scope), metrics_dict is empty.
    """
    # ── Initialize Metrics ───────────────────────────────────────────────
    metrics = QueryMetrics(
        query=prompt,
        query_timestamp=datetime.now().isoformat()
    )
    start_time = time.time()

    def _build_metrics_response(response_text: str) -> Dict[str, Any]:
        """Finalize metrics and build the metrics dict for the frontend."""
        metrics.total_response_time_ms = round((time.time() - start_time) * 1000, 1)
        metrics.finalize(response_text)
        evaluation = SystemEvaluator.evaluate(metrics, response_text)
        return {
            "debug_output": format_debug_output(metrics, evaluation),
            "developer_metrics": format_developer_metrics(metrics, evaluation),
            "confidence_score": metrics.confidence_score,
            "hallucination_risk": metrics.hallucination_risk,
            "retrieval_status": metrics.retrieval_status,
        }

    try:
        now = datetime.now()
        print(f"[{now}] --- ASSISTANT TRIGGERED --- query: {prompt}")
        metrics.log(f"Query received: {prompt}")

        # ── Greetings / Polite Expressions Guard ────────────────────────────
        if _is_greeting(prompt):
            print(f"[{now}] [GUARD] Query is a greeting/polite expression. Returning direct response.")
            metrics.log("Classified as greeting — skipping agent pipeline")
            return _get_greeting_response(prompt), {}

        # ── Out-of-Scope Guard ───────────────────────────────────────────────
        if not _is_uop_related(prompt):
            print(f"[{now}] [GUARD] Query is NOT related to UoP. Returning friendly redirect.")
            metrics.log("Classified as out-of-scope — skipping agent pipeline")
            return _OUT_OF_SCOPE_MSG, {}

        # ── Intent Classification ────────────────────────────────────────────
        intents = classify_query(prompt)
        metrics.intent_categories = [i.value for i in intents]
        metrics.log(f"Intent classification: {metrics.intent_categories}")

        # ── Crew Execution ───────────────────────────────────────────────────
        crew_start = time.time()
        metrics.log("Starting crew execution...")

        crew_instance = multi_agent().crew(query=prompt)
        result = crew_instance.kickoff(inputs={"query": prompt})
        result_str = str(result)

        crew_elapsed = (time.time() - crew_start) * 1000
        metrics.llm_latency_ms = round(crew_elapsed, 1)
        metrics.log(f"Crew execution completed in {crew_elapsed:.0f}ms")

        # ── Add a generic retrieval source entry for the crew run ────────────
        metrics.add_source(RetrievalSource(
            source_name="UOP Multi-Agent Crew",
            url="http://www.uop.edu.pk",
            timestamp=datetime.now().isoformat(),
            reliability="HIGH" if "SITE_UNAVAILABLE" not in result_str else "LOW",
            status_code=200 if "SITE_UNAVAILABLE" not in result_str else 0,
            latency_ms=crew_elapsed,
            content_length=len(result_str),
            success="SITE_UNAVAILABLE" not in result_str
        ))

        # ── Hallucination & Failure Detection ────────────────────────────────
        is_hallucinated, reason = _detect_hallucination(result_str)
        is_failure = any(marker.lower() in result_str.lower() for marker in FAILURE_MARKERS)

        if is_hallucinated:
            metrics.hallucination_risk = "HIGH"
            metrics.hallucination_reason = reason
            metrics.log(f"HALLUCINATION DETECTED: {reason}")
        elif is_failure:
            metrics.hallucination_risk = "MEDIUM"
            metrics.hallucination_reason = "site_unavailable"
            metrics.log("SITE_DOWN detected in response")
        else:
            metrics.hallucination_risk = "LOW"
            metrics.hallucination_reason = "ok"

        if is_hallucinated or is_failure:
            status = "HALLUCINATION" if is_hallucinated else "SITE_DOWN"
            print(f"[{datetime.now()}] [WARNING] {status} DETECTED — Activating Self-Healing Protocol...")
            metrics.log(f"Self-Healing Protocol activated: {status}")
            
            # Step 1: Check semantic cache first (Self-Optimization)
            cached_match = response_cache.search(prompt, threshold=0.70)
            if cached_match:
                print(f"[{datetime.now()}] [SUCCESS] CACHE HIT — Returning semantic match.")
                metrics.cache_hit = True
                metrics.cache_similarity = 0.70  # Minimum threshold that matched
                metrics.fallback_triggered = True
                metrics.fallback_source = "cache"
                metrics.log(f"Cache hit — returning cached response from {cached_match['timestamp'][:10]}")

                cached_answer = cached_match['answer']
                response = _extract_clean_answer(cached_answer)
                return response, _build_metrics_response(response)
            
            # Step 2: Self-Healing Fallback (RAG from Knowledge Base)
            if is_failure:
                print(f"[{datetime.now()}] [HEALING] Triggering Knowledge Base Fallback Crew...")
                metrics.log("Triggering RAG fallback crew...")
                try:
                    healing_crew = multi_agent().fallback_crew(query=prompt)
                    healing_result = healing_crew.kickoff(inputs={"query": prompt})
                    healing_str = str(healing_result)
                    
                    if "not_found" not in healing_str.lower() and len(healing_str) > 50:
                        print(f"[{datetime.now()}] [SUCCESS] SELF-HEALING COMPLETE — Returning factual response from internal records.")
                        metrics.fallback_triggered = True
                        metrics.fallback_source = "rag_fallback"
                        metrics.log("RAG fallback successful")
                        return _extract_clean_answer(healing_str), _build_metrics_response(healing_str)
                except Exception as he:
                    print(f"[{datetime.now()}] [ERROR] Self-Healing attempt failed: {he}")
                    metrics.log(f"RAG fallback failed: {he}")

            # Step 3: Final Friendly Fallback
            metrics.fallback_triggered = True
            metrics.fallback_source = "friendly_fallback"
            metrics.log("All recovery attempts failed — returning friendly fallback")
            fallback_response = _friendly_fallback(prompt, reason)
            return fallback_response, _build_metrics_response(fallback_response)

        print(f"[{datetime.now()}] --- SUCCESS --- Saving to cache.")
        metrics.log("Success — saving to cache")
        primary_intent = intents[0] if intents else "facts"
        response_cache.save(prompt, result_str, primary_intent.value if hasattr(primary_intent, 'value') else str(primary_intent))
        return _extract_clean_answer(result_str), _build_metrics_response(result_str)

    except Exception as e:
        now = datetime.now()
        print(f"[{now}] !!! ERROR !!!: {type(e).__name__}: {e}")
        metrics.log(f"EXCEPTION: {type(e).__name__}: {e}")
        metrics.hallucination_risk = "UNKNOWN"

        # Check for rate limit errors
        err_msg = str(e).lower()
        if "rate limit" in err_msg:
            error_response = (
                "I'm sorry, the system is currently experiencing high traffic. "
                "Please wait a moment and try again."
            )
            return error_response, _build_metrics_response(error_response)

        # Check for API key issues
        if "api key" in err_msg or "authentication" in err_msg:
            error_response = (
                "I'm sorry, there's a configuration issue with the system. "
                "Please contact support."
            )
            return error_response, _build_metrics_response(error_response)

        # Generic error
        error_response = (
            "I'm sorry, something went wrong while processing your request. "
            "Please try again in a moment. If the issue persists, you can visit "
            "http://www.uop.edu.pk directly or contact the university."
        )
        return error_response, _build_metrics_response(error_response)


if __name__ == "__main__":
    print("=" * 60)
    print("  University of Peshawar AI Assistant")
    print("  Ask about: departments, news, fees, admissions, and more!")
    print("=" * 60)
    print("Type 'exit', 'quit', or 'bye' to end the session.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye! Have a great day!")
            break

        response = ask_uop(user_input)
        print(f"\nAssistant: {response}\n")

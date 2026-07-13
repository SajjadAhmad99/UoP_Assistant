"""
UoP AI Assistant - Crew Configuration
Dynamically routes queries to the appropriate specialist agent.
"""
import os
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

from typing import List, Tuple, Optional, Dict, Any
from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv
from enum import Enum
load_dotenv()

from .tools.custom_tool import UoPHomepageScraperTool, UoPStudentCornerScraperTool, UoPExaminationScraperTool, UoPAcademicGovernanceScraperTool, UoPHostelScraperTool
from .tools.student_tool import UOPNewsScraperTool
from .tools.rag_tool import RAGTool
from .tools.department_tools import UOPDepartmentScraperTool

# ── NVIDIA NIM LLM Configuration ──────────────────────────────────────────
# Uses NVIDIA's OpenAI-compatible inference endpoint via the nvidia_nim/ provider.
# Model: meta/llama-3.1-8b-instruct  (free tier, actively maintained NIM)
# Docs: https://build.nvidia.com/meta/llama-3_1-8b-instruct

_NVIDIA_API_KEY = os.getenv("NVIDIA_NIM_API_KEY")
_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

LLM_FAST = LLM(
    model="nvidia_nim/meta/llama-3.1-70b-instruct",
    api_key=_NVIDIA_API_KEY,
    base_url=_NVIDIA_BASE_URL,
    temperature=0,
    max_tokens=2048
)

LLM_HIGH = LLM(
    model="nvidia_nim/meta/llama-3.1-70b-instruct",
    api_key=_NVIDIA_API_KEY,
    base_url=_NVIDIA_BASE_URL,
    temperature=0,
    max_tokens=1024
)

# ── Intent Classification Keywords ───────────────────────────────────────────
# Priority order: homepage > news > facts/fees > department > fallback(facts)

# Leadership and official contact queries - HIGHEST PRIORITY
HOMEPAGE_KEYWORDS = frozenset([
    "vice chancellor", "vc", "registrar", "chancellor", "pro vice", "pvc",
    "contact", "address", "phone", "email", "location", "office",
    "homepage", "treasurer", "controller", "examinations", "current vc",
    "current registrar", "current chancellor", "name of vc", "name of registrar",
    "who is vc", "who is registrar", "vc name", "registrar name",
    "genesis", "vision", "mission", "statutory body", "senate", "syndicate",
    "academic council", "board of studies", "research board", "finance committee",
    "affiliation committee", "discipline committee", "selection board", "anomaly committee",
    "board of faculties", "appellate committee", "administrative offices",
    "tell me about uop", "tell me about university of peshawar", "about uop", 
    "about university of peshawar", "about the university", "what is uop", 
    "what is university of peshawar", "university of peshawar info", "uop info",
    "introduction to uop", "introduction to university of peshawar", "general info",
    "general information", "uop overview", "university overview"
])

NEWS_KEYWORDS = frozenset([
    "news", "announcement", "scholarship", "tender", "job", "opening",
    "event", "events", "notice", "merit list", "deadline", "tenders", "vacancy",
    "admission notice", "result", "date sheet", "current", "latest",
    "recent", "circular", "notification"
])

STUDENT_CORNER_KEYWORDS = frozenset([
    "student corner", "bic", "business incubation", "incubation", "celebrations", "75 years",
    "scholarship", "aid", "private examinations", "sports", "distance education", "dde",
    "bara gali", "china study", "csc", "fata", "cfs", "community service", "csp",
    "digital library", "career development", "cdc", "environment", "envsoc",
    "harassment", "anti-sexual", "student resource", "student"
])

EXAMINATION_KEYWORDS = frozenset([
    "examination", "examinations", "exam", "exams", "controller message",
    "verification", "online verification", "result", "results", "private examination",
    "private examinations", "ba", "bsc", "ma", "msc", "apply", "how to apply",
    "date sheet", "datesheet", "download", "downloads"
])

ACADEMIC_GOVERNANCE_KEYWORDS = frozenset([
    "academic governance", "oric", "research", "innovation", "commercialization",
    "qec", "quality enhancement", "quality", "das", "advanced studies"
])

HOSTEL_KEYWORDS = frozenset([
    "hostel", "hostels", "provost", "accommodation", "boarding", "room",
    "regulations", "conduct", "discipline"
])

FEE_FACTS_KEYWORDS = frozenset([
    "fee", "fees", "tuition", "cost", "payment", "charges",
    "semester fee", "annual fee", "admission fee", "merit", "eligibility",
    "criteria", "admission", "requirement", "qualifying", "minimum marks",
    "aggregate", "closing merit", "seat", "seats", "structure", "how much",
    "what is the fee", "fee structure", "rules", "policy", "history"
])

# Department queries - includes academic structure AND "how many" questions about departments
DEPARTMENT_KEYWORDS = frozenset([
    "department", "faculty", "program", "professors", "programme", "teacher",
    "lecturer", "subject", "course", "institute", "computer science", "physics",
    "chemistry", "botany", "mathematics", "english", "economics", "history",
    "statistics", "zoology", "geology", "pharmacy", "law", "education",
    "islamic", "urdu", "pashto", "sociology", "journalism", "psychology",
    "political", "library", "architecture", "fine arts", "sports",
    "dean", "chairman", "hod", "faculty member", "researcher", "lab",
    "faculty of", "department of", "institute of", "how many department",
    "how many departments", "total departments", "list of department",
    "list of departments", "strongest department", "high strength", "best department"
])


class IntentCategory(str, Enum):
    HOMEPAGE = "homepage"
    NEWS = "news"
    STUDENT_CORNER = "student_corner"
    ACADEMIC_GOVERNANCE = "academic_governance"
    EXAMINATION = "examination"
    HOSTEL = "hostel"
    FACTS = "facts"
    DEPARTMENT = "department"


INTENT_PRIORITY = {
    IntentCategory.HOMEPAGE: 80,
    IntentCategory.NEWS: 70,
    IntentCategory.ACADEMIC_GOVERNANCE: 60,
    IntentCategory.EXAMINATION: 50,
    IntentCategory.HOSTEL: 40,
    IntentCategory.STUDENT_CORNER: 30,
    IntentCategory.FACTS: 20,
    IntentCategory.DEPARTMENT: 10
}


# ── Intent Descriptions for Embedding Router ──────────────────────────────────
INTENT_DESCRIPTIONS = {
    IntentCategory.HOMEPAGE: "General information about the university, leadership (Vice Chancellor, Registrar), statutory bodies (Senate, Syndicate, Academic Council), vision, mission, history, and administrative offices contact details.",
    IntentCategory.NEWS: "Time-sensitive announcements, recent news, upcoming events, merit lists, job openings, tenders, and admission notices.",
    IntentCategory.STUDENT_CORNER: "Resources for current students including scholarships, financial aid, business incubation center, sports, digital library, and distance education.",
    IntentCategory.ACADEMIC_GOVERNANCE: "Information regarding research, quality enhancement (QEC), advanced studies (DAS), innovation, and commercialization (ORIC).",
    IntentCategory.EXAMINATION: "Details about examinations, date sheets, results, private examinations, online verification, and exam fee structures.",
    IntentCategory.HOSTEL: "Information related to university hostels, accommodation, provost, and hostel rules/discipline.",
    IntentCategory.FACTS: "Factual knowledge base ONLY for fee structures, admission criteria, university rules, policies, and eligibility requirements.",
    IntentCategory.DEPARTMENT: "Academic architecture, list of faculties, departments, institutes, programs offered, and faculty members (professors, lecturers)."
}


class HybridRouter:
    """Multi-tiered router: Keyword -> Embedding -> LLM.
    Uses the shared embeddings singleton to avoid duplicate model loads.
    """

    _intent_embeddings = None

    @classmethod
    def _init_embeddings(cls):
        """Lazy-load intent embeddings using the shared singleton model."""
        if cls._intent_embeddings is None:
            import numpy as np
            from .embeddings_singleton import get_embeddings_model

            print("[HybridRouter] Precomputing intent embeddings via shared model...")
            model = get_embeddings_model()
            cls._np = np

            intents = list(INTENT_DESCRIPTIONS.keys())
            descriptions = [INTENT_DESCRIPTIONS[i] for i in intents]
            embeddings = model.embed_documents(descriptions)
            cls._intent_embeddings = {
                intent: np.array(emb)
                for intent, emb in zip(intents, embeddings)
            }
            print("[HybridRouter] Intent embeddings ready.")

    @staticmethod
    def keyword_route(query: str) -> List[IntentCategory]:
        import re
        q = query.lower()
        
        def has_match(patterns):
            return any(re.search(rf"\b{re.escape(kw)}\b", q) for kw in patterns)

        leadership_patterns = [
            "vc", "who is the", "name of",
            "current vc", "current registrar", "current chancellor",
            "vice chancellor", "pro vice", "pvc", "registrar", "chancellor"
        ]
        
        matched_intents = []
        if has_match(leadership_patterns): matched_intents.append(IntentCategory.HOMEPAGE)
        if has_match(HOMEPAGE_KEYWORDS): matched_intents.append(IntentCategory.HOMEPAGE)
        if has_match(NEWS_KEYWORDS): matched_intents.append(IntentCategory.NEWS)
        if has_match(STUDENT_CORNER_KEYWORDS): matched_intents.append(IntentCategory.STUDENT_CORNER)
        if has_match(ACADEMIC_GOVERNANCE_KEYWORDS): matched_intents.append(IntentCategory.ACADEMIC_GOVERNANCE)
        if has_match(EXAMINATION_KEYWORDS): matched_intents.append(IntentCategory.EXAMINATION)
        if has_match(HOSTEL_KEYWORDS): matched_intents.append(IntentCategory.HOSTEL)
        if has_match(FEE_FACTS_KEYWORDS): matched_intents.append(IntentCategory.FACTS)
        if has_match(DEPARTMENT_KEYWORDS): matched_intents.append(IntentCategory.DEPARTMENT)
        
        # Return unique matches
        return list(set(matched_intents))

    @classmethod
    def embedding_route(cls, query: str, threshold: float = 0.50) -> List[IntentCategory]:
        cls._init_embeddings()
        from .embeddings_singleton import get_embeddings_model
        model = get_embeddings_model()
        query_emb = cls._np.array(model.embed_query(query))

        matches = []
        for intent, emb in cls._intent_embeddings.items():
            norm = cls._np.linalg.norm(query_emb) * cls._np.linalg.norm(emb)
            score = float(cls._np.dot(query_emb, emb) / norm) if norm > 0 else 0.0
            if score >= threshold:
                matches.append((intent, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        print(f"[HybridRouter] Embedding matches: {[m[0].value for m in matches]}")
        return [m[0] for m in matches]

    @staticmethod
    def llm_route(query: str) -> List[IntentCategory]:
        intents_list = ", ".join([i.value for i in INTENT_DESCRIPTIONS.keys()])
        prompt = (
            f"Identify all relevant categories for the following query from this list: [{intents_list}].\n"
            f"If the query covers multiple topics (e.g., news AND fees), list ALL that apply.\n"
            f"Respond only with a comma-separated list of categories. No other text.\n\n"
            f"Query: {query}"
        )
        
        print("[HybridRouter] Routing via LLM fallback (Multi-Intent Detection)...")
        try:
            response = LLM_FAST.call([{"role": "user", "content": prompt}])
            results = [r.strip().lower() for r in response.split(",")]
            
            import string
            final_intents = []
            for res in results:
                res = res.translate(str.maketrans('', '', string.punctuation))
                try:
                    final_intents.append(IntentCategory(res))
                except ValueError:
                    continue
            
            print(f"[HybridRouter] LLM chose intents: {[i.value for i in final_intents]}")
            return final_intents
        except Exception as e:
            print(f"[HybridRouter] LLM routing failed: {e}")
            return []


def classify_query(query: str) -> List[IntentCategory]:
    """
    Detect all relevant intents using Hybrid Router Technique.
    Returns a list of unique IntentCategory values.
    """
    print(f"\n[Router] Analyzing Multi-Intent Query: '{query}'")
    
    # 1. Keyword Route (Fastest, High Confidence)
    keyword_intents = HybridRouter.keyword_route(query)
    if keyword_intents:
        print(f"[Router] Tier 1 Keywords Matched: {[i.value for i in keyword_intents]}")
        return keyword_intents
        
    # 2. Embedding Route (Semantic overlap)
    embedding_intents = HybridRouter.embedding_route(query, threshold=0.50)
    if embedding_intents:
        print(f"[Router] Tier 2 Embeddings Matched: {[i.value for i in embedding_intents]}")
        return embedding_intents
        
    # 3. LLM Route (Deep reasoning fallback)
    llm_intents = HybridRouter.llm_route(query)
    if llm_intents:
        print(f"[Router] Tier 3 LLM Matched: {[i.value for i in llm_intents]}")
        return llm_intents
    
    # 4. Final Fallback
    print("[Router] No specific intent detected. Falling back to FACTS.")
    return [IntentCategory.FACTS]


STRICT_ANSWER_DIRECTIVE = (
    "\n\nSTRICT ANSWERING RULES:\n"
    "- Extract ONLY information that directly answers the query.\n"
    "- Do NOT include unrelated, additional, or suggested information.\n"
    "- Treat cached/internal data as potentially outdated, partially incorrect, incomplete, stale, and lower priority than live sources.\n"
    "- If the query is outside your specific agent's domain/role (e.g. you are asked about fees/admissions but you are the department agent, or vice-versa), do NOT say the website is down or unavailable. Instead, output ONLY: 'Not applicable to this specialist domain.'\n"
    "\nANTI-HALLUCINATION PROTOCOL (MANDATORY):\n"
    "- NEVER hallucinate facts, URLs, names, dates, fee structures, departments, or notices.\n"
    "- If verification fails, respond ONLY with: 'No verified information found.'\n"
    "- If the website is unavailable: clearly state: 'The live website could not be reached. The following information may be based on cached/internal records and could be outdated.'\n"
    "- For faculty names, chairman/HOD names, staff members, and administrative positions: ONLY use officially retrieved website data. NEVER use LLM memory or training knowledge. NEVER infer names or autocomplete partial records. If no verified source exists, respond: 'No verified faculty/staff information found.'\n"
    "\nSOURCE VALIDATION RULES:\n"
    "- Prioritize: Official Live Website > Official API > Recently Verified Database > Cached Internal Records > Archived Data.\n"
    "- Mention the source, URL, retrieval timestamp, and reliability level for every fact.\n"
    "- If multiple sources conflict: compare all sources, list differences with timestamps, select the highest reliability source, and do NOT silently merge them."
)

# ── Agent Factory Functions ──────────────────────────────────────────────────
def make_news_agent() -> Agent:
    """Create the News Monitor Agent for current announcements."""
    return Agent(
        role="University News Monitor",
        goal="Report ONLY real news items returned by the scraper tool. Never invent headlines, dates, or URLs.",
        backstory=(
            "You retrieve live news from the University of Peshawar using the news scraper tool.\n\n"
            "ABSOLUTE RULES:\n"
            "1. ALWAYS call the university_of_peshawar_news_scraper tool first.\n"
            "2. Your FINAL ANSWER must be the text returned by the tool — do not reformat it "
            "and do not add new items.\n"
            "3. If the tool returns 'SITE_UNAVAILABLE' — write a warm, friendly apology "
            "that the UOP website is temporarily down and suggest visiting http://www.uop.edu.pk/news/ directly.\n"
            "4. If the tool returns 'NO_DATA_FOUND' — politely say no news was found.\n"
            "5. NEVER create a numbered list with blank Title, Date, or URL fields.\n"
            "6. NEVER invent any news headlines, dates, or links.\n"
            "7. Do NOT answer fee structure or department questions — those belong to other specialists.\n"
            "8. Be DIRECT and CONCISE — give the answer immediately without lengthy introductions."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UOPNewsScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_researcher_agent() -> Agent:
    """Create the Primary Fact-Checker Agent for knowledge base queries."""
    return Agent(
        role="University Primary Fact-Checker",
        goal="Retrieve absolute factual truth about UOP fees, admission criteria, rules, and history from the internal knowledge base.",
        backstory=(
            "You are the most precise specialist. You search the internal university documents "
            "for fee structures, admission criteria, merit requirements, and university history.\n\n"
            "YOUR RESPONSIBILITIES:\n"
            "- Fee structures for all programs\n"
            "- Admission eligibility and merit criteria\n"
            "- University rules, regulations, and policies\n"
            "- University history and general academic information\n\n"
            "CONSTRAINTS:\n"
            "- Never speculate. If not found, return NOT_FOUND.\n"
            "- Do NOT answer live news questions — those belong to the News Monitor.\n"
            "- Do NOT answer department-specific faculty questions — those belong to the Department Specialist.\n"
            "- Be DIRECT and CONCISE — answer the question immediately with specific facts/figures."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[RAGTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_homepage_agent() -> Agent:
    """Create the Homepage Monitor Agent for general university information."""
    return Agent(
        role="University General & Administrative Monitor",
        goal="Extract information about UOP officials, contact details, statutory bodies, committees, vision, mission, and general info from the website.",
        backstory=(
            "You are the live search engine for the UOP homepage and administrative pages.\n"
            "Find current officials (VC, Registrar), contact info, statutory bodies (Senate, Syndicate, etc.), vision/mission, and general announcements visible on the site.\n\n"
            "INSTRUCTIONS:\n"
            "- Call the university_of_peshawar_homepage_scraper tool first.\n"
            "- Report only information found on the homepage or administrative pages.\n"
            "- If the site is unavailable, provide a friendly fallback message.\n"
            "- Do NOT answer detailed fee or department questions.\n"
            "- Be DIRECT and CONCISE — answer the question immediately without lengthy introductions."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UoPHomepageScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_student_corner_agent() -> Agent:
    """Create the Student Corner Monitor Agent for student resources."""
    return Agent(
        role="University Student Corner Monitor",
        goal="Extract information about student resources, scholarships, incubation center, distance education, etc. from the student corner.",
        backstory=(
            "You are the live search engine for the UOP Student Corner.\n"
            "Find current information about scholarships, sports, distance education, career development, and other student services.\n\n"
            "INSTRUCTIONS:\n"
            "- Call the university_of_peshawar_student_corner_scraper tool first.\n"
            "- Report only information found in the student corner.\n"
            "- If the site is unavailable, provide a friendly fallback message.\n"
            "- Do NOT answer detailed fee or department questions.\n"
            "- Be DIRECT and CONCISE — answer the question immediately without lengthy introductions."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UoPStudentCornerScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_examination_agent() -> Agent:
    """Create the Examination Monitor Agent for examination resources."""
    return Agent(
        role="University Examination Specialist",
        goal="Extract information about examinations, results, date sheets, private exams, fee structure, verification, etc. from the examination sections.",
        backstory=(
            "You are the live search engine for the UOP Examination portal.\n"
            "Find current information about results, private examinations, ba/bsc/ma/msc exams, how to apply, date sheets, and verification.\n\n"
            "INSTRUCTIONS:\n"
            "- Call the university_of_peshawar_examination_scraper tool first.\n"
            "- Report only information found in the examination sections.\n"
            "- If the site is unavailable, provide a friendly fallback message.\n"
            "- Do NOT answer detailed fee or department questions unless they specifically relate to private exams or exam fees.\n"
            "- Be DIRECT and CONCISE — answer the question immediately without lengthy introductions."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UoPExaminationScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_academic_governance_agent() -> Agent:
    """Create the Academic Governance Monitor Agent for research and quality resources."""
    return Agent(
        role="University Academic Governance Specialist",
        goal="Extract information about research, innovation, quality enhancement, and advanced studies from the ORIC, QEC, and DAS sections.",
        backstory=(
            "You are the live search engine for the UOP Academic Governance sections.\n"
            "Find current information about ORIC, QEC, Directorate of Advanced Studies, research, and innovation.\n\n"
            "INSTRUCTIONS:\n"
            "- Call the university_of_peshawar_academic_governance_scraper tool first.\n"
            "- Report only information found in the academic governance sections.\n"
            "- If the site is unavailable, provide a friendly fallback message.\n"
            "- Do NOT answer detailed fee or department questions.\n"
            "- Be DIRECT and CONCISE — answer the question immediately without lengthy introductions."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UoPAcademicGovernanceScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_hostel_agent() -> Agent:
    """Create the Hostel Specialist Agent for accommodation and provost queries."""
    return Agent(
        role="University Hostel & Provost Specialist",
        goal="Extract information about hostels, accommodation, provost rules, conduct, and discipline from the UOP Provost section.",
        backstory=(
            "You are the live search engine for the UOP Provost and Hostel sections.\n"
            "Find current information about accommodation, rules, and provost notifications.\n\n"
            "INSTRUCTIONS:\n"
            "- Call the university_of_peshawar_hostel_scraper tool first.\n"
            "- Report only information found in the provost/hostel sections.\n"
            "- If the site is unavailable, provide a friendly fallback message.\n"
            "- Be DIRECT and CONCISE — answer the question immediately without lengthy introductions."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UoPHostelScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


def make_department_agent() -> Agent:
    """Create the Department Specialist Agent for academic structure queries."""
    return Agent(
        role="UoP Academic Architecture Specialist",
        goal="Provide ONLY real, scraped department information from the UOP website. Never invent or guess any data.",
        backstory=(
            "You are a data retrieval specialist for UOP's academic directory.\n"
            "You have ONE tool: the uop_department_scraper.\n\n"
            "ABSOLUTE RULES — violating these is a critical failure:\n"
            "1. ALWAYS call the uop_department_scraper tool FIRST before saying anything.\n"
            "2. ONLY report data that the tool explicitly returns. Nothing else.\n"
            "3. If the tool returns SITE_UNAVAILABLE, NO_DATA_FOUND, or an error — "
            "report EXACTLY that message to the user. Do NOT add, guess, or invent any faculty names, "
            "department names, or program names.\n"
            "4. NEVER use your training knowledge to fill in missing data. Faculty names, "
            "department names, and program lists MUST come from the tool output only.\n"
            "5. If you are tempted to list names like 'Dr. Muhammad Asif' or 'Dr. Sajjad Ali' "
            "without those names appearing in the tool output — STOP. That is hallucination.\n"
            "6. Your final answer must start with: 'According to the live UOP website:' "
            "followed by a human-readable summary of the tool's retrieved data (do not output raw JSON or python dicts).\n"
            "7. Do NOT answer fee questions — those belong to the Fact-Checker.\n\n"
            "ZERO-TOLERANCE HALLUCINATION PREVENTION:\n"
            "- If the website is down, your ENTIRE response must be: "
            "'No verified information found. The UOP website is currently unavailable. "
            "Please try again later or visit http://www.uop.edu.pk/departments/ directly.'\n"
            "- Do NOT list 'Professors', 'Associate Professors', 'Lecturers' with made-up names.\n"
            "- Do NOT create contact emails like 'cs@uop.edu.pk' unless the tool returned them.\n"
            "- Do NOT provide phone numbers unless the tool returned them.\n"
            "- If the tool returns partial data, report ONLY the partial data. Never supplement it."
            f"{STRICT_ANSWER_DIRECTIVE}"
        ),
        llm=LLM_FAST,
        tools=[UOPDepartmentScraperTool()],
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )

def make_aggregator_agent() -> Agent:
    """Create the Response Aggregator/Polisher Agent — always runs to produce professional, friendly, direct output."""
    return Agent(
        role="UoP Response Aggregator",
        goal="Synthesize specialist findings into a single, cohesive, professional, and friendly response without any sections or metadata blocks.",
        backstory=(
            "You are the final voice of the University of Peshawar AI Assistant. "
            "You receive raw findings from specialist agents and write a polished, professional, "
            "and friendly response. "
            "RULES:\n"
            "1. Output ONLY the final polished answer directly — do NOT include section headers, metadata blocks, or bracketed labels (like '[Final Verified Answer]' or '[Verification Status]'). Show the answer directly.\n"
            "2. Use a friendly, professional, and welcoming tone — as if you are a helpful university staff member.\n"
            "3. Structure the answer with proper formatting: use bullet points, numbered lists, or short paragraphs where appropriate.\n"
            "4. If a specialist reported 'not applicable', 'no data found', or errors — do not mention the raw error. "
            "Instead, say something like: 'Unfortunately, this information is not available at the moment.'\n"
            "5. Never invent or hallucinate facts. Only use information the specialists provided.\n"
            "6. If the website was unavailable, gently mention that live website access is currently limited, so the information may be based on internal/cached records."
        ),
        llm=LLM_FAST,
        verbose=True,
        max_iter=1,
        allow_delegation=False,
    )


# ── Main Crew Builder ────────────────────────────────────────────────────────
class multi_agent:
    """
    Dynamically builds a collaborative multi-agent crew based on query intents.
    Always uses the Aggregator/Polisher agent to produce professional, friendly, direct responses.
      - Single intent  → 1 specialist + aggregator (direct output)
      - Multi intent   → N specialists (async parallel) + aggregator (sequential)
    """

    def crew(self, query: str) -> Crew:
        intents = classify_query(query)
        from datetime import datetime
        print(f"[{datetime.now()}] [COLLABORATION] Triggering specialists for: {[i.value for i in intents]}")

        GENTLE_FALLBACK = (
            "IMPORTANT: If the tool returns SITE_UNAVAILABLE, NO_DATA_FOUND, or any error — "
            "do NOT show the raw error text. Instead, write a short, warm, and helpful message "
            "like: 'I'm sorry, the University of Peshawar website seems to be temporarily unavailable "
            "right now. You can try visiting the relevant page directly, or ask me again in a few minutes.' "
            "Keep the tone friendly and apologetic."
        )

        dispatch_config = {
            IntentCategory.STUDENT_CORNER: {
                "factory": make_student_corner_agent,
                "desc": f"Search the UOP Student Corner for: {query}.\n{GENTLE_FALLBACK}",
                "expected": "Information from Student Corner."
            },
            IntentCategory.ACADEMIC_GOVERNANCE: {
                "factory": make_academic_governance_agent,
                "desc": f"Search the UOP Academic Governance sections for: {query}.\n{GENTLE_FALLBACK}",
                "expected": "Information from ORIC/QEC/DAS."
            },
            IntentCategory.HOSTEL: {
                "factory": make_hostel_agent,
                "desc": f"Search the UOP Provost/Hostel sections for: {query}.\n{GENTLE_FALLBACK}",
                "expected": "Information about hostels/provost."
            },
            IntentCategory.EXAMINATION: {
                "factory": make_examination_agent,
                "desc": f"Search the UOP Examination portal for: {query}.\n{GENTLE_FALLBACK}",
                "expected": "Information from Examination portal."
            },
            IntentCategory.NEWS: {
                "factory": make_news_agent,
                "desc": f"Find news/announcements related to: {query}.\n{GENTLE_FALLBACK}",
                "expected": "Latest news items."
            },
            IntentCategory.DEPARTMENT: {
                "factory": make_department_agent,
                "desc": f"Retrieve department/faculty info for: {query}.\n{GENTLE_FALLBACK}",
                "expected": "Structured department data."
            },
            IntentCategory.HOMEPAGE: {
                "factory": make_homepage_agent,
                "desc": f"Search UOP homepage for: {query}.\n{GENTLE_FALLBACK}",
                "expected": "General university/official info."
            },
            IntentCategory.FACTS: {
                "factory": make_researcher_agent,
                "desc": f"Search knowledge base for fees/rules about: {query}.",
                "expected": "Factual answers from documents."
            }
        }

        specialist_tasks = []
        specialist_agents = []
        is_multi_intent = len(intents) > 1

        for intent in intents:
            config = dispatch_config[intent]
            agent = config["factory"]()
            specialist_agents.append(agent)

            task = Task(
                description=config["desc"],
                expected_output=config["expected"],
                agent=agent,
                async_execution=is_multi_intent,
            )
            specialist_tasks.append(task)

        # Always run the Aggregator/Polisher LLM call at the end
        aggregator_agent = make_aggregator_agent()
        aggregation_task = Task(
            description=(
                f"Review and polish the findings from the specialist agents for: '{query}'.\n\n"
                "OUTPUT REQUIREMENTS:\n"
                "- Output ONLY the final polished response directly.\n"
                "- Do NOT use any section headers, metadata blocks, or bracketed labels (do NOT include '[Final Verified Answer]' or any of the 7 sections).\n"
                "- Ensure the tone is friendly, helpful, and professional."
            ),
            expected_output="A polished, professional, and friendly direct response with no section headers or metadata blocks.",
            agent=aggregator_agent,
            context=specialist_tasks
        )

        return Crew(
            agents=specialist_agents + [aggregator_agent],
            tasks=specialist_tasks + [aggregation_task],
            process=Process.sequential,
            verbose=True,
            memory=False,
            cache=False,
        )

    def fallback_crew(self, query: str) -> Crew:
        """
        Self-Healing: relies solely on the internal Knowledge Base (RAG) + Aggregator.
        Triggered when live website data is unavailable.
        """
        rag_agent = make_researcher_agent()
        aggregator = make_aggregator_agent()

        task_rag = Task(
            description=(
                f"The University website is currently unreachable. Search the internal knowledge base "
                f"(PDFs/Documents) to find information about: '{query}'.\n"
                f"Provide a direct, helpful answer. If nothing is found, say so clearly."
            ),
            expected_output="A direct answer from internal documents.",
            agent=rag_agent
        )

        task_agg = Task(
            description=(
                f"Synthesize the internal knowledge for the query '{query}' into a polished response.\n\n"
                "OUTPUT REQUIREMENTS:\n"
                "- Output ONLY the final answer directly.\n"
                "- Do NOT include any section headers, metadata, or bracketed labels.\n"
                "- Since the website is down, gently mention that the live website is currently unreachable and the info is from internal records."
            ),
            expected_output="A polished, professional, and friendly direct response based on internal documents, without any section headers.",
            agent=aggregator,
            context=[task_rag]
        )

        return Crew(
            agents=[rag_agent, aggregator],
            tasks=[task_rag, task_agg],
            process=Process.sequential,
            verbose=True
        )



"""
UoP Department Scraper Tool
Precision retrieval system for University of Peshawar department data.

BASE URL: http://www.uop.edu.pk/departments/

Supports:
  - Teaching Faculty  -> /departments/?q={Dept}&r=Teaching-Faculty
  - Academic Programs -> /departments/?q={Dept}&r=Academic-Programs
  - Publications      -> /departments/?q={Dept}&r=Publications
  - Graduates         -> /departments/?q={Dept}&r=Graduates
  - Gallery           -> /departments/gallery/?q={Dept}
  - General overview  -> /departments/?q={Dept}
  - Global hierarchy  -> /faculties/ (static HTML, primary dept-discovery source)
"""
import re
import time
import requests
from typing import Dict, List, Any, Optional, Type, Tuple
from datetime import datetime

from pydantic import BaseModel
from bs4 import BeautifulSoup
from crewai.tools import BaseTool

# Shared HTTP helper — avoids code duplication and uses the hardened version
# with Sec-Fetch headers, full retry/backoff, and metadata instrumentation.
from .utils import safe_get

# ── Constants ─────────────────────────────────────────────────────────────────
BASE_URL      = "http://www.uop.edu.pk/departments/"
FACULTIES_URL = "http://www.uop.edu.pk/faculties/"
GALLERY_BASE  = "http://www.uop.edu.pk/departments/gallery/"

# Sub-section slugs
SUBSECTIONS = {
    "faculty":      "Teaching-Faculty",
    "programs":     "Academic-Programs",
    "publications": "Publications",
    "graduates":    "Graduates",
}

# Error tokens
DATA_UNAVAILABLE     = "DATA_UNAVAILABLE: Unable to access live UoP department page at this time."
DEPARTMENT_NOT_FOUND = "DEPARTMENT_NOT_FOUND"
SECTION_NOT_AVAILABLE = "SECTION_NOT_AVAILABLE"




# ── HTML Cleaner ───────────────────────────────────────────────────────────────
def _clean_html(soup: BeautifulSoup) -> str:
    """
    Strip scripts, styles, nav, and boilerplate noise.
    Returns clean readable text (max ~1100 chars to avoid bloat).
    """
    for tag in soup(["script", "style", "noscript", "nav", "footer",
                     "header", "aside", "form", "meta", "link"]):
        tag.decompose()

    text = re.sub(r'\s+', ' ', soup.get_text(separator=" ")).strip()
    if len(text) > 1100:
        text = text[:1100] + "...(truncated)"
    return text


# ── URL Builder ────────────────────────────────────────────────────────────────
def _build_dept_slug(dept_name: str) -> str:
    """Convert full dept name to URL slug. e.g. 'Dept of CS' → 'Dept-of-CS'"""
    return dept_name.strip().replace(" ", "-")


def _build_section_url(dept_slug: str, intent: str) -> str:
    """
    Build the correct URL for a given intent.
    intent: 'faculty' | 'programs' | 'publications' | 'graduates' | 'gallery' | 'general'
    """
    if intent == "gallery":
        return f"{GALLERY_BASE}?q={dept_slug}"
    sub = SUBSECTIONS.get(intent)
    if sub:
        return f"{BASE_URL}?q={dept_slug}&r={sub}"
    return f"{BASE_URL}?q={dept_slug}"


# ── Intent Classifier ──────────────────────────────────────────────────────────
def _classify_intent(query: str) -> str:
    """
    Determine information type from user query.
    Returns one of: 'faculty' | 'programs' | 'publications' | 'graduates' | 'gallery' | 'general'
    """
    q = query.lower()

    if any(kw in q for kw in ["gallery", "image", "photo", "picture", "media"]):
        return "gallery"
    if any(kw in q for kw in ["publication", "research paper", "paper", "journal", "article"]):
        return "publications"
    if any(kw in q for kw in ["graduate", "alumni", "passed out", "graduates"]):
        return "graduates"
    if any(kw in q for kw in [
        "faculty", "professor", "teacher", "lecturer", "staff",
        "hod", "chairman", "head", "dr.", "instructor", "name"
    ]):
        return "faculty"
    if any(kw in q for kw in [
        "program", "course", "degree", "bs", "ms", "msc", "phd",
        "academic", "offer", "curriculum", "syllabus", "admission"
    ]):
        return "programs"

    return "general"


# ── Confidence Scorer ──────────────────────────────────────────────────────────
def _confidence_score(matched_dept: Optional[str], query: str, intent: str) -> int:
    """
    Dynamic confidence based on match quality.
      100 → exact dept name present in query
       85 → strong stem/keyword match
       70 → word-overlap match
       40 → fuzzy fallback match
        0 → no dept matched
    """
    if not matched_dept:
        return 0
    q = query.lower()
    dept_lower = matched_dept.lower()
    # Exact match
    if dept_lower in q or q in dept_lower:
        return 100
    # Strong keyword: every meaningful dept word found in query
    dept_words = set(re.findall(r"\b\w+\b", dept_lower)) - {
        "department", "of", "the", "institute", "college", "centre", "center"
    }
    query_words = set(re.findall(r"\b\w+\b", q))
    if dept_words and dept_words.issubset(query_words):
        return 85
    # Stem match: at least one 6-char stem hit
    for w in dept_words:
        if len(w) >= 4:
            if w[:6] in q:
                return 70
    # Fuzzy fallback
    return 40


# ── Static Faculties Page Scraper (dept discovery) ─────────────────────────────
def scrape_faculties_page() -> Dict[str, Any]:
    """
    Scrapes http://www.uop.edu.pk/faculties/ (fully static HTML).
    Used ONLY for department discovery and global hierarchy queries.

    Returns:
      {
        "Faculty of Arts and Humanities": {
            "dean_info": "...",
            "departments": ["Department of History", ...]
        },
        ...
      }
    """
    response = safe_get(FACULTIES_URL)
    if response is None:
        return {"error": DATA_UNAVAILABLE}

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        result: Dict[str, Dict] = {}

        for faculty_h3 in soup.find_all("h3"):
            faculty_name = faculty_h3.get_text(strip=True)
            if not faculty_name:
                continue
            if (
                "Faculty of" not in faculty_name
                and "Others" not in faculty_name
                and "Research" not in faculty_name
            ):
                continue

            faculty_data: Dict[str, Any] = {"dean_info": "", "departments": []}
            sibling = faculty_h3.find_next_sibling()
            while sibling and sibling.name != "h3":
                if sibling.name == "div":
                    text = re.sub(r'\s+', ' ', sibling.get_text(separator=" ")).strip()
                    if text and len(text) > 10:
                        faculty_data["dean_info"] = text
                    for a_tag in sibling.find_all("a"):
                        dept_text = a_tag.get_text(strip=True)
                        if dept_text and len(dept_text) > 5 and any(
                            kw in dept_text
                            for kw in ["Department", "Institute", "College", "Centre", "Center"]
                        ):
                            faculty_data["departments"].append(dept_text)
                elif sibling.name in ["ol", "ul"]:
                    for li in sibling.find_all("li"):
                        dname = li.get_text(strip=True)
                        if dname:
                            dname = re.sub(r"^\d+\.\s*", "", dname)
                            faculty_data["departments"].append(dname)
                elif sibling.name in ["p", "a"]:
                    dname = sibling.get_text(strip=True)
                    if dname and len(dname) > 5 and "Department" in dname:
                        faculty_data["departments"].append(dname)
                sibling = sibling.find_next_sibling()

            faculty_data["departments"] = list(dict.fromkeys(faculty_data["departments"]))
            result[faculty_name] = faculty_data

        return result
    except Exception as e:
        return {"error": f"Failed to parse faculties page: {str(e)}"}


# ── Gallery Extractor ──────────────────────────────────────────────────────────
def _extract_gallery(soup: BeautifulSoup, source_url: str) -> List[Dict[str, str]]:
    """
    Extract meaningful images from a gallery page.
    Filters out tiny icons, logos, and UI assets.
    Returns list of {url, caption, alt_text}.
    """
    images = []
    skip_patterns = re.compile(
        r'(logo|icon|bullet|banner|bg|background|sprite|flag|arrow|btn)',
        re.IGNORECASE
    )
    valid_ext = re.compile(r'\.(jpg|jpeg|png|webp)(\?.*)?$', re.IGNORECASE)

    for img in soup.find_all("img"):
        src = img.get("src", "").strip()
        if not src:
            continue
        # Skip non-image extensions
        if not valid_ext.search(src):
            continue
        # Skip UI asset patterns
        if skip_patterns.search(src):
            continue
        # Skip tiny declared images
        width = img.get("width", "")
        try:
            if width and int(width) < 100:
                continue
        except ValueError:
            pass

        # Resolve relative URL
        if src.startswith("http"):
            full_url = src
        elif src.startswith("/"):
            full_url = "http://www.uop.edu.pk" + src
        else:
            full_url = source_url.rstrip("/") + "/" + src

        caption = (
            img.get("title", "")
            or img.find_parent("figure", {"figcaption": True}) and
               img.find_parent("figure").find("figcaption", {}) and
               img.find_parent("figure").find("figcaption").get_text(strip=True)
            or ""
        )
        alt_text = img.get("alt", "")
        images.append({"url": full_url, "caption": caption, "alt_text": alt_text})

    return images


# ── Sub-section Content Extractor ─────────────────────────────────────────────
def _extract_section_content(soup: BeautifulSoup, intent: str, source_url: str) -> Any:
    """
    Extract content from a loaded department sub-section page.
    Returns either a string summary or a structured list/dict.
    """
    if intent == "gallery":
        return _extract_gallery(soup, source_url)

    # For AJAX-heavy pages (Teaching Faculty), try article.static-page first
    article = soup.find("article", class_="static-page")
    content_root = article if article else soup

    ignore = {
        "News", "Upcoming Events", "Quick Links", "Campus Location",
        "Contact Us", "Overview", "Teaching Faculty", "Academic Programs",
        "Publications", "Graduates", "Gallery"
    }

    items = []
    for tag in content_root.find_all(["h2", "h3", "h4", "li", "p"]):
        text = re.sub(r'\s+', ' ', tag.get_text(strip=True)).strip()
        if text and len(text) > 3 and text not in ignore:
            items.append(text)

    unique_items = list(dict.fromkeys(items))[:40]

    if not unique_items:
        # Try generic clean text as fallback
        clean = _clean_html(content_root)
        return clean if clean else SECTION_NOT_AVAILABLE

    return unique_items


# ── Fuzzy Department Matching ──────────────────────────────────────────────────
def fuzzy_match_department(query: str, all_depts: List[str]) -> Tuple[Optional[str], int]:
    """
    Match a user query to the best department name.
    Returns (matched_dept_or_None, score_tier: 100|85|70|40|0).
    """
    q = query.lower().strip()

    noise_words = {
        "faculty", "members", "member", "names", "name", "list", "professors",
        "professor", "teachers", "teacher", "lecturers", "lecturer", "staff",
        "hod", "chairman", "head", "dean", "director", "contact", "details",
        "information", "info", "about", "tell", "me", "give", "overview",
        "what", "is", "are", "who", "which", "where", "how", "many", "show",
        "gallery", "image", "photo", "picture", "publication", "graduate",
        "program", "course", "degree", "academic"
    }

    # 1. Exact / substring match → score 100
    for dept in all_depts:
        dl = dept.lower()
        if q in dl or dl in q:
            return dept, 100

    stop_words = {
        "department", "of", "the", "institute", "college", "centre", "center",
        "university", "peshawar", "uop"
    } | noise_words
    qwords = set(re.findall(r"\b\w+\b", q))
    subject_words = qwords - stop_words

    # 2. Scored stem-prefix matching → score 85
    stem_scores: Dict[str, int] = {}
    for dept in all_depts:
        dl = dept.lower()
        score = sum(
            1 for w in subject_words
            if len(w) >= 4 and w[:min(len(w), 6)] in dl
        )
        if score > 0:
            stem_scores[dept] = score

    if stem_scores:
        best = max(stem_scores, key=lambda d: stem_scores[d])
        vals = sorted(stem_scores.values(), reverse=True)
        if len(vals) == 1 or vals[0] > vals[1]:
            return best, 85
        # Tied — fall through to word overlap

    # 3. Word overlap → score 70
    best_match, best_score = None, 0
    for dept in all_depts:
        dwords = set(re.findall(r"\b\w+\b", dept.lower()))
        overlap = len(subject_words & dwords)
        if overlap > best_score:
            best_score, best_match = overlap, dept

    if best_score >= 1:
        return best_match, 70

    # 4. fuzzywuzzy fallback → score 40
    try:
        from fuzzywuzzy import process
        clean_q = " ".join(w for w in re.findall(r"\b\w+\b", q) if w not in noise_words)
        result = process.extractOne(clean_q, all_depts)
        if result and result[1] > 65:
            return result[0], 40
    except ImportError:
        pass

    return None, 0


# ── Input Models ───────────────────────────────────────────────────────────────
class FlexibleInput(BaseModel):
    """Tolerant input — accepts any extra fields."""
    query: Optional[str] = None

    class Config:
        extra = "allow"


class DepartmentScraperInput(FlexibleInput):
    """Legacy alias."""
    pass


# ── Main Tool ──────────────────────────────────────────────────────────────────
class UOPDepartmentScraperTool(BaseTool):
    """
    Precision retrieval tool for UoP department data.

    Returns structured JSON:
    {
      "department": str,
      "query_intent": str,
      "source_url": str,
      "extracted_data": str | list,
      "sub_section_used": str,
      "timestamp": str,
      "confidence_score": int (0-100)
    }
    """

    name: str = "uop_department_scraper"
    description: str = (
        "Retrieves structured, real-time academic data from the University of Peshawar "
        "departments website. Supports: Teaching Faculty, Academic Programs, Publications, "
        "Graduates, Gallery, and general department info. "
        "Use for any question about UoP departments, programs, faculty members, or academic structure."
    )
    args_schema: Type[BaseModel] = FlexibleInput

    # ── Internal helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _extract_query(args: tuple, kwargs: dict) -> Optional[str]:
        if args and isinstance(args[0], str):
            return args[0]
        if "query" in kwargs:
            return kwargs["query"]
        for val in kwargs.values():
            if isinstance(val, str):
                return val
        return None

    @staticmethod
    def _result(
        dept: str,
        intent: str,
        url: str,
        data: Any,
        sub_section: str,
        confidence: int,
    ) -> Dict[str, Any]:
        return {
            "department": dept,
            "query_intent": intent,
            "source_url": url,
            "extracted_data": data,
            "sub_section_used": sub_section,
            "timestamp": datetime.now().isoformat(),
            "confidence_score": confidence,
        }

    # ── _run ───────────────────────────────────────────────────────────────────
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        query = self._extract_query(args, kwargs)
        if not query:
            return {"error": "No query provided to UOPDepartmentScraperTool."}

        now = datetime.now()
        print(f"[{now}] >>> DEPT SCRAPER START <<< Query: {query}")
        q = query.lower()

        # ── Step 1: Discover departments via /faculties/ (static HTML) ─────────
        print(f"[{now}] Discovering departments from /faculties/ page...")
        faculties_data = scrape_faculties_page()
        if "error" in faculties_data:
            return self._result(
                dept="",
                intent="error",
                url=FACULTIES_URL,
                data=DATA_UNAVAILABLE,
                sub_section="none",
                confidence=0,
            )

        all_depts: List[str] = []
        dept_to_faculty: Dict[str, str] = {}
        for fac_name, fdata in faculties_data.items():
            for dept in fdata.get("departments", []):
                all_depts.append(dept)
                dept_to_faculty[dept] = fac_name

        # ── Step 2: Global / hierarchy queries ────────────────────────────────
        global_kw = ["all", "list", "faculties", "departments", "every",
                     "hierarchy", "structure", "how many"]
        is_global = (
            any(kw in q for kw in global_kw)
            and not any(kw in q for kw in ["faculty of", "department of", "institute of"])
        )
        if "faculty of" in q and not any(kw in q for kw in ["department of", "institute of"]):
            is_global = True  # "Faculty of X" → show that specific faculty

        if is_global:
            print(f"[{now}] Global/hierarchy query detected.")

            # Specific faculty?
            if "faculty of" in q:
                for f_name, fdata in faculties_data.items():
                    if f_name.lower() in q:
                        return self._result(
                            dept=f_name,
                            intent="faculty_hierarchy",
                            url=FACULTIES_URL,
                            data={
                                "dean_info": fdata.get("dean_info", ""),
                                "departments": fdata.get("departments", [])
                            },
                            sub_section="faculties_page",
                            confidence=100,
                        )

            summary = {
                fn: {"dean": fd.get("dean_info", ""), "departments": fd.get("departments", [])}
                for fn, fd in faculties_data.items()
            }
            return self._result(
                dept="All Faculties",
                intent="global_hierarchy",
                url=FACULTIES_URL,
                data={
                    "total_faculties": len(summary),
                    "total_departments": len(all_depts),
                    "faculties": summary,
                },
                sub_section="faculties_page",
                confidence=100,
            )

        # ── Step 3: Identify target department ───────────────────────────────
        print(f"[{now}] Identifying target department...")

        _noise_trail = re.compile(
            r"\s+(faculty|members?|names?|professors?|lecturers?|teachers?|staff|"
            r"hod|chairman|head|dean|director|contact|details|information|info|"
            r"about|overview|list|all|show|gallery|images?|photos?|publications?|"
            r"graduates?|programs?|courses?).*$",
            re.IGNORECASE,
        )

        matched_dept: Optional[str] = None
        confidence: int = 0

        # Try explicit "Department of X" extraction first
        explicit = re.search(
            r"(?:department|institute|college|centre|center)\s+of\s+([^,?.\n!]+)",
            query,
            re.IGNORECASE,
        )
        if explicit:
            raw = explicit.group(1).strip()
            clean = _noise_trail.sub("", raw).strip()
            print(f"[{now}] Explicit dept extracted: '{raw}' → '{clean}'")
            matched_dept, confidence = fuzzy_match_department(clean, all_depts)

        if not matched_dept:
            matched_dept, confidence = fuzzy_match_department(query, all_depts)

        if not matched_dept:
            print(f"[{now}] Department not found for query: '{query}'")
            return self._result(
                dept=DEPARTMENT_NOT_FOUND,
                intent="unknown",
                url=BASE_URL,
                data=(
                    f"Could not identify a department from: '{query}'. "
                    f"Sample available departments: {', '.join(all_depts[:8])}..."
                ),
                sub_section="none",
                confidence=0,
            )

        print(f"[{now}] Matched: '{matched_dept}' (confidence={confidence})")

        # ── Step 4: Classify intent ───────────────────────────────────────────
        intent = _classify_intent(query)
        print(f"[{now}] Intent: {intent}")

        # ── Step 5: Decision gate — skip fetch for very low confidence ────────
        if confidence == 0:
            return self._result(
                dept=matched_dept,
                intent=intent,
                url=BASE_URL,
                data=DEPARTMENT_NOT_FOUND,
                sub_section="none",
                confidence=0,
            )

        # ── Step 6: Build URL and fetch section ───────────────────────────────
        dept_slug = _build_dept_slug(matched_dept)
        source_url = _build_section_url(dept_slug, intent)
        sub_section_label = (
            SUBSECTIONS.get(intent, "main")
            if intent != "gallery"
            else "Gallery"
        )
        print(f"[{now}] Fetching: {source_url}")

        response = safe_get(source_url)
        if response is None:
            return self._result(
                dept=matched_dept,
                intent=intent,
                url=source_url,
                data=DATA_UNAVAILABLE,
                sub_section=sub_section_label,
                confidence=confidence,
            )

        soup = BeautifulSoup(response.text, "html.parser")
        extracted = _extract_section_content(soup, intent, source_url)

        # If section came back empty / unavailable, fall back to main page
        if extracted in (SECTION_NOT_AVAILABLE, [], ""):
            if intent != "general":
                print(f"[{now}] Section empty, falling back to main dept page...")
                main_url = f"{BASE_URL}?q={dept_slug}"
                main_resp = safe_get(main_url)
                if main_resp:
                    main_soup = BeautifulSoup(main_resp.text, "html.parser")
                    extracted = _extract_section_content(main_soup, "general", main_url)
                    source_url = main_url
                    sub_section_label = "main_page_fallback"
                    # Downgrade confidence slightly since we fell back
                    confidence = max(confidence - 10, 10)

        # ── Step 7: Append parent faculty context for specific dept queries ────
        parent_faculty = dept_to_faculty.get(matched_dept, "")
        faculty_info = faculties_data.get(parent_faculty, {})
        dean_info = faculty_info.get("dean_info", "")

        print(f"[{now}] >>> DEPT SCRAPER END <<< (Success)")
        return self._result(
            dept=matched_dept,
            intent=intent,
            url=source_url,
            data={
                "content": extracted,
                "parent_faculty": parent_faculty,
                "faculty_dean_info": dean_info,
            } if intent not in ("gallery",) else {
                "images": extracted,
                "parent_faculty": parent_faculty,
            },
            sub_section=sub_section_label,
            confidence=confidence,
        )

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """Async — delegates to sync."""
        return self._run(*args, **kwargs)

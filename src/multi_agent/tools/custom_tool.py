"""
UoP Homepage Scraper Tool
Scrapes general information from the University of Peshawar homepage.
"""
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from typing import Dict, Any, List, Set, Optional, Type
import re
from datetime import datetime

from .utils import (
    safe_get,
    safe_text,
    safe_attr,
    build_absolute_url,
    SITE_UNAVAILABLE_MSG,
)


class HomepageScraperInput(BaseModel):
    """Input schema for UoPHomepageScraperTool."""
    query: str = Field(..., description="The query string to search on the UoP homepage.")


class UoPHomepageScraperTool(BaseTool):
    """
    Retrieves query-related information from the University of Peshawar homepage.
    Scans content from leadership sections, navigation, news sidebar, events, and contact info.
    """

    name: str = "university_of_peshawar_homepage_scraper"
    description: str = (
        "Scrapes the UOP homepage, Administrative Offices, About sections, and Statutory Bodies. "
        "Use for: official names, contact details, general announcements, vision/mission, university genesis, "
        "and statutory committees (Senate, Syndicate, Academic Council, etc.). "
        "Returns relevant text snippets matching the query."
    )
    args_schema: Type[BaseModel] = HomepageScraperInput

    def _run(self, query: str) -> Any:
        if not query or not isinstance(query, str):
            return {"error": True, "message": "A valid query string is required."}

        # Extract keywords from query
        keywords: Set[str] = {
            word.lower()
            for word in re.findall(r"\b\w+\b", query)
            if len(word) > 2
        }
        if not keywords:
            return {"error": True, "message": "Query must contain meaningful keywords."}

        # Priority terms for leadership queries
        priority_terms = {"vc", "vice chancellor", "registrar", "chancellor", "pro vice"}

        def is_relevant(content: str) -> bool:
            content_lower = content.lower()
            # If query is about leadership, prioritize those sections
            if any(term in content_lower for term in priority_terms):
                if any(kw in query.lower() for kw in ["vc", "vice", "registrar", "name", "who", "chancellor", "official"]):
                    return True
            
            # Stricter general relevance check to extract ONLY query-related information
            target_keywords = keywords.copy()
            if "vc" in target_keywords or "vice" in target_keywords:
                target_keywords.update(["vice", "chancellor"])
            
            words = set(re.findall(r"\b\w+\b", content_lower))
            match_count = sum(1 for kw in target_keywords if kw in words)
            
            if len(target_keywords) == 1:
                return match_count >= 1
            if len(target_keywords) == 2:
                return match_count >= 2  # Endorse stricter matching for 2-word queries
            return (match_count / len(target_keywords)) >= 0.6  # 60% of query keywords must match

        # Build URL list based on query intent
        base_url = "http://www.uop.edu.pk/"
        urls_to_check: List[str] = [base_url]

        admin_offices = {
            "vcoffice": "http://www.uop.edu.pk/vcoffice/",
            "vice chancellor": "http://www.uop.edu.pk/vcoffice/",
            "vc": "http://www.uop.edu.pk/vcoffice/",
            "examinations": "http://uop.edu.pk/examinations/",
            "controller": "http://uop.edu.pk/examinations/",
            "cits": "http://uop.edu.pk/cits/",
            "it service": "http://uop.edu.pk/cits/",
            "treasurer": "http://uop.edu.pk/Treasurer/",
            "qec": "http://uop.edu.pk/qec/",
            "quality enhancement": "http://uop.edu.pk/qec/",
            "admissions": "http://uop.edu.pk/admissions/",
            "das": "http://www.uop.edu.pk/das/",
            "advanced studies": "http://www.uop.edu.pk/das/",
            "pnd": "http://uop.edu.pk/pnd/",
            "planning": "http://uop.edu.pk/pnd/",
            "provost": "http://www.uop.edu.pk/provost/",
            "sports": "http://uop.edu.pk/sports/",
            "chrcd": "http://uop.edu.pk/chrcd/",
            "establishment": "http://uop.edu.pk/establishment/",
            "meetings": "http://www.uop.edu.pk/meetings/",
            "academic": "http://www.uop.edu.pk/academic/",
            "fro": "http://www.uop.edu.pk/fro/",
            "registrar": "http://www.uop.edu.pk/administration/?q=registrar-office",
            "pro vice": "http://www.uop.edu.pk/administration/?q=pro-vice-chancellor-office",
            "about": "http://www.uop.edu.pk/about/",
            "genesis": "http://www.uop.edu.pk/about/?q=genesis",
            "history": "http://www.uop.edu.pk/about/?q=genesis",
            "vision": "http://www.uop.edu.pk/about/?q=vision-mission",
            "mission": "http://www.uop.edu.pk/about/?q=vision-mission",
            "statutory body": "http://www.uop.edu.pk/administration/?q=statutory-body",
            "senate": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Senate",
            "syndicate": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Syndicate",
            "academic council": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Academic-Council",
            "board of studies": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Boards-of-Studies",
            "advance studies": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Advance-Studies-and-Research-Board",
            "research board": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Advance-Studies-and-Research-Board",
            "finance and planning": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Finance-and-Planning-Committee",
            "finance committee": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Finance-and-Planning-Committee",
            "affiliation committee": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Affiliation-Committee",
            "discipline committee": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Discipline-Committee",
            "selection board": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Selection-Board",
            "anomaly committee": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Anomaly-Committee",
            "board of faculties": "http://www.uop.edu.pk/administration/?q=statutory-body&r=The-Board-of-Faculties",
            "examination discipline": "http://www.uop.edu.pk/administration/?q=statutory-body&r=Examination-Discipline-Committee",
            "examination appellate": "http://www.uop.edu.pk/administration/?q=statutory-body&r=Examination-Appellate-Committee",
            "administrative offices": "http://www.uop.edu.pk/administration/?q=administrative-offices",
        }

        query_lower = query.lower()
        leadership_terms = {"vc", "vice chancellor", "registrar", "chancellor", "pro vice"}
        
        # Check against mapped admin offices and add matching URLs
        for term, url in admin_offices.items():
            # pad term with spaces for exact word match if it's too short, or just use 'in' 
            # safe matching for exactly the words user queried
            if term in query_lower:
                if url not in urls_to_check:
                    urls_to_check.append(url)

        found_snippets: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()

        for current_url in urls_to_check:
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            response = safe_get(current_url)
            if response is None:
                print(f"[{datetime.now()}] Skipping {current_url} - unreachable.")
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            # Exclude standard anchor list tags initially to avoid capturing pure navigation
            tags_to_scan = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]

            def clean_whitespace(val: str) -> str:
                # Remove tabs, newlines, zero-width spaces, and multiple spaces
                return re.sub(r'\s+', ' ', val).strip()

            for element in soup.find_all(tags_to_scan):
                raw_text = safe_text(element)
                text = clean_whitespace(raw_text)
                
                # Filter out very short noises / empty text
                if len(text) < 15:
                    continue
                    
                # Extract only query-related information
                if not is_relevant(text):
                    continue

                data_point: Dict[str, Any] = {
                    "text": text,
                    "source_url": current_url,
                }

                # Extract link if element is or contains an anchor
                href = safe_attr(element if element.name == "a" else element.find("a"), "href")
                if href:
                    link = build_absolute_url(href, base_url)
                    data_point["link"] = link
                    # Queue linked pages for leadership queries
                    if any(term in text.lower() for term in leadership_terms):
                        if link not in visited_urls and "uop.edu.pk" in link:
                            urls_to_check.append(link)

                # Add sibling context to form complete thoughts, maintaining cleanliness
                context_parts = [text]
                next_node = element.next_sibling
                captured = 0
                while next_node and captured < 1:  # Only capture 1 sibling to stay highly relevant
                    sib_text = clean_whitespace(safe_text(next_node))
                    # Prevent polluting with very short unhelpful context
                    if len(sib_text) > 10:
                        context_parts.append(sib_text)
                        captured += 1
                    next_node = next_node.next_sibling

                final_text = " ... ".join(context_parts)
                data_point["text"] = final_text

                # Clean + Remove Duplicates
                text_lower = final_text.lower()
                is_duplicate = False
                for existing in found_snippets:
                    exist_lower = existing["text"].lower()
                    
                    # If this explicitly matches or is a subset of an already extracted snippet
                    if text_lower in exist_lower:
                        is_duplicate = True
                        break
                    # If the newly found snippet contains the old one natively, prefer the richer context
                    elif exist_lower in text_lower:
                        existing["text"] = final_text
                        if "link" in data_point:
                            existing["link"] = data_point["link"]
                        is_duplicate = True
                        break

                if not is_duplicate:
                    found_snippets.append(data_point)
                    if len(found_snippets) >= 20:
                        break

            if len(found_snippets) >= 20:
                break

        # Check if we successfully accessed the site
        if base_url not in visited_urls:
            return SITE_UNAVAILABLE_MSG

        if not found_snippets:
            return {
                "error": False,
                "message": "No information related to your query was found on the homepage.",
                "query": query,
            }

        print(f"[{datetime.now()}] Homepage scraper found {len(found_snippets)} relevant snippets.")
        return {"error": False, "data": {"snippets": found_snippets, "query": query}}


class StudentCornerScraperInput(BaseModel):
    """Input schema for UoPStudentCornerScraperTool."""
    query: str = Field(..., description="The query string to search in the Student Corner sections.")


class UoPStudentCornerScraperTool(BaseTool):
    """
    Retrieves query-related information from the University of Peshawar Student Corner and related student sections.
    """

    name: str = "university_of_peshawar_student_corner_scraper"
    description: str = (
        "Scrapes the UOP Student Corner sections (e.g., Scholarships, Incubation Centre, Distance Education, Sports, Bara Gali, Career Development). "
        "Use ONLY for student-specific queries matching these sections. "
        "Returns relevant text snippets matching the query."
    )
    args_schema: Type[BaseModel] = StudentCornerScraperInput

    def _run(self, query: str) -> Any:
        if not query or not isinstance(query, str):
            return {"error": True, "message": "A valid query string is required."}

        # Extract keywords from query
        keywords: Set[str] = {
            word.lower()
            for word in re.findall(r"\b\w+\b", query)
            if len(word) > 2
        }
        if not keywords:
            return {"error": True, "message": "Query must contain meaningful keywords."}

        def is_relevant(content: str) -> bool:
            content_lower = content.lower()
            
            # Stricter general relevance check to extract ONLY query-related information
            target_keywords = keywords.copy()
            words = set(re.findall(r"\b\w+\b", content_lower))
            match_count = sum(1 for kw in target_keywords if kw in words)
            
            if len(target_keywords) == 1:
                return match_count >= 1
            if len(target_keywords) == 2:
                return match_count >= 2  # Endorse stricter matching for 2-word queries
            return (match_count / len(target_keywords)) >= 0.6  # 60% of query keywords must match

        # Build URL list based on query intent
        base_url = "http://www.uop.edu.pk/"
        urls_to_check: List[str] = []

        student_offices = {
            "bic": "https://bic.uop.edu.pk/",
            "business incubation": "https://bic.uop.edu.pk/",
            "incubation": "https://bic.uop.edu.pk/",
            "celebrations": "http://www.uop.edu.pk/celebrations/",
            "75 years": "http://www.uop.edu.pk/celebrations/",
            "scholarships": "http://www.uop.edu.pk/admissions/?q=Scholarships",
            "aid": "http://www.uop.edu.pk/admissions/?q=Scholarships",
            "private examinations": "http://www.uop.edu.pk/examinations/?q=Private-Examinations",
            "sports": "http://www.uop.edu.pk/sports/",
            "distance education": "http://www.uop.edu.pk/dde/",
            "dde": "http://www.uop.edu.pk/dde/",
            "bara gali": "http://www.uop.edu.pk/baragali/",
            "china study": "http://www.uop.edu.pk/csc/",
            "csc": "http://www.uop.edu.pk/csc/",
            "fata": "http://www.uop.edu.pk/cfs/",
            "cfs": "http://www.uop.edu.pk/cfs/",
            "community service": "http://www.uop.edu.pk/csp/",
            "csp": "http://www.uop.edu.pk/csp/",
            "digital library": "https://www.digitallibrary.edu.pk/peshuni.html",
            "career development": "http://cdc.uop.edu.pk/",
            "cdc": "http://cdc.uop.edu.pk/",
            "environment": "http://www.uop.edu.pk/envsoc/",
            "envsoc": "http://www.uop.edu.pk/envsoc/",
            "harassment": "http://uop.edu.pk/contacts/harassment-act.php",
            "anti-sexual": "http://uop.edu.pk/contacts/harassment-act.php",
        }

        query_lower = query.lower()
        
        for term, url in student_offices.items():
            if term in query_lower:
                if url not in urls_to_check:
                    urls_to_check.append(url)

        if not urls_to_check:
            return {
                "error": False,
                "message": "Query did not match any specific Student Corner sections. Try being more specific about the student resource you need.",
                "query": query,
            }

        found_snippets: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()

        for current_url in urls_to_check:
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            response = safe_get(current_url)
            if response is None:
                print(f"[{datetime.now()}] Skipping {current_url} - unreachable.")
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            tags_to_scan = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]

            def clean_whitespace(val: str) -> str:
                return re.sub(r'\s+', ' ', val).strip()

            for element in soup.find_all(tags_to_scan):
                raw_text = safe_text(element)
                text = clean_whitespace(raw_text)
                
                if len(text) < 15:
                    continue
                    
                if not is_relevant(text):
                    continue

                data_point: Dict[str, Any] = {
                    "text": text,
                    "source_url": current_url,
                }

                href = safe_attr(element if element.name == "a" else element.find("a"), "href")
                if href:
                    link = build_absolute_url(href, base_url)
                    data_point["link"] = link

                context_parts = [text]
                next_node = element.next_sibling
                captured = 0
                while next_node and captured < 1:
                    sib_text = clean_whitespace(safe_text(next_node))
                    if len(sib_text) > 10:
                        context_parts.append(sib_text)
                        captured += 1
                    next_node = next_node.next_sibling

                final_text = " ... ".join(context_parts)
                data_point["text"] = final_text

                text_lower = final_text.lower()
                is_duplicate = False
                for existing in found_snippets:
                    exist_lower = existing["text"].lower()
                    
                    if text_lower in exist_lower:
                        is_duplicate = True
                        break
                    elif exist_lower in text_lower:
                        existing["text"] = final_text
                        if "link" in data_point:
                            existing["link"] = data_point["link"]
                        is_duplicate = True
                        break

                if not is_duplicate:
                    found_snippets.append(data_point)
                    if len(found_snippets) >= 20:
                        break

            if len(found_snippets) >= 20:
                break

        if not found_snippets:
            return {
                "error": False,
                "message": "No information related to your query was found in the Student Corner sections.",
                "query": query,
            }

        print(f"[{datetime.now()}] Student Corner scraper found {len(found_snippets)} relevant snippets.")
        return {"error": False, "data": {"snippets": found_snippets, "query": query}}


class ExaminationScraperInput(BaseModel):
    """Input schema for UoPExaminationScraperTool."""
    query: str = Field(..., description="The query string to search in the Examination sections.")


class UoPExaminationScraperTool(BaseTool):
    """
    Retrieves query-related information from the University of Peshawar Examination sections.
    """

    name: str = "university_of_peshawar_examination_scraper"
    description: str = (
        "Scrapes the UOP Examination sections (e.g., Results, Private Examinations, Date Sheets, Fee Structure, Verification, Downloads). "
        "Use ONLY for examination-specific queries matching these sections. "
        "Returns relevant text snippets matching the query."
    )
    args_schema: Type[BaseModel] = ExaminationScraperInput

    def _run(self, query: str) -> Any:
        if not query or not isinstance(query, str):
            return {"error": True, "message": "A valid query string is required."}

        # Extract keywords from query
        keywords: Set[str] = {
            word.lower()
            for word in re.findall(r"\b\w+\b", query)
            if len(word) > 2
        }
        if not keywords:
            return {"error": True, "message": "Query must contain meaningful keywords."}

        def is_relevant(content: str) -> bool:
            content_lower = content.lower()
            
            target_keywords = keywords.copy()
            words = set(re.findall(r"\b\w+\b", content_lower))
            match_count = sum(1 for kw in target_keywords if kw in words)
            
            if len(target_keywords) == 1:
                return match_count >= 1
            if len(target_keywords) == 2:
                return match_count >= 2
            return (match_count / len(target_keywords)) >= 0.6

        base_url = "http://www.uop.edu.pk/"
        urls_to_check: List[str] = []

        examination_offices = {
            "examination": "http://www.uop.edu.pk/examinations/",
            "controller message": "http://www.uop.edu.pk/examinations/?q=Overview&r=Controller-Message",
            "online verification": "http://www.uop.edu.pk/examinations/?q=Overview&r=Online-Verification-of-Documents",
            "verification": "http://www.uop.edu.pk/examinations/?q=Overview&r=Online-Verification-of-Documents",
            "result": "http://www.uop.edu.pk/examinations/?q=Results",
            "private examination": "http://www.uop.edu.pk/examinations/?q=Private-Examinations",
            "private": "http://www.uop.edu.pk/examinations/?q=Private-Examinations",
            "ba": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=BA-and-BSc",
            "bsc": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=BA-and-BSc",
            "ma": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=MA-and-MSc",
            "msc": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=MA-and-MSc",
            "apply": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=How-to-Apply",
            "how to apply": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=How-to-Apply",
            "fee": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=Fee-Structure",
            "fee structure": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=Fee-Structure",
            "date sheet": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=Date-Sheet",
            "datesheet": "http://www.uop.edu.pk/examinations/?q=Private-Examinations&r=Date-Sheet",
            "download": "http://www.uop.edu.pk/examinations/?q=Downloads",
        }

        query_lower = query.lower()
        
        for term, url in examination_offices.items():
            if term in query_lower:
                if url not in urls_to_check:
                    urls_to_check.append(url)

        if not urls_to_check:
            # Fallback to main examinations page if no specific section is matched
            urls_to_check.append("http://www.uop.edu.pk/examinations/")

        found_snippets: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()

        for current_url in urls_to_check:
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            response = safe_get(current_url)
            if response is None:
                print(f"[{datetime.now()}] Skipping {current_url} - unreachable.")
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            tags_to_scan = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]

            def clean_whitespace(val: str) -> str:
                return re.sub(r'\s+', ' ', val).strip()

            for element in soup.find_all(tags_to_scan):
                raw_text = safe_text(element)
                text = clean_whitespace(raw_text)
                
                if len(text) < 15:
                    continue
                    
                if not is_relevant(text):
                    continue

                data_point: Dict[str, Any] = {
                    "text": text,
                    "source_url": current_url,
                }

                href = safe_attr(element if element.name == "a" else element.find("a"), "href")
                if href:
                    link = build_absolute_url(href, base_url)
                    data_point["link"] = link

                context_parts = [text]
                next_node = element.next_sibling
                captured = 0
                while next_node and captured < 1:
                    sib_text = clean_whitespace(safe_text(next_node))
                    if len(sib_text) > 10:
                        context_parts.append(sib_text)
                        captured += 1
                    next_node = next_node.next_sibling

                final_text = " ... ".join(context_parts)
                data_point["text"] = final_text

                text_lower = final_text.lower()
                is_duplicate = False
                for existing in found_snippets:
                    exist_lower = existing["text"].lower()
                    
                    if text_lower in exist_lower:
                        is_duplicate = True
                        break
                    elif exist_lower in text_lower:
                        existing["text"] = final_text
                        if "link" in data_point:
                            existing["link"] = data_point["link"]
                        is_duplicate = True
                        break

                if not is_duplicate:
                    found_snippets.append(data_point)
                    if len(found_snippets) >= 20:
                        break

            if len(found_snippets) >= 20:
                break

        if not found_snippets:
            return {
                "error": False,
                "message": "No information related to your query was found in the Examination sections.",
                "query": query,
            }

        print(f"[{datetime.now()}] Examination scraper found {len(found_snippets)} relevant snippets.")
        return {"error": False, "data": {"snippets": found_snippets, "query": query}}


class AcademicGovernanceScraperInput(BaseModel):
    """Input schema for UoPAcademicGovernanceScraperTool."""
    query: str = Field(..., description="The query string to search in the Academic Governance sections.")


class UoPAcademicGovernanceScraperTool(BaseTool):
    """
    Retrieves query-related information from the University of Peshawar Academic Governance sections.
    """

    name: str = "university_of_peshawar_academic_governance_scraper"
    description: str = (
        "Scrapes the UOP Academic Governance sections (e.g., ORIC, QEC, Advanced Studies & Research). "
        "Use ONLY for queries relating to research, quality enhancement, advanced studies, innovation, and commercialization. "
        "Automatically handles sub-sections. Returns relevant text snippets matching the query."
    )
    args_schema: Type[BaseModel] = AcademicGovernanceScraperInput

    def _run(self, query: str) -> Any:
        if not query or not isinstance(query, str):
            return {"error": True, "message": "A valid query string is required."}

        # Extract keywords from query
        keywords: Set[str] = {
            word.lower()
            for word in re.findall(r"\b\w+\b", query)
            if len(word) > 2
        }
        if not keywords:
            return {"error": True, "message": "Query must contain meaningful keywords."}

        def is_relevant(content: str) -> bool:
            content_lower = content.lower()
            target_keywords = keywords.copy()
            words = set(re.findall(r"\b\w+\b", content_lower))
            match_count = sum(1 for kw in target_keywords if kw in words)
            
            if len(target_keywords) == 1:
                return match_count >= 1
            if len(target_keywords) == 2:
                return match_count >= 2
            return (match_count / len(target_keywords)) >= 0.6

        base_url = "http://www.uop.edu.pk/"
        urls_to_check: List[str] = []

        governance_offices = {
            "oric": "http://www.uop.edu.pk/oric/",
            "research": "http://www.uop.edu.pk/oric/",
            "innovation": "http://www.uop.edu.pk/oric/",
            "commercialization": "http://www.uop.edu.pk/oric/",
            "qec": "http://www.uop.edu.pk/qec/",
            "quality": "http://www.uop.edu.pk/qec/",
            "quality enhancement": "http://www.uop.edu.pk/qec/",
            "das": "http://www.uop.edu.pk/das/",
            "advanced studies": "http://www.uop.edu.pk/das/",
        }

        query_lower = query.lower()
        
        for term, url in governance_offices.items():
            if term in query_lower:
                if url not in urls_to_check:
                    urls_to_check.append(url)

        if not urls_to_check:
            # Fallback to all three main pages if no specific section is matched
            urls_to_check.extend([
                "http://www.uop.edu.pk/oric/",
                "http://www.uop.edu.pk/qec/",
                "http://www.uop.edu.pk/das/"
            ])

        found_snippets: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()

        for current_url in urls_to_check:
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            response = safe_get(current_url)
            if response is None:
                print(f"[{datetime.now()}] Skipping {current_url} - unreachable.")
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            tags_to_scan = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]

            def clean_whitespace(val: str) -> str:
                return re.sub(r'\s+', ' ', val).strip()

            for element in soup.find_all(tags_to_scan):
                raw_text = safe_text(element)
                text = clean_whitespace(raw_text)
                
                if len(text) < 15:
                    continue

                is_rel = is_relevant(text)
                data_point: Dict[str, Any] = {}

                href = safe_attr(element if element.name == "a" else element.find("a"), "href")
                if href:
                    link = build_absolute_url(href, base_url)
                    # Automatically queue sub-links to handle sub-sections
                    if link not in visited_urls and "uop.edu.pk" in link and any(p in link for p in ["oric", "qec", "das"]):
                        urls_to_check.append(link)
                    
                    if is_rel:
                        data_point = {"text": text, "source_url": current_url, "link": link}
                elif is_rel:
                    data_point = {"text": text, "source_url": current_url}
                
                if not is_rel:
                    continue

                context_parts = [text]
                next_node = element.next_sibling
                captured = 0
                while next_node and captured < 1:
                    sib_text = clean_whitespace(safe_text(next_node))
                    if len(sib_text) > 10:
                        context_parts.append(sib_text)
                        captured += 1
                    next_node = next_node.next_sibling

                final_text = " ... ".join(context_parts)
                data_point["text"] = final_text

                text_lower = final_text.lower()
                is_duplicate = False
                for existing in found_snippets:
                    exist_lower = existing["text"].lower()
                    
                    if text_lower in exist_lower:
                        is_duplicate = True
                        break
                    elif exist_lower in text_lower:
                        existing["text"] = final_text
                        if "link" in data_point:
                            existing["link"] = data_point["link"]
                        is_duplicate = True
                        break

                if not is_duplicate:
                    found_snippets.append(data_point)
                    if len(found_snippets) >= 20:
                        break

            if len(found_snippets) >= 20:
                break

        if not found_snippets:
            return {
                "error": False,
                "message": "No information related to your query was found in the Academic Governance sections.",
                "query": query,
            }

        print(f"[{datetime.now()}] Academic Governance scraper found {len(found_snippets)} relevant snippets.")
        return {"error": False, "data": {"snippets": found_snippets, "query": query}}


class HostelScraperInput(BaseModel):
    """Input schema for UoPHostelScraperTool."""
    query: str = Field(..., description="The query string to search in the Hostel/Provost sections.")


class UoPHostelScraperTool(BaseTool):
    """
    Retrieves query-related information from the University of Peshawar Hostel/Provost sections.
    """

    name: str = "university_of_peshawar_hostel_scraper"
    description: str = (
        "Scrapes the UOP Provost and Hostel sections. "
        "Use ONLY for queries relating to hostels, accommodation, provost, hostel regulations, conduct, and discipline. "
        "Automatically handles sub-sections. Returns relevant text snippets matching the query."
    )
    args_schema: Type[BaseModel] = HostelScraperInput

    def _run(self, query: str) -> Any:
        if not query or not isinstance(query, str):
            return {"error": True, "message": "A valid query string is required."}

        # Extract keywords from query
        keywords: Set[str] = {
            word.lower()
            for word in re.findall(r"\b\w+\b", query)
            if len(word) > 2
        }
        if not keywords:
            return {"error": True, "message": "Query must contain meaningful keywords."}

        def is_relevant(content: str) -> bool:
            content_lower = content.lower()
            target_keywords = keywords.copy()
            words = set(re.findall(r"\b\w+\b", content_lower))
            match_count = sum(1 for kw in target_keywords if kw in words)
            
            if len(target_keywords) == 1:
                return match_count >= 1
            if len(target_keywords) == 2:
                return match_count >= 2
            return (match_count / len(target_keywords)) >= 0.6

        base_url = "http://www.uop.edu.pk/"
        urls_to_check: List[str] = [
            "http://www.uop.edu.pk/provost/",
            "http://www.uop.edu.pk/provost/?q=Hostel-Regulations",
            "http://www.uop.edu.pk/provost/?q=Conduct-and-Discipline-Regulations"
        ]

        found_snippets: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()

        for current_url in urls_to_check:
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            response = safe_get(current_url)
            if response is None:
                print(f"[{datetime.now()}] Skipping {current_url} - unreachable.")
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            tags_to_scan = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div", "li"]

            def clean_whitespace(val: str) -> str:
                return re.sub(r'\s+', ' ', val).strip()

            for element in soup.find_all(tags_to_scan):
                raw_text = safe_text(element)
                text = clean_whitespace(raw_text)
                
                if len(text) < 15:
                    continue

                is_rel = is_relevant(text)
                data_point: Dict[str, Any] = {}

                href = safe_attr(element if element.name == "a" else element.find("a"), "href")
                if href:
                    link = build_absolute_url(href, base_url)
                    # Automatically queue sub-links to handle sub-sections
                    if link not in visited_urls and "uop.edu.pk" in link and "provost" in link.lower():
                        urls_to_check.append(link)
                    
                    if is_rel:
                        data_point = {"text": text, "source_url": current_url, "link": link}
                elif is_rel:
                    data_point = {"text": text, "source_url": current_url}
                
                if not is_rel:
                    continue

                context_parts = [text]
                next_node = element.next_sibling
                captured = 0
                while next_node and captured < 1:
                    sib_text = clean_whitespace(safe_text(next_node))
                    if len(sib_text) > 10:
                        context_parts.append(sib_text)
                        captured += 1
                    next_node = next_node.next_sibling

                final_text = " ... ".join(context_parts)
                data_point["text"] = final_text

                text_lower = final_text.lower()
                is_duplicate = False
                for existing in found_snippets:
                    exist_lower = existing["text"].lower()
                    
                    if text_lower in exist_lower:
                        is_duplicate = True
                        break
                    elif exist_lower in text_lower:
                        existing["text"] = final_text
                        if "link" in data_point:
                            existing["link"] = data_point["link"]
                        is_duplicate = True
                        break

                if not is_duplicate:
                    found_snippets.append(data_point)
                    if len(found_snippets) >= 20:
                        break

            if len(found_snippets) >= 20:
                break

        if not found_snippets:
            return {
                "error": False,
                "message": "No information related to your query was found in the Hostel sections.",
                "query": query,
            }

        print(f"[{datetime.now()}] Hostel scraper found {len(found_snippets)} relevant snippets.")
        return {"error": False, "data": {"snippets": found_snippets, "query": query}}



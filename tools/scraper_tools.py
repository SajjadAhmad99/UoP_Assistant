"""
Web scraping tools for university information
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from crewai_tools import BaseTool
from datetime import datetime
import time

from config import UNIVERSITY_URLS
from utils.logger import setup_logger

logger = setup_logger()

class UniversityScraperTool(BaseTool):
    """Base scraper tool for university websites"""
    
    name: str = "University Website Scraper"
    description: str = "Scrapes information from University of Peshawar official website"
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UniversityBot/1.0 (Educational Purpose)'
        })
    
    def _scrape_url(self, url: str, selectors: Dict = None) -> Optional[str]:
        """Generic URL scraper"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Use custom selectors if provided
            if selectors:
                content = soup.select_one(selectors.get('content', 'body'))
            else:
                content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if content:
                # Clean up text
                text = content.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                return '\n'.join(lines[:100])  # Limit to first 100 lines
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _run(self, url: str) -> str:
        """Run the scraper"""
        content = self._scrape_url(url)
        return content or "Unable to retrieve content"

class AdmissionScraperTool(UniversityScraperTool):
    """Scraper for admission information"""
    
    def __init__(self):
        super().__init__()
        self.name = "Admission Information Scraper"
        self.description = "Scrapes admission information from University of Peshawar website"
    
    def _run(self, query: Optional[str] = None) -> str:
        """Scrape admission information"""
        url = UNIVERSITY_URLS["admission"]
        selectors = {
            'content': '.admission-content, .main-content, #content'
        }
        
        content = self._scrape_url(url, selectors)
        
        if content:
            # Extract key information
            lines = content.split('\n')
            admission_info = []
            
            keywords = ['deadline', 'apply', 'requirement', 'eligibility', 'program', 'fee']
            
            for line in lines:
                if any(keyword in line.lower() for keyword in keywords):
                    admission_info.append(line)
            
            if admission_info:
                return "Admission Information:\n" + "\n".join(admission_info[:20])
        
        return "Current admission information not found online. Please visit the official admission portal or contact admission office."

class ExamScraperTool(UniversityScraperTool):
    """Scraper for examination information"""
    
    def __init__(self):
        super().__init__()
        self.name = "Examination Information Scraper"
        self.description = "Scrapes exam schedules and results from University of Peshawar website"
    
    def _run(self, query: Optional[str] = None) -> str:
        """Scrape exam information"""
        url = UNIVERSITY_URLS["exams"]
        
        content = self._scrape_url(url)
        
        if content:
            # Look for exam-related information
            lines = content.split('\n')
            exam_info = []
            
            exam_keywords = [
                'schedule', 'date', 'time', 'venue', 'result',
                'transcript', 'card', 'form', 'submit'
            ]
            
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in exam_keywords):
                    # Check if it's about exams
                    if 'exam' in line_lower or 'test' in line_lower or 'paper' in line_lower:
                        exam_info.append(line)
            
            if exam_info:
                return "Examination Information:\n" + "\n".join(exam_info[:15])
        
        return "Exam information not found online. Please check the examination portal or contact exam office."

# Similar tools for FeeScraperTool, MeritScraperTool, DepartmentScraperTool
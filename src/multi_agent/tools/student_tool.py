"""
UOP News Scraper Tool
Scrapes latest news and announcements from University of Peshawar.
"""
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from typing import Any, Type
from datetime import datetime

from .utils import safe_get, SITE_UNAVAILABLE_MSG, NO_DATA_FOUND_MSG


class NewsScraperInput(BaseModel):
    """Input schema for UOPNewsScraperTool."""
    topic: str = Field(..., description="The topic or keywords to search for news or events.")


class UOPNewsScraperTool(BaseTool):
    """
    Scrapes latest news/announcements from UOP news page.
    Returns pre-formatted text to prevent LLM hallucination.
    """

    name: str = "university_of_peshawar_news_scraper"
    description: str = (
        "Scrapes University of Peshawar news page (www.uop.edu.pk/news/) or events page (www.uop.edu.pk/events/). "
        "Returns latest announcements, scholarships, tenders, job openings, and events. "
        "Pass any topic string. Returns formatted news or events text with dates and URLs."
    )
    args_schema: Type[BaseModel] = NewsScraperInput

    def _run(self, topic: str) -> str:
        now = datetime.now()
        print(f"[{now}] >>> NEWS SCRAPER START <<< Topic: {topic}")

        url = "http://www.uop.edu.pk/news/"
        topic_lower = topic.lower()
        if "event" in topic_lower:
            url = "http://www.uop.edu.pk/events/"
            
        response = safe_get(url)

        if response is None:
            print(f"[{now}] >>> NEWS SCRAPER FAILED <<< Site unreachable")
            return SITE_UNAVAILABLE_MSG

        from bs4 import BeautifulSoup, Tag

        soup = BeautifulSoup(response.text, "html.parser")
        news_items = []
        MAX_ITEMS = 5
        current_date = None

        for article in soup.find_all("article"):
            if not isinstance(article, Tag):
                continue
            for block in article.find_all("div", class_="history-moment clearfix"):
                if not isinstance(block, Tag):
                    continue

                # Extract date from header
                header = block.find("header")
                if isinstance(header, Tag):
                    current_date = header.get_text(strip=True)

                # Extract title and link
                title_tag = block.find("h5", class_="history-title")
                if not isinstance(title_tag, Tag):
                    continue

                a_tag = title_tag.find("a")
                if not isinstance(a_tag, Tag):
                    continue

                title = a_tag.get_text(strip=True)
                href = a_tag.get("href")

                if not isinstance(href, str) or not title.strip():
                    continue

                # Build absolute URL
                if href.startswith("?q="):
                    link = url + href
                elif href.startswith("/"):
                    link = "http://www.uop.edu.pk" + href
                else:
                    link = href

                # Only add if we have real content
                if title and link:
                    news_items.append({
                        "date": current_date or "Date not available",
                        "title": title,
                        "url": link
                    })

                if len(news_items) >= MAX_ITEMS:
                    break

            if len(news_items) >= MAX_ITEMS:
                break

        print(f"[{now}] >>> NEWS SCRAPER END <<< Found {len(news_items)} items")

        if not news_items:
            return NO_DATA_FOUND_MSG

        # Pre-format as clean text so LLM cannot hallucinate blank fields
        section_name = "events" if "event" in topic_lower else "news items"
        lines = [f"Here are the latest {section_name} from the University of Peshawar:\n"]
        for i, item in enumerate(news_items, 1):
            lines.append(f"{i}. {item['title']}")
            lines.append(f"   Date: {item['date']}")
            lines.append(f"   Link: {item['url']}\n")

        return "\n".join(lines)

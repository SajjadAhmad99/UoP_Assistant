# tasks.py
# This file defines the tasks for the agents using crewai.
# Tasks are reusable and can be assigned to crews.
# The scrape_task is predefined, while query tasks are created dynamically in the app.

from crewai import Task
from agents import scraper_agent, rag_agent

# Task for the scraper agent (run once to build KB)
scrape_task = Task(
    description="""Scrape the University of Peshawar website starting from the home page: https://www.uop.edu.pk/.
    Analyze the content to find links to key sections like admissions (e.g., https://www.uop.edu.pk/admissions/), 
    departments (e.g., https://www.uop.edu.pk/departments/), faculties, news, and about pages.
    Scrape at least 5-10 relevant pages using the scrape_website tool.
    For each page, extract the content and add it to the knowledge base using add_to_knowledge_base with metadata like {'source': url}.
    Focus on text content relevant to university info, avoiding unnecessary HTML or scripts.""",
    expected_output="A confirmation message that the knowledge base has been populated with scraped data from multiple pages.",
    agent=scraper_agent
)

# Note: The RAG task will be created dynamically in app.py for each user query.
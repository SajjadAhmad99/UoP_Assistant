# # File: scraper_agent.py
# # This file defines the Scraper Agent using CrewAI.
# # The agent is responsible for scraping information from the University of Peshawar website.

# from crewai import Agent
# from langchain_ollama import OllamaLLM
# from .tools import scrape_website, build_rag_vectorstore  # Import tools

# # Define the LLM using the user's model
# llm = OllamaLLM(model="llama3.2:3b-instruct-q2_K")

# scraper_agent = Agent(
#     role="Website Scraper",
#     goal="Scrape relevant information from the University of Peshawar website and prepare it for RAG.",
#     backstory="You are an expert web scraper with 10 years of experience in extracting data from educational websites. You focus on clean, relevant text extraction.",
#     tools=[scrape_website, build_rag_vectorstore],  # Tools for scraping and building vectorstore
#     llm=llm,
#     verbose=True
# )

# # Example task for the scraper agent (can be used in main.py)
# from crewai import Task

# scrape_task = Task(
#     description="Scrape the main page and admissions page of https://www.uop.edu.pk/. Then build a vectorstore from the scraped data.",
#     expected_output="A message confirming the vectorstore is built.",
#     tools=[scrape_website, build_rag_vectorstore],
#     agent=scraper_agent
# )
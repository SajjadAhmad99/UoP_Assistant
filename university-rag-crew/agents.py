# # agents.py
# # This file defines the agents using crewai.
# # Each agent has a role, goal, backstory, and assigned tools.
# # The LLM is the local Ollama model specified by the user.

# from crewai import Agent
# from langchain_ollama import Ollama
# from tools import (scrape_website, add_to_knowledge_base, query_knowledge_base)

# # Shared LLM instance
# llm = Ollama(model="llama3.2:3b-instruct-q2_K", temperature=0.2)  # Low temperature for accuracy

# scraper_agent = Agent(
#     role="Website Scraper Agent",
#     goal="Scrape and extract relevant information from the University of Peshawar website and add it to the knowledge base.",
#     backstory="""You are a senior web scraper with 10 years of experience in extracting structured information from university websites. 
#     You focus on key sections like home, admissions, departments, faculties, and news. You use tools to scrape URLs and add content to the KB.""",
#     tools=[scrape_website, add_to_knowledge_base],
#     llm=llm,
#     verbose=True,
#     allow_delegation=False  # No delegation needed for this agent
# )

# rag_agent = Agent(
#     role="RAG Query Answering Agent",
#     goal="Answer user questions accurately and quickly using retrieval-augmented generation from the knowledge base.",
#     backstory="""You are a senior RAG specialist with 10 years of experience in building and querying knowledge bases for fast, accurate responses. 
#     You retrieve relevant context from the KB and generate precise answers without hallucination.""",
#     tools=[query_knowledge_base],
#     llm=llm,
#     verbose=True,
#     allow_delegation=False  # No delegation needed
# )
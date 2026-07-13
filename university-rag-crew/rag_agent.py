# # # File: rag_agent.py
# # # This file defines the RAG Agent using CrewAI.
# # # The agent is responsible for querying the RAG system built from scraped data.

# # from crewai import Agent
# # from langchain_ollama import OllamaLLM
# # from .tools import query_rag  # Import RAG tool

# # # Define the LLM using the user's model
# # llm = OllamaLLM(model="llama3.2:3b-instruct-q2_K")

# # rag_agent = Agent(
# #     role="RAG Query Handler",
# #     goal="Answer queries using retrieval-augmented generation based on scraped university data.",
# #     backstory="You are an expert in RAG systems with 10 years of experience in building and querying vector databases for accurate information retrieval.",
# #     tools=[query_rag],  # Tool for querying the RAG
# #     llm=llm,
# #     verbose=True
# # )

# # # Example task for the RAG agent (can be used in main.py)
# # from crewai import Task

# # rag_task = Task(
# #     description="Query the RAG system with: 'What are the admission requirements for University of Peshawar?'",
# #     expected_output="A detailed answer based on retrieved data.",
# #     tools=[query_rag],
# #     agent=rag_agent
# # )
# #==================================================================================================
# import crewai
# from crewai import Agent,Crew,Process,Task
# from crewai.project import CrewBase, agent , crew ,task
# from crewai.agents.agent_builder.base_agent import BaseAgent
# from typing import List

# @CrewBase
# class final_year_project():
#     agents: list[BaseAgent]
#     tasks: list[Task]

#     agents_config="agent.yaml"
#     tasks_config="tasks.yaml"

#     @agent
#     def report_generator(self) -> Agent:
#         return Agent(
#             config=self.agents_config["report_generator"]
#         )
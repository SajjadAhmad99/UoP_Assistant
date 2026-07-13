# # File: main.py
# # This file orchestrates the multi-agent system using CrewAI and LangGraph for workflow.
# # We use CrewAI for the crew and LangGraph to define a simple stateful graph for sequencing agents.

# from crewai import Crew
# from langgraph.graph import StateGraph, END
# from typing import TypedDict, List
# import json

# # Import agents and tasks
# from scraper_agent import scraper_agent, scrape_task
# from rag_agent import rag_agent, rag_task

# # Define state for LangGraph
# class AgentState(TypedDict):
#     scraped_data: List[str]
#     rag_response: str

# # Define nodes for LangGraph
# def scrape_node(state: AgentState) -> AgentState:
#     print("Running Scraper Agent...")
#     # Run the scrape task
#     crew = Crew(agents=[scraper_agent], tasks=[scrape_task], verbose=True,stream=False)
#     result = crew.kickoff()
#     # Assume result contains scraped data; in practice, parse it
#     state["scraped_data"] = ["Scraped data placeholder"]  # Replace with actual
#     return state

# def rag_node(state: AgentState) -> AgentState:
#     print("Running RAG Agent...")
#     # Run the RAG task
#     crew = Crew(agents=[rag_agent], tasks=[rag_task], verbose=True,stream=False)
#     result = crew.kickoff()
#     state["rag_response"] = result.raw
#     return state

# # Build the graph
# workflow = StateGraph(state_schema=AgentState)
# workflow.add_node("scrape", scrape_node)
# workflow.add_node("rag", rag_node)
# workflow.add_edge("scrape", "rag")
# workflow.add_edge("rag", END)
# workflow.set_entry_point("scrape")

# # Compile the graph
# app = workflow.compile()

# # Run the multi-agent system
# # if __name__ == "__main__":
# #     initial_state = {"scraped_data": [], "rag_response": ""}
# #     result = app.invoke(initial_state)
# #     print("Final RAG Response:", result["rag_response"])
# if __name__ == "__main__":
#     initial_state: AgentState = {
#         "scraped_data": [],
#         "rag_response": ""
#     }

#     result = app.invoke(initial_state)           # ← now typed correctly
#     print("Final RAG Response:", result["rag_response"])
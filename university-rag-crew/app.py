# # app.py
# # This file sets up the Streamlit frontend and the multi-agent backend.
# # It uses crewai for agent orchestration, langchain for tools and LLM, and langgraph for a simple stateful graph (to demonstrate usage).
# # Langgraph is used here for a basic query flow: retrieve -> generate.
# # Run this file with: streamlit run app.py
# # Note: Ensure Ollama is running locally with the model pulled.

# import streamlit as st
# from crewai import Crew
# from agents import scraper_agent, rag_agent
# from tasks import scrape_task
# from langgraph.graph import StateGraph, END
# from typing import TypedDict, Annotated
# import operator

# # Langgraph state definition (simple for demonstration)
# class QueryState(TypedDict):
#     query: str
#     context: str
#     answer: str

# # Langgraph nodes
# def retrieve_node(state: QueryState) -> QueryState:
#     context = query_knowledge_base(state["query"])
#     return {"context": context}

# def generate_node(state: QueryState) -> QueryState:
#     prompt = f"Based on this context: {state['context']}\nAnswer the question: {state['query']}"
#     answer = rag_agent.llm.invoke(prompt).content  # Use agent's LLM for generation
#     return {"answer": answer}

# # Build langgraph for RAG query (retrieve -> generate)
# graph = StateGraph(QueryState)
# graph.add_node("retrieve", retrieve_node)
# graph.add_node("generate", generate_node)
# graph.add_edge("retrieve", "generate")
# graph.add_edge("generate", END)
# rag_graph = graph.compile()

# def build_kb():
#     """Build the knowledge base using the scraper agent."""
#     crew = Crew(
#         agents=[scraper_agent],
#         tasks=[scrape_task],
#         verbose=2  # Detailed logging
#     )
#     return crew.kickoff()

# st.title("University of Peshawar Chatbot")
# st.markdown("Ask questions about the university. The system scrapes and uses RAG for accurate answers.")

# # Build KB if not done (persists via FAISS local save)
# if 'kb_built' not in st.session_state:
#     with st.spinner("Building knowledge base from University of Peshawar website... This may take a few minutes."):
#         build_kb()
#     st.session_state.kb_built = True
#     st.success("Knowledge base built!")

# # Chat history
# if "messages" not in st.session_state:
#     st.session_state["messages"] = []

# # Display chat history
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])

# # User input
# if prompt := st.chat_input("Ask a question about University of Peshawar (e.g., admissions, departments)"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.write(prompt)
    
#     with st.chat_message("assistant"):
#         with st.spinner("Processing query..."):
#             # Use crewai for overall orchestration, but langgraph for the RAG flow
#             query_task = Task(
#                 description=f"Answer this question using the knowledge base: {prompt}. Retrieve context and generate an accurate response.",
#                 expected_output="A full, accurate answer to the user's question.",
#                 agent=rag_agent
#             )
#             crew = Crew(
#                 agents=[rag_agent],
#                 tasks=[query_task],
#                 verbose=2
#             )
#             # Kickoff crew, but integrate langgraph for precise RAG
#             initial_state = {"query": prompt}
#             rag_result = rag_graph.invoke(initial_state)
#             response = rag_result["answer"]
#             # If crew needs to override or add, but here we use the graph result
#         st.write(response)
#     st.session_state.messages.append({"role": "assistant", "content": response})
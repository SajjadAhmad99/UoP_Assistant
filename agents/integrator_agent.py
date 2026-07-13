# from typing import List, Dict, Any
# from langgraph.graph import StateGraph, END
# from pydantic import BaseModel, Field
# from langchain_community.llms import Ollama
# from config.settings import settings
# from config.prompts import Prompts

# class AgentState(BaseModel):
#     """State for agent workflow"""
#     query: str = Field(description="User query")
#     intent: str = Field(description="Detected intent")
#     selected_agents: List[str] = Field(default_factory=list, description="Selected agents")
#     context: Dict[str, Any] = Field(default_factory=dict, description="Context data")
#     response: str = Field(default="", description="Final response")

# class IntegratorAgent:
#     def __init__(self):
#         self.llm = Ollama(
#             base_url=settings.OLLAMA_BASE_URL,
#             model=settings.OLLAMA_MODEL
#         )
#         self.prompts = Prompts()
#         self.workflow = self._create_workflow()
    
#     def _create_workflow(self):
#         """Create LangGraph workflow for agent routing"""
#         workflow = StateGraph(AgentState)
        
#         # Add nodes
#         workflow.add_node("intent_detection", self.detect_intent)
#         workflow.add_node("agent_selection", self.select_agents)
#         workflow.add_node("execute_agents", self.execute_agents)
#         workflow.add_node("format_response", self.format_response)
        
#         # Add edges
#         workflow.set_entry_point("intent_detection")
#         workflow.add_edge("intent_detection", "agent_selection")
#         workflow.add_edge("agent_selection", "execute_agents")
#         workflow.add_edge("execute_agents", "format_response")
#         workflow.add_edge("format_response", END)
        
#         return workflow.compile()
    
#     def detect_intent(self, state: AgentState) -> AgentState:
#         from agents.conversation_agent import ConversationAgent
#         conversation_agent = ConversationAgent()
#         state.intent = conversation_agent.detect_intent(state.query)
#         return state
    
#     def select_agents(self, state: AgentState) -> AgentState:
#         """Select appropriate agents based on intent"""
#         intent_to_agents = {
#             "admission_query": ["admission_agent"],
#             "fee_query": ["fee_agent"],
#             "merit_query": ["merit_agent"],
#             "department_query": ["department_agent"],
#             "visualization_query": ["visualization_agent"],
#             "rag_query": ["rag_agent"],
#             "general_query": ["general_agent"]
#         }
        
#         state.selected_agents = intent_to_agents.get(state.intent, ["general_agent"])
#         return state
    
#     def execute_agents(self, state: AgentState) -> AgentState:
#         """Execute selected agents"""
#         responses = []
        
#         for agent_name in state.selected_agents:
#             if agent_name == "admission_agent":
#                 from agents.admission_agent import AdmissionAgent
#                 agent = AdmissionAgent()
#                 response = agent.process_query(state.query)
#             # elif agent_name == "fee_agent":
#             #     from agents.fee_agent import FeeAgent
#             #     agent = FeeAgent()
#             #     response = agent.process_query(state.query)
#             # ... similar for other agents
#             elif agent_name == "rag_agent":
#                 from rag.retriever import RAGRetriever
#                 retriever = RAGRetriever()
#                 response = retriever.query(state.query)
#             else:
#                 response = f"I can help with {state.query}. For more specific information, please contact the university administration."
            
#             responses.append(response)
        
#         state.context["agent_responses"] = responses
#         return state
    
#     def format_response(self, state: AgentState) -> AgentState:
#         """Format final response"""
#         responses = state.context.get("agent_responses", [])
#         if responses:
#             state.response = "\n\n".join(responses)
#         else:
#             state.response = "I couldn't process your query. Please try rephrasing."
        
#         return state
    
#     def process_query(self, query: str) -> str:
#         """Main method to process user query"""
#         initial_state = AgentState(query=query)
#         result = self.workflow.invoke(initial_state)
#         return result["response"]
"""
Agent Orchestrator using simple routing for University queries.
Reverted from LangGraph to simple Python logic as requested.
"""

from typing import Dict, Any, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os

from config import AGENT_CONFIG, LLM_MODEL
from agents.admission_agent import AdmissionAgent
from rag_engine import RAGEngine
from utils.logger import setup_logger

logger = setup_logger()

class AgentOrchestrator:
    """Orchestrates multiple agents using simple routing"""
    
    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        # Use LLM for intent detection
        model_name = LLM_MODEL.replace("groq/", "") if LLM_MODEL.startswith("groq/") else LLM_MODEL
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        self.rag_engine = rag_engine
        
        # Initialize agents
        self.agents = {
            "admission": AdmissionAgent(),
        }
        
    def _detect_intent(self, query: str) -> str:
        """Detect which agent should handle the query"""
        prompt = f"""
        Analyze the following query and classify it into one of these categories:
        - admission: Questions about admissions, deadlines, programs, eligibility
        - general: General questions about University of Peshawar
        
        Query: "{query}"
        
        Return only the category name.
        """
        
        messages = [
            SystemMessage(content="You are an intent classifier for university queries."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages).content.strip().lower()
            if "admission" in response:
                return "admission"
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            
        return "general"
    
    def route_query(self, query: str) -> Tuple[str, str]:
        """Main method to route and process query using simple logic"""
        try:
            intent = self._detect_intent(query)
            
            if intent == "admission" and "admission" in self.agents:
                logger.info("Routing to admission agent")
                response = self.agents["admission"].process_query(query)
                agent_used = "Admission Agent"
            else:
                logger.info("Using RAGEngine for query")
                if self.rag_engine:
                    response = self.rag_engine.query(query)
                    agent_used = "RAG System"
                else:
                    response = "I'm here to help with University of Peshawar queries. How can I assist you today?"
                    agent_used = "Orchestrator"
            
            return response, agent_used
            
        except Exception as e:
            logger.error(f"Error in routing query: {e}")
            return "I apologize, but I encountered an error processing your request.", "Error"
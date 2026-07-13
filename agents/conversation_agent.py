from typing import Dict, Any
from langchain_community.llms import Ollama
from config.settings import settings
from config.prompts import Prompts

class ConversationAgent:
    def __init__(self,intent="general"):
        self.intent = intent
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.1
        )
        self.prompts = Prompts()
    
    def detect_intent(self, query: str) -> str:
        """Detect the intent of the user query"""
        prompt = self.prompts.CONVERSATION_AGENT.format(
            university_name=settings.UNIVERSITY_NAME,
            query=query
        )
        
        response = self.llm.invoke(prompt)
        
        # Extract intent from response
        intents = [
            "admission_query", "fee_query", "merit_query", 
            "department_query", "visualization_query", 
            "general_query", "rag_query"
        ]
        
        for intent in intents:
            if intent in response.lower():
                return intent
        
        return "general_query"
    
    def is_university_related(self, query: str) -> bool:
        """Check if query is related to University of Peshawar"""
        keywords = [
            "university of peshawar", "uop", "peshawar university",
            "admission", "fee", "merit", "department", "program",
            "deadline", "application", "exam", "result"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in keywords)
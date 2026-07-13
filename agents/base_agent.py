# """
# Base Agent Class for all specialized agents
# """

# from abc import ABC, abstractmethod
# from typing import Dict, Any, Optional
# from crewai import Agent, Task, Crew
# from crewai_tools import BaseTool
# from langchain.chat_models import ChatOpenAI

# from config import AGENT_CONFIG, LLM_MODEL
# from tools.scraper_tools import UniversityScraperTool
# from tools.cache_tools import CacheManager
# from utils.logger import setup_logger

# logger = setup_logger()

# class BaseAgent(ABC):
#     """Base class for all university agents"""
    
#     def __init__(self, role: str, goal: str, backstory: str):
#         self.role = role
#         self.goal = goal
#         self.backstory = backstory
#         self.llm = ChatOpenAI(
#             model=LLM_MODEL,
#             temperature=AGENT_CONFIG["temperature"],
#             max_tokens=AGENT_CONFIG["max_tokens"]
#         )
#         self.cache = CacheManager()
#         self.scraper = UniversityScraperTool()
#         self.agent = self._create_agent()
#         self.tools = []
        
#     def _create_agent(self) -> Agent:
#         """Create CrewAI agent"""
#         return Agent(
#             role=self.role,
#             goal=self.goal,
#             backstory=self.backstory,
#             verbose=AGENT_CONFIG["verbose"],
#             llm=self.llm,
#             tools=self.tools,
#             allow_delegation=False
#         )
    
#     def _check_cache(self, query: str) -> Optional[str]:
#         """Check if response is in cache"""
#         return self.cache.get(query)
    
#     def _save_to_cache(self, query: str, response: str):
#         """Save response to cache"""
#         self.cache.set(query, response)
    
#     @abstractmethod
#     def process_query(self, query: str) -> str:
#         """Process query and return response"""
#         pass
    
#     def _format_response(self, response: str, sources: list = None) -> str:
#         """Format agent response with metadata"""
#         formatted = response
        
#         if sources:
#             formatted += "\n\n**Sources:**\n"
#             for source in sources:
#                 formatted += f"• {source}\n"
        
#         return formatted
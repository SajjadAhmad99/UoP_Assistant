"""
UoP AI Assistant - Tools Package
Exports all custom tools for the University of Peshawar assistant.
"""

from .custom_tool import UoPHomepageScraperTool
from .student_tool import UOPNewsScraperTool
from .department_tools import UOPDepartmentScraperTool
from .rag_tool import RAGTool

__all__ = [
    "UoPHomepageScraperTool",
    "UOPNewsScraperTool",
    "UOPDepartmentScraperTool",
    "RAGTool",
]

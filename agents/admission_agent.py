# import requests
# from bs4 import BeautifulSoup
# from crewai import Agent, Task
# from langchain.tools import tool
# from config.settings import settings
# from config.prompts import Prompts

# class AdmissionAgent:
#     def __init__(self):
#         self.llm = None  # Will be initialized when needed
#         self.prompts = Prompts()
    
#     @tool
#     def scrape_admission_info(self):
#         """Scrape admission information from university website"""
#         try:
#             response = requests.get(settings.ADMISSION_URL, timeout=10)
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Extract relevant information
#             admission_data = {
#                 "deadlines": self._extract_deadlines(soup),
#                 "programs": self._extract_programs(soup),
#                 "requirements": self._extract_requirements(soup),
#                 "last_updated": "2024-01-30"  # You might extract this from page
#             }
            
#             return admission_data
#         except Exception as e:
#             return {"error": f"Failed to scrape admission info: {str(e)}"}
    
#     def _extract_deadlines(self, soup):
#         """Extract admission deadlines"""
#         # Implement specific extraction logic
#         deadlines = []
#         # Find deadline elements in the page
#         deadline_elements = soup.find_all(class_=['deadline', 'date', 'last-date'])
#         for elem in deadline_elements:
#             deadlines.append(elem.text.strip())
#         return deadlines
    
#     def _extract_programs(self, soup):
#         """Extract available programs"""
#         programs = []
#         # Find program elements
#         program_elements = soup.find_all(class_=['program', 'course', 'degree'])
#         for elem in program_elements:
#             programs.append(elem.text.strip())
#         return programs
    
#     def _extract_requirements(self, soup):
#         """Extract admission requirements"""
#         requirements = []
#         # Find requirement elements
#         req_elements = soup.find_all(class_=['requirement', 'eligibility', 'criteria'])
#         for elem in req_elements:
#             requirements.append(elem.text.strip())
#         return requirements
    
#     def process_query(self, query: str) -> str:
#         """Process admission-related queries"""
#         # Scrape fresh data
#         scraped_data = self.scrape_admission_info()
        
#         # Use CrewAI agent
#         from langchain_community.llms import Ollama
        
#         llm = Ollama(
#             base_url=settings.OLLAMA_BASE_URL,
#             model=settings.OLLAMA_MODEL
#         )
        
#         agent = Agent(
#             role='University Admission Specialist',
#             goal='Provide accurate admission information for University of Peshawar',
#             backstory='Expert in university admissions with access to current data',
#             tools=[self.scrape_admission_info],
#             llm=llm,
#             verbose=True
#         )
        
#         task = Task(
#             description=f"""
#             Answer this query about University of Peshawar admissions:
#             Query: {query}
            
#             Use the scraped data: {scraped_data}
            
#             Provide a comprehensive, accurate answer.
#             """,
#             agent=agent,
#             expected_output="A detailed answer about admission information"
#         )
        
#         # Execute task
#         result = task.execute()
#         return result
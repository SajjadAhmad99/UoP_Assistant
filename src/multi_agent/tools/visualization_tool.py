# from crewai.tools import BaseTool
# from .visualization import admission_visualization_tool
# from typing import Optional,Literal
# class UETVizTool(BaseTool):
#     name: str = "UET Lahore Visualization Generator"
#     description: str = "Generates interactive charts: merit trends, latest 2025 merits, fees, seats. Params: query_type (merit_trends/latest_merits/fee_trends/seats/comparison), department (optional)."

#     def _run(self, query_type: str, department: Optional[str] = None, output_format: Literal["html", "figure"] = "html",):
#         result = admission_visualization_tool(query_type, department, output_format)
#         return result
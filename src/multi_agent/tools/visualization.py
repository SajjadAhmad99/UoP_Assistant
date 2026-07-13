"""
UoP Admission Visualization Tool
Creates interactive Plotly charts for University of Peshawar admissions data.
"""
from typing import Optional, Literal, Union
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from langchain_core.tools import tool


@tool
def uop_admission_visualization(
    query_type: Literal[
        "merit_trends",
        "latest_merits",
        "fee_trends",
        "seats",
        "comparison"
    ],
    department: Optional[str] = None,
    output_format: Literal["html", "fig"] = "html"
) -> Union[str, go.Figure]:
    """
    Visualization tool for University of Peshawar admissions.
    Creates interactive Plotly charts about merit trends, fees, seats, etc.

    Supported query_type values:
    - "merit_trends"     → Line chart: historical closing merit % (2020–2025), can filter by department
    - "latest_merits"    → Bar chart: final 2025 closing aggregates – most competitive departments
    - "comparison"       → Same as latest_merits (alias)
    - "fee_trends"       → Bar chart: approximate subsidized tuition fee per semester over years
    - "seats"            → Bar chart: approximate number of seats per department (main campus)

    Args:
        query_type: Must be one of the values listed above
        department: Optional department name filter (only meaningful for "merit_trends")
                    Examples: "Computer", "Software", "Zoology", "Civil"
        output_format: "html" → returns embeddable HTML string (recommended for chat / web)
                       "fig"  → returns Plotly Figure object (good for Streamlit / Jupyter)

    Returns:
        HTML string (Plotly chart) or Plotly Figure object
    """
    # ── Merit Trends Data (Historical approx + 2025 real final) ─────────────
    merit_trends_data = {
        'Year': [2020, 2021, 2022, 2023, 2024, 2025],
        'Computer Science (%)': [80.2, 79.8, 81.0, 78.5, 75.0, 74.045],
        'Software Engineering (%)': [79.5, 78.9, 79.5, 78.0, 76.5, 73.299],
        'Zoology (%)': [80.0, 80.5, 81.5, 82.0, 83.0, 76.259],
        'Civil Engineering (%)': [78.8, 78.2, 78.0, 77.0, 75.0, 73.211]
    }
    merit_df = pd.DataFrame(merit_trends_data)

    fig: go.Figure

    if query_type == "merit_trends":
        cols = merit_df.columns[1:]  # all departments by default
        if department:
            cols = [col for col in cols if department.lower() in col.lower()]
            if not cols:
                cols = merit_df.columns[1:]  # fallback to all if no match

        fig = px.line(
            merit_df,
            x='Year',
            y=cols,
            title='University of Peshawar Main Campus: Closing Merit Trends (A1 Category, 2020–2025)',
            markers=True,
            labels={'value': 'Closing Aggregate %', 'variable': 'Department'}
        )
        fig.update_layout(
            hovermode='x unified',
            yaxis_title='Closing Merit %',
            xaxis_title='Year',
            legend_title='Department'
        )
        fig.update_traces(mode='lines+markers')

    elif query_type in ("latest_merits", "comparison"):
        latest_data = {
            'Department': [
                'Computer Science', 'Zoology', 'Economics',
                'English', 'Artificial Intelligence', 'Software Engg'
            ],
            'Closing Aggregate % (2025 A1)': [74.045, 76.259, 73.211, 74.326, 76.013, 73.299]
        }
        latest_df = pd.DataFrame(latest_data)

        fig = px.bar(
            latest_df,
            x='Department',
            y='Closing Aggregate % (2025 A1)',
            title='University of Peshawar 2025 Final Closing Merits (Main Campus A1 – Most Competitive)',
            color='Department',
            text_auto=True
        )
        fig.update_layout(yaxis_title='Closing %', xaxis_tickangle=-45)

    # ── Fee Trends (Approximate subsidized A1 category) ─────────────────────
    elif query_type == "fee_trends":
        fee_data = {
            'Year': [2020, 2021, 2022, 2023, 2024, 2025],
            'Approx Tuition per Semester (PKR)': [40000, 42000, 45000, 48000, 52000, 55000]
        }
        fee_df = pd.DataFrame(fee_data)

        fig = px.bar(
            fee_df,
            x='Year',
            y='Approx Tuition per Semester (PKR)',
            title='University of Peshawar Fee Trends (Subsidized A1, Per Semester Approx)',
            color_discrete_sequence=['royalblue']
        )
        fig.update_traces(texttemplate='%{y:,}', textposition='outside')
        fig.update_layout(yaxis_title='Fee (PKR)')

    # ── Department-wise Seats (Latest estimates) ────────────────────────────
    elif query_type == "seats":
        seats_data = {
            'Department': [
                'Computer Science', 'Zoology', 'Economics',
                'English', 'Artificial Intelligence', 'Software Engg'
            ],
            'Approx Seats (Main Campus)': [150, 80, 100, 130, 100, 100]
        }
        seats_df = pd.DataFrame(seats_data)

        fig = px.bar(
            seats_df,
            x='Department',
            y='Approx Seats (Main Campus)',
            title='University of Peshawar Department-Wise Seats (Approx Latest, Main Campus)',
            color='Department'
        )
        fig.update_layout(xaxis_tickangle=-45, yaxis_title='Number of Seats')

    else:
        return (
            "Invalid query_type. Supported values: "
            "'merit_trends', 'latest_merits', 'fee_trends', 'seats', 'comparison'"
        )

    if output_format == "html":
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    return fig

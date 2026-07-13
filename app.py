"""
Main Streamlit Application for University Chatbot (Restored Simple Version)
"""

import streamlit as st
import time
from typing import Optional
from datetime import datetime

# Import custom modules
from agent_orchestrator import AgentOrchestrator
from rag_engine import RAGEngine
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

# Page configuration
st.set_page_config(
    page_title="University of Peshawar AI Assistant",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None

def initialize_systems():
    """Initialize agents and RAG system"""
    try:
        with st.spinner("Initializing AI Systems..."):
            # Initialize RAG Engine
            # Note: RAGEngine might need documents in data/documents
            st.session_state.rag_engine = RAGEngine()
            
            # Initialize Agent Orchestrator
            st.session_state.orchestrator = AgentOrchestrator(
                rag_engine=st.session_state.rag_engine
            )
        st.success("Systems initialized successfully!")
    except Exception as e:
        st.error(f"Initialization failed: {str(e)}")
        logger.error(f"Initialization error: {e}")

def display_chat_message(role: str, content: str, agent: Optional[str] = None):
    """Display chat message with agent info"""
    with st.chat_message(role):
        if agent:
            st.caption(f"🤖 {agent}")
        st.markdown(content)

# UI Header
st.title("🎓 University of Peshawar AI Assistant")
st.markdown("""
    Welcome to the University of Peshawar Official Assistant.
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("🔄 Initialize/Restart Systems", use_container_width=True):
        initialize_systems()
    
    st.divider()
    
    st.header("📊 System Status")
    if st.session_state.orchestrator:
        st.success("✅ Active")
    else:
        st.warning("⚠️ Not Initialized")

# Main chat interface
if not st.session_state.orchestrator:
    st.info("👈 Please initialize the system from the sidebar to begin.")
else:
    # Display chat history
    for message in st.session_state.chat_history:
        display_chat_message(
            message['role'],
            message['content'],
            message.get('agent')
        )

    # Chat input
    if prompt := st.chat_input("Ask about University of Peshawar..."):
        # Add user message to chat
        display_chat_message("user", prompt)
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        
        with st.spinner("Analyzing..."):
            try:
                # Route query via orchestrator
                response, agent = st.session_state.orchestrator.route_query(prompt)
                
                # Display response
                display_chat_message("assistant", response, agent)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'agent': agent,
                    'time': datetime.now().strftime("%H:%M:%S")
                })
            except Exception as e:
                st.error(f"Error: {str(e)}")
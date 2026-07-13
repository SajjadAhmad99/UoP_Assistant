# # tools.py
# # This file defines the custom tools used by the agents.
# # Tools are defined using langchain's @tool decorator.
# # We use WebBaseLoader for scraping and FAISS for the vector store.
# # Note: Ensure you have installed langchain, langchain-community, langchain-ollama, faiss-cpu, and beautifulsoup4 (for WebBaseLoader).

# from langchain.tools import tool
# from langchain_community.document_loaders import WebBaseLoader
# from langchain_ollama import OllamaEmbeddings
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS

# # Global embeddings model for consistency
# embeddings = OllamaEmbeddings(model="llama3.2:3b-instruct-q2_K")

# @tool
# def scrape_website(url: str) -> str:
#     """Scrape the content from a given URL on the University of Peshawar website."""
#     loader = WebBaseLoader(url)
#     docs = loader.load()
#     return docs[0].page_content

# @tool
# def add_to_knowledge_base(content: str, metadata: dict) -> str:
#     """Add scraped content to the FAISS-based knowledge base for RAG."""
#     splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     chunks = splitter.split_text(content)
    
#     try:
#         vectorstore = FAISS.load_local("uop_kb", embeddings, allow_dangerous_deserialization=True)
#     except Exception:
#         # Initialize if not exists
#         vectorstore = FAISS.from_texts(["Initial empty document"], embeddings)
    
#     vectorstore.add_texts(chunks, metadatas=[metadata for _ in chunks])
#     vectorstore.save_local("uop_kb")
#     return "Content added to knowledge base successfully."

# @tool
# def query_knowledge_base(query: str) -> str:
#     """Query the knowledge base for relevant documents based on the query."""
#     try:
#         vectorstore = FAISS.load_local("uop_kb", embeddings, allow_dangerous_deserialization=True)
#         docs = vectorstore.similarity_search(query, k=4)  # Retrieve top 4 relevant chunks
#         return "\n\n".join([f"Source: {doc.metadata.get('source', 'unknown')}\nContent: {doc.page_content}" for doc in docs])
#     except Exception:
#         return "Knowledge base not found or empty. Please build it first."
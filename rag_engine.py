# """
# RAG Engine for document-based question answering
# """

# import os
# from typing import List, Optional
# from langchain.vectorstores import Chroma
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.document_loaders import (
#     PyMuPDFLoader,
#     TextLoader,
#     DirectoryLoader
# )
# from langchain.chains import RetrievalQA
# from langchain.chat_models import ChatOpenAI

# from config import RAG_CONFIG, EMBEDDING_MODEL, DOCUMENTS_DIR
# from utils.logger import setup_logger

# logger = setup_logger()

# class RAGEngine:
#     """Retrieval Augmented Generation Engine for university documents"""
    
#     def __init__(self, persist_directory: str = "./data/chroma_db"):
#         self.persist_directory = persist_directory
#         self.embeddings = HuggingFaceEmbeddings(
#             model_name=EMBEDDING_MODEL
#         )
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=RAG_CONFIG["chunk_size"],
#             chunk_overlap=RAG_CONFIG["chunk_overlap"]
#         )
#         self.vectorstore = None
#         self.qa_chain = None
        
#         self._initialize()
    
#     def _load_documents(self) -> List:
#         """Load documents from documents directory"""
#         documents = []
        
#         try:
#             # Load PDFs
#             pdf_loader = DirectoryLoader(
#                 DOCUMENTS_DIR,
#                 glob="**/*.pdf",
#                 loader_cls=PyMuPDFLoader
#             )
#             pdf_docs = pdf_loader.load()
#             documents.extend(pdf_docs)
            
#             # Load text files
#             text_loader = DirectoryLoader(
#                 DOCUMENTS_DIR,
#                 glob="**/*.txt",
#                 loader_cls=TextLoader
#             )
#             text_docs = text_loader.load()
#             documents.extend(text_docs)
            
#             logger.info(f"Loaded {len(documents)} documents")
#             return documents
            
#         except Exception as e:
#             logger.error(f"Error loading documents: {e}")
#             return []
    
#     def _create_vectorstore(self, documents: List):
#         """Create or load vector store"""
#         if os.path.exists(self.persist_directory):
#             logger.info("Loading existing vector store")
#             self.vectorstore = Chroma(
#                 persist_directory=self.persist_directory,
#                 embedding_function=self.embeddings
#             )
#         else:
#             logger.info("Creating new vector store")
            
#             # Split documents
#             texts = self.text_splitter.split_documents(documents)
            
#             # Create vector store
#             self.vectorstore = Chroma.from_documents(
#                 documents=texts,
#                 embedding=self.embeddings,
#                 persist_directory=self.persist_directory
#             )
#             self.vectorstore.persist()
    
#     def _initialize_qa_chain(self):
#         """Initialize QA chain"""
#         if self.vectorstore:
#             retriever = self.vectorstore.as_retriever(
#                 search_kwargs={"k": RAG_CONFIG["similarity_top_k"]}
#             )
            
#             llm = ChatOpenAI(
#                 model="gpt-4-turbo-preview",
#                 temperature=0.1
#             )
            
#             self.qa_chain = RetrievalQA.from_chain_type(
#                 llm=llm,
#                 chain_type="stuff",
#                 retriever=retriever,
#                 return_source_documents=True
#             )
    
#     def _initialize(self):
#         """Initialize the RAG system"""
#         try:
#             # Load documents
#             documents = self._load_documents()
            
#             if documents:
#                 # Create vector store
#                 self._create_vectorstore(documents)
                
#                 # Initialize QA chain
#                 self._initialize_qa_chain()
                
#                 logger.info("RAG Engine initialized successfully")
#             else:
#                 logger.warning("No documents found for RAG")
                
#         except Exception as e:
#             logger.error(f"Error initializing RAG Engine: {e}")
    
#     def query(self, question: str) -> str:
#         """Query the RAG system"""
#         if not self.qa_chain:
#             return "I apologize, but the document system is not yet initialized."
        
#         try:
#             # Add university context
#             enhanced_question = f"""
#             About University of Peshawar: {question}
            
#             If the information is not in the provided context, 
#             say "This information is not available in the provided documents. 
#             Please contact the university administration for accurate information."
#             """
            
#             result = self.qa_chain({"query": enhanced_question})
            
#             # Format response with sources
#             response = result["result"]
            
#             # Add source information if available
#             if "source_documents" in result and result["source_documents"]:
#                 sources = list(set([
#                     doc.metadata.get("source", "Unknown") 
#                     for doc in result["source_documents"]
#                 ]))
                
#                 if sources:
#                     response += f"\n\n📚 **Sources:** {', '.join(sources)}"
            
#             return response
            
#         except Exception as e:
#             logger.error(f"Error in RAG query: {e}")
#             return "I encountered an error while searching the documents. Please try again."
    
#     def add_document(self, file_path: str):
#         """Add a new document to the RAG system"""
#         try:
#             # Load document
#             if file_path.endswith('.pdf'):
#                 loader = PyMuPDFLoader(file_path)
#             else:
#                 loader = TextLoader(file_path)
            
#             documents = loader.load()
            
#             # Split and add to vector store
#             texts = self.text_splitter.split_documents(documents)
            
#             if self.vectorstore:
#                 self.vectorstore.add_documents(texts)
#                 self.vectorstore.persist()
                
#                 # Reinitialize QA chain
#                 self._initialize_qa_chain()
                
#                 logger.info(f"Added document: {file_path}")
#                 return True
#             else:
#                 logger.error("Vector store not initialized")
#                 return False
                
#         except Exception as e:
#             logger.error(f"Error adding document: {e}")
#             return False
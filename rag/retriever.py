# from langchain.chains import RetrievalQA
# from langchain_community.llms import Ollama
# from rag.vector_store import VectorStoreManager
# from config.settings import settings

# class RAGRetriever:
#     def __init__(self):
#         self.llm = Ollama(
#             base_url=settings.OLLAMA_BASE_URL,
#             model=settings.OLLAMA_MODEL
#         )
#         self.vector_store_manager = VectorStoreManager()
#         self.qa_chain = self._setup_qa_chain()
    
#     def _setup_qa_chain(self):
#         """Setup QA chain with retrieval"""
#         vector_store = self.vector_store_manager.get_vector_store()
        
#         if not vector_store:
#             raise ValueError("Vector store not found. Please create it first.")
        
#         retriever = vector_store.as_retriever(
#             search_kwargs={"k": 4}
#         )
        
#         qa_chain = RetrievalQA.from_chain_type(
#             llm=self.llm,
#             chain_type="stuff",
#             retriever=retriever,
#             return_source_documents=True
#         )
        
#         return qa_chain
    
#     def query(self, question: str) -> str:
#         """Query the RAG system"""
#         result = self.qa_chain.invoke({"query": question})
        
#         answer = result["result"]
#         sources = result.get("source_documents", [])
        
#         # Add source information
#         if sources:
#             answer += "\n\nSources:\n"
#             for i, source in enumerate(sources[:3], 1):
#                 answer += f"{i}. {source.metadata.get('source', 'Unknown')}\n"
        
#         return answer
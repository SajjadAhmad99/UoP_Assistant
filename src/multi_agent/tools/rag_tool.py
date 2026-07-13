"""
RAG Tool for UoP Knowledge Base
Answers questions using the internal FAISS vector store with HuggingFace embeddings.
"""
import os
from datetime import datetime
from typing import Optional, Type, Any
import time
import traceback

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
load_dotenv()

# ── Global Cache for Embeddings and FAISS ───────────────────────────────────
_GLOBAL_EMBEDDINGS: Optional[HuggingFaceEmbeddings] = None
_GLOBAL_FAISS: Optional[FAISS] = None


class RAGToolInput(BaseModel):
    """Input schema for the RAG tool."""
    query: str = Field(..., description="The query string to search and generate a response for.")
    top_k: Optional[int] = Field(default=5, description="Number of top documents to retrieve (default: 5).")


class RAGTool(BaseTool):
    """
    RAG-based tool for answering UoP questions from internal knowledge base.
    Uses HuggingFace embeddings and FAISS for retrieval, NVIDIA NIM LLM for generation.
    """

    name: str = "rag_tool"
    description: str = (
        "Answer UoP questions using the internal knowledge base. "
        "Use for: fee structures, admission criteria, eligibility requirements, "
        "university rules, history, and policies. "
        "Returns 'NOT_FOUND' if information is not in the knowledge base."
    )
    args_schema: Type[BaseModel] = RAGToolInput

    # Instance fields
    vector_store: Optional[FAISS] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None
    _llm: Optional[ChatOpenAI] = None
    _prompt: Optional[ChatPromptTemplate] = None
    _rag_chain: Optional[Any] = None

    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_components()

    def _initialize_components(self):
        """Initialize embeddings, FAISS, LLM, and RAG chain."""
        global _GLOBAL_EMBEDDINGS, _GLOBAL_FAISS

        index_path = "faiss_index"

        # Load embeddings model (cached globally)
        if _GLOBAL_EMBEDDINGS is None:
            print("[RAG] Loading HuggingFace Embeddings model...")
            try:
                _GLOBAL_EMBEDDINGS = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True}
                )
                print("[RAG] Embeddings model loaded successfully.")
            except Exception as e:
                raise RuntimeError(f"Failed to load embeddings: {e}")

        self._embeddings = _GLOBAL_EMBEDDINGS

        # Load FAISS index (cached globally)
        if _GLOBAL_FAISS is None:
            print(f"[RAG] Loading FAISS index from {index_path}...")
            try:
                if not os.path.exists(index_path):
                    raise FileNotFoundError(
                        f"FAISS index not found at {index_path}. "
                        "Please run rag_indexer.py first to create the index."
                    )
                _GLOBAL_FAISS = FAISS.load_local(
                    index_path,
                    self._embeddings,
                    allow_dangerous_deserialization=True
                )
                # docstore._dict is the current API (index_to_doc was removed in newer langchain)
                doc_count = len(_GLOBAL_FAISS.docstore._dict)
                print(f"[RAG] FAISS index loaded successfully ({doc_count} documents).")
            except FileNotFoundError as e:
                raise
            except Exception as e:
                raise RuntimeError(f"Failed to load FAISS index: {e}")

        self.vector_store = _GLOBAL_FAISS

        # Initialize LLM — use NVIDIA NIM (same provider as crew.py agents)
        nvidia_key = os.getenv("NVIDIA_NIM_API_KEY")
        if not nvidia_key:
            raise ValueError("NVIDIA_NIM_API_KEY is required.")
        self._llm = ChatOpenAI(
            model="meta/llama-3.1-70b-instruct",
            api_key=nvidia_key,
            base_url="https://integrate.api.nvidia.com/v1",
            temperature=0,
            max_tokens=1024
        )

        # Define RAG prompt template with strict constraints
        self._prompt = ChatPromptTemplate.from_template(
            "You are a factual research assistant for the University of Peshawar.\n"
            "Answer the query STRICTLY using the provided context. Do NOT use external knowledge.\n"
            "If the information is not present in the context, respond with exactly 'NOT_FOUND'.\n"
            "Respond in the same language as the query (English or Urdu).\n"
            "Be concise and include specific figures, dates, or rules when available.\n\n"
            "Context:\n{context}\n\n"
            "Query: {query}\n\n"
            "Response:"
        )

        # Build RAG chain
        self._rag_chain = self._prompt | self._llm | StrOutputParser()

    def _format_docs(self, docs: list) -> str:
        """Helper to format retrieved documents."""
        if not docs:
            return ""
        return "\n\n".join(doc.page_content for doc in docs)

    def _run(self, query: str, top_k: Optional[int] = 5) -> str:
        """
        Execute RAG query.

        Args:
            query: User's question
            top_k: Number of documents to retrieve

        Returns:
            str: Answer from RAG system or error/not_found message
        """
        try:
            now = datetime.now()
            print(f"[{now}] >>> RAG TOOL START <<< query: {query}")

            # Validate top_k
            if top_k is None or not isinstance(top_k, int) or top_k < 1:
                top_k = 5
            top_k = min(top_k, 10)  # Cap at 10 to avoid context overflow

            # Safety check: ensure vector store is initialized
            if self.vector_store is None:
                raise RuntimeError("Vector store not initialized")

            # Retrieve documents
            retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": top_k, "score_threshold": 0.2}
            )
            docs = retriever.invoke(query)

            if not docs:
                print(f"[{now}] >>> RAG TOOL END <<< (NOT_FOUND - no docs retrieved)")
                return "NOT_FOUND: No relevant documents found in the knowledge base."

            formatted_docs = self._format_docs(docs)
            print(f"[{now}] Retrieved {len(docs)} documents (total chars: {len(formatted_docs)})")

            # Generate response with rate limit retry
            max_attempts = 3
            last_error = None

            for attempt in range(max_attempts):
                try:
                    response = self._rag_chain.invoke({
                        "context": formatted_docs,
                        "query": query
                    }).strip()

                    # Check for NOT_FOUND response
                    if "not_found" in response.lower() or len(response) < 5:
                        print(f"[{now}] >>> RAG TOOL END <<< (NOT_FOUND - LLM could not find answer)")
                        return "NOT_FOUND: Information not found in internal documents."

                    print(f"[{now}] >>> RAG TOOL END <<< (SUCCESS)")
                    return response

                except Exception as e:
                    last_error = e
                    err_msg = str(e).lower()

                    if "rate limit" in err_msg and attempt < max_attempts - 1:
                        wait_time = 10 * (attempt + 1)  # Exponential backoff
                        print(f"[{now}] !!! RATE LIMIT HIT !!! Waiting {wait_time}s for attempt {attempt + 2}...")
                        time.sleep(wait_time)
                        continue
                    elif "context" in err_msg or "token" in err_msg:
                        # Context too long - reduce top_k and retry
                        if top_k > 2:
                            top_k = max(2, top_k - 2)
                            print(f"[{now}] !!! CONTEXT TOO LARGE !!! Reducing top_k to {top_k} and retrying...")
                            return self._run(query, top_k)
                        else:
                            break
                    else:
                        break

            # All attempts failed
            print(f"[{now}] !!! RAG TERMINAL ERROR !!!: {last_error}")
            return f"TERMINAL_ERROR: Could not generate response after {max_attempts} attempts: {type(last_error).__name__}"

        except FileNotFoundError as e:
            return f"CONFIGURATION_ERROR: {str(e)}"
        except Exception as e:
            now = datetime.now()
            print(f"[{now}] !!! RAG ERROR !!!\n{traceback.format_exc()}")
            return f"ERROR: An unexpected error occurred: {type(e).__name__}: {str(e)}"

    async def _arun(self, query: str, top_k: Optional[int] = 5) -> str:
        """Async version - delegates to sync implementation."""
        return self._run(query, top_k)

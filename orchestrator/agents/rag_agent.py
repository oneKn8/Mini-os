"""
RAG Agent for knowledge retrieval and question answering.

This agent uses the RAG utilities from backend.rag to perform document
retrieval and generate responses based on retrieved context.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.llm_client import LLMClient
from orchestrator.state import OpsAgentState

logger = logging.getLogger(__name__)

# Try to import RAG utilities
try:
    from backend.rag import get_embedding_model, get_llm
    from backend.rag.utils import create_vectorstore_langchain

    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG utilities not available: {e}. RAG agent will use fallback LLM.")
    RAG_AVAILABLE = False


class RAGAgent(BaseAgent):
    """Agent for retrieval-augmented generation using document knowledge base."""

    def __init__(self, name: str = "rag", use_rag_llm: bool = True):
        """
        Initialize the RAG agent.

        Args:
            name: Agent name for identification
            use_rag_llm: If True and RAG is available, use RAG's get_llm().
                        Otherwise, use the standard LLMClient.
        """
        super().__init__(name)
        self.use_rag_llm = use_rag_llm and RAG_AVAILABLE
        self._vectorstore = None
        self._llm = None
        self._embedder = None

    def _init_components(self):
        """Lazily initialize RAG components."""
        if self._llm is None:
            if self.use_rag_llm:
                try:
                    self._llm = get_llm()
                    self._embedder = get_embedding_model()
                    self._vectorstore = create_vectorstore_langchain(self._embedder)
                    logger.info("Initialized RAG components with RAG utilities")
                except Exception as e:
                    logger.warning(f"Failed to init RAG components: {e}. Using fallback.")
                    self._llm = LLMClient()
            else:
                self._llm = LLMClient()

    async def run(self, context: Union[AgentContext, OpsAgentState]) -> AgentResult:
        """
        Execute RAG-based query answering.

        This agent processes queries that require knowledge retrieval:
        1. Extracts the query from context
        2. Retrieves relevant documents from vectorstore
        3. Generates a response using LLM with retrieved context

        Args:
            context: Agent context or state with query information

        Returns:
            AgentResult with the generated answer and retrieved sources
        """
        start_time = datetime.now()
        ctx = self._get_context(context)

        try:
            # Initialize components if needed
            self._init_components()

            # Extract query from context
            query = self._extract_query(ctx)
            if not query:
                return self._create_result(
                    status="error",
                    error_message="No query found in context",
                    duration_ms=self._elapsed_ms(start_time),
                )

            # Retrieve relevant documents
            retrieved_docs = await self._retrieve_documents(query)

            # Generate response
            response = await self._generate_response(query, retrieved_docs)

            # Build output summary
            output_summary = {
                "query": query,
                "response": response,
                "num_sources": len(retrieved_docs),
                "sources": [doc.get("source", "unknown") for doc in retrieved_docs[:3]],
            }

            return self._create_result(
                status="success",
                output_summary=output_summary,
                metadata_updates=[{"rag_response": response, "rag_sources": retrieved_docs}],
                duration_ms=self._elapsed_ms(start_time),
            )

        except Exception as e:
            logger.error(f"RAG agent error: {e}", exc_info=True)
            return self._create_result(
                status="error",
                error_message=str(e),
                duration_ms=self._elapsed_ms(start_time),
            )

    def _extract_query(self, ctx: AgentContext) -> Optional[str]:
        """Extract the query from context."""
        # Check metadata for explicit query
        if ctx.metadata and "query" in ctx.metadata:
            return ctx.metadata["query"]

        # Check items for a query item
        for item in ctx.items:
            if item.get("type") == "query":
                return item.get("content") or item.get("text")
            if "question" in item:
                return item["question"]

        # Check if there's a message in metadata
        if ctx.metadata and "message" in ctx.metadata:
            return ctx.metadata["message"]

        return None

    async def _retrieve_documents(self, query: str, top_k: int = 4) -> List[Dict]:
        """Retrieve relevant documents from the vectorstore."""
        if not self._vectorstore:
            logger.debug("No vectorstore available, returning empty results")
            return []

        try:
            # Use similarity search
            docs = self._vectorstore.similarity_search(query, k=top_k)
            return [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "metadata": doc.metadata,
                }
                for doc in docs
            ]
        except Exception as e:
            logger.warning(f"Document retrieval failed: {e}")
            return []

    async def _generate_response(self, query: str, documents: List[Dict]) -> str:
        """Generate a response using the LLM with retrieved context."""
        # Build context from retrieved documents
        if documents:
            context = "\n\n".join([f"Source: {doc['source']}\n{doc['content']}" for doc in documents])
            prompt = f"""Based on the following context, answer the question.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {query}

Answer:"""
        else:
            prompt = f"""Answer the following question to the best of your ability.

Question: {query}

Answer:"""

        # Call LLM
        if hasattr(self._llm, "invoke"):
            # LangChain-style LLM
            response = self._llm.invoke(prompt)
            if hasattr(response, "content"):
                return response.content
            return str(response)
        elif hasattr(self._llm, "call"):
            # Our LLMClient
            return self._llm.call(prompt)
        else:
            raise ValueError(f"Unknown LLM type: {type(self._llm)}")

    def _elapsed_ms(self, start_time: datetime) -> int:
        """Calculate elapsed milliseconds since start_time."""
        return int((datetime.now() - start_time).total_seconds() * 1000)

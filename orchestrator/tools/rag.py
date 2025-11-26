"""
RAG (Retrieval-Augmented Generation) tools for the conversational agent.

Provides tools for querying the knowledge base and answering questions
using retrieved context from documents.
"""

import logging
from typing import List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SourceDocument(BaseModel):
    """A source document used in the response."""

    source: str = Field(description="Source identifier or filename")
    content_preview: str = Field(description="Preview of relevant content")
    relevance_score: float = Field(description="Relevance score 0-1", default=0.0)


class RAGQueryOutput(BaseModel):
    """Output schema for RAG queries."""

    answer: str = Field(description="The generated answer based on retrieved context")
    sources: List[SourceDocument] = Field(
        description="Source documents used to generate the answer", default_factory=list
    )
    confidence: str = Field(description="Confidence level: high, medium, low", default="medium")
    has_context: bool = Field(description="Whether relevant context was found", default=False)


def _get_vectorstore():
    """Get or create the vectorstore for RAG."""
    try:
        from backend.rag import get_embedding_model, create_vectorstore_langchain, is_rag_available

        if not is_rag_available():
            logger.warning("RAG utilities not available")
            return None

        embedder = get_embedding_model()
        vectorstore = create_vectorstore_langchain(embedder)
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to get vectorstore: {e}")
        return None


def _search_user_data(query: str, limit: int = 5) -> List[dict]:
    """
    Search user data (emails, events) for relevant context.

    This provides context from the user's actual data even if
    the main vectorstore is empty.
    """
    try:
        from backend.api.database import SessionLocal
        from backend.api.models import Item
        from sqlalchemy import or_

        db = SessionLocal()
        try:
            search_pattern = f"%{query}%"

            items = (
                db.query(Item)
                .filter(
                    or_(
                        Item.title.ilike(search_pattern),
                        Item.body_preview.ilike(search_pattern),
                        Item.body_full.ilike(search_pattern),
                    )
                )
                .limit(limit)
                .all()
            )

            return [
                {
                    "source": f"{item.source_type}:{item.id}",
                    "content": f"Subject: {item.title}\n{item.body_preview or ''}",
                    "type": item.source_type,
                }
                for item in items
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to search user data: {e}")
        return []


@tool
def query_knowledge_base(question: str, include_user_data: bool = True, max_sources: int = 4) -> RAGQueryOutput:
    """
    Answer a question using the knowledge base and user data.

    This tool retrieves relevant documents and generates an answer
    based on the retrieved context. It can search both the document
    knowledge base and the user's emails/events.

    Args:
        question: The question to answer
        include_user_data: Whether to include user's emails/events in search (default: True)
        max_sources: Maximum number of source documents to retrieve (default: 4)

    Returns:
        An answer with source citations and confidence level
    """
    from orchestrator.llm_client import LLMClient

    sources: List[SourceDocument] = []
    context_pieces: List[str] = []
    has_context = False

    # Try vectorstore retrieval
    vectorstore = _get_vectorstore()
    if vectorstore:
        try:
            docs = vectorstore.similarity_search(question, k=max_sources)
            for doc in docs:
                source_name = doc.metadata.get("source", "document")
                content = doc.page_content[:500]
                sources.append(
                    SourceDocument(
                        source=source_name,
                        content_preview=content[:200],
                        relevance_score=0.8,  # Placeholder - would come from similarity score
                    )
                )
                context_pieces.append(f"[Source: {source_name}]\n{content}")
                has_context = True
        except Exception as e:
            logger.warning(f"Vectorstore search failed: {e}")

    # Search user data
    if include_user_data:
        user_data = _search_user_data(question, limit=max_sources)
        for item in user_data:
            sources.append(
                SourceDocument(source=item["source"], content_preview=item["content"][:200], relevance_score=0.7)
            )
            context_pieces.append(f"[From your {item['type']}]\n{item['content']}")
            has_context = True

    # Generate answer
    try:
        llm = LLMClient()

        if context_pieces:
            context_text = "\n\n".join(context_pieces[:max_sources])
            prompt = f"""Based on the following context, answer the user's question.
If the context doesn't contain relevant information, say so and provide general guidance.

Context:
{context_text}

Question: {question}

Provide a helpful, accurate answer based on the context. If you're not certain, acknowledge that."""
        else:
            prompt = f"""Answer the following question to the best of your ability.
If you don't have specific information, provide general helpful guidance.

Question: {question}

Answer:"""

        answer = llm.call(prompt, temperature=0.5, max_tokens=800)

        # Determine confidence
        if has_context and len(sources) >= 2:
            confidence = "high"
        elif has_context:
            confidence = "medium"
        else:
            confidence = "low"

        return RAGQueryOutput(
            answer=answer.strip(), sources=sources[:max_sources], confidence=confidence, has_context=has_context
        )

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return RAGQueryOutput(
            answer=f"I apologize, but I encountered an error while searching for information: {str(e)}",
            sources=[],
            confidence="low",
            has_context=False,
        )

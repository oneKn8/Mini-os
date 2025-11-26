"""
RAG API routes for knowledge retrieval and document ingestion.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Check RAG availability
try:
    from backend.rag import (
        is_rag_available,
        is_openai_available,
        is_nvidia_available,
        get_available_vectorstores,
        get_llm,
        get_embedding_model,
        get_config,
        create_vectorstore_langchain,
    )

    RAG_AVAILABLE = is_rag_available()
except ImportError as e:
    logger.warning(f"RAG module not available: {e}")
    RAG_AVAILABLE = False


# Request/Response models
class RAGQueryRequest(BaseModel):
    """Request body for RAG query."""

    query: str = Field(..., min_length=1, max_length=2000, description="The question to answer")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of documents to retrieve")
    use_reranking: bool = Field(default=False, description="Whether to use reranking")


class RAGQueryResponse(BaseModel):
    """Response for RAG query."""

    answer: str
    sources: List[Dict[str, Any]] = []
    query: str
    processing_time_ms: int
    model_used: str


class RAGStatusResponse(BaseModel):
    """Response for RAG system status."""

    available: bool
    openai_available: bool
    nvidia_available: bool
    vectorstores: List[str]
    configured_llm: Optional[str] = None
    configured_embeddings: Optional[str] = None
    configured_vectorstore: Optional[str] = None


class DocumentIngestRequest(BaseModel):
    """Request for document text ingestion."""

    content: str = Field(..., min_length=1, description="Document content to ingest")
    source: str = Field(default="manual", description="Source identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentIngestResponse(BaseModel):
    """Response for document ingestion."""

    success: bool
    message: str
    chunks_created: int = 0


# Global vectorstore instance (lazy initialized)
_vectorstore = None
_embedder = None


def _get_vectorstore():
    """Get or create the vectorstore instance."""
    global _vectorstore, _embedder

    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG module not available. Install required dependencies.")

    if _vectorstore is None:
        try:
            _embedder = get_embedding_model()
            _vectorstore = create_vectorstore_langchain(_embedder)
            logger.info("Vectorstore initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vectorstore: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to initialize vectorstore: {str(e)}")

    return _vectorstore


@router.get("/status", response_model=RAGStatusResponse)
async def get_rag_status():
    """Get the current status of the RAG system."""
    if not RAG_AVAILABLE:
        return RAGStatusResponse(
            available=False,
            openai_available=False,
            nvidia_available=False,
            vectorstores=[],
        )

    try:
        config = get_config()
        return RAGStatusResponse(
            available=True,
            openai_available=is_openai_available(),
            nvidia_available=is_nvidia_available(),
            vectorstores=get_available_vectorstores(),
            configured_llm=f"{config.llm.model_engine}/{config.llm.model_name}",
            configured_embeddings=f"{config.embeddings.model_engine}/{config.embeddings.model_name}",
            configured_vectorstore=config.vector_store.name,
        )
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        return RAGStatusResponse(
            available=False,
            openai_available=False,
            nvidia_available=False,
            vectorstores=[],
        )


@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_base(request: RAGQueryRequest):
    """Query the knowledge base using RAG."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG module not available. Install required dependencies.")

    start_time = datetime.now()

    try:
        # Get LLM
        llm = get_llm()
        config = get_config()
        model_name = f"{config.llm.model_engine}/{config.llm.model_name}"

        # Try to retrieve from vectorstore
        sources = []
        context = ""

        try:
            vectorstore = _get_vectorstore()
            docs = vectorstore.similarity_search(request.query, k=request.top_k)
            sources = [
                {
                    "content": doc.page_content[:500],  # Truncate for response
                    "source": doc.metadata.get("source", "unknown"),
                    "metadata": doc.metadata,
                }
                for doc in docs
            ]
            context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            logger.warning(f"Vectorstore retrieval failed (may be empty): {e}")
            # Continue without context - will answer from LLM knowledge

        # Build prompt
        if context:
            prompt = f"""Based on the following context, answer the question.
If the context doesn't contain relevant information, say so and provide what you know.

Context:
{context}

Question: {request.query}

Answer:"""
        else:
            prompt = f"""Answer the following question to the best of your ability.
Note: No documents are currently in the knowledge base, so this answer is based on general knowledge.

Question: {request.query}

Answer:"""

        # Get response from LLM
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)

        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return RAGQueryResponse(
            answer=answer,
            sources=sources,
            query=request.query,
            processing_time_ms=processing_time,
            model_used=model_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(request: DocumentIngestRequest):
    """Ingest a document into the knowledge base."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG module not available. Install required dependencies.")

    try:
        from langchain_core.documents import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        vectorstore = _get_vectorstore()

        # Split document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        chunks = text_splitter.split_text(request.content)

        # Create documents with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": request.source,
                    "chunk_index": i,
                    "ingested_at": datetime.now().isoformat(),
                    **request.metadata,
                },
            )
            for i, chunk in enumerate(chunks)
        ]

        # Add to vectorstore
        vectorstore.add_documents(documents)

        logger.info(f"Ingested document with {len(chunks)} chunks from source: {request.source}")

        return DocumentIngestResponse(
            success=True,
            message=f"Successfully ingested document into {len(chunks)} chunks",
            chunks_created=len(chunks),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/file", response_model=DocumentIngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """Ingest a file into the knowledge base."""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG module not available. Install required dependencies.")

    # Check file type
    allowed_extensions = {".txt", ".md", ".json", ".csv"}
    file_ext = os.path.splitext(file.filename or "")[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")

    try:
        # Read file content
        content = await file.read()
        text_content = content.decode("utf-8")

        # Use the text ingestion endpoint
        request = DocumentIngestRequest(
            content=text_content,
            source=file.filename or "uploaded_file",
            metadata={"original_filename": file.filename, "file_type": file_ext},
        )

        return await ingest_document(request)

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
    except Exception as e:
        logger.error(f"File ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")

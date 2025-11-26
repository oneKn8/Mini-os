# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""RAG module for document retrieval and generation.

This module provides utilities for:
- LLM initialization (NVIDIA AI Endpoints, OpenAI)
- Embedding model setup (HuggingFace, NVIDIA, OpenAI)
- Vector store creation (FAISS, Milvus, PGVector)
- Configuration management via YAML/JSON/env vars
- OpenTelemetry tracing (optional)

Configuration:
    Set APP_CONFIG_FILE to point to your config YAML/JSON, or use environment variables:
    - APP_LLM_MODELENGINE: openai, nvidia-ai-endpoints
    - APP_LLM_MODELNAME: gpt-4o-mini, meta/llama3-70b-instruct, etc.
    - APP_EMBEDDINGS_MODELENGINE: openai, huggingface, nvidia-ai-endpoints
    - APP_VECTORSTORE_NAME: faiss, milvus, pgvector
"""

import logging

logger = logging.getLogger(__name__)

# Import base classes (always available)
from backend.rag.base import BaseExample  # noqa: E402

# Import configuration (always available)
from backend.rag.configuration import (  # noqa: E402
    AppConfig,
    EmbeddingConfig,
    LLMConfig,
    RankingConfig,
    RetrieverConfig,
    TextSplitterConfig,
    VectorStoreConfig,
)

# Import utilities - these require additional dependencies
_UTILS_AVAILABLE = False
try:
    from backend.rag.utils import (
        create_vectorstore_langchain,
        get_config,
        get_embedding_model,
        get_llm,
        get_prompts,
        get_ranking_model,
        get_text_splitter,
        get_vectorstore,
        is_langchain_available,
        is_llamaindex_available,
        is_nvidia_available,
        is_openai_available,
        get_available_vectorstores,
    )

    _UTILS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG utilities not available: {e}")

    # Provide stub functions that raise helpful errors
    def get_llm(*args, **kwargs):
        raise RuntimeError("RAG utilities not available. Install: pip install langchain langchain-openai")

    def get_embedding_model(*args, **kwargs):
        raise RuntimeError("RAG utilities not available. Install: pip install langchain langchain-openai")

    def get_config(*args, **kwargs):
        raise RuntimeError("RAG utilities not available. Install: pip install dataclass-wizard")

    def get_prompts(*args, **kwargs):
        return {}

    def get_text_splitter(*args, **kwargs):
        raise RuntimeError("RAG utilities not available. Install: pip install langchain")

    def get_ranking_model(*args, **kwargs):
        return None

    def get_vectorstore(*args, **kwargs):
        raise RuntimeError("RAG utilities not available. Install: pip install langchain-community")

    def create_vectorstore_langchain(*args, **kwargs):
        raise RuntimeError("RAG utilities not available. Install: pip install langchain-community")

    def is_langchain_available():
        return False

    def is_llamaindex_available():
        return False

    def is_nvidia_available():
        return False

    def is_openai_available():
        return False

    def get_available_vectorstores():
        return []


def is_rag_available() -> bool:
    """Check if the RAG module is fully functional."""
    return _UTILS_AVAILABLE


__all__ = [
    # Base
    "BaseExample",
    # Configuration
    "AppConfig",
    "EmbeddingConfig",
    "LLMConfig",
    "RankingConfig",
    "RetrieverConfig",
    "TextSplitterConfig",
    "VectorStoreConfig",
    # Utilities
    "get_llm",
    "get_embedding_model",
    "get_config",
    "get_prompts",
    "get_text_splitter",
    "get_ranking_model",
    "get_vectorstore",
    "create_vectorstore_langchain",
    # Feature checks
    "is_rag_available",
    "is_langchain_available",
    "is_llamaindex_available",
    "is_nvidia_available",
    "is_openai_available",
    "get_available_vectorstores",
]

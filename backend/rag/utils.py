# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility functions for the LLM Chains."""
import logging
import os
from functools import lru_cache, wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)

# Track available features
_TORCH_AVAILABLE = False
_PSYCOPG2_AVAILABLE = False
_SQLALCHEMY_AVAILABLE = False
_LLAMAINDEX_AVAILABLE = False
_LANGCHAIN_AVAILABLE = False
_LANGCHAIN_NVIDIA_AVAILABLE = False
_FAISS_AVAILABLE = False
_MILVUS_AVAILABLE = False
_PGVECTOR_AVAILABLE = False

# Optional: torch for GPU detection
try:
    import torch

    _TORCH_AVAILABLE = True
except ImportError:
    logger.debug("torch not available - GPU detection disabled")
    torch = None

# Optional: psycopg2 for PostgreSQL
try:
    import psycopg2

    _PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.debug("psycopg2 not available - PostgreSQL support disabled")
    psycopg2 = None

# Optional: SQLAlchemy
try:
    from sqlalchemy.engine.url import make_url

    _SQLALCHEMY_AVAILABLE = True
except ImportError:
    logger.debug("SQLAlchemy not available")
    make_url = None

# Optional: LlamaIndex
try:
    from llama_index.core.indices import VectorStoreIndex
    from llama_index.core.postprocessor.types import BaseNodePostprocessor
    from llama_index.core.schema import MetadataMode
    from llama_index.core.utils import get_tokenizer
    from llama_index.core.callbacks import CallbackManager

    _LLAMAINDEX_AVAILABLE = True
except ImportError:
    logger.debug("LlamaIndex not available")
    VectorStoreIndex = None
    BaseNodePostprocessor = None
    MetadataMode = None
    get_tokenizer = None
    CallbackManager = None

# Optional: LlamaIndex embeddings and LLM wrappers
try:
    from llama_index.embeddings.langchain import LangchainEmbedding
    from llama_index.llms.langchain import LangChainLLM
except ImportError:
    LangchainEmbedding = None
    LangChainLLM = None

# Optional: LlamaIndex vector stores
try:
    from llama_index.vector_stores.milvus import MilvusVectorStore
    from llama_index.vector_stores.postgres import PGVectorStore as LlamaIndexPGVectorStore
except ImportError:
    MilvusVectorStore = None
    LlamaIndexPGVectorStore = None

# Core LangChain imports
try:
    from langchain_core.embeddings import Embeddings
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.documents.compressor import BaseDocumentCompressor

    _LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain core not available - RAG functionality limited")
    Embeddings = None
    BaseChatModel = None
    BaseDocumentCompressor = None

# Optional: LangChain text splitter
try:
    from langchain.text_splitter import SentenceTransformersTokenTextSplitter
except ImportError:
    SentenceTransformersTokenTextSplitter = None

# Optional: LangChain community embeddings
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None

# Optional: LangChain vectorstores
try:
    from langchain_core.vectorstores import VectorStore
except ImportError:
    VectorStore = None

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore

    _FAISS_AVAILABLE = True
except ImportError:
    FAISS = None
    InMemoryDocstore = None

try:
    from langchain_community.vectorstores import Milvus

    _MILVUS_AVAILABLE = True
except ImportError:
    Milvus = None

try:
    from langchain_community.vectorstores import PGVector

    _PGVECTOR_AVAILABLE = True
except ImportError:
    PGVector = None

# Optional: NVIDIA AI Endpoints
try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank

    _LANGCHAIN_NVIDIA_AVAILABLE = True
except ImportError:
    logger.debug("NVIDIA AI Endpoints not available")
    ChatNVIDIA = None
    NVIDIAEmbeddings = None
    NVIDIARerank = None

# Optional: OpenAI
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    _OPENAI_AVAILABLE = True
except ImportError:
    logger.debug("OpenAI not available")
    ChatOpenAI = None
    OpenAIEmbeddings = None
    _OPENAI_AVAILABLE = False

# Optional: FAISS index
try:
    from faiss import IndexFlatL2
except ImportError:
    IndexFlatL2 = None

# Import configuration
from backend.rag import configuration  # noqa: E402

if TYPE_CHECKING:
    from backend.rag.configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500


class LimitRetrievedNodesLength:
    """LlamaIndex chain filter to limit token lengths."""

    def __init__(self):
        if not _LLAMAINDEX_AVAILABLE:
            raise RuntimeError("LlamaIndex is required for LimitRetrievedNodesLength")

    def _postprocess_nodes(self, nodes: List = None, query_bundle=None) -> List:
        """Filter nodes by token limit."""
        if nodes is None:
            nodes = []

        included_nodes = []
        current_length = 0
        limit = DEFAULT_MAX_CONTEXT
        tokenizer = get_tokenizer() if get_tokenizer else lambda x: x.split()

        for node in nodes:
            content = node.get_content(metadata_mode=MetadataMode.LLM) if MetadataMode else str(node)
            current_length += len(tokenizer(content))
            if current_length > limit:
                break
            included_nodes.append(node)

        return included_nodes


def utils_cache(func: Callable) -> Callable:
    """Decorator to convert unhashable args to hashable ones."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        args_hashable = tuple(tuple(arg) if isinstance(arg, (list, dict, set)) else arg for arg in args)
        kwargs_hashable = {
            key: tuple(value) if isinstance(value, (list, dict, set)) else value for key, value in kwargs.items()
        }
        return func(*args_hashable, **kwargs_hashable)

    return wrapper


@lru_cache
def get_config() -> "ConfigWizard":
    """Parse the application configuration.

    Returns:
        ConfigWizard: Configuration object.
    """
    config_file = os.environ.get("APP_CONFIG_FILE", "/dev/null")
    config = configuration.AppConfig.from_file(config_file)
    if config:
        return config
    # Return default config if file not found
    return configuration.AppConfig.from_dict({})


@lru_cache
def get_prompts() -> Dict:
    """Retrieves prompt configurations from YAML file.

    Returns:
        Dict: Dictionary containing prompt configurations.
    """
    # Default config from backend/rag/prompts/
    default_config_path = os.path.join(os.path.dirname(__file__), "prompts", "prompt.yaml")
    default_config = {}
    if Path(default_config_path).exists():
        with open(default_config_path, "r") as file:
            default_config = yaml.safe_load(file) or {}

    # Load user-provided prompt.yaml
    config_file = os.environ.get("PROMPT_CONFIG_FILE", "")

    config = {}
    if config_file and Path(config_file).exists():
        with open(config_file, "r") as file:
            config = yaml.safe_load(file) or {}

    # Merge configs, prioritizing user config
    return _combine_dicts(default_config, config)


@utils_cache
@lru_cache()
def get_llm(**kwargs) -> Any:
    """Create the LLM connection.

    Supports NVIDIA AI Endpoints and OpenAI.

    Returns:
        LLM object from langchain.
    """
    settings = get_config()

    logger.info(f"Using {settings.llm.model_engine} as model engine. Model: {settings.llm.model_name}")

    if settings.llm.model_engine == "nvidia-ai-endpoints":
        if not _LANGCHAIN_NVIDIA_AVAILABLE:
            raise RuntimeError("langchain-nvidia-ai-endpoints is required but not installed")

        unused_params = [key for key in kwargs.keys() if key not in ["temperature", "top_p", "max_tokens"]]
        if unused_params:
            logger.warning(f"Unused parameters for NVIDIA: {unused_params}")

        if settings.llm.server_url:
            logger.info(f"Using LLM hosted at {settings.llm.server_url}")
            return ChatNVIDIA(
                base_url=f"http://{settings.llm.server_url}/v1",
                temperature=kwargs.get("temperature"),
                top_p=kwargs.get("top_p"),
                max_tokens=kwargs.get("max_tokens"),
            )
        else:
            logger.info(f"Using NVIDIA API catalog model: {settings.llm.model_name}")
            return ChatNVIDIA(
                model=settings.llm.model_name,
                temperature=kwargs.get("temperature"),
                top_p=kwargs.get("top_p"),
                max_tokens=kwargs.get("max_tokens"),
            )

    elif settings.llm.model_engine == "openai":
        if not _OPENAI_AVAILABLE:
            raise RuntimeError("langchain-openai is required but not installed")

        return ChatOpenAI(
            model=settings.llm.model_name or "gpt-4o-mini",
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens"),
        )

    else:
        raise RuntimeError(
            f"Unsupported LLM engine: {settings.llm.model_engine}. " "Supported: nvidia-ai-endpoints, openai"
        )


@lru_cache
def get_embedding_model() -> Any:
    """Create the embedding model.

    Returns:
        Embeddings object from langchain.
    """
    settings = get_config()

    model_kwargs = {"device": "cpu"}
    if _TORCH_AVAILABLE and torch.cuda.is_available():
        model_kwargs["device"] = "cuda:0"

    logger.info(f"Using {settings.embeddings.model_engine} for embeddings: {settings.embeddings.model_name}")

    if settings.embeddings.model_engine == "huggingface":
        if HuggingFaceEmbeddings is None:
            raise RuntimeError("langchain-community with HuggingFaceEmbeddings is required")
        return HuggingFaceEmbeddings(
            model_name=settings.embeddings.model_name,
            model_kwargs=model_kwargs,
            encode_kwargs={"normalize_embeddings": False},
        )

    elif settings.embeddings.model_engine == "nvidia-ai-endpoints":
        if not _LANGCHAIN_NVIDIA_AVAILABLE:
            raise RuntimeError("langchain-nvidia-ai-endpoints is required")

        if settings.embeddings.server_url:
            logger.info(f"Using embedding model at {settings.embeddings.server_url}")
            return NVIDIAEmbeddings(base_url=f"http://{settings.embeddings.server_url}/v1", truncate="END")
        else:
            logger.info(f"Using NVIDIA embedding model: {settings.embeddings.model_name}")
            return NVIDIAEmbeddings(model=settings.embeddings.model_name, truncate="END")

    elif settings.embeddings.model_engine == "openai":
        if not _OPENAI_AVAILABLE:
            raise RuntimeError("langchain-openai is required")
        return OpenAIEmbeddings(model=settings.embeddings.model_name or "text-embedding-3-small")

    else:
        raise RuntimeError(
            f"Unsupported embedding engine: {settings.embeddings.model_engine}. "
            "Supported: huggingface, nvidia-ai-endpoints, openai"
        )


@lru_cache
def get_ranking_model() -> Optional[Any]:
    """Create the ranking/reranking model.

    Returns:
        Reranker model or None if not configured.
    """
    settings = get_config()

    try:
        if settings.ranking.model_engine == "nvidia-ai-endpoints":
            if not _LANGCHAIN_NVIDIA_AVAILABLE:
                logger.warning("NVIDIA AI Endpoints not available for ranking")
                return None

            if settings.ranking.server_url:
                logger.info(f"Using ranking model at {settings.ranking.server_url}")
                return NVIDIARerank(
                    base_url=f"http://{settings.ranking.server_url}/v1", top_n=settings.retriever.top_k, truncate="END"
                )
            elif settings.ranking.model_name:
                logger.info(f"Using ranking model: {settings.ranking.model_name}")
                return NVIDIARerank(model=settings.ranking.model_name, top_n=settings.retriever.top_k, truncate="END")
        else:
            logger.debug(f"Ranking engine {settings.ranking.model_engine} not supported")
    except Exception as e:
        logger.error(f"Failed to initialize ranking model: {e}")

    return None


def get_text_splitter() -> Any:
    """Return the text splitter instance.

    Returns:
        Text splitter for chunking documents.
    """
    if SentenceTransformersTokenTextSplitter is None:
        raise RuntimeError("langchain with SentenceTransformersTokenTextSplitter is required")

    settings = get_config()
    embedding_model_name = settings.text_splitter.model_name

    return SentenceTransformersTokenTextSplitter(
        model_name=embedding_model_name,
        tokens_per_chunk=settings.text_splitter.chunk_size - 2,
        chunk_overlap=settings.text_splitter.chunk_overlap,
    )


def create_vectorstore_langchain(document_embedder: Any, collection_name: str = "") -> Any:
    """Create a vectorstore for LangChain.

    Args:
        document_embedder: Embedding model.
        collection_name: Name of the collection.

    Returns:
        VectorStore object.
    """
    config = get_config()

    if not collection_name:
        collection_name = os.getenv("COLLECTION_NAME", "vector_db")

    vectorstore_name = config.vector_store.name
    logger.info(f"Creating {vectorstore_name} vectorstore: {collection_name}")

    if vectorstore_name == "faiss":
        if not _FAISS_AVAILABLE or IndexFlatL2 is None:
            raise RuntimeError("faiss-cpu and langchain-community are required for FAISS")
        return FAISS(document_embedder, IndexFlatL2(config.embeddings.dimensions), InMemoryDocstore(), {})

    elif vectorstore_name == "pgvector":
        if not _PGVECTOR_AVAILABLE:
            raise RuntimeError("pgvector and langchain-community are required")
        db_name = os.getenv("POSTGRES_DB", "vectordb")
        connection_string = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', '')}@"
            f"{config.vector_store.url}/{db_name}"
        )
        return PGVector(
            collection_name=collection_name,
            connection_string=connection_string,
            embedding_function=document_embedder,
        )

    elif vectorstore_name == "milvus":
        if not _MILVUS_AVAILABLE:
            raise RuntimeError("pymilvus and langchain-community are required for Milvus")
        url = urlparse(config.vector_store.url)
        return Milvus(
            document_embedder,
            connection_args={"host": url.hostname, "port": url.port or 19530},
            collection_name=collection_name,
            index_params={
                "index_type": config.vector_store.index_type,
                "metric_type": "L2",
                "nlist": config.vector_store.nlist,
            },
            search_params={"nprobe": config.vector_store.nprobe},
            auto_id=True,
        )

    else:
        raise ValueError(f"Unsupported vector store: {vectorstore_name}. Supported: faiss, pgvector, milvus")


def get_vectorstore(vectorstore: Optional[Any], document_embedder: Any) -> Any:
    """Get or create a vectorstore.

    Args:
        vectorstore: Existing vectorstore or None.
        document_embedder: Embedding model.

    Returns:
        VectorStore object.
    """
    if vectorstore is None:
        return create_vectorstore_langchain(document_embedder)
    return vectorstore


def _combine_dicts(dict_a: Dict[str, Any], dict_b: Dict[str, Any]) -> Dict[str, Any]:
    """Combine two dictionaries recursively, prioritizing dict_b.

    Args:
        dict_a: First dictionary.
        dict_b: Second dictionary (takes priority).

    Returns:
        Combined dictionary.
    """
    combined = dict_a.copy()

    for key, value_b in dict_b.items():
        if key in combined:
            value_a = combined[key]
            if isinstance(value_a, dict) and isinstance(value_b, dict):
                combined[key] = _combine_dicts(value_a, value_b)
            else:
                combined[key] = value_b
        else:
            combined[key] = value_b

    return combined


# Feature availability checks
def is_llamaindex_available() -> bool:
    """Check if LlamaIndex is available."""
    return _LLAMAINDEX_AVAILABLE


def is_langchain_available() -> bool:
    """Check if LangChain is available."""
    return _LANGCHAIN_AVAILABLE


def is_nvidia_available() -> bool:
    """Check if NVIDIA AI Endpoints are available."""
    return _LANGCHAIN_NVIDIA_AVAILABLE


def is_openai_available() -> bool:
    """Check if OpenAI is available."""
    return _OPENAI_AVAILABLE


def get_available_vectorstores() -> List[str]:
    """Get list of available vectorstore backends."""
    available = []
    if _FAISS_AVAILABLE:
        available.append("faiss")
    if _PGVECTOR_AVAILABLE:
        available.append("pgvector")
    if _MILVUS_AVAILABLE:
        available.append("milvus")
    return available

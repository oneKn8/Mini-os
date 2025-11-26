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

"""The definition of the application configuration."""
from backend.rag.configuration_wizard import ConfigWizard, configclass, configfield


@configclass
class VectorStoreConfig(ConfigWizard):
    """Configuration class for the Vector Store connection.

    :cvar name: Name of vector store (faiss, pgvector, milvus)
    :cvar url: URL of Vector Store
    """

    name: str = configfield(
        "name",
        default="faiss",
        help_txt="The name of vector store. Supported: faiss, pgvector, milvus",
    )
    url: str = configfield(
        "url",
        default="http://localhost:19530",
        help_txt="The host URL of the vector store (for milvus/pgvector)",
    )
    nlist: int = configfield(
        "nlist",
        default=64,
        help_txt="Number of cluster units (for Milvus IVF indexes)",
    )
    nprobe: int = configfield(
        "nprobe",
        default=16,
        help_txt="Number of units to query (for Milvus IVF indexes)",
    )
    index_type: str = configfield(
        "index_type",
        default="IVF_FLAT",
        help_txt="Index type for vector db (e.g., IVF_FLAT, GPU_IVF_FLAT)",
    )


@configclass
class LLMConfig(ConfigWizard):
    """Configuration class for the LLM connection.

    :cvar server_url: The location of the LLM server (for self-hosted models).
    :cvar model_name: The name of the model.
    :cvar model_engine: The LLM provider (nvidia-ai-endpoints, openai).
    """

    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The URL of self-hosted LLM server (optional, for NIM deployments)",
    )
    model_name: str = configfield(
        "model_name",
        default="gpt-4o-mini",
        help_txt="The name of the LLM model",
    )
    model_engine: str = configfield(
        "model_engine",
        default="openai",
        help_txt="The LLM provider. Supported: nvidia-ai-endpoints, openai",
    )
    model_name_pandas_ai: str = configfield(
        "model_name_pandas_ai",
        default="gpt-4o-mini",
        help_txt="The model to use with PandasAI agent",
    )


@configclass
class TextSplitterConfig(ConfigWizard):
    """Configuration class for the Text Splitter.

    :cvar chunk_size: Number of tokens per chunk.
    :cvar chunk_overlap: Overlapping tokens between chunks.
    """

    model_name: str = configfield(
        "model_name",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help_txt="The Sentence Transformer model for tokenization",
    )
    chunk_size: int = configfield(
        "chunk_size",
        default=512,
        help_txt="Maximum tokens per chunk",
    )
    chunk_overlap: int = configfield(
        "chunk_overlap",
        default=50,
        help_txt="Overlapping tokens between chunks",
    )


@configclass
class EmbeddingConfig(ConfigWizard):
    """Configuration class for Embeddings.

    :cvar model_name: The embedding model name.
    :cvar model_engine: The embedding provider.
    """

    model_name: str = configfield(
        "model_name",
        default="text-embedding-3-small",
        help_txt="The embedding model name",
    )
    model_engine: str = configfield(
        "model_engine",
        default="openai",
        help_txt="The embedding provider. Supported: huggingface, nvidia-ai-endpoints, openai",
    )
    dimensions: int = configfield(
        "dimensions",
        default=1536,
        help_txt="The embedding vector dimensions",
    )
    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The URL of self-hosted embedding server (optional)",
    )


@configclass
class RankingConfig(ConfigWizard):
    """Configuration class for Re-ranking.

    :cvar model_name: The ranking model name.
    :cvar model_engine: The ranking provider.
    """

    model_name: str = configfield(
        "model_name",
        default="",
        help_txt="The ranking/reranking model name (optional)",
    )
    model_engine: str = configfield(
        "model_engine",
        default="nvidia-ai-endpoints",
        help_txt="The ranking provider. Supported: nvidia-ai-endpoints",
    )
    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The URL of self-hosted ranking server (optional)",
    )


@configclass
class RetrieverConfig(ConfigWizard):
    """Configuration class for the Retrieval pipeline.

    :cvar top_k: Number of documents to retrieve.
    :cvar score_threshold: Minimum similarity score threshold.
    """

    top_k: int = configfield(
        "top_k",
        default=4,
        help_txt="Number of documents to retrieve",
    )
    score_threshold: float = configfield(
        "score_threshold",
        default=0.25,
        help_txt="Minimum similarity score for retrieved documents",
    )
    nr_url: str = configfield(
        "nr_url",
        default="",
        help_txt="The NVIDIA Retriever microservice URL (optional)",
    )
    nr_pipeline: str = configfield(
        "nr_pipeline",
        default="ranked_hybrid",
        help_txt="The retriever pipeline type: ranked_hybrid or hybrid",
    )


@configclass
class AppConfig(ConfigWizard):
    """Main application configuration.

    All settings can be overridden via:
    - Environment variables (e.g., APP_LLM_MODELENGINE=openai)
    - Config file specified by APP_CONFIG_FILE env var
    """

    vector_store: VectorStoreConfig = configfield(
        "vector_store",
        env=False,
        help_txt="Vector store configuration",
        default=VectorStoreConfig(),
    )
    llm: LLMConfig = configfield(
        "llm",
        env=False,
        help_txt="LLM configuration",
        default=LLMConfig(),
    )
    text_splitter: TextSplitterConfig = configfield(
        "text_splitter",
        env=False,
        help_txt="Text splitter configuration",
        default=TextSplitterConfig(),
    )
    embeddings: EmbeddingConfig = configfield(
        "embeddings",
        env=False,
        help_txt="Embedding model configuration",
        default=EmbeddingConfig(),
    )
    ranking: RankingConfig = configfield(
        "ranking",
        env=False,
        help_txt="Ranking/reranking model configuration",
        default=RankingConfig(),
    )
    retriever: RetrieverConfig = configfield(
        "retriever",
        env=False,
        help_txt="Retriever pipeline configuration",
        default=RetrieverConfig(),
    )

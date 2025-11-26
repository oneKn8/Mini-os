# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Observability module for RAG tracing with OpenTelemetry."""

from backend.rag.observability.langchain.opentelemetry_callback import (
    OpenTelemetryCallbackHandler as LangchainOpenTelemetryCallbackHandler,
)
from backend.rag.observability.llamaindex.opentelemetry_callback import (
    OpenTelemetryCallbackHandler as LlamaIndexOpenTelemetryCallbackHandler,
)

__all__ = [
    "LangchainOpenTelemetryCallbackHandler",
    "LlamaIndexOpenTelemetryCallbackHandler",
]

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""LlamaIndex observability module."""

from backend.rag.observability.llamaindex.opentelemetry_callback import OpenTelemetryCallbackHandler

__all__ = ["OpenTelemetryCallbackHandler"]

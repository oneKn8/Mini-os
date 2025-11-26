# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Langchain observability module."""

from backend.rag.observability.langchain.opentelemetry_callback import OpenTelemetryCallbackHandler

__all__ = ["OpenTelemetryCallbackHandler"]

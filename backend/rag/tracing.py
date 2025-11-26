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

"""Module for configuring objects used to create OpenTelemetry traces."""

import logging
import os
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Track what's available
_LANGCHAIN_AVAILABLE = False
_LLAMAINDEX_AVAILABLE = False
_OTEL_AVAILABLE = False

# Try importing LangChain callback handler
try:
    from langchain.callbacks.base import BaseCallbackHandler as langchain_base_cb_handler

    _LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.debug(f"LangChain not available: {e}")
    langchain_base_cb_handler = None

# Try importing LlamaIndex callback handler
try:
    from llama_index.core.callbacks.simple_llm_handler import SimpleLLMHandler as llama_index_base_cb_handler

    _LLAMAINDEX_AVAILABLE = True
except ImportError as e:
    logger.debug(f"LlamaIndex not available: {e}")
    llama_index_base_cb_handler = None

# Try importing OpenTelemetry
try:
    from opentelemetry import context, trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.propagate import get_global_textmap, set_global_textmap
    from opentelemetry.propagators.composite import CompositePropagator
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    _OTEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenTelemetry not available, tracing disabled: {e}")
    context = None
    trace = None

# Initialize tracing components
tracer = None
propagator = None
langchain_cb_handler = None
llama_index_cb_handler = None

if _OTEL_AVAILABLE:
    # Configure tracer used by the Chain Server to create spans
    resource = Resource.create({SERVICE_NAME: "chain-server"})
    provider = TracerProvider(resource=resource)

    if os.environ.get("ENABLE_TRACING") == "true":
        try:
            processor = SimpleSpanProcessor(OTLPSpanExporter())
            provider.add_span_processor(processor)
            logger.info("OpenTelemetry tracing enabled with OTLP exporter")
        except Exception as e:
            logger.warning(f"Failed to configure OTLP exporter: {e}")

    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("chain-server")

    if os.environ.get("ENABLE_TRACING") == "true":
        # Configure Propagator for trace context
        propagator = TraceContextTextMapPropagator()

        # Configure Langchain OpenTelemetry callback handler
        if _LANGCHAIN_AVAILABLE:
            try:
                from backend.rag.observability.langchain import opentelemetry_callback as langchain_otel_cb

                langchain_cb_handler = langchain_otel_cb.OpenTelemetryCallbackHandler(tracer)
            except Exception as e:
                logger.warning(f"Failed to configure LangChain OTEL handler: {e}")
                langchain_cb_handler = langchain_base_cb_handler() if langchain_base_cb_handler else None

        # Configure LlamaIndex OpenTelemetry callback handler
        if _LLAMAINDEX_AVAILABLE:
            try:
                from backend.rag.observability.llamaindex import opentelemetry_callback as llama_index_otel_cb

                llama_index_cb_handler = llama_index_otel_cb.OpenTelemetryCallbackHandler(tracer)
            except Exception as e:
                logger.warning(f"Failed to configure LlamaIndex OTEL handler: {e}")
                llama_index_cb_handler = llama_index_base_cb_handler() if llama_index_base_cb_handler else None
    else:
        propagator = CompositePropagator([])  # No-op propagator
        if _LANGCHAIN_AVAILABLE and langchain_base_cb_handler:
            langchain_cb_handler = langchain_base_cb_handler()
        if _LLAMAINDEX_AVAILABLE and llama_index_base_cb_handler:
            llama_index_cb_handler = llama_index_base_cb_handler()

    set_global_textmap(propagator)


def llamaindex_instrumentation_wrapper(func: Callable) -> Callable:
    """Wrapper function to perform LlamaIndex instrumentation."""
    if not _OTEL_AVAILABLE or not _LLAMAINDEX_AVAILABLE:
        return func

    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if request and hasattr(request, "headers"):
            ctx = get_global_textmap().extract(request.headers)
            if ctx is not None:
                context.attach(ctx)
        result = func(*args, **kwargs)
        return await result

    return wrapper


def langchain_instrumentation_method_wrapper(func: Callable) -> Callable:
    """Wrapper function to perform Langchain instrumentation."""
    if not _OTEL_AVAILABLE or not _LANGCHAIN_AVAILABLE or langchain_cb_handler is None:
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(langchain_cb_handler, *args, **kwargs)
        return result

    return wrapper


def langchain_instrumentation_class_wrapper(cls: type) -> type:
    """Wrapper class to perform Langchain instrumentation."""
    if not _OTEL_AVAILABLE or not _LANGCHAIN_AVAILABLE or langchain_cb_handler is None:
        return cls

    class WrapperClass(cls):
        def __init__(self, *args, **kwargs):
            self.cb_handler = langchain_cb_handler
            super().__init__(*args, **kwargs)

    return WrapperClass


def inject_context(ctx: Any) -> dict:
    """Inject trace context into a carrier dict."""
    carrier = {}
    if _OTEL_AVAILABLE:
        get_global_textmap().inject(carrier, context=ctx)
    return carrier


def instrumentation_wrapper(func: Callable) -> Callable:
    """Wrapper function to perform general instrumentation."""
    if not _OTEL_AVAILABLE or tracer is None:
        return func

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        span_name = func.__name__
        span = tracer.start_span(span_name)
        span_ctx = trace.set_span_in_context(span)
        carrier = inject_context(span_ctx)
        for kw in kwargs:
            try:
                span.set_attribute(str(kw), str(kwargs[kw]))
            except Exception:
                pass  # Skip attributes that can't be serialized
        result = func(self, carrier, *args, **kwargs)
        span.end()
        return result

    return wrapper


# Export availability flags for other modules
def is_tracing_available() -> bool:
    """Check if OpenTelemetry tracing is available and configured."""
    return _OTEL_AVAILABLE and tracer is not None


def is_langchain_available() -> bool:
    """Check if LangChain is available."""
    return _LANGCHAIN_AVAILABLE


def is_llamaindex_available() -> bool:
    """Check if LlamaIndex is available."""
    return _LLAMAINDEX_AVAILABLE

#!/bin/bash

# Thin wrapper to keep existing workflows intact.
# Delegates to the native stop script which knows how to
# tear down the uvicorn/vite processes started by ./start.sh.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$SCRIPT_DIR/stop_native.sh" "$@"

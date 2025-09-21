#!/bin/bash


echo ""
echo "=============================="
echo "Running LLDB tests"
echo "=============================="
echo ""

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_DIR="${SCRIPT_DIR}/python3.11"
PYTHON="${PYTHON_DIR}/bin/python3"

LLDB="${SCRIPT_DIR}/build-linux-x86_64/install/bin/lldb"

export PYTHONPATH=$("${LLDB}" -P)

echo "PYTHONPATH == ${PYTHONPATH}"
"$PYTHON" -c 'import lldb; print("hello")'


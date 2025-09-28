#!/bin/bash


echo ""
echo "=============================="
echo "Running LLDB tests"
echo "=============================="
echo ""

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ANDROID_NDK_HOME="${SCRIPT_DIR}/ndk/android-ndk-r28c"

# This is what we'd normally use.
#PYTHON_DIR="${SCRIPT_DIR}/python3.11"
# For now, using the LLDB from NDK, and using Python from NDK.
PYTHON_DIR="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/python3"


export PYTHONPATH="${PYTHON_DIR}/../lib/python3.11/site-packages"
#LLDB="${SCRIPT_DIR}/build-linux-x86_64/install/bin/lldb"
#export PYTHONPATH=$("${LLDB}" -P)

#export PYTHONPATH="${SCRIPT_DIR}/build-linux-x86_64/install/lib/python3.11/site-packages"

# TO fix missing libedit.so
export LD_LIBRARY_PATH="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/lib:${LD_LIBRARY_PATH}"

PYTHON="${PYTHON_DIR}/bin/python3"
"$PYTHON" test.py


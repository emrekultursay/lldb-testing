#!/bin/bash


echo ""
echo "=============================="
echo "Running LLDB tests"
echo "=============================="
echo ""

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ANDROID_NDK_HOME="${SCRIPT_DIR}/ndk/android-ndk-r28c"

LLDB="${SCRIPT_DIR}/build-linux-x86_64/install/bin/lldb"
chmod +x "${LLDB}"

PYTHON_DIR="${SCRIPT_DIR}/python3.11"
PYTHON="${PYTHON_DIR}/bin/python3"

# We set PYTHONPATH this way so that Python can execute `import lldb`
export PYTHONPATH=$("${LLDB}" -P)

"$PYTHON" test.py



# If we want to use the Python and LLDB from the NDK, replace the above with
# these:
#PYTHON_DIR="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/python3"
# To fix missing libedit.so
#export LD_LIBRARY_PATH="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/lib:${LD_LIBRARY_PATH}"
#"$PYTHON" test.py

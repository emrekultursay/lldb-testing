#!/bin/bash

ANDROID_ABI=${ANDROID_ABI:-arm64-v8a}

echo ""
echo "=============================="
echo "Running LLDB tests"
echo "=============================="
echo ""

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ANDROID_NDK_HOME="${SCRIPT_DIR}/ndk/android-ndk-r28c"
JAVA_HOME="${SCRIPT_DIR}/jdk"

LLDB="${SCRIPT_DIR}/build-linux-x86_64/install/bin/lldb"
chmod +x "${LLDB}"

PYTHON_DIR="${SCRIPT_DIR}/python3.11"
PYTHON="${PYTHON_DIR}/bin/python3"

# We set PYTHONPATH this way so that Python can execute `import lldb`
export PYTHONHOME="${SCRIPT_DIR}/python3.11"
export PYTHONPATH=$("${LLDB}" -P)

# TEST_REPEAT runs the test several times, e.g. to measure flakiness.
TEST_REPEAT="${TEST_REPEAT:-1}"
FAILURES=0
for i in $(seq 1 "${TEST_REPEAT}"); do
  echo "=== Run ${i}/${TEST_REPEAT} (${ANDROID_ABI})"
  if ! "$PYTHON" test.py --android_abi="${ANDROID_ABI}"; then
    FAILURES=$((FAILURES + 1))
  fi
done
echo "=== ${ANDROID_ABI}: ${FAILURES}/${TEST_REPEAT} runs failed"
[[ "${FAILURES}" -eq 0 ]]



# If we want to use the Python and LLDB from the NDK, replace the above with
# these:
#PYTHON_DIR="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/python3"
# To fix missing libedit.so
#export LD_LIBRARY_PATH="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/lib:${LD_LIBRARY_PATH}"
#"$PYTHON" test.py

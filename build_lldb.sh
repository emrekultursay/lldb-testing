#!/bin/bash

echo ""
echo "=============================="
echo "Building LLDB for linux-x86_64"
echo "=============================="
echo ""

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CMAKE="${SCRIPT_DIR}/cmake/3.22.1/bin/cmake"
NINJA="${SCRIPT_DIR}/cmake/3.22.1/bin/ninja"
ANDROID_NDK_HOME="${SCRIPT_DIR}/ndk/android-ndk-r28c"
PYTHON_DIR="${SCRIPT_DIR}/python3.11"

CMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE:-Debug}"

BUILD_DIR="${SCRIPT_DIR}/build-linux-x86_64"
OUT_DIR="${BUILD_DIR}/out"
mkdir -p "${BUILD_DIR}"
mkdir -p "${OUT_DIR}"


# Note: Python requires swig. We assume it's installed on the local machine.

pushd "${BUILD_DIR}"
$CMAKE ../llvm-project/llvm -G Ninja \
  -B "${OUT_DIR}" \
  -DCMAKE_MAKE_PROGRAM="${NINJA}" \
  -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
  -DLLVM_ENABLE_PROJECTS="clang;lldb" \
  -DLLDB_ENABLE_PYTHON=ON \
  -DPython3_LIBRARIES="${PYTHON_DIR}/lib/libpython3.11.so" \
  -DPython3_INCLUDE_DIRS="${PYTHON_DIR}/include/python3.11" \
  -DPython3_EXECUTABLE="${PYTHON_DIR}/bin/python3" \
  -DLLDB_ENABLE_LIBEDIT=0 \
  -DLLDB_ENABLE_CURSES=0 \
  -DLLVM_TARGETS_TO_BUILD="X86" \
  -DLLVM_HOST_TRIPLE="x86_64-unknown-linux-gnu"

pushd "${OUT_DIR}"
time "${NINJA}" lldb

# TODO: enable stripping.
#echo "Stripping lldb binary to reduce size"
#"${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip bin/lldb"

echo ""
echo "=============================="
echo ""

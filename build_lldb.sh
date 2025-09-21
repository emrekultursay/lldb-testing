#!/bin/bash

echo ""
echo "=============================="
echo "Building LLDB for linux-x86_64"
echo "=============================="
echo ""

set -x

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CMAKE="${SCRIPT_DIR}/cmake/3.22.1/bin/cmake"
NINJA="${SCRIPT_DIR}/cmake/3.22.1/bin/ninja"
ANDROID_NDK_HOME="${SCRIPT_DIR}/ndk/android-ndk-r28c"

CMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE:-Debug}"

BUILD_DIR="${SCRIPT_DIR}/build-linux-x86_64"
OUT_DIR="${BUILD_DIR}/out"
mkdir -p "${BUILD_DIR}"
mkdir -p "${OUT_DIR}"


# TODO: Enable Python so that we can write python-based tests.

pushd "${BUILD_DIR}"
$CMAKE ../llvm-project/llvm -G Ninja \
  -B "${OUT_DIR}" \
  -DCMAKE_MAKE_PROGRAM="${NINJA}" \
  -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
  -DLLVM_ENABLE_PROJECTS="clang;lld;lldb" \
  -DLLDB_ENABLE_PYTHON=0 \
  -DLLDB_ENABLE_LIBEDIT=0 \
  -DLLDB_ENABLE_CURSES=0 \
  -DCMAKE_TOOLCHAIN_FILE="${ANDROID_NDK_HOME}/build/cmake/android.toolchain.cmake" \
  -DCROSS_TOOLCHAIN_FLAGS_NATIVE='-DCMAKE_C_COMPILER=cc;-DCMAKE_CXX_COMPILER=c++'

pushd "${OUT_DIR}"
time "${NINJA}" lldb

echo "Stripping lldb-server binary to reduce size"
"${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip bin/lldb"

echo ""
echo "=============================="
echo ""

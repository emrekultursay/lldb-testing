#!/bin/bash

ANDROID_ABI=${ANDROID_ABI:-arm64-v8a}

echo ""
echo "=============================="
echo "Building lldb-server for ${ANDROID_ABI}"
echo "=============================="
echo ""

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Cross compiling
CMAKE="${SCRIPT_DIR}/cmake/3.22.1/bin/cmake"
NINJA="${SCRIPT_DIR}/cmake/3.22.1/bin/ninja"
ANDROID_NDK_HOME="${SCRIPT_DIR}/ndk/android-ndk-r28c"

ANDROID_PLATFORM=android-24

if [[ "$ANDROID_ABI" == "arm64-v8a" ]]; then
  LLVM_HOST_TRIPLE=aarch64-unknown-linux-android
  LLVM_TARGET=AArch64
elif [[ "$ANDROID_ABI" == "armeabi-v7a" ]]; then
  LLVM_HOST_TRIPLE=arm-unknown-linux-androideabi
  LLVM_TARGET=ARM
elif [[ "$ANDROID_ABI" == "x86_64" ]]; then
  LLVM_HOST_TRIPLE=x86_64-unknown-linux-android
  LLVM_TARGET=X86
else
  echo "Invalid ANDROID_ABI=$ANDROID_ABI"
  exit 1
fi


CMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}"

BUILD_DIR="${SCRIPT_DIR}/build-${ANDROID_ABI}"
OUT_DIR="${BUILD_DIR}/out"
mkdir -p "${BUILD_DIR}"
mkdir -p "${OUT_DIR}"

# Reuse the host-built tablegen tools (llvm-tblgen, clang-tblgen, lldb-tblgen, ...)
# from build_lldb.sh instead of building them again for each ABI. LLVM falls back
# to building any tool that is missing from this directory.
# LLVM_TABLEGEN and CLANG_TABLEGEN are CMake cache variables, so they must be
# passed explicitly to take effect on an existing build directory.
NATIVE_TOOL_DIR="${SCRIPT_DIR}/build-linux-x86_64/out/bin"
TABLEGEN_FLAGS=()
if [[ -x "${NATIVE_TOOL_DIR}/llvm-tblgen" && -x "${NATIVE_TOOL_DIR}/clang-tblgen" ]]; then
  TABLEGEN_FLAGS=(
    -DLLVM_TABLEGEN="${NATIVE_TOOL_DIR}/llvm-tblgen"
    -DCLANG_TABLEGEN="${NATIVE_TOOL_DIR}/clang-tblgen"
  )
else
  echo "Host tablegen tools not found in ${NATIVE_TOOL_DIR}; they will be built."
fi

# Use ccache if available. CI keeps its cache outside the workspace, so it
# survives the checkout cleanup between runs.
CCACHE_FLAGS=()
if command -v ccache >/dev/null; then
  CCACHE_FLAGS=(
    -DCMAKE_C_COMPILER_LAUNCHER=ccache
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
  )
fi

pushd "${BUILD_DIR}"
$CMAKE ../llvm-project/llvm -G Ninja \
  -B "${OUT_DIR}" \
  -DCMAKE_MAKE_PROGRAM="${NINJA}" \
  -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
  -DLLVM_ENABLE_PROJECTS="clang;lldb" \
  -DLLDB_ENABLE_PYTHON=0 \
  -DLLDB_ENABLE_LIBEDIT=0 \
  -DLLDB_ENABLE_CURSES=0 \
  -DCMAKE_TOOLCHAIN_FILE="${ANDROID_NDK_HOME}/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI="${ANDROID_ABI}" \
  -DANDROID_PLATFORM="${ANDROID_PLATFORM}" \
  -DANDROID_ALLOW_UNDEFINED_SYMBOLS=On \
  -DLLVM_HOST_TRIPLE="${LLVM_HOST_TRIPLE}" \
  -DLLVM_TARGETS_TO_BUILD="${LLVM_TARGET}" \
  -DLLVM_NATIVE_TOOL_DIR="${NATIVE_TOOL_DIR}" \
  -DLLVM_INCLUDE_TESTS=OFF \
  -DLLVM_INCLUDE_BENCHMARKS=OFF \
  -DLLVM_INCLUDE_EXAMPLES=OFF \
  -DCLANG_INCLUDE_TESTS=OFF \
  -DLLDB_INCLUDE_TESTS=OFF \
  -DCMAKE_DISABLE_PRECOMPILE_HEADERS=ON \
  "${TABLEGEN_FLAGS[@]}" \
  "${CCACHE_FLAGS[@]}" \
  -DCROSS_TOOLCHAIN_FLAGS_NATIVE='-DCMAKE_C_COMPILER=cc;-DCMAKE_CXX_COMPILER=c++'

pushd "${OUT_DIR}"
time "${NINJA}" lldb-server

echo "Stripping lldb-server binary to reduce size"
"${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" bin/lldb-server

echo ""
echo "=============================="
echo ""

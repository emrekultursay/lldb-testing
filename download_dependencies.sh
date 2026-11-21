#!/bin/bash

set -ex

echo ""
echo "=============================="
echo "Downloading dependencies..."
echo "=============================="
echo ""


SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CMAKE_DIR="${SCRIPT_DIR}/cmake/3.31.6"
if [[ ! -d "${CMAKE_DIR}" ]]; then
  wget --progress=dot:giga https://dl.google.com/android/repository/cmake-3.31.6-linux.zip
  mkdir -p "${CMAKE_DIR}"
  unzip -q cmake-3.31.6-linux.zip -d "${CMAKE_DIR}"
  rm cmake-3.31.6-linux.zip
fi

NDK_DIR="${SCRIPT_DIR}/ndk"
if [[ ! -d "${NDK_DIR}" ]]; then
  wget --progress=dot:giga https://dl.google.com/android/repository/android-ndk-r28c-linux.zip
  mkdir -p "${NDK_DIR}"
  unzip -q android-ndk-r28c-linux.zip -d "${NDK_DIR}"
  rm android-ndk-r28c-linux.zip
fi

# Pinned JDK (Temurin 17.0.21.1+2), verified by SHA-256.
JDK_DIR="${SCRIPT_DIR}/jdk"
JDK_URL="https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21.1%2B2/OpenJDK17U-jdk_x64_linux_hotspot_17.0.21.1_2.tar.gz"
JDK_SHA256=0b0ac5eab6db6abaec68c9913bcddb31321e5da411c45073d520d9c125e6f7b4
if [[ ! -d "${JDK_DIR}" ]]; then
  curl -fL "${JDK_URL}" -o jdk.tar.gz
  echo "${JDK_SHA256}  jdk.tar.gz" | sha256sum -c -
  mkdir -p "${JDK_DIR}"
  tar -xzf jdk.tar.gz -C "${JDK_DIR}" --strip-components=1
  rm jdk.tar.gz
fi


#!/bin/bash


set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

"${SCRIPT_DIR}/download_dependencies.sh"


ANDROID_ABI=arm64-v8a "${SCRIPT_DIR}/build_lldb_server.sh"
ANDROID_ABI=armeabi-v7a "${SCRIPT_DIR}/build_lldb_server.sh"

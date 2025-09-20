#!/bin/bash

set -e

wget https://dl.google.com/android/repository/cmake-3.22.1-linux.zip
mkdir -p cmake/3.22.1/
unzip cmake-3.22.1-linux.zip -d cmake/3.22.1/
rm cmake-3.22.1-linux.zip

wget https://dl.google.com/android/repository/android-ndk-r28c-linux.zip
mkdir -p ndk/28.2.13676358
unzip android-ndk-r28c-linux.zip -d ndk/28.2.13676358
rm android-ndk-r28c-linux.zip



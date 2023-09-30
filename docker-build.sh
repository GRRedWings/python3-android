#!/bin/bash

set -e
set -x

apt-get update -y
apt-get install -y xz-utils autoconf-archive autoconf automake cmake gawk gettext git gcc make patch pkg-config

export ANDROID_NDK=/android-ndk

if [ ! -d "$ANDROID_NDK" ] ; then
    # In general we don't want download NDK for every build, but it is simpler to do it here
    # for CI builds
    NDK_VER=r25b
    apt-get install -y wget zip
    wget --no-verbose https://dl.google.com/android/repository/android-ndk-$NDK_VER-linux.zip
    unzip android-ndk-${NDK_VER}-linux.zip
    ANDROID_NDK=/android-ndk-$NDK_VER
fi

cd /python3-android

./build.sh "$@"

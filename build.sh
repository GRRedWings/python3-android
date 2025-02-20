#!/bin/bash

set -e
set -x

THIS_DIR="$PWD"

PYVER=3.13.0
SRCDIR=src/Python-$PYVER

COMMON_ARGS="--arch ${ARCH:-arm} --api ${ANDROID_API:-30}"

if [ ! -d $SRCDIR ]; then
    mkdir -p src
    pushd src
    curl -vLO https://www.python.org/ftp/python/$PYVER/Python-$PYVER.tar.xz

    # Use --no-same-owner so that files extracted are still owned by the
    # running user in a rootless container
	tar --no-same-owner -xf Python-$PYVER.tar.xz
    pip install --no-input patch
    popd

fi

cp -r Android $SRCDIR
pushd $SRCDIR
autoreconf -ifv
./Android/build_deps.py $COMMON_ARGS
./Android/configure.py $COMMON_ARGS --prefix=/usr "$@"
make
make install DESTDIR="$THIS_DIR/build"
popd
cp -r $SRCDIR/Android/sysroot/usr/share/terminfo build/usr/share/
cp devscripts/env.sh build/

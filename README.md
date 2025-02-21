Python 3 Android
================

This is an experimental set of build scripts that will cross-compile Python 3.13.0 for an Android device.

Building requires:
-----

1. Linux. This project might work on other systems supported by NDK but no guarantee.
2. Android NDK r28 installed and environment variable ``$ANDROID_NDK`` points to its root directory. Older NDK may not work and NDK <= r18 is known to be incompatible.
   <br>An example of how to set the environment variable would be ``export ANDROID_NDK="/home/myuser/android-ndk-r28-linux" >> $HOME/.bashrc``

<br>
Running requires:
-----

1. Android 11 (Red Velvet Cake, API 30) or above
2. arm, arm64, x86, x86_64

<br>
Build
-----

1. Run `sudo ./clean.sh` for good measure, and after each build.
2. You will need a separate build run for every API Level/architecture combination you wish to run on:
   <br>Here are a couple of examples to build a static version of the library with docker.
   * Build 64 bit `sudo docker run --rm -it -v $(pwd):/python3-android -v /mnt/c/SPE/android-ndk-r28 --env ARCH=arm64 --env ANDROID_API=30 --env ANDROID_NDK=/android-ndk-r28 python:3.13.0-slim /python3-android/docker-build.sh --enable-shared --without-ensurepip --disable-ipv6 --with-build-python`
   * Build x86_64 `sudo docker run --rm -it -v $(pwd):/python3-android -v /mnt/c/SPE/android-ndk-r28 --env ARCH=x86_64 --env ANDROID_API=30 --env ANDROID_NDK=/android-ndk-r28 python:3.13.0-slim /python3-android/docker-build.sh --enable-shared --without-ensurepip --disable-ipv6 --with-build-python`


Installation & Running
------------

1. This project has a sample application. It is most likely out of date file wise, but it is a good starting point to understand how to use it.
2. Make sure `adb shell` works fine
3. Copy all files in `build` to a folder on the device (e.g., ```/data/local/tmp/python3```). Note that on most devices `/sdcard` is not on a POSIX-compliant filesystem, so the python binary will not run from there.
4. In adb shell:
<pre>
cd /data/local/tmp/build
. ./env.sh
python3
</pre>
   And have fun!

SSL/TLS
-------
SSL certificates have old and new naming schemes. Android uses the old scheme yet the latest OpenSSL uses the new one. If you got ```CERTIFICATE_VERIFY_FAILED``` when using SSL/TLS in Python, you need to collect system certificates:
```
cd /data/local/tmp/build
mkdir -p etc/ssl
cat /system/etc/security/cacerts/* > etc/ssl/cert.pem
```
Path for certificates may vary with device vendor and/or Android version. Note that this approach only collects system certificates. If you need to collect user-installed certificates, most likely root access on your Android device is needed.

Check SSL/TLS functionality with:
```
import urllib.request
print(urllib.request.urlopen('https://httpbin.org/ip').read().decode('ascii'))
```

Known Issues
------------

No big issues! yay

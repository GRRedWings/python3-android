#!/usr/bin/env python3
import shlex
import logging
import os
import re
import subprocess
from typing import List

from util import ARCHITECTURES, BASE, SYSROOT, env_vars, ndk_unified_toolchain, parse_args

logger = logging.getLogger(__name__)

class Package:
    def __init__(self, target_arch_name: str, android_api_level: int):
        self.target_arch_name = target_arch_name
        self.target_arch = ARCHITECTURES[target_arch_name]
        self.android_api_level = android_api_level

    def run(self, cmd: List[str]):
        cwd = BASE / 'deps' / re.sub(r'\.tar\..*', '', os.path.basename(self.source))
        logger.debug(f'Running in {cwd}: ' + ' '.join([shlex.quote(str(arg)) for arg in cmd]))
        subprocess.check_call(cmd, cwd=cwd)

    def build(self):
        self.configure()
        self.make()
        self.make_install()

    def configure(self):
        self.run([
            './configure',
            '--prefix=/usr',
            '--libdir=/usr/lib',
            '--host=' + self.target_arch.ANDROID_TARGET,
            '--disable-shared',
        ] + getattr(self, 'configure_args', []))

    def make(self):
        self.run(['make'])

    def make_install(self):
        self.run(['make', 'install', f'DESTDIR={SYSROOT}'])

class BZip2(Package):
    source = 'https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz'

    def configure(self):
        pass

    def make(self):
        self.run([
            'make', 'libbz2.a',
            f'CC={os.environ["CC"]}',
            f'CFLAGS={os.environ["CFLAGS"]} {os.environ["CPPFLAGS"]}',
            f'AR={os.environ["AR"]}',
            f'RANLIB={os.environ["RANLIB"]}',
        ])

    def make_install(self):
        # The install target in bzip2's Makefile needs too many fixes -
        # Installing files manually is simpler.
        self.run(['install', '-Dm644', 'libbz2.a', '-t', str(SYSROOT / 'usr' / 'lib')])
        self.run(['install', '-Dm644', 'bzlib.h', '-t', str(SYSROOT / 'usr' / 'include')])

class GDBM(Package):
    source = 'https://ftp.gnu.org/gnu/gdbm/gdbm-1.23.tar.gz'
    configure_args = ['--enable-libgdbm-compat']

class LibFFI(Package):
    source = 'https://github.com/libffi/libffi/releases/download/v3.4.4/libffi-3.4.4.tar.gz'
    # libffi may fail to configure with Docker on WSL2 (#33)
    configure_args = ['--disable-builddir']

class LibUUID(Package):
    source = 'https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v2.38/util-linux-2.38.1.tar.xz'
    configure_args = ['--disable-all-programs', '--enable-libuuid']

class NCurses(Package):
    source = 'https://ftp.gnu.org/gnu/ncurses/ncurses-6.3.tar.gz'
    # Not stripping the binaries as there is no easy way to specify the strip program for Android
    configure_args = ['--without-ada', '--enable-widec', '--without-debug', '--without-cxx-binding', '--disable-stripping']

class OpenSSL(Package):
    source = 'https://www.openssl.org/source/openssl-3.0.7.tar.gz'

    def configure(self):
        # OpenSSL handles NDK internal paths by itself
        path = os.pathsep.join((
            # OpenSSL requires NDK's clang in $PATH to enable usage of clang
            str(ndk_unified_toolchain()),
            # and it requires unprefixed binutils, too
            str(ndk_unified_toolchain().parent / self.target_arch.ANDROID_TARGET / 'bin'),
            os.environ['PATH'],
        ))

        logger.debug(f'$PATH for OpenSSL: {path}')

        os.environ['PATH'] = path

        openssl_target = 'android-' + self.target_arch_name

        self.run(['./Configure', '--prefix=/usr', '--openssldir=/etc/ssl', openssl_target,
                  'no-shared', 'no-tests', f'-D__ANDROID_API__={self.android_api_level}'])

    def make_install(self):
        self.run(['make', 'install_sw', 'install_ssldirs', f'DESTDIR={SYSROOT}'])

class Readline(Package):
    source = 'https://ftp.gnu.org/gnu/readline/readline-8.2.tar.gz'

    # See the wcwidth() test in aclocal.m4. Tested on Android 6.0 and it's broken
    # XXX: wcwidth() is implemented in [1], which may be in Android P
    # Need a conditional configuration then?
    # [1] https://android.googlesource.com/platform/bionic/+/c41b560f5f624cbf40febd0a3ec0b2a3f74b8e42
    configure_args = ['bash_cv_wcwidth_broken=yes']

class SQLite(Package):
    source = 'https://sqlite.org/2022/sqlite-autoconf-3390400.tar.gz'

class XZ(Package):
    source = 'https://tukaani.org/xz/xz-5.2.7.tar.xz'

class ZLib(Package):
    source = 'https://www.zlib.net/zlib-1.3.tar.gz'

    def configure(self):
        os.environ.update({
            'CHOST': self.target_arch.ANDROID_TARGET + '-',
            'CFLAGS': ' '.join([os.environ['CPPFLAGS'], os.environ['CFLAGS']]),
        })

        self.run([
            './configure',
            '--prefix=/usr',
            '--static',
        ])

    def make(self):
        self.run(['make', 'libz.a'])

def build_package(pkg: Package):
    subprocess.check_call(['curl', '-fLO', pkg.source], cwd=BASE / 'deps')
    subprocess.check_call(['tar', '--no-same-owner', '-xf', os.path.basename(pkg.source)], cwd=BASE / 'deps')

    try:
        saved_env = os.environ.copy()
        pkg.build()
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

def main():
    logging.basicConfig(level=logging.DEBUG)

    args, _ = parse_args()

    os.environ.update(env_vars(args.target_arch_name, args.android_api_level))

    (BASE / 'deps').mkdir(exist_ok=True)
    SYSROOT.mkdir(exist_ok=True)

    package_classes = (
        # ncurses is a dependency of readline
        NCurses,
        BZip2, GDBM, LibFFI, LibUUID, OpenSSL, Readline, SQLite, XZ, ZLib,
    )

    for pkg_cls in package_classes:
        build_package(pkg_cls(args.target_arch_name, args.android_api_level))

if __name__ == '__main__':
    main()

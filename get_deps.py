#!/usr/bin/env python3
import platform
import os
import subprocess
import platform
import shutil
from get_arch import conan_archs, get_arch

def install_deps(arch):
    # Use Conan to install dependencies
    settings = []

    if platform.system() == 'Windows':
        settings.append('os=Windows')
    elif platform.system() == 'Darwin':
        settings.append('os=Macos')
        settings.append('compiler=apple-clang')
        # if arch == 'armv8':
        settings.append('compiler.version=11.0')
        # else:
        #     settings.append('compiler.version=10.15')
        settings.append('compiler.libcxx=libc++')
    elif platform.system() == 'Linux':
        settings.append('os=Linux')
        settings.append('compiler=gcc')
        settings.append('compiler.version=10')
        settings.append('compiler.libcxx=libstdc++')
    if arch:
        settings.append('arch=' + arch)

    build = []
    if platform.system() == 'Linux':
        # Need to compile dependencies if Linux
        build.append('*')
    elif (not shutil.which('cmake') and 
        (platform.architecture()[0] == '32bit' or 
        platform.machine().lower() not in (conan_archs['armv8'] + conan_archs['x86']))):
        build.append('cmake*')
    
    if build == []:
        build.append('missing')
    
    print('conan cli settings:')
    print('settings: ' + str(settings))
    print('build: ' + str(build))
    
    subprocess.run(['conan', 'profile', 'detect'])

    conan_output = os.path.join('conan_output', arch)

    subprocess.run([
                    'conan', 'install', 
                    *[x for s in settings for x in ('-s', s)],
                    *[x for b in build for x in ('-b', b)], 
                    '-of', conan_output, '--deployer=direct_deploy', '.'
                    ])
    
    return conan_output

def main():
    arch = get_arch()
    conan_output = 'conan_output/' + arch + '/direct_deploy'
    if os.path.isdir(conan_output):
        print('Dependencies found at:' + conan_output)
        print('Skip conan install...')
        return

    conan_output = install_deps(arch)

    if os.getenv('APNGASM_COMPILE_TARGET') == 'universal2':
        # Repeat to install the other architecture version of libwebp
        conan_output_x64 = install_deps('x86_64')
        conan_output_universal2 = conan_output.replace('armv8', 'universal2')
        shutil.rmtree(conan_output_universal2, ignore_errors=True)
        subprocess.run([
                        'python3', 'lipo-dir-merge/lipo-dir-merge.py', 
                        conan_output_x64, conan_output, conan_output_universal2
                        ])

if __name__ == '__main__':
    main()
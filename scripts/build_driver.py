# This script is to build the snowflake driver in github action
import os
import sys


def build_windows():
    arch = os.environ.get('ARCH', 'x64')
    target = os.environ.get('TARGET', 'release')
    vs = os.environ.get('VS', 'vs15')
    



def main():
    current_os = os.name
    if current_os == 'nt':
        build_windows()
    else:
        build_posix()


if __name__ == "__main__":
    main(sys.argv)

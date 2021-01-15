#!/bin/bash

# Usage: BuildSimbaICU.sh <SIMBA_PLATFORM> <BUILD_STATIC_ONLY_FLAG>. 
# Platforms are the cases listed below and use 1 to build *only* static libraries (default is to build both Shared and Static libraries)
# Example: ./BuildSimbaICU.sh Darwin_universal 1 (to build only static) or ./BuildSimbaICU.sh Darwin_universal (to build shared and static)
# NOTE: For certain platforms (Linux and Darwin), you might need to pass in LD_FLAGS to force the ICU's autoconv to use Position-Independent Code when compileling. 
# Simply set the LD_FLAGS to the desired flag (ie LD_FLAGS='-fPIC')

SIMBA_PLATFORM=$1
BUILD_STATIC=$2
BUILD_CONFIG=$3

MAKE_CMD='gmake'

if [ z$BUILD_STATIC == z1 ]; then
	echo ENABLING STATIC
    TYPE_FLAGS='--enable-static --disable-shared'
else
	echo DISABLING STATIC
    TYPE_FLAGS='--enable-static --enable-shared'
fi

if [ z$RENAME_STATIC_LIBS == z ]; then
    RENAME_STATIC_LIBS=1
fi

case "$SIMBA_PLATFORM" in
    AIX_powerpc64)
        OS='AIX'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS=
        ;;
    AIX_powerpc)
        OS='AIX'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS=
        ;;
    AIX_powerpc64_gcc)
        OS='AIX/GCC'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
        ;;
    AIX_powerpc_gcc)
        OS='AIX/GCC'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS='-fPIC'
        ;;
    HP-UX_pa64)
        OS='HP-UX/ACC'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS=
        ;;
    HP-UX_pa)
        OS='HP-UX/ACC'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS=
        ;;
    HP-UX_ia64)
        OS='HP-UX/ACC'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS=
        ;;
    HP-UX_ia64_32)
        OS='HP-UX/ACC'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS=
        ;;
    Linux_x8664_gcc4_4)
        OS='Linux'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
        MAKE_CMD='gmake CC=gcc44 CXX=g++44 LD=g++44'
        ;;
    Linux_x8664_gcc4_8)
        OS='Linux'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
        MAKE_CMD='gmake CC=gcc48 CXX=g++48 LD=g++48'
        ;;
    Linux_x8664_gcc4_9)
        OS='Linux'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
        MAKE_CMD='gmake CC=gcc49 CXX=g++49 LD=g++49'
        ;;
    Linux_x8664_gcc5_5)
        OS='Linux'
        SUFFIX='_sb64'
        CXX='g++55'
        CC='gcc55'
        OPTS="CXX=$CXX CC=$CC LD=$CXX --enable-64bit-libs "
        MAKE_CMD="gmake"
        LD_FLAGS='-ldl -fPIC'
        ;;
    Linux_ppc64le)
        OS='Linux'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
		MAKE_CMD='gmake CC=gcc48 CXX=g++48 LD=g++48'
        ;;		
    Linux_ppc32le)
        OS='Linux'
        SUFFIX='_sb64'
        OPTS='--disable-64bit-libs'
        LD_FLAGS='-fPIC'
		MAKE_CMD='gmake CC=gcc48 CXX=g++48 LD=g++48'
        ;;		
    Linux_x86_gcc4_4)
        OS='Linux'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS='-fPIC'
		MAKE_CMD='gmake CC=gcc44 CXX=g++44 LD=g++44'
        ;;
    Linux_x86_gcc4_8)
        OS='Linux'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS='-fPIC'
        MAKE_CMD='gmake CC=gcc48 CXX=g++48 LD=g++48'
        ;;
    Linux_x86_gcc4_9)
        OS='Linux'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS='-fPIC'
        MAKE_CMD='gmake CC=gcc49 CXX=g++49 LD=g++49'
        ;;
    Linux_x86_gcc5_5)
        OS='Linux'
        SUFFIX='_sb32'
        CXX='g++55'
	CC='gcc55'
        OPTS="CXX=$CXX CC=$CC LD=$CXX --disable-64bit-libs "
        MAKE_CMD="gmake"
        LD_FLAGS='-ldl -fPIC'
        ;;
    Linux_ia64)
        OS='Linux'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
        ;;
    Solaris_sparc64)
        OS='Solaris'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS=
        ;;
    Solaris_sparc)
        OS='Solaris'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS=
        ;;
    Solaris_x8664)
        OS='SolarisX86'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS=
        ;;
    Solaris_x86)
        OS='SolarisX86'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS=
        ;;
    Solaris_sparc64_gcc)
        OS='Solaris/GCC'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        ;;
    Solaris_sparc_gcc)
        OS='Solaris/GCC'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        ;;
    Solaris11_sparc64_gcc)
        CC='gcc-4.9'
        CXX='g++-4.9'
        OS='Solaris/GCC'
        SUFFIX='_sb64'
        OPTS="--enable-64bit-libs CC=$CC CXX=$CXX"
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        ;;
    Solaris11_sparc_gcc)
        CC='gcc-4.9'
        CXX='g++-4.9'
        OS='Solaris/GCC'
        SUFFIX='_sb32'
        OPTS="--disable-64bit-libs CC=$CC CXX=$CXX"
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        ;;
    Solaris11_sparc64_ss12_6)
        OS='Solaris'
        SUFFIX='_sb64'
        OPTS="--enable-64bit-libs CC=$CC CXX=$CXX"
        MAKE_CMD='gmake'
        LD_FLAGS=''
        CPPFLAGS=''
        CXXFLAGS='-abiopt=mangle6'
        CFLAGS='-std=c99 -D_XPG6'
        ;;
    Solaris11_sparc_ss12_6)
        OS='Solaris'
        SUFFIX='_sb32'
        OPTS="--disable-64bit-libs CC=$CC CXX=$CXX"
        MAKE_CMD='gmake'
        LD_FLAGS=''
        CPPFLAGS=''
        CXXFLAGS='-abiopt=mangle6'
        CFLAGS='-std=c99 -D_XPG6'
        ;;
    Solaris11_x8664_ss12_6)
        OS='SolarisX86'
        SUFFIX='_sb64'
        OPTS="--enable-64bit-libs CC=$CC CXX=$CXX"
        MAKE_CMD='gmake'
        LD_FLAGS=''
        CPPFLAGS=''
        CXXFLAGS=''
        CFLAGS='-std=c99 -D_XPG6'
        ;;
    Solaris11_x86_ss12_6)
        OS='SolarisX86'
        SUFFIX='_sb32'
        OPTS="--disable-64bit-libs CC=$CC CXX=$CXX"
        MAKE_CMD='gmake'
        LD_FLAGS=''
        CPPFLAGS=''
        CXXFLAGS='-abiopt=mangle6'
        CFLAGS='-std=c99 -D_XPG6'
        ;;
    Solaris_x8664_gcc)
        OS='Solaris/GCC'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        ;;
    Solaris_x86_gcc)
        OS='Solaris/GCC'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        ;;
    Darwin_x8664)
        OS='MacOSX'
        SUFFIX='_sb64'
        OPTS='--enable-64bit-libs'
        LD_FLAGS='-fPIC'
        CPPFLAGS='-DUCLN_AUTO_ATEXIT'
        ;;
    Darwin_x8664_clang)
        OS='MacOSX'
        SUFFIX='_sbUniversal'
        OPTS='--enable-64bit-libs'
        MAKE_CMD='make'
        LD_FLAGS='-mmacosx-version-min=10.9 -fPIC'
        CPPFLAGS='-DUCLN_AUTO_ATEXIT'
        ;;
    Darwin_x86)
        OS='MacOSX'
        SUFFIX='_sb32'
        OPTS='--disable-64bit-libs'
        LD_FLAGS='-fPIC'
        CPPFLAGS='-DUCLN_AUTO_ATEXIT'
        ;;
    Darwin_universal)
        OS='MacOSX'
        SUFFIX='_sbUniversal'
        OPTS='--enable-64bit-libs'
        MAKE_CMD='gmake'
        LD_FLAGS='-fPIC'
        CPPFLAGS='-DUCLN_AUTO_ATEXIT'
        ;;
    Darwin_universal_clang)
        OS='MacOSX_clang'
        SUFFIX='_sbUniversal'
        OPTS='--enable-64bit-libs'
        MAKE_CMD='make'
        LD_FLAGS='-fPIC'
        CPPFLAGS='-DUCLN_AUTO_ATEXIT'
        ;;
    Linux_s390x)
        OS='Linux'
        SUFFIX='_sb64'
	CROSS_BUILD_DIR=`pwd`/cxbuild
        CXX='s390x-linux-gnu-g++'
	CC='s390x-linux-gnu-gcc'
        OPTS="--host=s390x-linux-gnu --with-cross-build=$CROSS_BUILD_DIR CXX=$CXX CC=$CC LD=$CXX"
        MAKE_CMD='make'
        LD_FLAGS='-fPIC'
        ;;
    Linux_s390x32)
        OS='Linux'
        SUFFIX='_sb32'
	CROSS_BUILD_DIR=`pwd`/cxbuild
        CXX='s390x-linux-gnu-g++'
	CC='s390x-linux-gnu-gcc'
        OPTS="--host=s390x-linux-gnu --with-cross-build=$CROSS_BUILD_DIR CXX=$CXX CC=$CC LD=$CXX CFLAGS=-m31 LDFLAGS=-m31 CXXFLAGS=-m31"
        MAKE_CMD='make'
        LD_FLAGS='-fPIC -m31'
        ;;
    Linux_aarch64)
        OS='Linux'
        SUFFIX='_sb64'
        CXX='g++-5'
	CC='gcc-5'
        OPTS="CXX=$CXX CC=$CC LD=$CXX"
        MAKE_CMD="gmake"
        LD_FLAGS='-ldl -fPIC'
        ;;
    Linux_Cross_aarch64)
        OS='Linux'
        SUFFIX='_sb64'
	CROSS_BUILD_DIR=`pwd`/cxbuild
	CXX='aarch64-linux-gnu-g++-8'	
	CC='aarch64-linux-gnu-gcc-8'
        OPTS="--host=aarch64-linux-gnu --with-cross-build=$CROSS_BUILD_DIR CXX=$CXX CC=$CC LD=$CXX"
        MAKE_CMD='make'
        LD_FLAGS='-fPIC'
        ;;
    Linux_Cross_armhf)
        OS='Linux'
        SUFFIX='_sb32'
	CROSS_BUILD_DIR=`pwd`/cxbuild
        CXX='arm-linux-gnueabihf-g++-8'
	CC='arm-linux-gnueabihf-gcc-8'
        OPTS="--host=arm-linux-gnueabihf --with-cross-build=$CROSS_BUILD_DIR CXX=$CXX CC=$CC LD=$CXX"
        MAKE_CMD='make'
        LD_FLAGS='-fPIC -mfloat-abi=hard'	
	CPPFLAGS='-mfloat-abi=hard'
	;;
    *)
        echo
        echo "Unsupported or missing platform."
        echo "Usage: $0 <PLATFORM> <STATIC>"
        echo "Platform is one of:"
        echo "    Linux_x8664_gcc44"
        echo "    Linux_x86_gcc44"
        echo "    Linux_x8664_gcc48"
        echo "    Linux_x86_gcc48"
        echo "    Linux_x8664_gcc49"
        echo "    Linux_x86_gcc49"
        echo "    Linux_x8664_gcc55"
        echo "    Linux_x86_gcc55"
        echo "    Linux_ia64"
        echo "    Linux_s390x"
        echo "    Linux_s390x32"
        echo "    Linux_aarch64"
        echo "    AIX_powerpc64"
        echo "    AIX_powerpc"
        echo "    AIX_powerpc64_gcc"
        echo "    AIX_powerpc_gcc"
        echo "    HP-UX_pa64"
        echo "    HP-UX_pa"
        echo "    HP-UX_ia64"
        echo "    HP-UX_ia64_32"
        echo "    Solaris_sparc64"
        echo "    Solaris_sparc"
        echo "    Solaris11_sparc64_gcc"
        echo "    Solaris11_sparc_gcc"
        echo "    Solaris11_sparc64_ss12_6"
        echo "    Solaris11_sparc_ss12_6"
        echo "    Solaris11_x8664_ss12_6"
        echo "    Solaris11_x86_ss12_6"
        echo "    Solaris_x8664"
        echo "    Solaris_x86"
        echo "    Solaris_sparc64_gcc"
        echo "    Solaris_sparc_gcc"
        echo "    Solaris_x8664_gcc"
        echo "    Solaris_x86_gcc"
        echo "    Darwin_x8664"
        echo "    Darwin_x8664_clang"
        echo "    Darwin_x86"
        echo "    Darwin_universal"
        echo "    Darwin_universal_clang"
        echo "    Linux_ppc64le" 
        echo "    Linux_ppc32le"
        echo "    Linux_Cross_aarch64"
        echo "    Linux_Cross_aarch32"	
        echo "Static only flag is optional and if set to 1 will build only static libraries. Default is to build static and shared."
        exit 1
        ;;
esac

# just in case there are old obj files around

if [ z$CROSS_BUILD_DIR != z ]; then
    mkdir -p $CROSS_BUILD_DIR
    CURDIR=`pwd`
    cd $CROSS_BUILD_DIR
    $CURDIR/runConfigureICU `uname -s` $CROSS_BUILD_OPTS
    make -j 4
    cd $CURDIR
fi

$MAKE_CMD clean
# delete old libs built
rm -rf lib
mkdir lib

#Export LD_FLAGS for platforms
export CFLAGS="$CFLAGS $LD_FLAGS"
export CXXFLAGS="$CXXFLAGS $LD_FLAGS"

export CPPFLAGS

if [ $SIMBA_PLATFORM == "Darwin_universal_clang" ] || [ $SIMBA_PLATFORM == "Darwin_x8664_clang" ] ;then
    export CC=clang
    export CXX=clang++
    export CFLAGS="$CFLAGS -O2 -stdlib=libc++"
    export CXXFLAGS="$CXXFLAGS -O2 -stdlib=libc++"
    if [ $BUILD_CONFIG == "release" ] ;then
        RUNCMD="./configure --enable-auto-cleanup --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
    else
        RUNCMD="./configure --enable-debug --enable-auto-cleanup --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
    fi
    $RUNCMD
else
    if [ $BUILD_CONFIG == "release" ] ;then
        RUNCMD="./runConfigureICU $OS --enable-auto-cleanup --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
    else
        RUNCMD="./runConfigureICU $OS --enable-debug --enable-auto-cleanup --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
    fi
    $RUNCMD
fi

if [ "$?" -ne "0" ]; then
    echo
    echo "Failed to configure ICU with command: $RUNCMD"
    echo
    exit 1
fi

$MAKE_CMD -j 4 VERBOSE=1

if [ "$?" -ne "0" ]; then
    echo
    echo "Failed to build ICU after configuring with command: $RUNCMD"
    echo
    exit 1
fi

# For Darwin universal, we build 64-bit first so now build 32-bit and combine for the universal binary
# Note this is to work around issues building the universal binaries directly
if [ "$SIMBA_PLATFORM" == "Darwin_universal" ] || [ $SIMBA_PLATFORM == "Darwin_universal_clang" ]; then

    #create output directories for the 64-bit files
    mkdir -p Simba_Libs/"$SIMBA_PLATFORM"64/$BUILD_CONFIG/lib 2> /dev/null

    #move all 64-bit libs built
    mv lib/* Simba_Libs/"$SIMBA_PLATFORM"64/$BUILD_CONFIG/lib/
    
    #switch to 32-bit mode
    OPTS='--disable-64bit-libs'

    rm -rf lib
    $MAKE_CMD clean

    if [ $SIMBA_PLATFORM == "Darwin_universal_clang" ] ;then
        if [ $BUILD_CONFIG == "release" ] ;then
            RUNCMD="./configure --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
        else
            RUNCMD="./configure --enable-debug --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
        fi
        $RUNCMD
    else
        if [ $BUILD_CONFIG == "release" ] ;then
            RUNCMD="./runConfigureICU $OS --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
        else
            RUNCMD="./runConfigureICU $OS --enable-debug --with-library-suffix=$SUFFIX $OPTS $TYPE_FLAGS"
        fi
        $RUNCMD
    fi

    if [ "$?" -ne "0" ]; then
        echo
        echo "Failed to configure ICU with command: $RUNCMD"
        echo
        exit 1
    fi

    $MAKE_CMD

    if [ "$?" -ne "0" ]; then
        echo
        echo "Failed to build ICU after configuring with command: $RUNCMD"
        echo
        exit 1
    fi

    #create output directories for the 32-bit files
    mkdir -p Simba_Libs/"$SIMBA_PLATFORM"32/$BUILD_CONFIG/lib 2> /dev/null

    #move all 32-bit libs built
    mv lib/* Simba_Libs/"$SIMBA_PLATFORM"32/$BUILD_CONFIG/lib/

    #create final output directories
    mkdir -p Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/lib 2> /dev/null
    mkdir -p Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/unicode 2> /dev/null
    mkdir -p Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/layout 2> /dev/null

    #create the universal files
    for i in Simba_Libs/"$SIMBA_PLATFORM"32/$BUILD_CONFIG/lib/*
    do
        if [ -h $i ]; then
            # Copy symbolic links
            cp -a $i Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/lib
        else
            f=$(basename $i)
            lipo -create Simba_Libs/"$SIMBA_PLATFORM"32/$BUILD_CONFIG/lib/$f Simba_Libs/"$SIMBA_PLATFORM"64/$BUILD_CONFIG/lib/$f -output Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/lib/$f
        fi
    done

    if [ "$?" -ne "0" ]; then
        echo
        echo "Failed to combine 32- and 64-bit Darwin ICU binaries"
        echo
        exit 1
    fi

    #remove all the intermediate 32/64 files
    rm -rf Simba_Libs/"$SIMBA_PLATFORM"32
    rm -rf Simba_Libs/"$SIMBA_PLATFORM"64
else
    #create output directories
    mkdir -p Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/lib 2> /dev/null
    mkdir -p Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/unicode 2> /dev/null
    mkdir -p Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/layout 2> /dev/null

    #move all libs built
    if [ z$RENAME_STATIC_LIBS = z1 ]; then
        for i in lib/*.a
        do 
            f=$(basename $i)
            mv lib/$f Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/lib/`echo $f | perl -pe 's/^lib/libs/'`
        done
    fi
    mv lib/* Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG//lib 
fi

#copy unicode headers (all headers from 3 folders)
cp common/unicode/*.h Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/unicode/
cp i18n/unicode/*.h Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/unicode/
cp io/unicode/*.h Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/unicode/

#copy layout headers (only certain headers so use a list of files to copy)
LAYOUT_INCLUDES="\
./layoutex/layout/ParagraphLayout.h \
./layoutex/layout/playout.h \
./layoutex/layout/plruns.h \
./layoutex/layout/RunArrays.h"

cp $LAYOUT_INCLUDES Simba_Libs/$SIMBA_PLATFORM/$BUILD_CONFIG/include/layout/

#Syntax error near 'fi', commented out
#Change static 'lib' prefix to 'libs'
#if [$SIMBA_PLATFORM -ne "AIX_powerpc" ] || [ $SIMBA_PLATFORM -ne "AIX_powerpc64" ] || [ $SIMBA_PLATFORM -ne "AIX_powerpc_gcc" ] || [ $SIMBA_PLATFORM -ne "AIX_powerpc64_gcc" ]
#cd Simba_Libs/$SIMBA_PLATFORM/lib/
#for file in *.a ; do
#    mv ./"$file" "${file:0:3}s${file:3}"
#done
#fi

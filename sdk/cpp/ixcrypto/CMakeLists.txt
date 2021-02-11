#
# Author: Benjamin Sergeant
# Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
#
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../CMake;${CMAKE_MODULE_PATH}")

set (IXCRYPTO_SOURCES
    ixcrypto/IXHMac.cpp
    ixcrypto/IXBase64.cpp
    ixcrypto/IXUuid.cpp
    ixcrypto/IXHash.cpp
)

set (IXCRYPTO_HEADERS
    ixcrypto/IXHMac.h
    ixcrypto/IXBase64.h
    ixcrypto/IXUuid.h
    ixcrypto/IXHash.h
)

add_library(ixcrypto STATIC
    ${IXCRYPTO_SOURCES}
    ${IXCRYPTO_HEADERS}
)

set(IXCRYPTO_INCLUDE_DIRS
    .
    ../ixcore)

target_include_directories( ixcrypto PUBLIC ${IXCRYPTO_INCLUDE_DIRS} )

# hmac computation needs a crypto library which will be mbedtls on non
# apple platforms

if (NOT APPLE)
    find_package(MbedTLS REQUIRED)
    target_include_directories(ixcrypto PUBLIC ${MBEDTLS_INCLUDE_DIRS})
    target_link_libraries(ixcrypto ${MBEDTLS_LIBRARIES})
    target_compile_definitions(ixcrypto PUBLIC IXCRYPTO_USE_MBED_TLS)
endif()

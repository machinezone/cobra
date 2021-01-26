cmake_minimum_required (VERSION 3.14)
project (cobra_cli)

set (CMAKE_CXX_STANDARD 17)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

#
# uvw-http-server
#
add_executable(cobra_cli)

target_sources(cobra_cli PRIVATE
  ixcrypto/ixcrypto/IXUuid.cpp
  ixcrypto/ixcrypto/IXHMac.cpp
  ixcrypto/ixcrypto/IXBase64.cpp
  ixcrypto/ixcrypto/IXHash.cpp
  ixbots/ixbots/IXCobraToStatsdBot.cpp
  ixbots/ixbots/IXCobraToSentryBot.cpp
  ixbots/ixbots/IXCobraBot.cpp
  ixbots/ixbots/IXStatsdClient.cpp
  ixbots/ixbots/IXCobraToCobraBot.cpp
  ixbots/ixbots/IXCobraToPythonBot.cpp
  ixbots/ixbots/IXCobraToStdoutBot.cpp
  ixcore/ixcore/utils/IXCoreLogger.cpp
  cli/cobra_cli.cpp
  ixcobra/ixcobra/IXCobraConnection.cpp
  ixcobra/ixcobra/IXCobraMetricsThreadedPublisher.cpp
  ixcobra/ixcobra/IXCobraMetricsPublisher.cpp
  ixsentry/ixsentry/IXSentryClient.cpp
)

target_link_libraries(cobra_cli ${CONAN_LIBS})

target_include_directories(cobra_cli PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/
  ${CMAKE_CURRENT_SOURCE_DIR}/ixcore
  ${CMAKE_CURRENT_SOURCE_DIR}/ixcrypto
  ${CMAKE_CURRENT_SOURCE_DIR}/ixbots
  ${CMAKE_CURRENT_SOURCE_DIR}/ixcobra
  ${CMAKE_CURRENT_SOURCE_DIR}/ixsentry
  >
)
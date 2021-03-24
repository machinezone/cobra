cmake_minimum_required (VERSION 3.14)
project (cobra_cli)

set (CMAKE_CXX_STANDARD 11)

if (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "4.9.0")
    message(FATAL_ERROR "Insufficient gcc version. Minimun supported version is 4.9.0")
  else()
    add_definitions( -DHAVE_STD_REGEX=1 )
  endif()
else()
  add_definitions( -DHAVE_STD_REGEX=1 )
endif()

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
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

find_package(Python COMPONENTS Development)
target_link_libraries(cobra_cli ${CONAN_LIBS} ${Python_LIBRARIES})
target_compile_definitions(cobra_cli PRIVATE IXBOTS_USE_PYTHON)

target_include_directories(cobra_cli PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/
  ${CMAKE_CURRENT_SOURCE_DIR}/ixcore
  ${CMAKE_CURRENT_SOURCE_DIR}/ixcrypto
  ${CMAKE_CURRENT_SOURCE_DIR}/ixbots
  ${CMAKE_CURRENT_SOURCE_DIR}/ixcobra
  ${CMAKE_CURRENT_SOURCE_DIR}/ixsentry
  ${Python_INCLUDE_DIRS}
  >
)

install(TARGETS cobra_cli RUNTIME DESTINATION bin)

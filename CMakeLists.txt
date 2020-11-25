cmake_minimum_required(VERSION 3.4)
project(cspice C)

include(conanbuildinfo.cmake)
conan_basic_setup()

option(BUILD_UTILITIES "Build cspice utilities" ON)

set(SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/source_subfolder/src)

file(GLOB CSPICE_SRC_FILES ${SRC_DIR}/cspice/*.c)
add_library(cspice ${CSPICE_SRC_FILES})

if(WIN32)
  target_compile_definitions(cspice PRIVATE "_COMPLEX_DEFINED;MSDOS;OMIT_BLANK_CC;NON_ANSI_STDIO")
  if(BUILD_SHARED_LIBS)
    set_target_properties(cspice PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS TRUE)
  endif()
elseif(UNIX)
  target_compile_definitions(cspice PRIVATE "NON_UNIX_STDIO")
  target_compile_options(cspice PRIVATE -ansi)
endif()
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  target_link_libraries(cspice PRIVATE m)
endif()

# Behavior of implicitly defined functions changed in AppleClang 12
# https://developer.apple.com/documentation/xcode-release-notes/xcode-12-release-notes
if(CMAKE_C_COMPILER_ID STREQUAL "AppleClang" AND CMAKE_C_COMPILER_VERSION VERSION_GREATER_EQUAL "12")
  target_compile_options(cspice PRIVATE -Wno-error=implicit-function-declaration)
endif()

install(
  TARGETS cspice
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

file(GLOB INCLUDE_FILES ${CMAKE_CURRENT_SOURCE_DIR}/source_subfolder/include/*.h)
install(FILES ${INCLUDE_FILES} DESTINATION include)

if(BUILD_UTILITIES)
  file(GLOB CSUPPORT_SRC_FILES ${SRC_DIR}/csupport/*.c)
  add_library(csupport STATIC ${CSUPPORT_SRC_FILES})
  target_link_libraries(csupport PRIVATE cspice)

  set(CSPICE_UTILITIES brief chrnos ckbref commnt dskbrief dskexp frmdif inspkt
                       mkdsk mkspk msopck spacit spkdif spkmrg tobin toxfr versn)
  foreach(CSPICE_UTILITY ${CSPICE_UTILITIES})
    file(GLOB CSPICE_UTILITY_SRC_FILES ${SRC_DIR}/${CSPICE_UTILITY}_c/*.c)
    add_executable(${CSPICE_UTILITY} ${CSPICE_UTILITY_SRC_FILES})
    target_link_libraries(${CSPICE_UTILITY} PRIVATE csupport cspice)
    install(TARGETS ${CSPICE_UTILITY} DESTINATION ${CMAKE_INSTALL_BINDIR})
  endforeach()
endif()

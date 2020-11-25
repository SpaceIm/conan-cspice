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
  # csupport lib is common to all utilities, but not intended to be used as a lib by consumers
  file(GLOB CSUPPORT_SRC_FILES "${SRC_DIR}/csupport/*.c")
  add_library(csupport STATIC ${CSUPPORT_SRC_FILES})
  target_link_libraries(csupport PRIVATE cspice)

  # Walk into all utilities subfolders and build them (except cook_c which only contains examples)
  set(CSPICE_UTILITIES_SUBDIRS brief_c chrnos_c ckbref_c commnt_c dskbrief_c dskexp_c
                               frmdif_c inspkt_c mkdsk_c mkspk_c msopck_c spacit_c
                               spkdif_c spkmrg_c tobin_c toxfr_c versn_c)
  foreach(CSPICE_SUBDIR ${CSPICE_UTILITIES_SUBDIRS})
    set(UTILITY_SRC_DIR "${SRC_DIR}/${CSPICE_SUBDIR}")

    # Each .pgm file is the entry point of an executable
    file(GLOB PGM_FILES "${UTILITY_SRC_DIR}/*.pgm")

    # Remove (only required in Windows source code?):
    # - existing main.c file
    # - .c files with the same name than .pgm files
    file(REMOVE "${UTILITY_SRC_DIR}/main.c")
    foreach(PGM_FILE ${PGM_FILES})
      get_filename_component(PGM_FILENAME ${PGM_FILE} NAME_WE)
      file(REMOVE "${UTILITY_SRC_DIR}/${PGM_FILENAME}.c")
    endforeach()

    # Generate a local static lib from existing .c files
    file(GLOB CSPICE_UTILITY_SRC_FILES ${UTILITY_SRC_DIR}/*.c)
    if(CSPICE_UTILITY_SRC_FILES)
      add_library(${CSPICE_SUBDIR}_OBJ OBJECT ${CSPICE_UTILITY_SRC_FILES})
    endif()

    # Generate one executable per pgm file
    foreach(PGM_FILE ${PGM_FILES})
      # Generate:
      # - <pgm_filename>_main.c file from .pgm file
      # - <pgm_filename>.c from main.x file:
      get_filename_component(CSPICE_UTILITY ${PGM_FILE} NAME_WE)
      set(PGM_MAIN_SRC_FILE "${UTILITY_SRC_DIR}/${CSPICE_UTILITY}_main.c")
      set(GENERIC_MAIN_SRC_FILE "${UTILITY_SRC_DIR}/${CSPICE_UTILITY}.c")
      configure_file(${PGM_FILE} ${PGM_MAIN_SRC_FILE} COPYONLY)
      configure_file("${UTILITY_SRC_DIR}/main.x" ${GENERIC_MAIN_SRC_FILE} COPYONLY)

      add_executable(${CSPICE_UTILITY} ${PGM_MAIN_SRC_FILE} ${GENERIC_MAIN_SRC_FILE})
      target_link_libraries(${CSPICE_UTILITY} PRIVATE csupport cspice)
      if(TARGET ${CSPICE_SUBDIR}_OBJ)
        target_link_libraries(${CSPICE_UTILITY} PRIVATE ${CSPICE_SUBDIR}_OBJ)
      endif()
      install(TARGETS ${CSPICE_UTILITY} DESTINATION ${CMAKE_INSTALL_BINDIR})
    endforeach()
  endforeach()
endif()

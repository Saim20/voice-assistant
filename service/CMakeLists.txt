cmake_minimum_required(VERSION 3.15)
project(willow-service VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build options
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)

# Auto-detect CUDA
find_package(CUDAToolkit QUIET)
if(CUDAToolkit_FOUND)
    option(GGML_CUDA "Enable CUDA support" ON)
    message(STATUS "CUDA Toolkit found - enabling CUDA support")
else()
    option(GGML_CUDA "Enable CUDA support" OFF)
    message(STATUS "CUDA Toolkit not found - CUDA support disabled")
endif()

# Auto-detect Vulkan
find_package(Vulkan QUIET)
if(Vulkan_FOUND)
    option(GGML_VULKAN "Enable Vulkan support" ON)
    message(STATUS "Vulkan SDK found - enabling Vulkan support")
else()
    option(GGML_VULKAN "Enable Vulkan support" OFF)
    message(STATUS "Vulkan SDK not found - Vulkan support disabled")
endif()

# Find dependencies
find_package(PkgConfig REQUIRED)

# sdbus-c++
pkg_check_modules(SDBUS REQUIRED IMPORTED_TARGET sdbus-c++)

# JsonCpp
pkg_check_modules(JSONCPP REQUIRED IMPORTED_TARGET jsoncpp)

# Whisper.cpp - look for it in the whisper.cpp submodule or system
set(WHISPER_CPP_DIR "${CMAKE_SOURCE_DIR}/../whisper.cpp" CACHE PATH "Path to whisper.cpp")

if(EXISTS "${WHISPER_CPP_DIR}/CMakeLists.txt")
    message(STATUS "Using whisper.cpp from: ${WHISPER_CPP_DIR}")
    
    # Set whisper.cpp build options before adding subdirectory
    if(CUDAToolkit_FOUND)
        set(GGML_CUDA ON CACHE BOOL "Enable CUDA" FORCE)
    else()
        set(GGML_CUDA OFF CACHE BOOL "Enable CUDA" FORCE)
    endif()
    
    if(Vulkan_FOUND)
        set(GGML_VULKAN ON CACHE BOOL "Enable Vulkan" FORCE)
    else()
        set(GGML_VULKAN OFF CACHE BOOL "Enable Vulkan" FORCE)
    endif()
    
    add_subdirectory(${WHISPER_CPP_DIR} whisper.cpp EXCLUDE_FROM_ALL)
else()
    message(STATUS "Looking for system whisper library")
    find_library(WHISPER_LIBRARY NAMES whisper libwhisper)
    find_path(WHISPER_INCLUDE_DIR whisper.h)
    
    if(NOT WHISPER_LIBRARY OR NOT WHISPER_INCLUDE_DIR)
        message(FATAL_ERROR "Whisper library not found. Please set WHISPER_CPP_DIR or install whisper.cpp")
    endif()
    
    add_library(whisper UNKNOWN IMPORTED)
    set_target_properties(whisper PROPERTIES
        IMPORTED_LOCATION "${WHISPER_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${WHISPER_INCLUDE_DIR}"
    )
endif()

# PulseAudio for audio capture
pkg_check_modules(PULSEAUDIO IMPORTED_TARGET libpulse-simple)

# Source files
set(SOURCES
    src/main.cpp
    src/VoiceAssistantService.cpp
)

set(HEADERS
    src/VoiceAssistantService.hpp
)

# Create executable
add_executable(willow-service ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(willow-service
    PRIVATE
        PkgConfig::SDBUS
        PkgConfig::JSONCPP
        whisper
        pthread
)

if(PULSEAUDIO_FOUND)
    target_link_libraries(willow-service PRIVATE PkgConfig::PULSEAUDIO)
    target_compile_definitions(willow-service PRIVATE HAVE_PULSEAUDIO)
endif()

# Include directories
target_include_directories(willow-service
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Compiler flags
target_compile_options(willow-service
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        $<$<CONFIG:Debug>:-g -O0>
        $<$<CONFIG:Release>:-O3>
)

# Install targets
install(TARGETS willow-service
    RUNTIME DESTINATION bin
)

# Install D-Bus service file
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/../dbus/com.github.saim.Willow.service.in
    ${CMAKE_CURRENT_BINARY_DIR}/com.github.saim.Willow.service
    @ONLY
)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/com.github.saim.Willow.service
    DESTINATION share/dbus-1/services
)

# Install D-Bus interface XML
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/../dbus/com.github.saim.Willow.xml
    DESTINATION share/dbus-1/interfaces
)

# Print build info
message(STATUS "")
message(STATUS "Voice Assistant Service Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "  CUDA Support: ${GGML_CUDA}")
message(STATUS "  Vulkan Support: ${GGML_VULKAN}")
message(STATUS "")

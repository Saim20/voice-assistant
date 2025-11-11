cmake_minimum_required(VERSION 3.15)
project(voice-assistant-service VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build options
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)

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
add_executable(voice-assistant-service ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(voice-assistant-service
    PRIVATE
        PkgConfig::SDBUS
        PkgConfig::JSONCPP
        whisper
        pthread
)

if(PULSEAUDIO_FOUND)
    target_link_libraries(voice-assistant-service PRIVATE PkgConfig::PULSEAUDIO)
    target_compile_definitions(voice-assistant-service PRIVATE HAVE_PULSEAUDIO)
endif()

# Include directories
target_include_directories(voice-assistant-service
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Compiler flags
target_compile_options(voice-assistant-service
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        $<$<CONFIG:Debug>:-g -O0>
        $<$<CONFIG:Release>:-O3>
)

# Install targets
install(TARGETS voice-assistant-service
    RUNTIME DESTINATION bin
)

# Install D-Bus service file
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/../dbus/com.github.saim.VoiceAssistant.service.in
    ${CMAKE_CURRENT_BINARY_DIR}/com.github.saim.VoiceAssistant.service
    @ONLY
)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/com.github.saim.VoiceAssistant.service
    DESTINATION share/dbus-1/services
)

# Install D-Bus interface XML
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/../dbus/com.github.saim.VoiceAssistant.xml
    DESTINATION share/dbus-1/interfaces
)

# Print build info
message(STATUS "")
message(STATUS "Voice Assistant Service Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")

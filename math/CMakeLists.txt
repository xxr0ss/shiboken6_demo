set(${cppmath_library}_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/mathematician.cpp
)

add_library(${cppmath_library} SHARED ${${cppmath_library}_sources})
add_compile_definitions(BINDINGS_BUILD)
cmake_minimum_required(VERSION 3.14) # to support generator Visual Studio 16 2019

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED On)

project(shiboken_simple)

set(cppmath_library "libmath")
set(bindings_library "Cppmath") # same as the binding package name

# get python environment for this project
if (NOT python_interpreter)
    find_program(python_interpreter "python")
endif()
message(STATUS "Using python: ${python_interpreter}")


add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/math)

# =============================== Shiboken Configurations & build =============================
# use our wrap_src_gen.py to generate names like xxx_wrapper.cpp
set(bindings_dir ${CMAKE_CURRENT_SOURCE_DIR}/bindings)

execute_process(COMMAND ${python_interpreter} ${bindings_dir}/wrap_src_gen.py 
                ${CMAKE_CURRENT_BINARY_DIR}         # output dir
                OUTPUT_VARIABLE generated_sources)  # save returned value in generated_sources
list(LENGTH generated_sources list_len)
message([*] "length: ${list_len}")
foreach(src ${generated_sources})
    message([*] ${src})
endforeach()


macro(pyside_config option output_var)
    if(${ARGC} GREATER 2)
        set(is_list ${ARGV2})
    else()
        set(is_list "")
    endif()

    execute_process(
      COMMAND ${python_interpreter} "${bindings_dir}/pyside_config.py"
              ${option}
      OUTPUT_VARIABLE ${output_var}
      OUTPUT_STRIP_TRAILING_WHITESPACE)

    if ("${${output_var}}" STREQUAL "")
        message(FATAL_ERROR "Error: Calling pyside_config.py ${option} returned no output.")
    endif()
    if(is_list)
        string (REPLACE " " ";" ${output_var} "${${output_var}}")
    endif()
endmacro()

pyside_config(--shiboken-module-path shiboken_module_path)
pyside_config(--shiboken-generator-path shiboken_generator_path)
pyside_config(--shiboken-generator-include-path shiboken_include_dir 1)
pyside_config(--shiboken-module-shared-libraries-cmake shiboken_shared_libraries 0)
pyside_config(--python-include-path python_include_dir)
pyside_config(--python-link-flags-cmake python_linking_data 0)
message(STATUS "shiboken_module_path: ${shiboken_module_path}")
message(STATUS "shiboken_generator_path: ${shiboken_generator_path}")
message(STATUS "python_include_dir: ${python_include_dir}")
message(STATUS "shiboken_include_dir: ${shiboken_include_dir}")
message(STATUS "shiboken_shared_libraries: ${shiboken_shared_libraries}")
message(STATUS "python_linking_data: ${python_linking_data}")


set(wrapped_header ${bindings_dir}/bindings.h)
set(typesystem_file ${bindings_dir}/bindings.xml)

set(shiboken_options --generator-set=shiboken --enable-parent-ctor-heuristic
    --enable-return-value-heuristic --use-isnull-as-nb_nonzero
    --avoid-protected-hack
    -I${bindings_dir}
    -I${CMAKE_CURRENT_SOURCE_DIR}/math   # Include paths used by the C++ parser
    -T${bindings_dir}   # Path used when searching for type system files
    --output-directory=${CMAKE_CURRENT_BINARY_DIR})
set(shiboken_path ${shiboken_generator_path}/shiboken6${CMAKE_EXECUTABLE_SUFFIX})
set(generated_sources_dependencies ${wrapped_header} ${typesystem_file})

add_custom_command(OUTPUT ${generated_sources}
                    COMMAND ${shiboken_path}
                    ${shiboken_options} ${wrapped_header} ${typesystem_file}
                    DEPENDS ${generated_sources_dependencies}
                    IMPLICIT_DEPENDS CXX ${wrapped_header}
                    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                    COMMENT "Running generator for ${typesystem_file}.")


# =============================== CMake target - bindings_library =============================

# Set the cpp files which will be used for the bindings library.
set(${bindings_library}_sources ${generated_sources})

# Define and build the bindings library.
add_library(${bindings_library} MODULE ${${bindings_library}_sources})

# Apply relevant include and link flags.
target_include_directories(${bindings_library} PRIVATE ${python_include_dir})
target_include_directories(${bindings_library} PRIVATE ${shiboken_include_dir})
target_include_directories(${bindings_library} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/math)

target_link_libraries(${bindings_library} PRIVATE ${shiboken_shared_libraries})
target_link_libraries(${bindings_library} PRIVATE ${cppmath_library})

# Adjust the name of generated module.
set_property(TARGET ${bindings_library} PROPERTY PREFIX "")
set_property(TARGET ${bindings_library} PROPERTY OUTPUT_NAME
             "${bindings_library}${PYTHON_EXTENSION_SUFFIX}")
if(WIN32)
    set_property(TARGET ${bindings_library} PROPERTY SUFFIX ".pyd")
endif()

# Make sure the linker doesn't complain about not finding Python symbols on macOS.
if(APPLE)
  set_target_properties(${bindings_library} PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
endif(APPLE)

# Find and link to the python import library only on Windows.
# On Linux and macOS, the undefined symbols will get resolved by the dynamic linker
# (the symbols will be picked up in the Python executable).
if (WIN32)
    message(STATUS "building on WIN32")
    list(GET python_linking_data 0 python_libdir)
    list(GET python_linking_data 1 python_lib)
    find_library(python_link_flags ${python_lib} PATHS ${python_libdir} HINTS ${python_libdir})
    target_link_libraries(${bindings_library} PRIVATE ${python_link_flags})
endif()


# ================================= Dubious deployment section ================================

set(windows_shiboken_shared_libraries)

if(WIN32)
    # =========================================================================================
    # !!! (The section below is deployment related, so in a real world application you will
    # want to take care of this properly (this is simply to eliminate errors that users usually
    # encounter.
    # =========================================================================================
    # Circumvent some "#pragma comment(lib)"s in "include/pyconfig.h" which might force to link
    # against a wrong python shared library.

    set(python_versions_list 3 36 37 38 39)
    set(python_additional_link_flags "")
    foreach(ver ${python_versions_list})
        set(python_additional_link_flags
            "${python_additional_link_flags} /NODEFAULTLIB:\"python${ver}_d.lib\"")
        set(python_additional_link_flags
            "${python_additional_link_flags} /NODEFAULTLIB:\"python${ver}.lib\"")
    endforeach()

    set_target_properties(${bindings_library}
                           PROPERTIES LINK_FLAGS "${python_additional_link_flags}")

    # Compile a list of shiboken shared libraries to be installed, so that
    # the user doesn't have to set the PATH manually to point to the PySide6 package.
    foreach(library_path ${shiboken_shared_libraries})
        string(REGEX REPLACE ".lib$" ".dll" library_path ${library_path})
        file(TO_CMAKE_PATH ${library_path} library_path)
        list(APPEND windows_shiboken_shared_libraries "${library_path}")
    endforeach()
    # =========================================================================================
    # !!! End of dubious section.
    # =========================================================================================
endif()

# =============================================================================================
# !!! (The section below is deployment related, so in a real world application you will want to
# take care of this properly with some custom script or tool).
# =============================================================================================
# Install the library and the bindings module into the source folder near the main.py file, so
# that the Python interpeter successfully imports the used module.
install(TARGETS ${cppmath_library} ${bindings_library}    # Since CMake 3.13, install can use TARGETS in subdirectories
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)
message(STATUS "Install files: ${windows_shiboken_shared_libraries}")
install(FILES ${windows_shiboken_shared_libraries} DESTINATION ${CMAKE_CURRENT_SOURCE_DIR})
# =============================================================================================
# !!! End of dubious section.
# =============================================================================================

# Copyright: (C) Robotics Brain and Cognitive Sciences (RBCS) - Istituto Italiano di Tecnologia
# CopyPolicy: Released under the terms of the GNU GPL v2.0.

cmake_minimum_required(VERSION 3.12)

set(NAME_VENV ${PROJECT_NAME}_venv)

set(PROGRAM_PERMISSIONS_DEFAULT
        OWNER_WRITE OWNER_READ OWNER_EXECUTE
        GROUP_READ GROUP_EXECUTE
        WORLD_READ WORLD_EXECUTE)

# Find Python and Virtualenv.
find_program(VIRTUALENV virtualenv)

if(NOT VIRTUALENV)
    message(FATAL_ERROR "Could not find `virtualenv`, please install it with `apt-get install python3-virtualenv`")
endif()

set(VIRTUALENV ${VIRTUALENV})

set(ICUB_APPLICATIONS_PREFIX "$ENV{ICUB_ROOT}" CACHE PATH "Application path prefix")


# Find python command
execute_process(
    COMMAND bash -c "which python3.12"
    OUTPUT_VARIABLE PYTHON_EXE
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Print which python is being used
message(STATUS "BUILDING VIRTUAL ENV BASED ON PYTHON: ${PYTHON_EXE}")

# Find python version
execute_process(
    COMMAND bash -c "echo python$(python --version | grep -o -E '[0-9].[0-9]')"
    OUTPUT_VARIABLE PYTHON_VER
    OUTPUT_STRIP_TRAILING_WHITESPACE
)


# Generate the virtualenv and ensure it's up to date.
add_custom_command(
    # DEPENDS python_exe
    OUTPUT ${NAME_VENV}
    COMMAND ${VIRTUALENV} --python=${PYTHON_EXE} ${NAME_VENV} #${PYTHON_EXE}
)

# Install requirements from .txt file
add_custom_command(
        OUTPUT requirements
        DEPENDS ${NAME_VENV}
        COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt  ${CMAKE_CURRENT_BINARY_DIR}/requirements.txt
        COMMAND ./${NAME_VENV}/bin/pip3 install -r requirements.txt
)

# Custom targets for CMake
# Create a virtual-env and install all requirements
add_custom_target(build-python  ALL
        DEPENDS requirements 
        SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt
        )


# set PATH_TO_VENV so that the python modules can find the virtualenv
set(PATH_TO_VENV ${CMAKE_CURRENT_BINARY_DIR}/${NAME_VENV})
message(STATUS "PATH_TO_VENV: ${PATH_TO_VENV}")


# add the modules you want to install
add_subdirectory(meta_reasoner)
#add_subdirectory(spatial_memory)


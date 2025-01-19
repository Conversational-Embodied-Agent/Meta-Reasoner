# source di ogni cartella, ogni cartella figlio (modules) ha un file .sh che attiva il venv (ereditato) e poi esegue il file .py
set(MODULE_NAME metaReasoner)

set(SCRIPT_CONTENT "#!/bin/bash\n\n# Function to terminate the child process when the bash father is terminated \nterminate_child_process() {\n    kill -SIGINT $PID\n}\n\n# Catch the quitting signal and send it to the child process\ntrap terminate_child_process EXIT\n# Activate virtual env\nsource ${PATH_TO_VENV}/bin/activate\n# Run python script\npython3 ${PATH_TO_SCRIPT} \"$@\"  &\nPID=$!\n\n# Wait for the python process to end\nwait $PID")

message("Installing ${MODULE_NAME}")

# attach ".sh" to the end of the module name
set(PATH_TO_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/main.py)

# Set the name of the script file to be generated with extension ".sh"
set(SCRIPT_FILE_NAME ${MODULE_NAME})

# Set the command to activate the virtual environment and run the Python script
set(SCRIPT_CONTENT "#!/bin/bash\nsource ${PATH_TO_VENV}/bin/activate \npython ${PATH_TO_SCRIPT} \"$@\"")

# Generate the script file
file(WRITE ${CMAKE_BINARY_DIR}/bin/${SCRIPT_FILE_NAME} ${SCRIPT_CONTENT})

# Make the script file executable
execute_process(COMMAND chmod +x ${SCRIPT_FILE_NAME})

# Output instructions to the user
message("Your ${SCRIPT_FILE_NAME} script has been created. You can now run it from terminal or yarpmanager.")

find_package(ICUBcontrib REQUIRED)
include(ICUBcontribHelpers)
include(ICUBcontribOptions)
icubcontrib_set_default_prefix()

SET(CMAKE_MODULE_PATH ${ICUB_MODULE_PATH} ${CMAKE_MODULE_PATH})

#print CMAKE_MODULE_PATH
message(STATUS "CMAKE_MODULE_PATH: " ${CMAKE_MODULE_PATH})

# print CMAKE_INSTALL_PREFIX
message(STATUS "CMAKE_INSTALL_PREFIX: " ${CMAKE_INSTALL_PREFIX})

message(STATUS "Installing ${MODULE_NAME} in ${ICUBcontrib_DIR}/bin/${SCRIPT_FILE_NAME}")

# Find Yarp and iCubCONTRIB packages
find_package(YARP  REQUIRED)
FIND_PACKAGE(ICUBcontrib REQUIRED)
list(APPEND CMAKE_MODULE_PATH ${ICUBCONTRIB_MODULE_PATH})
include(ICUBcontribHelpers)
include(ICUBcontribOptions)

icubcontrib_set_default_prefix()
set(ICUB_APPLICATIONS_PREFIX "$ENV{ICUB_ROOT}" CACHE PATH "Application path prefix")

install(FILES ${CMAKE_BINARY_DIR}/bin/${SCRIPT_FILE_NAME} PERMISSIONS ${PROGRAM_PERMISSIONS_DEFAULT} DESTINATION bin)
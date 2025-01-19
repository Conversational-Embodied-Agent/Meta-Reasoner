# Copyright: (C) 2022 Istituto Italiano di Tecnologia | Robotics, Brains and Cognitive Science
# CopyPolicy: Released under the terms of the GNU GPL v2.0.

set(appname ${PROJECT_NAME})

file(GLOB conf ${CMAKE_CURRENT_SOURCE_DIR}/conf/*.ini ${CMAKE_CURRENT_SOURCE_DIR}/conf/*.xml ${CMAKE_CURRENT_SOURCE_DIR}/conf/*.txt ${CMAKE_CURRENT_SOURCE_DIR}/conf/*.sh)
file(GLOB scripts ${CMAKE_CURRENT_SOURCE_DIR}/scripts/*.xml)

yarp_install(FILES ${conf} DESTINATION ${ICUBCONTRIB_CONTEXTS_INSTALL_DIR}/${appname})
#yarp_install(FILES ${scripts} DESTINATION ${ICUBCONTRIB_APPLICATIONS_TEMPLATES_INSTALL_DIR})
yarp_install(FILES ${scripts} DESTINATION ${ICUBCONTRIB_APPLICATIONS_INSTALL_DIR})



project(TestprojectClient)
cmake_minimum_required(VERSION 2.8)

#hardcoded the paths to the RPC folders that appear in rpc_config.cfg
#ideally you would generate the next 3 lines from the config
FILE(GLOB RPC_SOURCES RPC/src/*.c)
FILE(GLOB RPC_HEADERS RPC/generic_include/*.h)
FILE(GLOB RPC_HEADERS RPC/specific_include/*.h)

FILE(GLOB SOURCES *.c*)
FILE(GLOB CPPSOURCES *.c*)
FILE(GLOB HEADERS *.h*)
FILE(GLOB NETWORK_HEADERS ../../SharedSocketCode/*.h*)
FILE(GLOB NETWORK_SOURCES ../../SharedSocketCode/*.c*)

source_group(headers FILES ${HEADERS})
source_group(sources FILES ${SOURCES} ${CPPSOURCES})
source_group(RPC FILES ${RPC_SOURCES})
source_group(RPC FILES ${RPC_HEADERS})
source_group(network FILES ${NETWORK_HEADERS})
source_group(network FILES ${NETWORK_SOURCES})

add_executable(${PROJECT_NAME} ${HEADERS} ${SOURCES} ${RPC_HEADERS} ${RPC_SOURCES} ${NETWORK_HEADERS} ${NETWORK_SOURCES})

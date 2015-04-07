cmake_minimum_required(VERSION 2.8)
execute_process(COMMAND python ../RPC-gen.py ../Testproject/Client/client.h ../Testproject/Server)
add_subdirectory(../Testproject/Client ../bin/Client)
add_subdirectory(../Testproject/Server ../bin/Server)

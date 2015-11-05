# RPC-Generator
A python script that generates code to call functions from one device on another device using a network.

## Current State
The project is completely broken, try again next week.

## Idea
The RPC generator implements serializing and deserializing of function calls and their arguments. When communicating with a device you normally need to make up a protocol, give each message an ID and serialize, deserialize and interpret arguments. This work is done for you by the RPC generator.

## Dependencies

### Required
- [Python](https://www.python.org/)
- [ply.lex](http://www.dabeaz.com/ply/)

### Recommended
- [cmake](http://www.cmake.org/)

### Internally used
- [CppHeaderParser-2.5](https://sourceforge.net/projects/cppheaderparser/)

### Platform
- A C-compiler is required for both the client and the server
- Python is required on the build mashine
- The platform must implement threads and mutexes to allow sending and listening at the same time

## Functionality

Given a server header file (`server.h`) and a client directory, the RPC-Generator will produce the following files:
* RPC_server.h      - Function declarations similar to those in server.h that allow to call the functions across networks.
* RPC_server.c      - Implementation for the RPC-functionality
* RPC_types.h       - Declaration of types used by the RPC
* RPC_network.h     - Declarations of network functions that need to be implemented by the user. See examples for an implementation for TCP sockets
* server.xml        - XML-representation of how function calls are represented by bytes (useful to be read by programs)
* server.html       - HTML-representation of how function calls are represented by bytes (useful to be read by humans)
* documentation.css - Styling for `server.html`

## Getting started

Generate a project using CMake inside `Testprojects/ClientServer/Project` or `Testprojects/AliceBob/Project`.
Compile and run the `ClientServer` testproject to see one way communication and the `AliceBob` testproject to see 2-way communication over TCP sockets.
Next you can add suitable functions in server.h and their implementation in the server to make them available.
Next you may want to replace the network implementation inside network.cpp with communication over USB, Bluetooth, Comports or other network devices.

## TODO

* Add support for unions
* Add python script to read .xml file to implement encode/decode functionality
* Copy comments from source to header
* Add documentation for pragmas
* Benchmark performance, possibly make comparison to other RPC-generators
* Improve smartness of enum values to take #defines and variables into account
* Implement any bit length integer support
* Implement pointer support

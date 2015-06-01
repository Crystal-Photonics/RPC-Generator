# RPC-Generator
A python script that generates code to call functions from one device on another device using a network.

## Current State
The project is in a very early stage and not yet useful.

## Idea
The RPC generator implements serializing and de-serializing of function calls and their arguments. When communicating with a device you normally need to make up a protocol, give each message an ID and serialize, deserialize and interpret arguments. This work is done for you by the RPC generator.

## Dependencies

### Required
- [Python](https://www.python.org/)
- [ply.lex](http://www.dabeaz.com/ply/)

### Recommended
- [cmake](http://www.cmake.org/)

### Internally used
- [CppHeaderParser-2.5](https://sourceforge.net/projects/cppheaderparser/)

## Functionality

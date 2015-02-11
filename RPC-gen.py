import sys
import CppHeaderParser
from copy import deepcopy
from enum import Enum
from itertools import chain

datatypes = {}
defines = {}
currentFile = ""

def getDatatype(signature, file = "???", line = "???"):
    #print(10*"+")
    #print(signature)
    signatureList = signature.split(" ")
    if len(signatureList) == 1: #basic type
        try:
            return datatypes[signature]
        except KeyError:
            try:
                return datatypes[defines[signature]]
            except KeyError:
                assert "Size for type " + signature + " is unknown."
    assert False, 'Unknown type "{0}" in {1}:{2}'.format(
        signature, #0
        file, #1
        line, #2
        )

def isVoidDatatype(datatype):
    try:
        return datatype.size_bytes == 0
    except AttributeError:
        return False

#Metatype describing what all datatypes must be capable of
class Datatype:
    #__init__ #depending on type
    def declaration(self, identifier):
        #returns the declaration for the datatype given its identifier such as "i" -> "int i" or "ia" -> "int ia[32][47]"
        raise NotImplemented
    def stringify(self, destination, identifier, indention):
        #destination is the name of a char * pointing to a buffer
        #identifier is the name of the identifier we want to stringify, can be an expression
        #indention is the indention level of the code
        #returns code that does the stringifying
        raise NotImplemented
    def unstringify(self, source, identifier, indention):
        #source is the name of a char * pointing to a buffer
        #identifier is the name of the identifier we want to unstringify, can be an expression
        #indention is the indention level of the code
        #returns code that does the unstringifying
        raise NotImplemented

class BasicDatatype(Datatype):
    #simple memcpy
    def __init__(self, signature, size_bytes):
        self.signature = signature
        self.size_bytes = size_bytes
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def stringify(self, destination, identifier, indention):
        if self.size_bytes == 0:
            return ""
        return """
{0}/* writing basic type {3} {1} of size {4} */
{0}memcpy({2}, &{1}, {4});
{0}{2} += {4};""".format(
    indention * '\t', #0
    identifier, #1
    destination, #2
    self.signature, #3
    self.size_bytes, #4
    )
    def unstringify(self, source, identifier, indention):
        if self.size_bytes == 0:
            return ""
        if identifier[-1] != ']':
            return ""
        return """
{0}/* reading basic type {3} {1} of size {4} */
{0}memcpy(&{1}, {2}, {4});
{0}{2} += {4};""".format(
    indention * '\t', #0
    identifier, #1
    source, #2
    self.signature, #3
    self.size_bytes, #4
    )

class BasicTransferDatatype(Datatype):
    #copy to temp and then memcpy
    def __init__(self, signature, size_bytes, transfertype):
        self.signature = signature
        self.size_bytes = size_bytes
        self.transfertype = transfertype
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def stringify(self, destination, identifier, indention):
        if self.size_bytes == 0:
            return ""
        return """
{0}/* writing basic type {3} {1} of size {4} */
{0}{{
{0}\t{5} temp = ({5}){1};
{0}\tmemcpy({2}, &temp, {4});
{0}}}
{0}{2} += {4};""".format(
    indention * '\t', #0
    identifier, #1
    destination, #2
    self.signature, #3
    self.size_bytes, #4
    self.transfertype, #5
    )
    def unstringify(self, source, identifier, indention):
        if self.size_bytes == 0:
            return ""
        if identifier[-1] != ']':
            return ""
        return """
{0}/* reading basic type {3}{1} of size {4} */
{0}{
{0}\t{5} temp;
{0}\tmemcpy(&temp, {2}, {4});
{0}\t{2} = temp;
{0}}
{0}{2} += {4};""".format(
    indention * '\t', #0
    identifier, #1
    source, #2
    self.signature, #3
    self.size_bytes, #4
    self.transfertype, #5
    )

class ArrayDatatype(Datatype):
    #need to be mindful of padding, otherwise it is a fixed size loop
    def __init__(self, numberOfElements, datatype, parametername):
        self.numberOfElements = numberOfElements
        self.datatype = datatype
        self.In = parametername.endswith("_in") or parametername.endswith("_inout")
        self.Out = parametername.endswith("_out") or parametername.endswith("_inout")
    def declaration(self, identifier):
        return self.datatype.declaration(identifier + "[" + str(self.numberOfElements) + "]")
    def isInput(identifier):
        return identifier.endswith("in") or identifier.endswith("inout")
    def isOutput(identifier):
        return identifier.endswith("out") or identifier.endswith("inout") or identifier.endswith(']')
    def stringify(self, destination, identifier, indention):
        if self.In:
            return """
{3}/* writing array {0} with {2} elements */
{3}{{
{3}\tint RPC_COUNTER_VAR{5};
{3}\tfor (RPC_COUNTER_VAR{5} = 0; RPC_COUNTER_VAR{5} < {2}; RPC_COUNTER_VAR{5}++){{
{4}
{3}\t}}
{3}}}""".format(
    identifier, #0
    None, #1
    self.numberOfElements, #2
    indention * '\t', #3
    self.datatype.stringify(destination, "" + identifier + "[RPC_COUNTER_VAR{0}]".format(indention), indention + 2), #4
    indention, #5
    )
        else:
            return """
{0}/*Skipping array "{1}", because it is not an input parameter*/""".format(indention * '\t', identifier)
    def unstringify(self, destination, identifier, indention):
        if not ArrayDatatype.isOutput(identifier):
            return '\n{0}/*Skipping array "{1}, because it is not an output parameter*/'.format(
                indention * '\t', #0
                identifier
                )
        return """
{3}/* reading array {0} with {2} elements */
{3}{{
{3}\tint RPC_COUNTER_VAR{5};
{3}\tfor (RPC_COUNTER_VAR{5} = 0; RPC_COUNTER_VAR{5} < {2}; RPC_COUNTER_VAR{5}++){{
{4}
{3}\t}}
{3}}}""".format(
    identifier, #0
    None, #1
    self.numberOfElements, #2
    indention * '\t', #3
    self.datatype.unstringify(destination, identifier + "[RPC_COUNTER_VAR{0}]".format(indention), indention + 2), #4
    indention, #5
    )

class PointerDatatype(Datatype):
    #need to be mindful of parring, otherwise it is a variable sized loop
    #if the pointer is used for input, output or both depends on the name, for example p_in, p_out or p_inout
    def __init__(self, signature, datatype, parametername):
        self.signature = signature
        self.datatype = datatype
        self.In = parametername.endswith("_in") or parametername.endswith("_inout")
        self.Out = parametername.endswith("_out") or parametername.endswith("_inout")
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def setNumberOfElementsIdentifier(self, numberOfElementsIdentifier):
        self.numberOfElementsIdentifier = numberOfElementsIdentifier
    def stringify(self, destination, identifier, indention):
        if self.In:
            return """
{3}/* writing pointer {1}{0} with [{2}] elements*/
{3}{{
{3}\tint i;
{3}\tfor (i = 0; i < {2}; i++){{
{4}
{3}\t}}
{3}}}""".format(
    identifier, #0
    self.signature, #1
    self.numberOfElementsIdentifier, #2
    indention * '\t', #3
    self.datatype.stringify(destination, identifier + "[i]", indention + 2) #4
    )
        else:
            return """
{0}/*Skipping pointer "{1}", because it is not an input parameter*/""".format(indention * '\t', identifier)
    def unstringify(self, destination, identifier, indention):
        return """
{3}/* reading pointer {1}{0} with [{2}] elements*/
{3}{{
{3}\tint i;
{3}\tfor (i = 0; i < {2}; i++){{
{4}
{3}\t}}
{3}}}""".format(
    identifier, #0
    self.signature, #1
    self.numberOfElementsIdentifier, #2
    indention * '\t', #3
    self.datatype.unstringify(destination, identifier + "[i]", indention + 2) #4
    )

class StructDatatype(Datatype):
    #just call the functions of all the members in order
    def __init__(self, signature, memberList, file, lineNumber):
        self.signature = signature
        self.memberList = memberList
        self.file = file
        self.lineNumber = lineNumber
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def stringify(self, destination, identifier, indention):
        members = ", ".join(m["type"] + " " + m["name"] for m in self.memberList)
        #print(self.memberList)
        memberStringification = "".join(getDatatype(m["type"], self.file, self.lineNumber).stringify(destination, identifier + "." + m["name"], indention + 1) for m in self.memberList)
        return "{0}/*writing {4} of type {1} to {2} with members {3}*/\n{0}{{{5}\n{0}}}".format(
            indention * '\t', #0
            self.signature, #1
            destination, #2
            members, #3
            identifier, #4
            memberStringification, #5
            )

class Function:
    #stringify turns a function call into a string and sends it to the other side
    #unstringify turns a string into arguments to pass to a function
    #assumes the send function has the signature (void *, size_t);
    #requests have even numbers, answers have odd numbers
    def __init__(self, ID, returntype, name, parameterlist):
        #returntype can either be a Datatype "void", but no pointer
        if not isVoidDatatype(returntype):
            returnValueName = "return_value_out"
            rt = ArrayDatatype(1, returntype, returnValueName)
            parameterlist.insert(0, (rt, returnValueName))
        self.name = name
        self.parameterlist = parameterlist
        #print(10*'+' + '\n' + "".join(str(p) for p in parameterlist) + '\n' + 10*'-' + '\n')
        self.ID = ID
    def getParameterDeclaration(self):
        parameterdeclaration = ", ".join(p[0].declaration(p[1]) for p in self.parameterlist)
        if parameterdeclaration == "":
            parameterdeclaration = "void"
        return parameterdeclaration
    def getDefinition(self, destination, sendFunction, indention):
        return """
{0}RPC_RESULT {5}({6}){{
{0}\t/***Serializing***/
{0}\tchar *current = {1};
{0}\t*current++ = {2}; /* save ID */
{3}
{0}\t{4}(start, current - {1});
{0}\tif (!(RPC_SLEEP()))
{0}\t\treturn RPC_FAILURE;

{0}\t/***Deserializing***/
{0}\t{7}
{0}\treturn RPC_SUCCESS;
{0}}}
""".format(
    indention * '\t', #0
    destination, #1
    self.ID * 2, #2
    "".join(p[0].stringify("current", p[1], indention + 1) for p in self.parameterlist), #3
    sendFunction, #4
    self.name, #5
    self.getParameterDeclaration(), #6
    "".join(p[0].unstringify("current", p[1], indention + 1) for p in self.parameterlist), #7
    )
    def getDeclaration(self):
        return "RPC_RESULT {0}({1});".format(
            self.name, #0
            self.getParameterDeclaration(), #1
            )

def setBasicDataType(signature, size_bytes):
    datatypes[signature] = BasicDatatype(signature, size_bytes)

def setBasicTransferDataType(signature, size_bytes, transfertype):
    datatypes[signature] = BasicTransferDatatype(signature, size_bytes, transfertype)

def setPredefinedDataTypes():
    typeslist = (
        ("void", 0),
        ("char", 1),
        ("signed char", 1),
        ("unsigned char", 1),
        ("uint8_t", 1),
        ("uint16_t", 2),
        ("uint24_t", 3),
        ("uint32_t", 4),
        ("uint64_t", 8),
        )
    for t in typeslist:
        setBasicDataType(t[0], t[1])

def setEnumTypes(enums):
    for e in enums:
        #calculating minimum and maximim can be done better with map(max, zip(*e["values"])) or something like that
        minimum = maximum = 0
        for v in e["values"]: #parse the definition of the enum values
            if type(v["value"]) == type(0): #its just a (default) int
                intValue = v["value"]
            else:
                try:
                    intValue = int("".join(v["value"].split(" ")))
                    #it is something like "- 1000"
                except:
                    #it is something complicated, assume an int has 4 bytes
                    intValue = 2 ** 30
            minimum = min(minimum, intValue)
            maximum = max(maximum, intValue)
        valRange = maximum - minimum
        name = e["name"] if e["typedef"] else "enum " + e["name"]
        if valRange < 1:
            setBasicDataType(name, 0)
            continue
        from math import log, ceil
        requiredBits = ceil(log(valRange, 2))
        requiredBytes = ceil(requiredBits / 8.)
        if requiredBytes == 0:
            pass
        elif requiredBytes == 1:
            cast = "int8_t"
        elif requiredBytes == 2:
            cast = "int16_t"
        elif requiredBytes == 3 or requiredBytes == 4:
            cast = "int32_t"
        else:
            assert False, "enum " + e["name"] +  " appears to require " + str(requiredBytes) + "bytes and does not fit in a 32 bit integer"
        if minimum < 0:
            cast = "u" + cast
        setBasicTransferDataType(name, requiredBytes, cast)

def setStructTypes(structs):
    for s in structs:
        memberList = []
        for t in structs[s]["properties"]["public"]:
            memberList.append({"type" : t["type"], "name" : t["name"]})
            isTypedef = t["property_of_class"] != s
        assert len(memberList) > 0, "struct with no members is not supported"
        signatue = s if isTypedef else "struct " + s
        datatypes[signatue] = StructDatatype(signatue, memberList, currentFile, structs[s]["line_number"])

def setDefines(newdefines):
    for d in newdefines:
        try:
            l = d.split(" ")
            defines[l[0]] = " ".join(o for o in l[1:])
        except:
            pass

def getFunctionReturnType(function):
    assert function["returns_pointer"] == 0, "in function " + function["debug"] + " line " + str(function["line_number"]) + ": " + "Pointers as return types are not supported"
    return getDatatype(function["rtnType"], currentFile, function["line_number"])

def getParameterArraySizes(parameter):
    tokens = parameter["method"]["debug"].split(" ")
    assert parameter["name"] in tokens, "Error: cannot get non-existing parameter " + parameter["name"] + " from declaration " + parameter["method"]["debug"]
    while tokens[0] != parameter["name"]:
        tokens = tokens[1:]
    tokens = tokens[1:]
    parameterSizes = []
    while tokens[0] == '[':
        tokens = tokens[1:]
        parameterSizes.append("")
        while tokens[0] != ']':
            parameterSizes[-1] += " " + tokens[0]
            tokens = tokens[1:]
        tokens = tokens[1:]
        parameterSizes[-1] = parameterSizes[-1][1:]
    return parameterSizes

def getFunctionParameter(parameter):
    #return (isPointerRequiringSize, DataType)
    if parameter["type"][-1] == '*': #pointer
        assert parameter["type"][-3] != '*', "Multipointer as parameter is not allowed"
        assert parameter["name"].endswith("_in") or parameter["name"].endswith("_out") or parameter["name"].endswith("_inout"),\
               'In {1}:{2}: Pointer parameter "{0}" must either have a suffix "_in", "_out", "_inout" or be a fixed size array.'.format(parameter["name"], currentFile, parameter["line_number"])
        return True, PointerDatatype(parameter["type"], getDatatype(parameter["type"][:-2], currentFile, parameter["line_number"]), parameter["name"])
    basetype = getDatatype(parameter["type"], currentFile, parameter["line_number"])
    if parameter["array"]: #array
        assert parameter["name"][-3:] == "_in" or parameter["name"][-4:] == "_out" or parameter["name"][-6:] == "_inout", 'Array parameter name "' + parameter["name"] + '" must end with "_in", "_out" or "_inout"'
        arraySizes = list(reversed(getParameterArraySizes(parameter)))
        current = ArrayDatatype(arraySizes[0], basetype, parameter["name"])
        arraySizes = arraySizes[1:]
        for arraySize in arraySizes:
            current = ArrayDatatype(arraySize, current, parameter["name"])
        return False, current
    else: #base type
        return False, basetype

def getFunctionParameterList(parameters):
    paramlist = []
    isPointerRequiringSize = False
    for p in parameters:
        if isPointerRequiringSize: #require a size parameter
            pointername = parameters[len(paramlist) - 1]["name"]
            pointersizename = p["name"]
            sizeParameterErrorText = 'Pointer parameter "{0}" must be followed by a size parameter with the name "{0}_size". Or use a fixed size array instead.'.format(pointername)
            assert pointersizename == pointername + "_size", sizeParameterErrorText
            isPointerRequiringSize, parameter = getFunctionParameter(p)
            assert not isPointerRequiringSize, sizeParameterErrorText
            paramlist[-1][0].setNumberOfElementsIdentifier(pointersizename)
            paramlist.append((parameter, p["name"]))
        else:
            isPointerRequiringSize, parameter = getFunctionParameter(p)
            if isVoidDatatype(parameter):
                continue
            parametername = p["name"]
            if parametername == "" and p["type"] != 'void':
                parametername = "unnamed_parameter" + str(len(paramlist))
            paramlist.append((parameter, parametername))
    assert not isPointerRequiringSize, 'Pointer parameter "{0}" must be followed by a size parameter with the name "{0}_size". Or use a fixed size array instead.'.format(parameters[len(paramlist) - 1]["name"])
    #for p in paramlist:
    #    print(p.stringify("buffer", "var", 1))
    return paramlist

def getFunction(function):
    functionList = []
    try:
        getFunction.functionID += 1
    except AttributeError:
        getFunction.functionID = 1
    #for attribute in function:
    #    print(attribute + ":", function[attribute])
    ID = getFunction.functionID
    returntype = getFunctionReturnType(function)
    name = function["name"]
    parameterlist = getFunctionParameterList(function["parameters"])
    return Function(ID, returntype, name, parameterlist)
    #for k in function.keys():
    #    print(k, '=', function[k])
    #for k in function["parameters"][0]["method"].keys():
        #print(k, '=', function["parameters"][0]["method"][k], "\n")
        #print(function["parameters"][0]["method"])
        #for k2 in k["method"].keys():
        #    print(k2, '=', str(k["method"][k2]))
    #print(10*'_')
    #print(function.keys())
    #print("\n")
    #print(10*"_")
    #print(returntype)
    #print(returntype.stringify("buffer", "var", 1))
    #returntype.stringify("buffer", "var", 1)
    #Function(ID, returntype, name, parameterlist)

def checkDefines(defines):
    checklist = (
        ("RPC_SEND", "A #define RPC_SEND is required that takes a const void * and a size and sends data over the network. Example: #define RPC_SEND send"),
        ("RPC_SLEEP", "A #define RPC_SLEEP is required that makes the current thread sleep until RPC_WAKEUP is called or a timeout occured. Returns whether RPC_WAKEUP was called (and a timeout did not occur)"),
        ("RPC_WAKEUP", "A #define RPC_WAKEUP is required that makes the thread sleeping due to RPC_SLEEP wake up"),
        )
    for c in checklist:
        success = False
        for d in defines:
            if d.split(" ")[0].split("(")[0] == c[0]:
                success = True
                break
        assert success, c[1]

def getPathAndFile(filepath):
    from os.path import split
    return split(filepath)

def getIncludeFilePath(include):
    return include[1:-1]

def setTypes(ast):
    setEnumTypes(ast.enums)
    setStructTypes(ast.structs)
    setStructTypes(ast.classes)
    setDefines(ast.defines)

def getNonstandardTypedefs():
    return "#include <stdint.h>\n" + "".join((
        "".join("typedef   int8_t  int{0}_t;\n".format(i) for i in range(1, 8)),
        "".join("typedef  int16_t  int{0}_t;\n".format(i) for i in range(9, 16)),
        "".join("typedef  int32_t  int{0}_t;\n".format(i) for i in range(17, 32)),
        "".join("typedef  uint8_t uint{0}_t;\n".format(i) for i in range(1, 8)),
        "".join("typedef uint16_t uint{0}_t;\n".format(i) for i in range(9, 16)),
        "".join("typedef uint32_t uint{0}_t;\n".format(i) for i in range(17, 32)),
        ))

def getGenericHeader(version):
    return """
/* This file has been generated by RPC Generator {0} */

/* typedefs for non-standard bit integers */
{1}
/* Return value of RPC functions */
typedef enum{{RPC_FAILURE, RPC_SUCCESS}} RPC_RESULT;
/* The optional original return value is returned through the first parameter */
""".format(version, getNonstandardTypedefs())

def generateCode(file):
    #ast = CppHeaderParser.CppHeader("""typedef enum EnumTest{Test} EnumTest;""",  argType='string')
    ast = CppHeaderParser.CppHeader(file)
    #return None
    checkDefines(ast.defines)
    setPredefinedDataTypes()
    #print(ast.includes)
    for i in ast.includes:
        global currentFile
        path = getIncludeFilePath(i)
        currentFile = path
        iast = CppHeaderParser.CppHeader(path)
        setTypes(iast)
    currentFile = file
    #print(ast.enums)
    #print(ast.typedefs_order)
    #print(ast.namespaces)
    #print(ast.global_enums)
    #print(ast.typedefs)
    #return None
    #for a in ast.__dict__:
    #    print(a + ": " + str(getattr(ast, a)))
    setTypes(ast)
    #TODO: structs
    #TODO: typedefs
    #for d in datatypes:
    #    print(d, datatypes[d].size_bytes)
    #return None
    #for a in ast.__dict__:
    #    print(a)
    #generateFunctionCode(ast.functions[0])
    functionlist = []
    for f in ast.functions:
        functionlist.append(getFunction(f))
    cfile = "".join(f.getDefinition("sendBuffer", "send", 0) for f in functionlist) + "\n"
    hfile = "".join(f.getDeclaration() for f in functionlist) + "\n"
    return hfile, cfile
    
hfile, cfile = generateCode("Testdata/multiDimensionalArrayTest.h")
#hfile, cfile = generateCode("test.h")
print(hfile, cfile)
print(len(hfile) + len(cfile), len(hfile.split("\n")) + len(cfile.split("\n")))
#print(" ".join(f["name"] for f in cppHeader.functions))



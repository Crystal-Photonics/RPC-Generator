# Source Header ->
# - RPC header
# - RPC implementation
# - requestParser implementation

import sys
import CppHeaderParser
from copy import deepcopy
from enum import Enum
from itertools import chain
import xml.etree.ElementTree as ET

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
    def setXml(self, xml):
        #adds a description of the data type to the xml entry
        raise NotImplemented
    def declaration(self, identifier):
        #returns the declaration for the datatype given its identifier such as "i" -> "int i" or "ia" -> "int ia[32][47]"
        raise NotImplemented
    def stringify(self, identifier, indention):
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
    def isInput(self, identifier):
        #returns True if this is an input parameter when passed to a function and False otherwise
        #pointers and arrays may be pure output parameters, integers are always input parameters
        #if pointers and arrays are input parameters depends on their identifier name
        raise NotImplemented
    def isOutput(self, identifier):
        #returns True if this is an output parameter when passed to a function and False otherwise
        #pointers and arrays can be output parameters, integers can never be output parameters
        #if pointers and arrays are output parameters depends on their identifier name
        raise NotImplemented
    def getSize(self):
        #returns the number of bytes required to send this datatype over the network
        #pointers return 0.
        raise NotImplemented        

class IntegralDatatype(Datatype):
    def __init__(self, signature, size_bytes):
        self.signature = signature
        self.size_bytes = size_bytes
    def setXml(self, xml):
        xml.set("bits", str(self.size_bytes * 8))
        xml.set("ctype", self.signature)
        if self.signature == "char":
            xml.set("type", "character")
        else:
            xml.set("type", "integer")
            typ = ET.SubElement(xml, "integer")
            signed = "False" if self.signature[0] == "u" else "True"
            typ.set("signed", signed)
    def getByte(number, identifier):
        assert number < 8, "Do not know how to portably deal with integers bigger than 64 bit"
        if number == 0:
            return "{0}".format(identifier)
        elif number < 2:
            return "{0} >> {1}".format(identifier, 8 * number)
        elif number < 4:
            return "{0} >> {1}".format(identifier, 8 * number)
        elif number < 8:
            return "{0} >> {1}".format(identifier, 8 * number)
    def orByte(number, identifier, source):
        assert number < 8, "Do not know how to portably deal with integers bigger than 64 bit"
        if number == 0:
            return "{0} |= {1}".format(identifier, source)
        elif number < 2:
            return "{0} |= {1} << {2}".format(identifier, source, 8 * number)
        elif number < 4:
            return "{0} |= {1} << {2}L".format(identifier, source, 8 * number)
        elif number < 8:
            return "{0} |= {1} << {2}LL".format(identifier, source, 8 * number)
    #use bitshift to prevent endianess problems
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def stringify(self, identifier, indention):
        return """
{indention}/* writing integral type {type} {identifier} of size {size} */
{datapush}""".format(
    indention = indention * '\t',
    identifier = identifier,
    type = self.signature,
    size = self.size_bytes,
    datapush = "".join(indention * '\t' + "RPC_push_byte((unsigned char)(" + IntegralDatatype.getByte(i, identifier) + "));\n" for i in range(self.size_bytes)), #5
    )
    def unstringify(self, source, identifier, indention):
        if self.size_bytes == 0:
            return ""
        return """
{0}/* reading integral type {3} {1} of size {4} */
{0}{1} = *{2}++;
{5}""".format(
    indention * '\t', #0
    identifier, #1
    source, #2
    self.signature, #3
    self.size_bytes, #4
    "".join(indention * '\t' + IntegralDatatype.orByte(i, identifier, "(*" + source + "++)") + ";\n" for i in range(1, self.size_bytes)), #5
    )
    def isInput(self, identifier):
        return True
    def isOutput(self, identifier):
        return False
    def getSize(self):
        assert type(self.size_bytes) == int
        return self.size_bytes
    
class BasicTransferDatatype(Datatype):
    def __init__(self, signature, size_bytes, transfertype):
        self.signature = signature
        self.size_bytes = size_bytes
        self.transfertype = transfertype
    def setXml(self, xml):
        xml.set("bits", str(self.size_bytes * 8))
        xml.set("ctype", self.signature)
        typ = ET.SubElement(xml, "basic")
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def stringify(self, identifier, indention):
        #TODO: Fix memcpy and destination
        if self.size_bytes == 0:
            return ""
        return """
{0}/* writing basic type {3} {1} of size {4} */
{0}{{
{0}	{5} temp = ({5}){1};
{0}	memcpy({2}, &temp, {4});
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
{0}	{5} temp;
{0}	memcpy(&temp, {2}, {4});
{0}	{2} = temp;
{0}}
{0}{2} += {4};""".format(
    indention * '\t', #0
    identifier, #1
    source, #2
    self.signature, #3
    self.size_bytes, #4
    self.transfertype, #5
    )
    def isInput(self, identifier):
        return True
    def isOutput(self, identifier):
        return False
    def getSize(self):
        assert type(self.size_bytes) == int
        return self.size_bytes

class ArrayDatatype(Datatype):
    #need to be mindful of padding, otherwise it is a fixed size loop
    def __init__(self, numberOfElements, datatype, parametername):
        self.numberOfElements = numberOfElements
        self.datatype = datatype
        self.In = parametername.endswith("_in") or parametername.endswith("_inout")
        self.Out = parametername.endswith("_out") or parametername.endswith("_inout")
    def setXml(self, xml):
        xml.set("bits", str(self.getSize() * 8))
        xml.set("ctype", self.declaration(""))
        xml.set("type", "array")
        typ = ET.SubElement(xml, "array")
        typ.set("elements", self.numberOfElements)
        self.datatype.setXml(typ)
    def declaration(self, identifier):
        return self.datatype.declaration(identifier + "[" + str(self.numberOfElements) + "]")
    def isInput(self, identifier):
        return identifier.endswith("in") or identifier.endswith("inout")
    def isOutput(self, identifier):
        return identifier.endswith("out") or identifier.endswith("inout") or identifier.endswith(']')
    def stringify(self, identifier, indention):
        if self.numberOfElements == "1":
            #no loop required for 1 element
            return "{0}{1}".format(indention * '\t', self.datatype.stringify("*" + identifier, indention))
        return """
{indention}/* writing array {name} with {numberOfElements} elements */
{indention}{{
{indention}	int RPC_COUNTER_VAR{indentID};
{indention}	for (RPC_COUNTER_VAR{indentID} = 0; RPC_COUNTER_VAR{indentID} < {numberOfElements}; RPC_COUNTER_VAR{indentID}++){{
{serialization}
{indention}	}}
{indention}}}""".format(
    name = identifier,
    numberOfElements = self.numberOfElements,
    indention = indention * '\t',
    serialization = self.datatype.stringify("" + identifier + "[RPC_COUNTER_VAR{0}]".format(indention), indention + 2),
    indentID = indention,
    )
    def unstringify(self, destination, identifier, indention):
        if self.numberOfElements == "1":
            #no loop required for 1 element
            return "{0}{1}".format(indention * '\t', self.datatype.unstringify(destination, "*" + identifier, indention))
        return """
{3}/* reading array {0} with {2} elements */
{3}{{
{3}	int RPC_COUNTER_VAR{5};
{3}	for (RPC_COUNTER_VAR{5} = 0; RPC_COUNTER_VAR{5} < {2}; RPC_COUNTER_VAR{5}++){{
{4}
{3}	}}
{3}}}""".format(
    identifier, #0
    None, #1
    self.numberOfElements, #2
    indention * '\t', #3
    self.datatype.unstringify(destination, identifier + "[RPC_COUNTER_VAR{0}]".format(indention), indention + 2), #4
    indention, #5
    )
    def getSize(self):
        return int(self.numberOfElements) * self.datatype.getSize()

class PointerDatatype(Datatype):
    #need to be mindful of parring, otherwise it is a variable sized loop
    #if the pointer is used for input, output or both depends on the name, for example p_in, p_out or p_inout
    def __init__(self, signature, datatype, parametername):
        assert None, "Code for pointers does not work yet"
        self.signature = signature
        self.datatype = datatype
        self.In = parametername.endswith("_in") or parametername.endswith("_inout")
        self.Out = parametername.endswith("_out") or parametername.endswith("_inout")
    def setXml(self, xml):
        xml.set("bits", "???")
        xml.set("ctype", self.signature)
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def setNumberOfElementsIdentifier(self, numberOfElementsIdentifier):
        self.numberOfElementsIdentifier = numberOfElementsIdentifier
    def stringify(self, identifier, indention):
        return """
{indention}/* writing pointer {type}{name} with {index} elements*/
{indention}{{
{indention}	int i;
{indention}	for (i = 0; i < {index}; i++){{
{serialization}
{indention}	}}
{indention}}}""".format(
    name = identifier,
    type = self.signature,
    index = self.numberOfElementsIdentifier,
    indention = indention * '\t',
    serialization = self.datatype.stringify(identifier + "[i]", indention + 2),
    )
    def unstringify(self, destination, identifier, indention):
        return """
{indention}/* reading pointer {signature}{identifier} with [{numberOfElementsIdentifier}] elements*/
{indention}{{
{indention}	int i;
{indention}	for (i = 0; i < {numberOfElementsIdentifier}; i++){{
{idDeserializer}
{indention}	}}
{indention}}}""".format(
    identifier = identifier,
    signature = self.signature,
    numberOfElementsIdentifier = self.numberOfElementsIdentifier,
    indention = indention * '\t',
    idDeserializer = self.datatype.unstringify(destination, identifier + "[i]", indention + 2),
    )
    def isInput(self, identifier):
        return self.In
    def isOutput(self, identifier):
        return self.Out
    def getSize(self):
        return 0.

class StructDatatype(Datatype):
    #just call the functions of all the members in order
    def __init__(self, signature, memberList, file, lineNumber):
        self.signature = signature
        self.memberList = memberList
        self.file = file
        self.lineNumber = lineNumber
    def setXml(self, xml):
        xml.set("bits", str(self.getSize()))
        xml.set("ctype", self.signature)
    def declaration(self, identifier):
        return self.signature + " " + identifier
    def stringify(self, identifier, indention):
        members = ", ".join(m["type"] + " " + m["name"] for m in self.memberList)
        #print(self.memberList)
        memberStringification = "".join(getDatatype(m["type"], self.file, self.lineNumber).stringify(identifier + "." + m["name"], indention + 1) for m in self.memberList)
        return "{indention}/*writing {identifier} of type {type} with members {members}*/\n{indention}{{{memberStringification}\n{indention}}}".format(
            indention = indention * '\t',
            type = self.signature,
            members = members,
            identifier = identifier,
            memberStringification = memberStringification,
            )
    def isInput(self, identifier):
        #TODO: Go through members and return if for any of them isInput is true
        raise NotImplemented
    def isOutput(self, identifier):
        #TODO: Go through members and return if for any of them isOutput is true
        raise NotImplemented
    def getSize(self):
        return sum(m.getSize() for m in self.memberList)

class Function:
    #stringify turns a function call into a string and sends it to the other side
    #unstringify turns a string into arguments to pass to a function
    #assumes the send function has the signature (void *, size_t);
    #requests have even numbers, answers have odd numbers
    def __init__(self, ID, returntype, name, parameterlist):
        #returntype can either be a Datatype "void", but no pointer
        self.isVoidReturnType = isVoidDatatype(returntype)
        if not self.isVoidReturnType:
            returnValueName = "return_value_out"
            rt = ArrayDatatype("1", returntype, returnValueName)
            parameterlist.insert(0, {"parameter":rt, "parametername":returnValueName})
        self.name = name
        self.parameterlist = parameterlist
        #print(10*'+' + '\n' + "".join(str(p) for p in parameterlist) + '\n' + 10*'-' + '\n')
        self.ID = ID
    def getXml(self, entry):
        if self.name in functionIgnoreList:
            return
        entry.set("name", self.name)
        declaration = ET.SubElement(entry, "declaration")
        declaration.text = self.getDeclaration()
        request = ET.SubElement(entry, "request")
        request.set("ID", str(self.ID * 2))
        i = 1
        for p in self.parameterlist:
            if not p["parameter"].isInput(p["parametername"]):
                continue
            param = ET.SubElement(request, "parameter")
            param.set("position", str(i))
            param.set("name", p["parametername"])
            i += 1
            p["parameter"].setXml(param)
        if self.name in functionNoAnswerList:
            return
        reply = ET.SubElement(entry, "reply")
        reply.set("ID", str(self.ID * 2 + 1))
        i = 1
        for p in self.parameterlist:
            if not p["parameter"].isOutput(p["parametername"]):
                continue
            param = ET.SubElement(reply, "parameter")
            param.set("position", str(i))
            param.set("name", p["parametername"])
            i += 1
            p["parameter"].setXml(param)
        
    def getParameterDeclaration(self):
        parameterdeclaration = ", ".join(p["parameter"].declaration(p["parametername"]) for p in self.parameterlist)
        if parameterdeclaration == "":
            parameterdeclaration = "void"
        return parameterdeclaration
    def getCall(self):
        #print(self.name, self.parameterlist)
        returnvalue = "*return_value_out = " if not self.isVoidReturnType else ""
        parameterlist = self.parameterlist if self.isVoidReturnType else self.parameterlist[1:]
        return "{returnvalue}{functionname}({parameterlist});".format(
            returnvalue = returnvalue,
            functionname = self.name,
            parameterlist = ", ".join(p["parametername"] for p in parameterlist),
            )
    def getDefinition(self):
        if self.name in functionNoAnswerList:
            return """
RPC_RESULT {functionname}({parameterdeclaration}){{
	RPC_RESULT result;
	RPC_mutex_lock(RPC_mutex_caller);
	RPC_mutex_lock(RPC_mutex_in_caller);

	/***Serializing***/
	RPC_push_byte({requestID}); /* save ID */
{inputParameterSerializationCode}
	result = RPC_commit();

	/* This function has been set to receive no answer */

	RPC_mutex_unlock(RPC_mutex_in_caller);
	RPC_mutex_unlock(RPC_mutex_caller);
	return result;
}}
""".format(
    requestID = self.ID * 2,
    inputParameterSerializationCode = "".join(p["parameter"].stringify(p["parametername"], 1) for p in self.parameterlist if p["parameter"].isInput(p["parametername"])),
    functionname = self.name,
    parameterdeclaration = self.getParameterDeclaration(),
    )
        return """
RPC_RESULT {functionname}({parameterdeclaration}){{
	RPC_mutex_lock(RPC_mutex_caller);
	
	for (;;){{
		RPC_mutex_lock(RPC_mutex_in_caller);

		/***Serializing***/
		RPC_push_byte({requestID}); /* save ID */
{inputParameterSerializationCode}
		if (RPC_commit() == RPC_SUCCESS){{ /* successfully sent request */
			if (RPC_mutex_lock_timeout(RPC_mutex_answer)){{ /* Wait for answer to arrive */
				if (*RPC_buffer++ != {answerID}){{ /* We got an incorrect answer */
					RPC_mutex_unlock(RPC_mutex_in_caller);
					RPC_mutex_lock(RPC_mutex_parsing_complete);
					RPC_mutex_unlock(RPC_mutex_parsing_complete);
					RPC_mutex_unlock(RPC_mutex_answer);
					continue; /* Try if next answer is correct */
				}}
				/***Deserializing***/
{outputParameterDeserialization}
				RPC_mutex_unlock(RPC_mutex_in_caller);
				RPC_mutex_lock(RPC_mutex_parsing_complete);
				RPC_mutex_unlock(RPC_mutex_parsing_complete);
				RPC_mutex_unlock(RPC_mutex_answer);
				RPC_mutex_unlock(RPC_mutex_caller);
				return RPC_SUCCESS;
			}}
			else {{ /* We failed to get an answer due to timeout */
				RPC_mutex_unlock(RPC_mutex_in_caller);
				RPC_mutex_unlock(RPC_mutex_caller);
				return RPC_FAILURE;
			}}
		}}
		else {{ /* Sending request failed */
			RPC_mutex_unlock(RPC_mutex_in_caller);
			RPC_mutex_unlock(RPC_mutex_caller);
			return RPC_FAILURE;
		}}
	}}
	/* assert_dead_code; */
}}
""".format(
    requestID = self.ID * 2,
    answerID = self.ID * 2 + 1,
    inputParameterSerializationCode = "".join(p["parameter"].stringify(p["parametername"], 2) for p in self.parameterlist if p["parameter"].isInput(p["parametername"])),
    functionname = self.name,
    parameterdeclaration = self.getParameterDeclaration(),
    outputParameterDeserialization = "".join(p["parameter"].unstringify("RPC_buffer", p["parametername"], 4) for p in self.parameterlist if p["parameter"].isOutput(p["parametername"])),
    )
    def getDeclaration(self):
        return "RPC_RESULT {0}({1});".format(
            self.name, #0
            self.getParameterDeclaration(), #1
            )
    def getRequestParseCase(self, buffer):
        if self.name in functionNoAnswerList:
            return """
		case {ID}: /* {declaration} */
		{{
		/* Declarations */
{parameterdeclarations}
		/* Read input parameters */
{inputParameterDeserialization}
		/* Call function */
			{functioncall}
		/* This function has been set to receive no answer */
		}}
		break;""".format(
    ID = self.ID * 2,
    declaration = self.getDeclaration(),
    parameterdeclarations = "".join("\t\t\t" + p["parameter"].declaration(p["parametername"]) + ";\n" for p in self.parameterlist),
    inputParameterDeserialization = "".join(p["parameter"].unstringify(buffer, p["parametername"], 3) for p in self.parameterlist if p["parameter"].isInput(p["parametername"])),
    functioncall = self.getCall(),
    )
        return """
		case {ID}: /* {declaration} */
		{{
		/***Declarations***/
{parameterdeclarations}
		/***Read input parameters***/
{inputParameterDeserialization}
		/***Call function***/
			{functioncall}
		/***send return value and output parameters***/
			RPC_push_byte({ID_plus_1});
			{outputParameterSerialization}
			RPC_commit();
		}}
		break;""".format(
    ID = self.ID * 2,
    declaration = self.getDeclaration(),
    parameterdeclarations = "".join("\t\t\t" + p["parameter"].declaration(p["parametername"]) + ";\n" for p in self.parameterlist),
    inputParameterDeserialization = "".join(p["parameter"].unstringify(buffer, p["parametername"], 3) for p in self.parameterlist if p["parameter"].isInput(p["parametername"])),
    functioncall = self.getCall(),
    outputParameterSerialization = "".join(p["parameter"].stringify(p["parametername"], 3) for p in self.parameterlist if p["parameter"].isOutput(p["parametername"])),
    ID_plus_1 = self.ID * 2 + 1
    )
    def getAnswerSizeCase(self, buffer):
        if self.name in functionNoAnswerList:
            return """\t\t/* case {ID}: {declaration}
\t\t\tThis function has been set to receive no answer */
""".format(
    declaration = self.getDeclaration(),
    ID = self.ID * 2 + 1,
    )
        size = 1 + sum(p["parameter"].getSize() for p in self.parameterlist if p["parameter"].isOutput(p["parametername"]))
        retvalsetcode = ""
        if type(size) == float: #variable length
            retvalsetcode += """			if (size_bytes >= 3)
				returnvalue.size = {buffer}[1] + {buffer}[2] << 8;
			else{{
				returnvalue.size = 3;
				returnvalue.result = RPC_COMMAND_INCOMPLETE;
			}}""".format(buffer = buffer)
        else:
            retvalsetcode += "\t\t\treturnvalue.size = " + str(size) + ";"
        return """\t\tcase {ID}: /* {declaration} */
{retvalsetcode}
\t\t\tbreak;
""".format(
    declaration = self.getDeclaration(),
    ID = self.ID * 2 + 1,
    retvalsetcode = retvalsetcode,
    )
    def getAnswerParseCase(self, buffer):
        if self.name in functionNoAnswerList:
            return ""
        return """\t\tcase {ID}: /* {declaration} */
\t\t\tbreak; /*TODO*/
""".format(
    ID = self.ID * 2 + 1,
    declaration = self.getDeclaration(),
    )
    def getRequestSizeCase(self, buffer):
        size = 1 + sum(p["parameter"].getSize() for p in self.parameterlist if p["parameter"].isInput(p["parametername"]))
        retvalsetcode = ""
        if type(size) == float: #variable length
            retvalsetcode += """			if (size_bytes >= 3)
				returnvalue.size = {buffer}[1] + {buffer}[2] << 8;
			else{{
				returnvalue.size = 3;
				returnvalue.result = RPC_COMMAND_INCOMPLETE;
			}}""".format(buffer = buffer)
        else:
            retvalsetcode += "\t\t\treturnvalue.size = " + str(size) + ";"
        return """
\t\tcase {answerID}: /* {functiondeclaration} */
{retvalsetcode}
\t\t\tbreak;
""".format(
    answerID = self.ID * 2,
    retvalsetcode = retvalsetcode,
    functiondeclaration = self.getDeclaration(),
    )

def setIntegralDataType(signature, size_bytes):
    datatypes[signature] = IntegralDatatype(signature, size_bytes)

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
        ("int8_t", 1),
        ("int16_t", 2),
        ("int24_t", 3),
        ("int32_t", 4),
        ("int64_t", 8),
        ("uint8_t", 1),
        ("uint16_t", 2),
        ("uint24_t", 3),
        ("uint32_t", 4),
        ("uint64_t", 8),
        )
    for t in typeslist:
        setIntegralDataType(t[0], t[1])

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
        return {"isPointerRequiringSize":True, "parameter":PointerDatatype(parameter["type"], getDatatype(parameter["type"][:-2], currentFile, parameter["line_number"]), parameter["name"])}
    basetype = getDatatype(parameter["type"], currentFile, parameter["line_number"])
    if parameter["array"]: #array
        assert parameter["name"][-3:] == "_in" or parameter["name"][-4:] == "_out" or parameter["name"][-6:] == "_inout", 'Array parameter name "' + parameter["name"] + '" must end with "_in", "_out" or "_inout"'
        arraySizes = list(reversed(getParameterArraySizes(parameter)))
        current = ArrayDatatype(arraySizes[0], basetype, parameter["name"])
        arraySizes = arraySizes[1:]
        for arraySize in arraySizes:
            current = ArrayDatatype(arraySize, current, parameter["name"])
        return {"isPointerRequiringSize":False, "parameter":current}
    else: #base type
        return {"isPointerRequiringSize":False, "parameter":basetype}

def getFunctionParameterList(parameters):
    paramlist = []
    isPointerRequiringSize = False
    for p in parameters:
        if isPointerRequiringSize: #require a size parameter
            pointername = parameters[len(paramlist) - 1]["name"]
            pointersizename = p["name"]
            sizeParameterErrorText = 'Pointer parameter "{0}" must be followed by a size parameter with the name "{0}_size". Or use a fixed size array instead.'.format(pointername)
            assert pointersizename == pointername + "_size", sizeParameterErrorText
            functionparameter = getFunctionParameter(p)
            isPointerRequiringSize = functionparameter["isPointerRequiringSize"]
            parameter = functionparameter["parameter"]
            assert not isPointerRequiringSize, sizeParameterErrorText
            paramlist[-1]["parameter"].setNumberOfElementsIdentifier(pointersizename)
            paramlist.append({"parameter":parameter, "parametername":p["name"]})
        else:
            functionparameter = getFunctionParameter(p)
            isPointerRequiringSize = functionparameter["isPointerRequiringSize"]
            parameter = functionparameter["parameter"]
            if isVoidDatatype(parameter):
                continue
            parametername = p["name"]
            if parametername == "" and p["type"] != 'void':
                parametername = "unnamed_parameter" + str(len(paramlist))
            paramlist.append({"parameter":parameter, "parametername":parametername})
    assert not isPointerRequiringSize, 'Pointer parameter "{0}" must be followed by a size parameter with the name "{0}_size". Or use a fixed size array instead.'.format(parameters[len(paramlist) - 1]["name"])
    #for p in paramlist:
    #    print(p.stringify("buffer", "var", 1))
    return paramlist

def getFunction(function):
    functionList = []
    try:
        getFunction.functionID += 1
        assert getFunction.functionID < 255, "Too many functions, require changes to allow bigger function ID variable"
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
/* The optional original return value is returned through the first parameter */
""".format(version, getNonstandardTypedefs())

def getSizeFunction(functions, clientHeader):
    return """#include "RPC_network.h"
#include "{}"

/* Receives a pointer to a (partly) received message and it's size.
   Returns a result and a size. If size equals RPC_SUCCESS then size is the
   size that the message is supposed to have. If result equals RPC_COMMAND_INCOMPLETE
   then more bytes are required to determine the size of the message. In this case
   size is the expected number of bytes required to determine the correct size.*/
RPC_SIZE_RESULT RPC_get_request_size(const void *buffer, size_t size_bytes){{
	const unsigned char *current = (const unsigned char *)buffer;
	RPC_SIZE_RESULT returnvalue;

	if (size_bytes == 0){{
		returnvalue.result = RPC_COMMAND_INCOMPLETE;
		returnvalue.size = 1;
		return returnvalue;
	}}

	switch (*current){{ /* switch by message ID */{}
		default:
			returnvalue.result = RPC_COMMAND_UNKNOWN;
			break;
	}}
	returnvalue.result = returnvalue.size > size_bytes ? RPC_COMMAND_INCOMPLETE : RPC_SUCCESS;
	return returnvalue;
}}
""".format(
    clientHeader,
    "".join(f.getRequestSizeCase("current") for f in functions),
    )

def getRequestParser(functions):
    buffername = "current"
    return """
/* This function parses RPC requests, calls the original function and sends an
   answer. */
void RPC_parse_request(const void *buffer, size_t size_bytes){{
	const unsigned char *{1} = (const unsigned char *)buffer;
	switch (*current++){{ /* switch (request ID) */ {0}
	}}
}}""".format(
    "".join(f.getRequestParseCase(buffername) for f in functions), #0
    buffername, #1
    )

def getAnswerParser(functions):
    return """
/* This function pushes the answers to the caller, doing all the necessary synchronization. */
void RPC_parse_answer(const void *buffer, size_t size_bytes){
	RPC_buffer = (const unsigned char *)buffer;
	assert(RPC_get_answer_length(buffer, size_bytes).result == RPC_SUCCESS);
	assert(RPC_get_answer_length(buffer, size_bytes).size <= size_bytes);

	RPC_mutex_unlock(RPC_mutex_answer);
	RPC_mutex_lock(RPC_mutex_in_caller);
	RPC_mutex_unlock(RPC_mutex_parsing_complete);
	RPC_mutex_lock(RPC_mutex_answer);
	RPC_mutex_lock(RPC_mutex_parsing_complete);
	RPC_mutex_unlock(RPC_mutex_in_caller);
}
"""

def getRPC_Parser_init():
    return """
void RPC_Parser_init(){
	if (RPC_initialized)
		return;
	RPC_initialized = 1;
	RPC_mutex_lock(RPC_mutex_parsing_complete);
	RPC_mutex_lock(RPC_mutex_answer);
}
"""

def getRPC_Parser_exit():
    return """
void RPC_Parser_exit(){
	if (!RPC_initialized)
		return;
	RPC_initialized = 0;
	RPC_mutex_unlock(RPC_mutex_parsing_complete);
	RPC_mutex_unlock(RPC_mutex_answer);
}
"""

def getAnswerSizeChecker(functions):
    return """/* Get (expected) size of (partial) answer. */
RPC_SIZE_RESULT RPC_get_answer_length(const void *buffer, size_t size_bytes){{
	RPC_SIZE_RESULT returnvalue;
	const unsigned char *current = (const unsigned char *)buffer;
	if (!size_bytes){{
		returnvalue.result = RPC_COMMAND_INCOMPLETE;
		returnvalue.size = 1;
		return returnvalue;
	}}
	switch (*current){{
{answercases}		default:
			returnvalue.result = RPC_COMMAND_UNKNOWN;
			return returnvalue;
	}}
	returnvalue.result = returnvalue.size > size_bytes ? RPC_COMMAND_INCOMPLETE : RPC_SUCCESS;
	return returnvalue;
}}
""".format(
    answercases = "".join(f.getAnswerSizeCase("current") for f in functions),
    )

functionIgnoreList = []
functionNoAnswerList = []
def evaluatePragmas(pragmas):
    for p in pragmas:
        program, command = p.split(" ", 1)
        if program == "RPC":
            try:
                command, target = command.split(" ", 1)
            except ValueError:
                assert False, "Invalid command or parameter: {} in {}".format(command, currentFile)
            if command == "ignore":
                assert len(target.split(" ")) == 1, "Invalid function name: {} in {}".format(target, currentFile)
                functionIgnoreList.append(target)
            elif command == "noanswer":
                functionNoAnswerList.append(target)
            else:
                assert False, "Unknown command {} in {}".format(command, currentFile)

def generateCode(file, xml):
    #ast = CppHeaderParser.CppHeader("""typedef enum EnumTest{Test} EnumTest;""",  argType='string')
    ast = CppHeaderParser.CppHeader(file)
    #return None
    #checkDefines(ast.defines)
    setPredefinedDataTypes()
    #print(ast.includes)
    for i in ast.includes:
        global currentFile
        path = getIncludeFilePath(i)
        currentFile = path
        try:
            iast = CppHeaderParser.CppHeader(path)
            setTypes(iast)
        except FileNotFoundError:
            print('Warning: #include file "{}" not found, skipping'.format(path))
    currentFile = file
    evaluatePragmas(ast.pragmas)
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
        if not f["name"] in functionIgnoreList:
            functionlist.append(getFunction(f))
    rpcHeader = "\n".join(f.getDeclaration() for f in functionlist)
    rpcImplementation = "\n".join(f.getDefinition() for f in functionlist)
    for f in functionlist:
        entry = ET.SubElement(xml, "function")
        f.getXml(entry)
    from os.path import basename
    requestParserImplementation = externC_intro + '\n' + getSizeFunction(functionlist, basename(file)) + getRequestParser(functionlist) + externC_outro
    answerSizeChecker = getAnswerSizeChecker(functionlist)
    answerParser = getAnswerParser(functionlist)
    return rpcHeader, rpcImplementation, requestParserImplementation, answerParser, answerSizeChecker

def getFilePaths():
    #get paths for various files that need to be created. all created files start with "RPC_"
    #parse input
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("ServerHeader", help = "Header file with functions that need to be called from the client", type = str)
    parser.add_argument("ClientDirectory", help = "Destination folder for RPC files", type = str)
    args = parser.parse_args()

    #check if input is valid
    from os.path import isfile, isdir, abspath, join, split
    assert isfile(args.ServerHeader)
    assert args.ServerHeader.endswith(".h"), args.ServerHeader + "Does not appear to be a header file"
    assert isdir(args.ClientDirectory)

    serverHeaderPath, serverHeaderFilename = split(args.ServerHeader)

    return {
        "ServerHeader" : abspath(args.ServerHeader),
        "ServerHeaderFileName" : serverHeaderFilename,
        "ClientHeader" : join(args.ClientDirectory, "RPC_" + serverHeaderFilename),
        "ClientImplementation" : join(args.ClientDirectory, "RPC_" + serverHeaderFilename[:-1] + 'c'),
        "RPC_serviceHeader" : join(serverHeaderPath, "RPC_service.h"),
        "RPC_serviceImplementation" : join(serverHeaderPath, "RPC_service.c"),
        "ClientRpcTypesHeader" : join(args.ClientDirectory, "RPC_types.h"),
        "ServerRpcTypesHeader" : join(serverHeaderPath, "RPC_types.h"),
        "ClientNetworkImplementation" : join(args.ClientDirectory, "RPC_network_implementation"),
        "ClientNetworkHeader" : join(args.ClientDirectory, "RPC_network.h"),
        "ServerNetworkHeader" : join(serverHeaderPath, "RPC_network.h"),
        "xmldump" : join(args.ClientDirectory, serverHeaderFilename[:-1] + "xml"),
        }

doNotModifyHeader = """/* This file has been automatically generated by RPC-Generator
   https://github.com/Crystal-Photonics/RPC-Generator
   You should not modify this file manually. */
"""

externC_intro = """#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */
"""
externC_outro = """
#ifdef __cplusplus
}
#endif /* __cplusplus */
"""

rpc_enum = """typedef enum{
    RPC_SUCCESS,
    RPC_FAILURE,
    RPC_COMMAND_UNKNOWN,
    RPC_COMMAND_INCOMPLETE
} RPC_RESULT;
"""

def getRPC_serviceHeader(headers, headername):
    headerDefine = headername.upper()
    return """{doNotModify}
{includeguardintro}
{externC_intro}
{rpc_declarations}{externC_outro}
{includeguardoutro}
""".format(
        doNotModify = doNotModifyHeader,
        externC_intro = externC_intro,
        externC_outro = externC_outro,
        includeguardintro = """#ifndef {}
#define {}
""".format(headerDefine, headerDefine),
        includeguardoutro = """#endif /* not {} */""".format(headerDefine),
        rpc_declarations = """#include <stddef.h>
#include <inttypes.h>
#include "RPC_types.h"

/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   The following functions's implementations are automatically generated.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

void RPC_Parser_init(void);
/* Initializes various states required for the RPC. Must be called before any
   other RPC_* function. Must be called by the parser thread. */

void RPC_Parser_exit(void);
/* Frees various states required for the RPC. Must be called after any
   other RPC_* function */

RPC_SIZE_RESULT RPC_get_answer_length(const void *buffer, size_t size);
/* Returns the (expected) length of the beginning of a (partial) message.
   If returnvalue.result equals RPC_SUCCESS then returnvalue.size equals the
   expected size in bytes.
   If returnvalue.result equals RPC_COMMAND_UNKNOWN then the buffer does not point
   to the beginning of a recognized message and returnvalue.size has no meaning.
   If returnvalue.result equals RPC_COMMAND_INCOMPLETE then returnvalue.size equals
   the minimum number of bytes required to figure out the length of the message. */

void RPC_parse_answer(const void *buffer, size_t size);
/* This function parses answer received from the network. {{buffer}} points to the
   buffer that contains the received data and {{size}} contains the number of bytes
   that have been received (NOT the size of the buffer!). This function will wake
   up RPC_*-functions below that are waiting for an answer.
   Do not call this function with an incomplete message. Use RPC_get_answer_length
   to make sure it is a complete message. */

/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   These are the payload functions made available by the RPC generator.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/
/* //TODO: copy comments for documentation */
{}
""".format(
    headers,
    ),)

def getNetworkHeader():
    return """
/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   IMPORTANT: The following functions must be implemented by YOU.
   They are required for the RPC to work.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

{}
#ifndef RPC_NETWORK_H
#define RPC_NETWORK_H

#include "RPC_types.h"

{}
void RPC_start_message(size_t size);
/*  This function is called when a new message starts. {{size}} is the number of
    bytes the message will require. In the implementation you can allocate  a
    buffer or write a preamble. The implementation can be empty if you do not
    need to do that. */

void RPC_push_byte(unsigned char byte);
/* Pushes a byte to be sent via network. You should put all the pushed bytes
   into a buffer and send the buffer when RPC_commit is called. If you run
   out of buffer space you can send multiple partial messages as long as the
   other side puts them back together. */

RPC_RESULT RPC_commit(void);
/* This function is called when a complete message has been pushed using
   RPC_push_byte. Now is a good time to send the buffer over the network,
   even if the buffer is not full yet. You may also want to free the buffer that
   you may have allocated in the RPC_start_message function.
   RPC_commit should return RPC_SUCCESS if the buffer has been successfully
   sent and RPC_FAILURE otherwise. */

/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   You need to define 4 mutexes to implement the RPC_mutex_* functions below.
   See RPC_types.h for a definition of RPC_mutex_id.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

void RPC_mutex_lock(RPC_mutex_id mutex_id);
/* Locks the mutex. If it is already locked it yields until it can lock the mutex. */

void RPC_mutex_unlock(RPC_mutex_id mutex_id);
/* Unlocks the mutex. The mutex is locked when the function is called. */

char RPC_mutex_lock_timeout(RPC_mutex_id mutex_id);
/* Tries to lock a mutex. Returns 1 if the mutex was locked and 0 if a timeout
   occured. The timeout length should be the time you want to wait for an answer
   before giving up. If the time is infinite a lost answer will get the calling
   thread stuck indefinitely. */
{}
#endif /* RPC_NETWORK_H */
""".format(doNotModifyHeader, externC_intro, externC_outro)



def getRpcTypesHeader():
    return """{}
#ifndef RPC_TYPES_H
#define RPC_TYPES_H

#include <stddef.h>

{}
typedef struct {{
	RPC_RESULT result;
	size_t size;
}} RPC_SIZE_RESULT;

typedef enum {{
    RPC_mutex_parsing_complete,
    RPC_mutex_caller,
    RPC_mutex_in_caller,
    RPC_mutex_answer,
    RPC_MUTEX_COUNT
}} RPC_mutex_id;
#define RPC_number_of_mutexes 4

#endif /* RPC_TYPES_H */
""".format(doNotModifyHeader, rpc_enum)

def getRequestParserHeader():
    return """{}
#include "RPC_types.h"

{}
/* Receives a pointer to a (partly) received message and it's size.
   Returns a result and a size. If size equals RPC_SUCCESS then size is the
   size that the message is supposed to have. If result equals RPC_COMMAND_INCOMPLETE
   then more bytes are required to determine the size of the message. In this case
   size is the expected number of bytes required to determine the correct size.*/
RPC_SIZE_RESULT RPC_get_request_size(const void *buffer, size_t size_bytes);

/* This function parses RPC requests, calls the original function and sends an
   answer. */
void RPC_parse_request(const void *buffer, size_t size_bytes);
{}
""".format(doNotModifyHeader, externC_intro, externC_outro)

try:
    root = ET.Element("RPC")

    files = getFilePaths()

    rpcHeader, rpcImplementation, requestParserImplementation, answerParser, answerSizeChecker = generateCode(files["ServerHeader"], root)

    requestParserImplementation = doNotModifyHeader + '\n' + requestParserImplementation

    rpcImplementation = '''{doNotModify}
    {externC_intro}

#include <stdint.h>
#include <assert.h>
#include "{rpc_client_header}"
#include "RPC_network.h"

static const unsigned char *RPC_buffer;
static char RPC_initialized;

{implementation}{externC_outro}
    '''.format(
        doNotModify = doNotModifyHeader,
        rpc_client_header = "RPC_" + files["ServerHeaderFileName"][:-1] + 'h',
        implementation = rpcImplementation,
        externC_outro = externC_outro,
        externC_intro = externC_intro,
        )

    for file, data in (
        ("ClientHeader", getRPC_serviceHeader(rpcHeader, "RPC_" + files["ServerHeaderFileName"][:-2] + '_H')),
        ("ClientRpcTypesHeader", getRpcTypesHeader()),
        ("ServerRpcTypesHeader", getRpcTypesHeader()),
        ("ClientNetworkHeader", getNetworkHeader()),
        ("ServerNetworkHeader", getNetworkHeader()),
        ("ClientImplementation", "".join((
            rpcImplementation,
            answerSizeChecker,
            answerParser,
            getRPC_Parser_init(),
            getRPC_Parser_exit(),
            externC_outro),
         )),
        ("RPC_serviceHeader", getRequestParserHeader()),
        ("RPC_serviceImplementation", requestParserImplementation),
        ):
        print(files[file])
        f = open(files[file], "w")
        f.write(data)
        f.close()
    xml = ET.ElementTree()
    xml._setroot(root)
    xml.write(files["xmldump"], encoding="UTF-8", xml_declaration = True)
except:
    import traceback
    traceback.print_exc(1)
    exit(-1)

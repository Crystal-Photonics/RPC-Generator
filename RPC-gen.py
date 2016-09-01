# Source Header ->
# - RPC header
# - RPC implementation
# - requestParser implementation

import sys
import CppHeaderParser
from copy import deepcopy
#from enum import Enum
from itertools import chain
import xml.etree.ElementTree as ET

datatypes = {}
datatypeDeclarations = []
defines = {}
currentFile = ""
prefix = "RPC_"  # change prefix inside the header with #pragma RPC prefix XMPL_

functionIgnoreList = []
functionNoAnswerList = []


def evaluatePragmas(pragmas):
    for p in pragmas:
        program, command = p.split(" ", 1)
        if program == "RPC":
            try:
                command, target = command.split(" ", 1)
            except ValueError:
                assert False, "Invalid command or parameter: {} in {}".format(
                    command, currentFile)
            if command == "ignore":
                assert len(
                    target.split(" ")) == 1, "Invalid function name: {} in {}".format(
                    target, currentFile)
                functionIgnoreList.append(target)
            elif command == "noanswer":
                functionNoAnswerList.append(target)
            elif command == "prefix":
                global prefix
                prefix = target
            else:
                assert False, "Unknown command {} in {}".format(
                    command, currentFile)


def calculateHash(filenames):
    from hashlib import md5
    hash = md5()
    for fn in filenames:
        with open(fn, "r") as f:
            hash.update(f.read().encode("UTF-8"))
    rh = d = hash.hexdigest()
    result = ""
    while len(d) > 0:
        result += "\\x"
        result += d[0:2]
        d = d[2:]
    return result, rh


def getFilePaths():
    # get paths for various files that need to be created. all created files start with prefix
    # parse input
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument(
        "ClientConfig",
        help="Configuration file for the client",
        type=str)
    parser.add_argument(
        "ServerConfig",
        help="Configuration file for the server",
        type=str)
    args = parser.parse_args()

    # check if input is valid
    from os.path import isfile, isdir, abspath, join, split
    from os import getcwd, chdir, makedirs
    assert isfile(args.ClientConfig), "Error: Config file " + \
        args.ClientConfig + " does not exist."
    assert isfile(args.ServerConfig), "Error: Config file " + \
        args.ServerConfig + " does not exist."
    from configparser import ConfigParser

    clientconfigpath = abspath(args.ClientConfig)
    serverconfigpath = abspath(args.ServerConfig)

    retval = {}

    # check client config for validity
    clientconfig = ConfigParser()
    clientconfig.read(args.ClientConfig)

    chdir(split(clientconfigpath)[0])
    retval["CLIENT_CONFIG_PATH"] = split(clientconfigpath)[0]
    if "DOCDIR" in clientconfig["configuration"]:
        makedirs(clientconfig["configuration"]['DOCDIR'], exist_ok=True)
        retval[
            "CLIENT_" +
            "DOCDIR"] = abspath(
            clientconfig["configuration"]["DOCDIR"])
    else:
        print(
            "Warning in \"" +
            clientconfigpath +
            "\": No DOCDIR specified. No documentation will be generated.")
    for d in ("SRCDIR", "GENINCDIR", "SPCINCDIR"):
        assert d in clientconfig["configuration"], "Error in \"" + \
            clientconfigpath + "\": No " + d + " specified. Abort."
        makedirs(clientconfig["configuration"][d], exist_ok=True)
        retval["CLIENT_" + d] = abspath(clientconfig["configuration"][d])

    # check server config for validity
    serverconfig = ConfigParser()
    serverconfig.read(serverconfigpath)
    chdir(split(serverconfigpath)[0])
    retval["SERVER_CONFIG_PATH"] = split(serverconfigpath)[0]
    retval["ServerHeaderName"] = split(
        abspath(serverconfig["configuration"]["SOURCEHEADER"]))[1][:-2]
    assert "SOURCEHEADER" in serverconfig[
        "configuration"], "Error in \"" + serverconfigpath + "\": No SOURCEHEADER specified. Abort."
    assert isfile(serverconfig["configuration"]["SOURCEHEADER"]), "Error in \"" + serverconfigpath + \
        "\": Required file \"" + \
        serverconfig["configuration"]["SOURCEHEADER"] + "\" not found. Abort."
    retval["ServerHeader"] = abspath(
        serverconfig["configuration"]["SOURCEHEADER"])

    if "INCLUDE_INTO_TYPES" in clientconfig["configuration"]:
        retval["EXTRA_INCLUDE_INTO_CLIENT_TYPES_H"] = clientconfig["configuration"]["INCLUDE_INTO_TYPES"]
    else:
        retval["EXTRA_INCLUDE_INTO_CLIENT_TYPES_H"] = ""

    if "DOCDIR" in serverconfig["configuration"]:
        makedirs(serverconfig["configuration"]['DOCDIR'], exist_ok=True)
        retval[
            "SERVER_" +
            "DOCDIR"] = abspath(
            serverconfig["configuration"]["DOCDIR"])
    else:
        print(
            "Warning in \"" +
            serverconfigpath +
            "\": No DOCDIR specified. No documentation will be generated.")
    for d in ("SRCDIR", "GENINCDIR"):
        assert d in serverconfig["configuration"], "Error in \"" + \
            serverconfigpath + "\": No " + d + " specified. Abort."
        makedirs(serverconfig["configuration"][d], exist_ok=True)
        retval["SERVER_" + d] = abspath(serverconfig["configuration"][d])

    global hashstring
    global rawhash
    from sys import argv
    hashstring, rawhash = calculateHash(
        (argv[0],
         clientconfigpath,
         serverconfigpath,
         retval["ServerHeader"]))

    ast = CppHeaderParser.CppHeader(
        abspath(serverconfig["configuration"]["SOURCEHEADER"]))
    evaluatePragmas(ast.pragmas)
    return retval
"""
fp = getFilePaths()
for k in fp:
    print(k, ": ", fp[k])
exit()
"""


def getDatatype(signature, file="???", line="???"):
    # print(10*"+")
    # print(signature)
    signatureList = signature.split(" ")
    if signature in datatypes:
        return datatypes[signature]
    if signature in defines and defines[signature] in datatypes:
        return datatypes[defines[signature]]
    if len(signatureList) == 2 and (signatureList[
            0] == "struct" or signatureList[0] == "enum"):
        assert signature in datatypes, 'Unknown type "{signature}" in {file}:{line}'.format(
            signature=signature,
            file=file,
            line=line,
        )
        return datatypes[signature]
    import sys

    print(">>>", datatypes)

    assert False, 'THIS Unknown type "{signature}" in {file}:{line}'.format(
        signature=signature,
        file=file,
        line=line,
    )


def getTypeDeclarations():
    return "\n".join(dd for dd in datatypeDeclarations)


def isVoidDatatype(datatype):
    try:
        return datatype.size_bytes == 0
    except AttributeError:
        return False

# Metatype describing what all datatypes must be capable of


class Datatype:
    #__init__ #depending on type

    def setXml(self, xml):
        # adds a description of the data type to the xml entry
        raise NotImplemented

    def declaration(self, identifier):
        # returns the declaration for the datatype given its identifier such as
        # "i" -> "int i" or "ia" -> "int ia[32][47]"
        raise NotImplemented

    def stringify(self, identifier, indention):
        # identifier is the name of the identifier we want to stringify, can be an expression
        # indention is the indention level of the code
        # returns code that does the stringifying
        raise NotImplemented

    def unstringify(self, source, identifier, indention):
        # source is the name of a char * pointing to a buffer
        # identifier is the name of the identifier we want to unstringify, can be an expression
        # indention is the indention level of the code
        # returns code that does the unstringifying
        raise NotImplemented

    def isInput(self):
        # returns True if this is an input parameter when passed to a function and False otherwise
        # pointers and arrays may be pure output parameters, integers are always input parameters
        # if pointers and arrays are input parameters depends on their
        # identifier name
        raise NotImplemented

    def isOutput(self):
        # returns True if this is an output parameter when passed to a function and False otherwise
        # pointers and arrays can be output parameters, integers can never be output parameters
        # if pointers and arrays are output parameters depends on their
        # identifier name
        raise NotImplemented

    def getSize(self):
        # returns the number of bytes required to send this datatype over the network
        # pointers return 0.
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
    # use bitshift to prevent endianess problems

    def declaration(self, identifier):
        return self.signature + " " + identifier

    def stringify(self, identifier, indention):
        return """
{indention}/* writing integral type {type} {identifier} of size {size} */
{datapush}""".format(
            indention=indention * '\t',
            identifier=identifier,
            type=self.signature,
            size=self.size_bytes,
            datapush="".join(
                indention *
                '\t' +
                prefix +
                "message_push_byte((unsigned char)(" +
                IntegralDatatype.getByte(
                    i,
                    identifier) +
                "));\n" for i in range(
                    self.size_bytes)),
            # 5
        )

    def unstringify(self, source, identifier, indention):
        if self.size_bytes == 0:
            return ""
        return """
{indention}/* reading integral type {signature} {identifier} of size {size} */
{indention}{identifier} = *{source}++;
{deserialization}""".format(
            indention=indention * '\t',
            identifier=identifier,
            source=source,
            signature=self.signature,
            size=self.size_bytes,
            deserialization="".join(
                indention *
                '\t' +
                IntegralDatatype.orByte(
                    i,
                    identifier,
                    "(*" +
                    source +
                    "++)") +
                ";\n" for i in range(
                    1,
                    self.size_bytes)),
        )

    def isInput(self):
        return True

    def isOutput(self):
        return False

    def getSize(self):
        assert isinstance(self.size_bytes, int)
        return self.size_bytes


class EnumDatatype(Datatype):

    def __init__(self, signature, size_bytes,
                 transfertype, values, name, typedef):
        self.signature = signature
        self.size_bytes = size_bytes
        self.transfertype = transfertype
        self.values = values
        self.typedef = typedef
        self.name = name

    def setXml(self, xml):
        xml.set("bits", str(self.size_bytes * 8))
        xml.set("ctype", self.declaration("")[:-1])
        xml.set("type", "enum")
        for v in self.values:
            typ = ET.SubElement(xml, "enum")
            typ.set("name", v["name"])
            typ.set("value", str(v["value"]))

    def getTypeDeclaration(self):
        declaration = ",\n\t".join(
            "{name} = {value}".format(
                name=v["name"],
                value=v["value"]) for v in self.values)
        if self.typedef:
            declaration = "typedef enum{{\n\t{declaration}\n}} {name};\n".format(
                declaration=declaration, name=self.name)
        else:  # no typedef
            declaration = "enum {name}{{\n\t{declaration}\n}};\n".format(
                declaration=declaration, name=self.name)
        return declaration

    def declaration(self, identifier):
        return self.signature + " " + identifier

    def stringify(self, identifier, indention):
        if self.size_bytes == 0:
            return ""
        return """
{indention}/* writing enum type {signature} {identifier} of size {size} */
{indention}{{
{indention}\t{transfertype} temp = ({transfertype}){identifier};
{serialization}
{indention}}}""".format(
            indention=indention * '\t',
            identifier=identifier,
            serialization=IntegralDatatype(
                self.transfertype, self.size_bytes).stringify(
                "temp", indention + 1),
            signature=self.signature,
            size=self.size_bytes,
            transfertype=self.transfertype,
        )

    def unstringify(self, source, identifier, indention):
        if self.size_bytes == 0:
            return ""
        return """
{indention}/* reading enum type {signature}{identifier} of size {size} */
{indention}{{
{indention}\t{transfertype} temp;
{deserialization}
{indention}\t{identifier} = temp;
{indention}}}""".format(
            indention=indention * '\t',
            identifier=identifier,
            source=source,
            signature=self.signature,
            size=self.size_bytes,
            transfertype=self.transfertype,
            deserialization=IntegralDatatype(
                self.transfertype, self.size_bytes).unstringify(
                source, "temp", indention + 1),
        )

    def isInput(self):
        return True

    def isOutput(self):
        return False

    def getSize(self):
        assert isinstance(self.size_bytes, int)
        return self.size_bytes


class ArrayDatatype(Datatype):
    # need to be mindful of padding, otherwise it is a fixed size loop

    def __init__(self, numberOfElements, datatype,
                 parametername, In=None, Out=None):
        self.numberOfElements = numberOfElements
        self.datatype = datatype
        self.In = parametername.endswith("_in") or parametername.endswith(
            "_inout") if In is None else In
        self.Out = parametername.endswith("_out") or parametername.endswith(
            "_inout") if Out is None else Out

    def setXml(self, xml):
        xml.set("bits", str(self.getSize() * 8))
        xml.set("ctype", self.declaration(""))
        xml.set("type", "array")
        typ = ET.SubElement(xml, "array")
        typ.set("elements", self.numberOfElements)
        self.datatype.setXml(typ)

    def declaration(self, identifier):
        return self.datatype.declaration(
            identifier + "[" + str(self.numberOfElements) + "]")

    def isInput(self):
        return self.In

    def isOutput(self):
        return self.Out

    def stringify(self, identifier, indention):
        if self.numberOfElements == "1":
            # no loop required for 1 element
            return "{0}{1}".format(
                indention * '\t', self.datatype.stringify("(*" + identifier + ")", indention))
        return """
{indention}/* writing array {name} with {numberOfElements} elements */
{indention}{{
{indention}	int {prefix}COUNTER_VAR{indentID};
{indention}	for ({prefix}COUNTER_VAR{indentID} = 0; {prefix}COUNTER_VAR{indentID} < {numberOfElements}; {prefix}COUNTER_VAR{indentID}++){{
{serialization}
{indention}	}}
{indention}}}""".format(
            name=identifier,
            numberOfElements=self.numberOfElements,
            indention=indention * '\t',
            serialization=self.datatype.stringify(
                "" +
                identifier +
                "[{}COUNTER_VAR{}]".format(
                    prefix,
                    indention),
                indention +
                2),
            indentID=indention,
            prefix=prefix,
        )

    def unstringify(self, destination, identifier, indention):
        if self.numberOfElements == "1":
            # no loop required for 1 element
            return "{0}{1}".format(
                indention * '\t', self.datatype.unstringify(destination, "(*" + identifier + ")", indention))
        return """
{indention}/* reading array {identifier} with {noe} elements */
{indention}{{
{indention}	int {prefix}COUNTER_VAR{ID};
{indention}	for ({prefix}COUNTER_VAR{ID} = 0; {prefix}COUNTER_VAR{ID} < {noe}; {prefix}COUNTER_VAR{ID}++){{
{payload}
{indention}	}}
{indention}}}""".format(
            identifier=identifier,
            noe=self.numberOfElements,
            indention=indention * '\t',
            payload=self.datatype.unstringify(
                destination,
                identifier +
                "[{}COUNTER_VAR{}]".format(
                    prefix,
                    indention),
                indention +
                2),
            ID=indention,
            prefix=prefix,
        )

    def getSize(self):
        return int(self.numberOfElements) * self.datatype.getSize()


class PointerDatatype(Datatype):
    # need to be mindful of parring, otherwise it is a variable sized loop
    # if the pointer is used for input, output or both depends on the name,
    # for example p_in, p_out or p_inout

    def __init__(self, signature, datatype, parametername):
        assert None, "Code for pointers does not work yet"
        self.signature = signature
        self.datatype = datatype
        self.In = parametername.endswith(
            "_in") or parametername.endswith("_inout")
        self.Out = parametername.endswith(
            "_out") or parametername.endswith("_inout")

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
            name=identifier,
            type=self.signature,
            index=self.numberOfElementsIdentifier,
            indention=indention * '\t',
            serialization=self.datatype.stringify(
                identifier + "[i]", indention + 2),
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
            identifier=identifier,
            signature=self.signature,
            numberOfElementsIdentifier=self.numberOfElementsIdentifier,
            indention=indention * '\t',
            idDeserializer=self.datatype.unstringify(
                destination, identifier + "[i]", indention + 2),
        )

    def isInput(self):
        return self.In

    def isOutput(self):
        return self.Out

    def getSize(self):
        return 0.


class StructDatatype(Datatype):
    # just call the functions of all the members in order

    def __init__(self, signature, memberList, file, lineNumber):
        self.signature = signature
        self.memberList = memberList
        self.file = file
        self.lineNumber = lineNumber

    def setXml(self, xml):
        xml.set("bits", str(self.getSize()))
        xml.set("ctype", self.signature)
        xml.set("type", "struct")
        memberpos = 1
        for e in self.memberList:
            member = ET.SubElement(xml, "parameter")
            member.set("memberpos", str(memberpos))
            member.set("name", e["name"])
            memberpos += 1
            e["datatype"].setXml(member)

    def declaration(self, identifier):
        return self.signature + " " + identifier

    def stringify(self, identifier, indention):
        members = ", ".join(m["datatype"].declaration(m["name"])
                            for m in self.memberList)
        # print(self.memberList)
        memberStringification = "".join(
            m["datatype"].stringify(
                identifier + "." + m["name"],
                indention + 1) for m in self.memberList)
        return "{indention}/*writing {identifier} of type {type} with members {members}*/\n{indention}{{{memberStringification}\n{indention}}}".format(
            indention=indention * '\t',
            type=self.signature,
            members=members,
            identifier=identifier,
            memberStringification=memberStringification,
        )

    def unstringify(self, destination, identifier, indention):
        memberUnstringification = "".join(
            m["datatype"].unstringify(
                destination,
                identifier + "." + m["name"],
                indention + 1) for m in self.memberList)
        return """
{indention}/* reading {signature}{identifier}*/
{indention}{{
{memberdeserialize}
{indention}}}""".format(
            identifier=identifier,
            signature=self.signature,
            indention=indention * '\t',
            memberdeserialize=memberUnstringification,
        )

    def isInput(self):
        # TODO: Go through members and return if for any of them isInput is
        # true
        raise NotImplemented

    def isOutput(self):
        # TODO: Go through members and return if for any of them isOutput is
        # true
        raise NotImplemented

    def getSize(self):
        # print(self.memberList)
        return sum(m["datatype"].getSize() for m in self.memberList)

    def getTypeDeclaration(self):
        siglist = self.signature.split(" ")
        isTypedefed = len(siglist) == 1
        memberDeclarations = ";\n\t".join(
            m["datatype"].declaration(
                m["name"]) for m in self.memberList)
        form = "typedef struct{{\n\t{members};\n}}{sig};\n" if isTypedefed else "{sig}{{\n\t{members};\n}};\n"
        return form.format(
            sig=self.signature,
            members=memberDeclarations,
        )


class Function:
    # stringify turns a function call into a string and sends it to the other side
    # unstringify turns a string into arguments to pass to a function
    # assumes the send function has the signature (void *, size_t);
    # requests have even numbers, answers have odd numbers

    def __init__(self, ID, returntype, name, parameterlist):
        #print("ID:", ID)
        #print("returntype:", returntype)
        #print("name:", name)
        #print("parameterlist:", parameterlist)
        # returntype can either be a Datatype "void", but no pointer
        self.isVoidReturnType = isVoidDatatype(returntype)
        if not self.isVoidReturnType:
            returnValueName = "return_value_out"
            rt = ArrayDatatype("1", returntype, returnValueName)
            parameterlist.insert(
                0, {"parameter": rt, "parametername": returnValueName})
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
            if not p["parameter"].isInput():
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
            if not p["parameter"].isOutput():
                continue
            param = ET.SubElement(reply, "parameter")
            param.set("position", str(i))
            param.set("name", p["parametername"])
            i += 1
            p["parameter"].setXml(param)

    def getOriginalDeclaration(self):
        returnvalue = "void " if self.isVoidReturnType else self.parameterlist[
            0]["parameter"].declaration("")
        if returnvalue.endswith(" [1]"):
            returnvalue = returnvalue[:-3]
        start = 0 if self.isVoidReturnType else 1
        return "{returnvalue}{functionname}({parameterlist});".format(
            returnvalue=returnvalue,
            functionname=self.name,
            parameterlist=", ".join(
                p["parameter"].declaration(
                    p["parametername"]) for p in self.parameterlist[
                    start:]),
        )

    def getParameterDeclaration(self):
        parameterdeclaration = ", ".join(
            p["parameter"].declaration(
                p["parametername"]) for p in self.parameterlist)
        if parameterdeclaration == "":
            parameterdeclaration = "void"
        return parameterdeclaration

    def getCall(self):
        #print(self.name, self.parameterlist)
        returnvalue = "*return_value_out = " if not self.isVoidReturnType else ""
        parameterlist = self.parameterlist if self.isVoidReturnType else self.parameterlist[
            1:]
        return "{returnvalue}{functionname}({parameterlist});".format(
            returnvalue=returnvalue,
            functionname=self.name if self.ID > 0 else self.name + "_impl",
            parameterlist=", ".join(p["parametername"] for p in parameterlist),
        )

    def getDefinition(self):
        if self.name in functionNoAnswerList:
            return """
RPC_RESULT {functionname}({parameterdeclaration}){{
	RPC_RESULT result;
	{prefix}mutex_lock(RPC_mutex_caller);
	{prefix}mutex_lock(RPC_mutex_in_caller);

	/***Serializing***/
	{prefix}message_start({messagesize});
	{prefix}message_push_byte({requestID}); /* save ID */
{inputParameterSerializationCode}
	result = {prefix}message_commit();

	/* This function has been set to receive no answer */

	{prefix}mutex_unlock(RPC_mutex_in_caller);
	{prefix}mutex_unlock(RPC_mutex_caller);
	return result;
}}
""".format(
                requestID=self.ID * 2,
                inputParameterSerializationCode="".join(
                    p["parameter"].stringify(
                        p["parametername"],
                        1) for p in self.parameterlist if p["parameter"].isInput()),
                functionname=self.name,
                parameterdeclaration=self.getParameterDeclaration(),
                prefix=prefix,
                messagesize=sum(p["parameter"].getSize() for p in self.parameterlist if p[
                                "parameter"].isInput()) + 1,
            )
        return """
RPC_RESULT {functionname}({parameterdeclaration}){{
	{prefix}mutex_lock(RPC_mutex_caller);

	for (;;){{
		{prefix}mutex_lock(RPC_mutex_in_caller);

		/***Serializing***/
		{prefix}message_start({messagesize});
		{prefix}message_push_byte({requestID}); /* save ID */
{inputParameterSerializationCode}
		if ({prefix}message_commit() == RPC_SUCCESS){{ /* successfully sent request */
			if ({prefix}mutex_lock_timeout(RPC_mutex_answer)){{ /* Wait for answer to arrive */
				if (*{prefix}buffer++ != {answerID}){{ /* We got an incorrect answer */
					{prefix}mutex_unlock(RPC_mutex_in_caller);
					{prefix}mutex_lock(RPC_mutex_parsing_complete);
					{prefix}mutex_unlock(RPC_mutex_parsing_complete);
					{prefix}mutex_unlock(RPC_mutex_answer);
					continue; /* Try if next answer is correct */
				}}
				/***Deserializing***/
{outputParameterDeserialization}
				{prefix}mutex_unlock(RPC_mutex_in_caller);
				{prefix}mutex_lock(RPC_mutex_parsing_complete);
				{prefix}mutex_unlock(RPC_mutex_parsing_complete);
				{prefix}mutex_unlock(RPC_mutex_answer);
				{prefix}mutex_unlock(RPC_mutex_caller);
				return RPC_SUCCESS;
			}}
			else {{ /* We failed to get an answer due to timeout */
				{prefix}mutex_unlock(RPC_mutex_in_caller);
				{prefix}mutex_unlock(RPC_mutex_caller);
				return RPC_FAILURE;
			}}
		}}
		else {{ /* Sending request failed */
			{prefix}mutex_unlock(RPC_mutex_in_caller);
			{prefix}mutex_unlock(RPC_mutex_caller);
			return RPC_FAILURE;
		}}
	}}
	/* assert_dead_code; */
}}
""".format(
            requestID=self.ID * 2,
            answerID=self.ID * 2 + 1,
            inputParameterSerializationCode="".join(
                p["parameter"].stringify(
                    p["parametername"],
                    2) for p in self.parameterlist if p["parameter"].isInput()),
            functionname=self.name,
            parameterdeclaration=self.getParameterDeclaration(),
            outputParameterDeserialization="".join(
                p["parameter"].unstringify(
                    prefix + "buffer",
                    p["parametername"],
                    4) for p in self.parameterlist if p["parameter"].isOutput()),
            prefix=prefix,
            messagesize=sum(p["parameter"].getSize() for p in self.parameterlist if p[
                            "parameter"].isInput()) + 1,
        )

    def getDeclaration(self):
        return "RPC_RESULT {}({});".format(
            #prefix,
            self.name,
            self.getParameterDeclaration(),
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
                ID=self.ID * 2,
                declaration=self.getDeclaration(),
                parameterdeclarations="".join(
                    "\t\t\t" +
                    p["parameter"].declaration(
                        p["parametername"]) +
                    ";\n" for p in self.parameterlist),
                inputParameterDeserialization="".join(
                    p["parameter"].unstringify(
                        buffer,
                        p["parametername"],
                        3) for p in self.parameterlist if p["parameter"].isInput()),
                functioncall=self.getCall(),
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
			{prefix}message_start({messagesize});
			{prefix}message_push_byte({ID_plus_1});
			{outputParameterSerialization}
			{prefix}message_commit();
		}}
		break;""".format(
            ID=self.ID * 2,
            declaration=self.getDeclaration(),
            parameterdeclarations="".join(
                "\t\t\t" +
                p["parameter"].declaration(
                    p["parametername"]) +
                ";\n" for p in self.parameterlist),
            inputParameterDeserialization="".join(
                p["parameter"].unstringify(
                    buffer,
                    p["parametername"],
                    3) for p in self.parameterlist if p["parameter"].isInput()),
            functioncall=self.getCall(),
            outputParameterSerialization="".join(
                p["parameter"].stringify(
                    p["parametername"],
                    3) for p in self.parameterlist if p["parameter"].isOutput()),
            ID_plus_1=self.ID * 2 + 1,
            prefix=prefix,
            messagesize=sum(p["parameter"].getSize() for p in self.parameterlist if p[
                            "parameter"].isOutput()) + 1,
        )

    def getAnswerSizeCase(self, buffer):
        if self.name in functionNoAnswerList:
            return """\t\t/* case {ID}: {declaration}
\t\t\tThis function has been set to receive no answer */
""".format(
                declaration=self.getDeclaration(),
                ID=self.ID * 2 + 1,
            )
        size = 1 + sum(p["parameter"].getSize()
                       for p in self.parameterlist if p["parameter"].isOutput())
        retvalsetcode = ""
        if isinstance(size, float):  # variable length
            retvalsetcode += """			if (size_bytes >= 3)
				returnvalue.size = {buffer}[1] + {buffer}[2] << 8;
			else{{
				returnvalue.size = 3;
				returnvalue.result = RPC_COMMAND_INCOMPLETE;
			}}""".format(buffer=buffer, prefix=prefix)
        else:
            retvalsetcode += "\t\t\treturnvalue.size = " + str(size) + ";"
        return """\t\tcase {ID}: /* {declaration} */
{retvalsetcode}
\t\t\tbreak;
""".format(
            declaration=self.getDeclaration(),
            ID=self.ID * 2 + 1,
            retvalsetcode=retvalsetcode,
        )

    def getAnswerParseCase(self, buffer):
        if self.name in functionNoAnswerList:
            return ""
        return """\t\tcase {ID}: /* {declaration} */
\t\t\tbreak; /*TODO*/
""".format(
            ID=self.ID * 2 + 1,
            declaration=self.getDeclaration(),
        )

    def getRequestSizeCase(self, buffer):
        size = 1 + sum(p["parameter"].getSize()
                       for p in self.parameterlist if p["parameter"].isInput())
        retvalsetcode = ""
        if isinstance(size, float):  # variable length
            retvalsetcode += """			if (size_bytes >= 3)
				returnvalue.size = {buffer}[1] + {buffer}[2] << 8;
			else{{
				returnvalue.size = 3;
				returnvalue.result = RPC_COMMAND_INCOMPLETE;
			}}""".format(buffer=buffer, prefix=prefix)
        else:
            retvalsetcode += "\t\t\treturnvalue.size = " + str(size) + ";"
        return """
\t\tcase {answerID}: /* {functiondeclaration} */
{retvalsetcode}
\t\t\tbreak;
""".format(
            answerID=self.ID * 2,
            retvalsetcode=retvalsetcode,
            functiondeclaration=self.getDeclaration(),
        )

    def getDocumentation(self):
        class BytePositionCounter:

            def __init__(self, start=0):
                self.position = start

            def getBytes(self, length):
                form = "{start}" if length == 1 else "{start}-{end}"
                self.position += length
                return form.format(start=self.position -
                                   length, end=self.position - 1)
        pos = BytePositionCounter(start=1)

        def stripOneDimensionalArray(vartype):
            if vartype.endswith(" [1]"):
                vartype = vartype[:-4]
            return vartype
        tableformat = """
            <td class="content">{bytes}</td>
            <td class="content">{type}</td>
            <td class="content">{length}</td>
            <td class="content">{varname}</td>"""
        inputvariables = "</tr><tr>".join(tableformat.format(
            length=p["parameter"].getSize(),
            varname=p["parametername"],
            bytes=pos.getBytes(p["parameter"].getSize()),
            type=stripOneDimensionalArray(p["parameter"].declaration("")),
        )
            for p in self.parameterlist if p["parameter"].isInput())
        ID = '<td class="content">0</td><td class="content">uint8_t</td><td class="content">1</td><td class="content">ID = {ID}</td>'.format(
            ID=self.ID * 2)
        inputvariables = ID + "</tr><tr>" + \
            inputvariables if len(inputvariables) > 0 else ID
        pos = BytePositionCounter(start=1)
        outputvariables = "</tr><tr>".join(tableformat.format(
            length=p["parameter"].getSize(),
            varname=p["parametername"] if self.ID != 0 else p["parametername"] + ' = 0x' + rawhash,
            bytes=pos.getBytes(p["parameter"].getSize()),
            type=stripOneDimensionalArray(p["parameter"].declaration("")),
        )
            for p in self.parameterlist if p["parameter"].isOutput())
        ID = '<td class="content">0</td><td class="content">uint8_t</td><td class="content">1</td><td class="content">ID = {ID}</td>'.format(
            ID=self.ID * 2 + 1)
        outputvariables = ID + "</tr><tr>" + \
            outputvariables if len(outputvariables) > 0 else ID

        structSet = set()

        def addToStructSet(structSet, parameter):
            if isinstance(parameter, StructDatatype):
                structSet.add(parameter)
                for m in parameter.memberList:
                    addToStructSet(structSet, m)
            elif isinstance(parameter, ArrayDatatype):
                addToStructSet(structSet, parameter.datatype)
        for p in self.parameterlist:
            addToStructSet(structSet, p["parameter"])
        enumSet = set()

        def addToEnumSet(enumSet, parameter):
            if isinstance(parameter, StructDatatype):
                for m in parameter.memberList:
                    addToEnumSet(structSet, m)
            elif isinstance(parameter, ArrayDatatype):
                addToEnumSet(enumSet, parameter.datatype)
            elif isinstance(parameter, EnumDatatype):
                enumSet.add(parameter)
        for p in self.parameterlist:
            addToEnumSet(enumSet, p["parameter"])
        contentformat = """
        <p class="static">{name}</p>
        <table>
            <tr>
                <th>Byte</th>
                <th>Type</th>
                <th>Length</th>
                <th>Variable</th>
            </tr>
            <tr>
                {content}
            </tr>
        </table>"""
        structcontent = ""
        for s in structSet:
            pos = BytePositionCounter()
            structcontent += contentformat.format(name=s.signature, content="</tr><tr>".join(
                tableformat.format(
                    length=m[
                        "datatype"].getSize(),
                    varname=m["name"],
                    bytes=pos.getBytes(
                        m["datatype"].getSize()),
                    type=stripOneDimensionalArray(
                        m["datatype"].declaration("")),
                ) for m in s.memberList)
            )
        enumcontent = ""
        for e in enumSet:
            pos = BytePositionCounter()
            enumcontent += """
        <p class="static">{name}</p>
        <table>
            <tr>
                <th>Name</th>
                <th>Value</th>
            </tr>
            <tr>
                {content}
            </tr>
        </table>""".format(name=e.name, content="</tr><tr>".join('<td class="content">{name}</td><td class="content">{value}</td>'.format(
                name=m["name"],
                value=m["value"])
                for m in e.values)
            )
        replycontent = contentformat.format(
            name="Reply", content=outputvariables)
        if self.name in functionNoAnswerList:
            replycontent = '<p class="static">Reply: None</p>'
        return '''<div class="function">
        <table class="declarations">
            <tr class="declarations">
                <td class="static">Original function</td>
                <td class="function">{originalfunctiondeclaration}</td>
            </tr>
            <tr class="declarations">
                <td class="static">Generated function</td>
                <td class="function">{functiondeclaration}</td>
            </tr>
        </table>
        {requestcontent}
        {replycontent}
        {structcontent}
        {enumcontent}
        </table>
        </div>'''.format(
            originalfunctiondeclaration=self.getOriginalDeclaration(),
            functiondeclaration=self.getDeclaration(),
            requestcontent=contentformat.format(
                name="Request", content=inputvariables),
            replycontent=replycontent,
            structcontent=structcontent,
            enumcontent=enumcontent,
            requestID=self.ID * 2,
            replyID=self.ID * 2 + 1,
        )


def setIntegralDataType(signature, size_bytes):
    datatypes[signature] = IntegralDatatype(signature, size_bytes)


def setBasicDataType(signature, size_bytes):
    datatypes[signature] = BasicDatatype(signature, size_bytes)


def setEnumDataType(signature, size_bytes, transfertype,
                    values, name, typedef):
    datatypes[signature] = EnumDatatype(
        signature, size_bytes, transfertype, values, name, typedef)


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
        # calculating minimum and maximim can be done better with map(max,
        # zip(*e["values"])) or something like that
        minimum = maximum = 0
        for v in e["values"]:  # parse the definition of the enum values+
            if isinstance(v["value"], type(0)):  # its just a (default) int
                intValue = v["value"]
            else:
                try:
                    intValue = int("".join(v["value"].split(" ")))
                    # it is something like "- 1000"
                except:
                    # it is something complicated, assume an int has 4 bytes
                    minimum = -2**30
                    intValue = 2 ** 30
            minimum = min(minimum, intValue)
            maximum = max(maximum, intValue)
        valRange = maximum - minimum
        name = e["name"] if e["typedef"] else "enum " + e["name"]
        if valRange < 1:
            setBasicDataType(name, 0)
            continue
        from math import log, ceil
        # +1 because a 2 element enum would result in 0 bit field
        requiredBits = ceil(log(valRange + 1, 2))
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
            assert False, "enum " + e["name"] + " appears to require " + str(
                requiredBytes) + "bytes and does not fit in a 32 bit integer"
        if minimum >= 0:
            cast = "u" + cast
        setEnumDataType(
            name,
            requiredBytes,
            cast,
            e["values"],
            e["name"],
            e["typedef"])
        datatypeDeclarations.append(datatypes[name].getTypeDeclaration())


def setStructTypes(structs):
    for s in structs:
        memberList = []
        for t in structs[s]["properties"]["public"]:
            memberList.append(
                {"name": t["name"], "datatype": getStructParameter(t)})
            # print(structs[s][t])
        assert len(memberList) > 0, "struct with no members is not supported"
        isTypedefed = structs[s]["properties"][
            "public"][0]['property_of_class'] != s
        signature = s if isTypedefed else "struct " + s
        datatypes[signature] = StructDatatype(
            signature, memberList, currentFile, structs[s]["line_number"])
        datatypeDeclarations.append(datatypes[signature].getTypeDeclaration())

def getHash():
    return """/* This hash is generated from the Python script that generated this file,
   the configs passed to it and the source header file specified within the
   server config. You can use it to verify that the client and the server
   use the same protocol. */
#define {prefix}HASH "{hashstring}"
#define {prefix}HASH_SIZE 16""".format(prefix = prefix, hashstring = hashstring)


def getStructParameter(parameter):
    basetype = getDatatype(
        parameter["type"],
        currentFile,
        parameter["line_number"])
    if 'multi_dimensional_array_size' in parameter:
        retval = ArrayDatatype(
            parameter["multi_dimensional_array_size"][-1], basetype, parameter["name"])
        for d in reversed(parameter["multi_dimensional_array_size"][:-1]):
            retval = ArrayDatatype(d, retval, parameter["name"])
        return retval
    if 'array_size' in parameter:
        return ArrayDatatype(
            parameter["array_size"], basetype, parameter["name"])
    assert parameter["type"][-1] != '*', "Pointers are not allowed in structs"
    return basetype


def setDefines(newdefines):
    for d in newdefines:
        try:
            l = d.split(" ")
            defines[l[0]] = " ".join(o for o in l[1:])
        except:
            pass


def getFunctionReturnType(function):
    assert function["returns_pointer"] == 0, "in function " + function["debug"] + " line " + \
        str(function["line_number"]) + ": " + \
        "Pointers as return types are not supported"
    return getDatatype(function["rtnType"],
                       currentFile, function["line_number"])


def getParameterArraySizes(parameter):
    try:
        tokens = parameter["method"]["debug"].split(" ")
        # print(tokens)
    except KeyError:
        if "array_size" in parameter:
            return [int(parameter["array_size"])]
        assert False, "Multidimensional arrays inside structs currently not supported"
    assert parameter["name"] in tokens, "Error: cannot get non-existing parameter " + \
        parameter["name"] + " from declaration " + parameter["method"]["debug"]
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
    # return (isPointerRequiringSize, DataType)
    if parameter["type"][-1] == '*':  # pointer
        assert parameter[
            "type"][-3] != '*', "Multipointer as parameter is not allowed"
        assert parameter["name"].endswith("_in") or parameter["name"].endswith("_out") or parameter["name"].endswith("_inout"),\
            'In {1}:{2}: Pointer parameter "{0}" must either have a suffix "_in", "_out", "_inout" or be a fixed size array.'.format(
                parameter["name"], currentFile, parameter["line_number"])
        return {"isPointerRequiringSize": True, "parameter": PointerDatatype(parameter["type"], getDatatype(
            parameter["type"][:-2], currentFile, parameter["line_number"]), parameter["name"])}
    basetype = getDatatype(
        parameter["type"],
        currentFile,
        parameter["line_number"])
    if parameter["array"]:  # array
        assert parameter["name"][-3:] == "_in" or parameter["name"][-4:] == "_out" or parameter["name"][-6:] == "_inout",\
            'Array parameter name "' + \
            parameter["name"] + '" must end with "_in", "_out" or "_inout" in {}:{} '.format(
                currentFile, parameter["line_number"])
        arraySizes = list(reversed(getParameterArraySizes(parameter)))
        current = ArrayDatatype(arraySizes[0], basetype, parameter["name"])
        arraySizes = arraySizes[1:]
        for arraySize in arraySizes:
            current = ArrayDatatype(arraySize, current, parameter["name"])
        return {"isPointerRequiringSize": False, "parameter": current}
    else:  # base type
        return {"isPointerRequiringSize": False, "parameter": basetype}


def getFunctionParameterList(parameters):
    paramlist = []
    isPointerRequiringSize = False
    for p in parameters:
        if isPointerRequiringSize:  # require a size parameter
            pointername = parameters[len(paramlist) - 1]["name"]
            pointersizename = p["name"]
            sizeParameterErrorText = 'Pointer parameter "{0}" must be followed by a size parameter with the name "{0}_size". Or use a fixed size array instead.'.format(
                pointername)
            assert pointersizename == pointername + "_size", sizeParameterErrorText
            functionparameter = getFunctionParameter(p)
            isPointerRequiringSize = functionparameter[
                "isPointerRequiringSize"]
            parameter = functionparameter["parameter"]
            assert not isPointerRequiringSize, sizeParameterErrorText
            paramlist[-1]["parameter"].setNumberOfElementsIdentifier(
                pointersizename)
            paramlist.append(
                {"parameter": parameter, "parametername": p["name"]})
        else:
            functionparameter = getFunctionParameter(p)
            isPointerRequiringSize = functionparameter[
                "isPointerRequiringSize"]
            parameter = functionparameter["parameter"]
            if isVoidDatatype(parameter):
                continue
            parametername = p["name"]
            if parametername == "" and p["type"] != 'void':
                parametername = "unnamed_parameter" + str(len(paramlist))
            paramlist.append(
                {"parameter": parameter, "parametername": parametername})
    assert not isPointerRequiringSize, 'Pointer parameter "{0}" must be followed by a size parameter with the name "{0}_size". Or use a fixed size array instead.'.format(parameters[
                                                                                                                                                                          len(paramlist) - 1]["name"])
    # for p in paramlist:
    #print(p.stringify("buffer", "var", 1))
    return paramlist


def getFunction(function):
    functionList = []
    try:
        getFunction.functionID += 1
        assert getFunction.functionID < 255, "Too many functions, require changes to allow bigger function ID variable"
    except AttributeError:
        getFunction.functionID = 1
    # for attribute in function:
        #print(attribute + ":", function[attribute])
    ID = getFunction.functionID
    returntype = getFunctionReturnType(function)
    name = function["name"]
    parameterlist = getFunctionParameterList(function["parameters"])
    return Function(ID, returntype, name, parameterlist)
    # for k in function.keys():
    #print(k, '=', function[k])
    # for k in function["parameters"][0]["method"].keys():
    #print(k, '=', function["parameters"][0]["method"][k], "\n")
    # print(function["parameters"][0]["method"])
    # for k2 in k["method"].keys():
    #print(k2, '=', str(k["method"][k2]))
    # print(10*'_')
    # print(function.keys())
    # print("\n")
    # print(10*"_")
    # print(returntype)
    #print(returntype.stringify("buffer", "var", 1))
    #returntype.stringify("buffer", "var", 1)
    #Function(ID, returntype, name, parameterlist)


def checkDefines(defines):
    checklist = (
        (prefix + "SEND",
         "A #define {prefix}SEND is required that takes a const void * and a size and sends data over the network. Example: #define {prefix}SEND send".format(prefix=prefix)),
        (
            prefix +
            "SLEEP",
            "A #define {prefix}SLEEP is required that makes the current thread sleep until {prefix}WAKEUP is called or a timeout occured. Returns whether {prefix}WAKEUP was called (and a timeout did not occur)".format(
                prefix=prefix)),
        (
            prefix +
            "WAKEUP",
            "A #define {prefix}WAKEUP is required that makes the thread sleeping due to {prefix}SLEEP wake up".format(
                prefix=prefix)),
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
        "".join("typedef   int8_t  int{0}_t;\n".format(i)
                for i in range(1, 8)),
        "".join("typedef  int16_t  int{0}_t;\n".format(i)
                for i in range(9, 16)),
        "".join("typedef  int32_t  int{0}_t;\n".format(i)
                for i in range(17, 32)),
        "".join("typedef  uint8_t uint{0}_t;\n".format(i)
                for i in range(1, 8)),
        "".join("typedef uint16_t uint{0}_t;\n".format(i)
                for i in range(9, 16)),
        "".join("typedef uint32_t uint{0}_t;\n".format(i)
                for i in range(17, 32)),
    ))


def getGenericHeader(version):
    return """
/* This file has been generated by RPC Generator {0} */

/* typedefs for non-standard bit integers */
{1}
/* The optional original return value is returned through the first parameter */
""".format(version, getNonstandardTypedefs())


def getSizeFunction(functions, clientHeader,
                    parser_to_generic_path, parser_to_server_header_path):
    return """#include "{network_include}"
#include "{parser_include}"
#include "{parser_to_server_header_path}"

#include <string.h>

{hash}

/* auto-generated implementation */
void {prefix}get_hash_impl(unsigned char hash[16]){{
	memcpy(hash, {prefix}HASH, 16);
}}

/* Receives a pointer to a (partly) received message and it's size.
   Returns a result and a size. If size equals RPC_SUCCESS then size is the
   size that the message is supposed to have. If result equals RPC_COMMAND_INCOMPLETE
   then more bytes are required to determine the size of the message. In this case
   size is the expected number of bytes required to determine the correct size.*/
RPC_SIZE_RESULT {prefix}get_request_size(const void *buffer, size_t size_bytes){{
	const unsigned char *current = (const unsigned char *)buffer;
	RPC_SIZE_RESULT returnvalue;
	returnvalue.result = RPC_COMMAND_INCOMPLETE;
	if (size_bytes == 0){{
		returnvalue.result = RPC_COMMAND_INCOMPLETE;
		returnvalue.size = 1;
		return returnvalue;
	}}

	switch (*current){{ /* switch by message ID */{cases}
		default:
			returnvalue.size = 0;
			returnvalue.result = RPC_COMMAND_UNKNOWN;
			return returnvalue;
	}}
	returnvalue.result = returnvalue.size > size_bytes ? RPC_COMMAND_INCOMPLETE : RPC_SUCCESS;
	return returnvalue;
}}
""".format(
        cases="".join(f.getRequestSizeCase("current") for f in functions),
        prefix=prefix,
        network_include=join(parser_to_generic_path, prefix + "network.h"),
        parser_include=join(parser_to_generic_path, prefix + "parser.h"),
        parser_to_server_header_path=parser_to_server_header_path,
    )


def getRequestParser(functions):
    buffername = "current"
    return """
/* This function parses RPC requests, calls the original function and sends an
   answer. */
void {prefix}parse_request(const void *buffer, size_t size_bytes){{
	(void)size_bytes;
	const unsigned char *{buffername} = (const unsigned char *)buffer;
	switch (*current++){{ /* switch (request ID) */ {cases}
	}}
}}""".format(
        cases="".join(f.getRequestParseCase(buffername) for f in functions),
        buffername=buffername,
        prefix=prefix,
    )


def getAnswerParser(functions):
    return """
/* This function pushes the answers to the caller, doing all the necessary synchronization. */
void {prefix}parse_answer(const void *buffer, size_t size_bytes){{
	{prefix}buffer = (const unsigned char *)buffer;
	assert({prefix}get_answer_length(buffer, size_bytes).result == RPC_SUCCESS);
	assert({prefix}get_answer_length(buffer, size_bytes).size <= size_bytes);

	{prefix}mutex_unlock(RPC_mutex_answer);
	{prefix}mutex_lock(RPC_mutex_in_caller);
	{prefix}mutex_unlock(RPC_mutex_parsing_complete);
	{prefix}mutex_lock(RPC_mutex_answer);
	{prefix}mutex_lock(RPC_mutex_parsing_complete);
	{prefix}mutex_unlock(RPC_mutex_in_caller);
}}
""".format(prefix=prefix)


def getRPC_Parser_init():
    return """
void {prefix}Parser_init(){{
	if ({prefix}initialized)
		return;
	{prefix}initialized = 1;
	{prefix}mutex_lock(RPC_mutex_parsing_complete);
	{prefix}mutex_lock(RPC_mutex_answer);
}}
""".format(prefix=prefix)


def getRPC_Parser_exit():
    return """
void {prefix}Parser_exit(){{
	if (!{prefix}initialized)
		return;
	{prefix}initialized = 0;
	{prefix}mutex_unlock(RPC_mutex_parsing_complete);
	{prefix}mutex_unlock(RPC_mutex_answer);
}}
""".format(prefix=prefix)


def getAnswerSizeChecker(functions):
    return """/* Get (expected) size of (partial) answer. */
RPC_SIZE_RESULT {prefix}get_answer_length(const void *buffer, size_t size_bytes){{
	RPC_SIZE_RESULT returnvalue = {{RPC_SUCCESS, 0}};
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
	if (returnvalue.result != RPC_COMMAND_UNKNOWN)
		returnvalue.result = returnvalue.size > size_bytes ? RPC_COMMAND_INCOMPLETE : RPC_SUCCESS;
	return returnvalue;
}}
""".format(
        answercases="".join(f.getAnswerSizeCase("current") for f in functions),
        prefix=prefix,
    )


def getHashFunction():
    return Function(0, getDatatype("void"), prefix + "get_hash", [{'parameter': ArrayDatatype(
        "16", getDatatype("unsigned char"), "hash", Out=True), 'parametername': "hash"}])


def generateCode(file, xml, parser_to_network_path,
                 parser_to_server_header_path):
    #ast = CppHeaderParser.CppHeader("""typedef enum EnumTest{Test} EnumTest;""",  argType='string')
    ast = CppHeaderParser.CppHeader(file)
    # return None
    # checkDefines(ast.defines)
    setPredefinedDataTypes()
    # print(ast.includes)
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
    # print(ast.enums)
    # print(ast.typedefs_order)
    # print(ast.namespaces)
    # print(ast.global_enums)
    # print(ast.typedefs)
    # return None
    # for a in ast.__dict__:
    #print(a + ": " + str(getattr(ast, a)))
    setTypes(ast)
    # TODO: structs
    # TODO: typedefs
    # for d in datatypes:
    #print(d, datatypes[d].size_bytes)
    # return None
    # for a in ast.__dict__:
    # print(a)
    # generateFunctionCode(ast.functions[0])
    functionlist = [getHashFunction()]
    for f in ast.functions:
        if not f["name"] in functionIgnoreList:
            functionlist.append(getFunction(f))
    rpcHeader = "\n".join(f.getDeclaration() for f in functionlist)
    rpcImplementation = "\n".join(f.getDefinition() for f in functionlist)
    documentation = ""
    for f in functionlist:
        if f.name in functionIgnoreList:
            continue
        entry = ET.SubElement(xml, "function")
        f.getXml(entry)
        documentation += "\n<hr>\n" + f.getDocumentation()
    from os.path import basename
    requestParserImplementation = externC_intro + '\n' + getSizeFunction(
        functionlist,
        basename(file),
        parser_to_network_path,
        parser_to_server_header_path) + getRequestParser(functionlist) + externC_outro
    answerSizeChecker = getAnswerSizeChecker(functionlist)
    answerParser = getAnswerParser(functionlist)
    return rpcHeader, rpcImplementation, requestParserImplementation, answerParser, answerSizeChecker, documentation

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


def get_rpc_enum():
    return """typedef enum{{
        RPC_SUCCESS,
        RPC_FAILURE,
        RPC_COMMAND_UNKNOWN,
        RPC_COMMAND_INCOMPLETE
    }} RPC_RESULT;
    """.format(
        prefix=prefix,
    )


def getRPC_serviceHeader(
        headers, headername, typedeclarations, specific_header_to_types_path):
    headerDefine = headername.upper()
    return """{doNotModify}
{includeguardintro}
{externC_intro}
{hash}

{rpc_declarations}{externC_outro}
{includeguardoutro}
""".format(
        hash=getHash(),
        doNotModify=doNotModifyHeader,
        externC_intro=externC_intro,
        externC_outro=externC_outro,
        includeguardintro="""#ifndef {}
#define {}
""".format(headerDefine, headerDefine),
        includeguardoutro="""#endif /* {} */""".format(headerDefine),
        rpc_declarations="""#include <stddef.h>
#include <inttypes.h>
#include "{specific_header_to_types_path}"

/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   These are the payload functions made available by the RPC generator.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/
/* //TODO: copy comments for documentation */
{typedeclarations}
{headers}
""".format(
            prefix=prefix,
            typedeclarations=typedeclarations,
            headers=headers,
            specific_header_to_types_path=specific_header_to_types_path,
        ),)


def getNetworkHeader():
    return """
/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   IMPORTANT: The following functions must be implemented by YOU.
   They are required for the RPC to work.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

{doNotModifyHeader}
#ifndef {prefix}NETWORK_H
#define {prefix}NETWORK_H

#include "RPC_types.h"

{externC_intro}
void {prefix}message_start(size_t size);
/*  This function is called when a new message starts. {{size}} is the number of
    bytes the message will require. In the implementation you can allocate  a
    buffer or write a preamble. The implementation can be empty if you do not
    need to do that. */

void {prefix}message_push_byte(unsigned char byte);
/* Pushes a byte to be sent via network. You should put all the pushed bytes
   into a buffer and send the buffer when {prefix}message_commit is called. If you run
   out of buffer space you can send multiple partial messages as long as the
   other side puts them back together. */

RPC_RESULT {prefix}message_commit(void);
/* This function is called when a complete message has been pushed using
   {prefix}message_push_byte. Now is a good time to send the buffer over the network,
   even if the buffer is not full yet. You may also want to free the buffer that
   you may have allocated in the {prefix}message_start function.
   {prefix}message_commit should return RPC_SUCCESS if the buffer has been successfully
   sent and RPC_FAILURE otherwise. */

/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   You need to define 4 mutexes to implement the {prefix}mutex_* functions below.
   See RPC_types.h for a definition of RPC_mutex_id.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

void {prefix}mutex_init(void);
/* Initializes all rpc mutexes. */

void {prefix}mutex_lock(RPC_mutex_id mutex_id);
/* Locks the mutex. If it is already locked it yields until it can lock the mutex. */

void {prefix}mutex_unlock(RPC_mutex_id mutex_id);
/* Unlocks the mutex. The mutex is locked when the function is called. */

char {prefix}mutex_lock_timeout(RPC_mutex_id mutex_id);
/* Tries to lock a mutex. Returns 1 if the mutex was locked and 0 if a timeout
   occured. The timeout length should be the time you want to wait for an answer
   before giving up. If the time is infinite a lost answer will get the calling
   thread stuck indefinitely. */


/* ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   The following functions's implementations are automatically generated.
   ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

void {prefix}Parser_init(void);
/* Initializes various states required for the RPC. Must be called before any
   other {prefix}* function. Must be called by the parser thread. */

void {prefix}Parser_exit(void);
/* Frees various states required for the RPC. Must be called after any
   other {prefix}* function */

RPC_SIZE_RESULT {prefix}get_answer_length(const void *buffer, size_t size);
/* Returns the (expected) length of the beginning of a (partial) message.
   If returnvalue.result equals RPC_SUCCESS then returnvalue.size equals the
   expected size in bytes.
   If returnvalue.result equals RPC_COMMAND_UNKNOWN then the buffer does not point
   to the beginning of a recognized message and returnvalue.size has no meaning.
   If returnvalue.result equals RPC_COMMAND_INCOMPLETE then returnvalue.size equals
   the minimum number of bytes required to figure out the length of the message. */

void {prefix}parse_answer(const void *buffer, size_t size);
/* This function parses answer received from the network. {{buffer}} points to the
   buffer that contains the received data and {{size}} contains the number of bytes
   that have been received (NOT the size of the buffer!). This function will wake
   up {prefix}*-functions below that are waiting for an answer.
   Do not call this function with an incomplete message. Use {prefix}get_answer_length
   to make sure it is a complete message. */


{externC_outro}
#endif /* {prefix}NETWORK_H */
""".format(
        doNotModifyHeader=doNotModifyHeader,
        externC_intro=externC_intro,
        externC_outro=externC_outro,
        prefix=prefix,
    )


def generateDocumentation(documentation, filename):
    import datetime
    now = datetime.datetime.now()
    return """
    <html>
        <head>
            <title>{filename}.h - RPC Documentation</title>
            <link rel="stylesheet" href="{prefix}{filename}.css">
        </head>
    <body>
        <div class="header">
            <table>
                <tr>
                    <th colspan=2>RPC Documentation<th>
                </tr>
                <tr>
                    <td class="static">Generated by:</td><td><a href="https://github.com/Crystal-Photonics/RPC-Generator">RPC-Generator</a></td>
                </tr>
                <tr>
                    <td class="static">File:</td><td>{filename}.h</td>
                </tr>
                <tr>
                    <td class="static">Date:</td><td>{date}</td>
                </tr>
            </table>
        </div>
        <div class="content">
            {documentation}
        </div>
    </body>
</html>""".format(
        documentation=documentation,
        filename=filename,
        date=now.strftime("%Y-%m-%d %H:%M"),
        prefix=prefix,
    )


def getCss():
    return """p.static {
  width: 100%;
  font-size: 16px;
  color: #000;
  margin-left: 20px;
  margin-top: 20px;
  margin-bottom: 10px;
}

p.function {
    font-size: 24px;
    font-family: monospace;
    font-weight: 700;
    color: #224;
    margin: 0px;
}

div.content table, div.content td.content {
    margin-left: 40px;
    border: 1px solid #aaa;
    font-size: 16px;
    border-collapse: collapse;
    padding: 8px;
}

div.content th {
    font-weight: 600;
    color: #000;
    background-color: #aaa;
    padding-left: 10px;
    padding-right: 10px;
}

hr{
    margin-top: 100px;
    margin-bottom: 100px;
}

div.content{
    margin-left: 6%;
    margin-top: 5%;
    margin-bottom: 6%;
    margin-right: 6%;
}

h1{
    font-size: 200%;
    font-weight: 500;
    font-family: sans-serif;
}

div.header{
    margin-top: 6%;
    margin-left: 6%;
    font-size: 130%;
}

div.header th{
    text-align: left;
    font-size: 250%;
    padding-bottom: 5%;
}

div.header td{
    font-size: 130%;
    padding-left: 5%;
}

div.function span.static{
    font-size: 80%;
    font-weight: 500;
    margin-right: 10px;
}

div.content td.function{
    font-size: 24px;
    font-family: monospace;
    font-weight: 700;
    color: #224;
    padding-bottom: 5px;
    vertical-align: top;
}

div.content td.static{
    padding-right: 10px;
    vertical-align: center;
}

div.content table.declarations{
    border: 0px;
    margin-left: 15px;
    margin-bottom: -10px;
}
"""


def getRpcTypesHeader():
    files = getFilePaths()
    return """{doNotModifyHeader}
#ifndef RPC_TYPES_H
#define RPC_TYPES_H

#include <stddef.h>

{extrainclude}

{rpc_enum}
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
""".format(
        doNotModifyHeader=doNotModifyHeader,
        rpc_enum=get_rpc_enum(),
        prefix=prefix,
        extrainclude = files["EXTRA_INCLUDE_INTO_CLIENT_TYPES_H"]
    )


def getRequestParserHeader():
    return """{doNotModifyHeader}
#include "RPC_types.h"

{externC_intro}
/* Receives a pointer to a (partly) received message and it's size.
   Returns a result and a size. If size equals RPC_SUCCESS then size is the
   size that the message is supposed to have. If result equals RPC_COMMAND_INCOMPLETE
   then more bytes are required to determine the size of the message. In this case
   size is the expected number of bytes required to determine the correct size.*/
RPC_SIZE_RESULT {prefix}get_request_size(const void *buffer, size_t size_bytes);

/* This function parses RPC requests, calls the original function and sends an
   answer. */
void {prefix}parse_request(const void *buffer, size_t size_bytes);
{externC_outro}
""".format(
        doNotModifyHeader=doNotModifyHeader,
        externC_intro=externC_intro,
        externC_outro=externC_outro,
        prefix=prefix,
    )

try:
    root = ET.Element("RPC")
    files = getFilePaths()
    from os.path import join, split, relpath

    rpcHeader, rpcImplementation, requestParserImplementation, answerParser, answerSizeChecker, documentation = \
        generateCode(
            files["ServerHeader"], root, relpath(
                files["SERVER_GENINCDIR"], files["SERVER_SRCDIR"]), relpath(
                files["ServerHeader"], files["SERVER_SRCDIR"]))

    requestParserImplementation = doNotModifyHeader + \
        '\n' + requestParserImplementation

    rpcImplementation = '''{doNotModify}
    {externC_intro}

#include <stdint.h>
#include <assert.h>
#include "{rpc_client_header}"
#include "{network_include}"

static const unsigned char *{prefix}buffer;
static char {prefix}initialized;

{implementation}{externC_outro}
    '''.format(
        doNotModify=doNotModifyHeader,
        rpc_client_header=join(
            relpath(
                files["CLIENT_SPCINCDIR"],
                files["CLIENT_SRCDIR"]),
            prefix +
            files["ServerHeaderName"] +
            '.h'),
        implementation=rpcImplementation,
        externC_outro=externC_outro,
        externC_intro=externC_intro,
        prefix=prefix,
        network_include=join(
            relpath(
                files["CLIENT_GENINCDIR"],
                files["CLIENT_SRCDIR"]),
            prefix + 'network.h')
    )

    xml = ET.ElementTree()
    xml._setroot(root)

    dir_name_content = []
    dir_name_content.append(("CLIENT_SPCINCDIR",
                             files["ServerHeaderName"] + ".h",
                             getRPC_serviceHeader(rpcHeader, prefix + files["ServerHeaderName"] + '_H',
                                                  getTypeDeclarations(),
                                                  join(relpath(files["CLIENT_GENINCDIR"],
                                                               files["CLIENT_SPCINCDIR"]),
                                                       "RPC_types.h"))))
    dir_name_content.append(
        ("CLIENT_GENINCDIR", "RPC_types.h", getRpcTypesHeader()))
    dir_name_content.append(
        ("CLIENT_GENINCDIR", "network.h", getNetworkHeader()))
    clientcode = "".join((
        rpcImplementation,
        answerSizeChecker,
        answerParser,
        getRPC_Parser_init(),
        getRPC_Parser_exit(),
        externC_outro),
    )
    dir_name_content.append(
        ("CLIENT_SRCDIR",
         files["ServerHeaderName"] + ".c",
         clientcode))
    """
        ("documentation", generateDocumentation(documentation, files["ServerHeaderFileName"])),
        ("style", getCss()),
    ]
    """
    print("Writing client files relative to " +
          files["CLIENT_CONFIG_PATH"] + ":")
    for dir, name, content in dir_name_content:
        filename = name if name.startswith("RPC_") else prefix + name
        print(
            "\t" +
            relpath(
                join(
                    files[dir],
                    filename),
                files["CLIENT_CONFIG_PATH"]))
        with open(join(files[dir], filename), "w") as f:
            f.write(content)
    if "CLIENT_DOCDIR" in files:
        print(
            "\t" +
            relpath(
                join(
                    files["CLIENT_DOCDIR"],
                    prefix +
                    files["ServerHeaderName"] +
                    ".html"),
                files["CLIENT_CONFIG_PATH"]))
        with open(join(files["CLIENT_DOCDIR"], prefix + files["ServerHeaderName"] + ".html"), "w") as f:
            f.write(
                generateDocumentation(
                    documentation,
                    files["ServerHeaderName"]))
        print(
            "\t" +
            relpath(
                join(
                    files["CLIENT_DOCDIR"],
                    prefix +
                    files["ServerHeaderName"] +
                    ".css"),
                files["CLIENT_CONFIG_PATH"]))
        with open(join(files["CLIENT_DOCDIR"], prefix + files["ServerHeaderName"] + ".css"), "w") as f:
            f.write(getCss())
        print(
            "\t" +
            relpath(
                join(
                    files["CLIENT_DOCDIR"],
                    prefix +
                    files["ServerHeaderName"] +
                    ".xml"),
                files["CLIENT_CONFIG_PATH"]))
        xml.write(join(files["CLIENT_DOCDIR"], prefix + files["ServerHeaderName"] + ".xml"), encoding="UTF-8", xml_declaration = True)
        xml.write(join(files["CLIENT_DOCDIR"], rawhash + ".xml"), encoding="UTF-8", xml_declaration = True)

    dir_name_content = []
    dir_name_content.append(
        ("SERVER_GENINCDIR", "RPC_types.h", getRpcTypesHeader()))
    dir_name_content.append(
        ("SERVER_GENINCDIR", "network.h", getNetworkHeader()))
    dir_name_content.append(
        ("SERVER_GENINCDIR",
         "parser.h",
         getRequestParserHeader()))
    dir_name_content.append(
        ("SERVER_SRCDIR", "parser.c", requestParserImplementation))
    print("Writing server files relative to " +
          files["SERVER_CONFIG_PATH"] + ":")
    for dir, name, content in dir_name_content:
        filename = name if name.startswith("RPC_") else prefix + name
        print(
            "\t" +
            relpath(
                join(
                    files[dir],
                    filename),
                files["SERVER_CONFIG_PATH"]))
        with open(join(files[dir], filename), "w") as f:
            f.write(content)
    if "SERVER_DOCDIR" in files:
        print(
            "\t" +
            relpath(
                join(
                    files["SERVER_DOCDIR"],
                    prefix +
                    files["ServerHeaderName"] +
                    ".html"),
                files["SERVER_CONFIG_PATH"]))
        with open(join(files["SERVER_DOCDIR"], prefix + files["ServerHeaderName"] + ".html"), "w") as f:
            f.write(
                generateDocumentation(
                    documentation,
                    files["ServerHeaderName"]))
        print(
            "\t" +
            relpath(
                join(
                    files["SERVER_DOCDIR"],
                    prefix +
                    files["ServerHeaderName"] +
                    ".css"),
                files["SERVER_CONFIG_PATH"]))
        with open(join(files["SERVER_DOCDIR"], prefix + files["ServerHeaderName"] + ".css"), "w") as f:
            f.write(getCss())
        print(
            "\t" +
            relpath(
                join(
                    files["SERVER_DOCDIR"],
                    prefix +
                    files["ServerHeaderName"] +
                    ".xml"),
                files["SERVER_CONFIG_PATH"]))
        xml.write(join(files["SERVER_DOCDIR"], prefix + files["ServerHeaderName"] + ".xml"), encoding="UTF-8", xml_declaration = True)
        xml.write(join(files["SERVER_DOCDIR"], rawhash + ".xml"), encoding="UTF-8", xml_declaration = True)
except SystemError:
    import traceback
    traceback.print_exc(1)
    exit(-1)

#include "Server.h"

#include <algorithm>
#include <iostream>
#include <string>
#include <cstdio>

void fillString(char *buffer, size_t length, std::string text){
	if (length == 0)
		return;
	if (text.size() >= length){
		text.resize(length - 1);
	}
	sprintf(buffer, "%s", text.c_str());
}

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

	int32_t simpleTest(int32_t i){
		std::cout << __FUNCTION__ "\n";
		return i * i;
	}

	void arrayTest(char text_inout[42]){
		std::cout << __FUNCTION__ "\n";
		std::reverse(text_inout, text_inout + strnlen(text_inout, 42));
	}

	void multiArrayTest(char text_inout[2][3][4]){
		std::cout << __FUNCTION__ "\n";
	}

	void arrayInputTest(char text_in[42]){
		std::cout << __FUNCTION__ << ' ' << std::string(text_in, text_in + strnlen(text_in, 42)) << "\n";
	}

	void arrayOutputTest(char text_out[42]){
		fillString(text_out, 42, "hi from function "  __FUNCTION__);
		std::cout << __FUNCTION__ << "\n";
	}

	void arrayInputOutputTest(char text_inout[42]){
		const auto length = strnlen(text_inout, 42);
		auto addText = std::string(text_inout, text_inout + length);
		std::reverse(std::begin(addText), std::end(addText));
		fillString(text_inout + length, 42 - length, std::move(addText));
	}

	void emptyTest(){
		std::cout << __FUNCTION__ "\n";
	}

#pragma RPC noanswer noAnswerTest
	void noAnswerTest(){
		std::cout << __FUNCTION__ "\n";
	}

	void multipleParametersTest(uint8_t p1, uint16_t p2, uint32_t p3){
		std::cout << __FUNCTION__ "\n";
	}

#pragma RPC ignore ignoreTest
	void ignoreTest(){
		std::cout << __FUNCTION__ "\n";
	}

#ifdef __cplusplus
}
#endif /* __cplusplus */

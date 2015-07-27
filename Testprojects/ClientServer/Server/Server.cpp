#define _CRT_SECURE_NO_WARNINGS
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
	void setCPS(uint16_t cps){
		std::cout << __FUNCTION__ " cps = " << cps << '\n';
	}

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
		std::cout << __FUNCTION__ << "\n";
		fillString(text_out, 42, "hi from function "  __FUNCTION__);
	}

	void arrayInputOutputTest(char text_inout[42]){
		std::cout << __FUNCTION__ "\n";
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
	
	void structTest(struct TestStruct s_out[1]){
		std::cout << __FUNCTION__ "\n";
		s_out->n1 = 1;
		s_out->n2 = 2;
		s_out->n3 = 3;
		s_out->n4 = 4;
	}

	void typedefStructTest(TypedefTestStruct s_inout[1]){
		int i = 0;
		for (auto &l1 : s_inout[0].iaa){
			for (auto &l2 : l1){
				for (auto &l3 : l2){
					l3 = i++;
				}
			}
		}
		std::cout << __FUNCTION__ << " with value " << s_inout->n << '\n';
	}

	void enumTest1(enum TestEnum testEnum){
		std::cout << __FUNCTION__ "\n";
	}

	enum TestEnum enumTest2(){
		std::cout << __FUNCTION__ "\n";
		return TEb;
	}

	void typedefEnumTest1(TypedefTestEnum testEnum){
		std::cout << __FUNCTION__ "\n";
	}

	TypedefTestEnum typedefEnumTest2(){
		std::cout << __FUNCTION__ "\n";
		return TTEd;
	}


#ifdef __cplusplus
}
#endif /* __cplusplus */

#include "Server.h"

#include <algorithm>
#include <iostream>

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

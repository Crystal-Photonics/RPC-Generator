#define _CRT_SECURE_NO_WARNINGS
#include "Bob.h"
#include "RPC\Alice_to_Bob\specific_include\RPC_Alice.h"

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

	void aliceToBobTest(void){
		std::cout << "Message from Alice\n";
	}
	void pong(void){
		std::cout << "Pong\n";
	}
	void infinitePingpongB(void){
		std::cout << "got infinitePingpongB\n";
		std::cout << "infinitePingpongA " << (infinitePingpongA() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
	}
	void networkFloodingB(void){
		std::cout << "got networkFloodingB\n";
		std::cout << "networkFloodingA " << (networkFloodingA() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
		std::cout << "networkFloodingA " << (networkFloodingA() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
	}

#ifdef __cplusplus
}
#endif /* __cplusplus */

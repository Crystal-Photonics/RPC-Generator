#include "Alice.h"
#include "RPC_Bob.h"
#include <iostream>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

	void bobToAliceTest(void){
		std::cout << "Message from Bob\n";
	}
	void ping(void){
		std::cout << "Pong\n";
	}
	void infinitePingpongA(void){
		std::cout << "got infinitePingpongA\n";
		std::cout << "infinitePingpongB " << (infinitePingpongB() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
	}
	void networkFloodingA(void){
		std::cout << "got networkFloodingA\n";
		std::cout << "networkFloodingB " << (networkFloodingB() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
		std::cout << "networkFloodingB " << (networkFloodingB() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
	}
#ifdef __cplusplus
}
#endif /* __cplusplus */

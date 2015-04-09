#include "Client.h"

#include <algorithm>
#include <iostream>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

int32_t square(int32_t i){
	return i * i;
}

void reverse(char text_inout[42]){
	std::reverse(text_inout, text_inout + strnlen(text_inout, 42));
}

void sayHello(){
	std::cout << "Hello!\n";
}

int32_t square2(int32_t i){
	std::cout << "square of " << i << " is " << i * i << ", but I'm not telling!\n";
	return i * i;
}

#ifdef __cplusplus
}
#endif /* __cplusplus */

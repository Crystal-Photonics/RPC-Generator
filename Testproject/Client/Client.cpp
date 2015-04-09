#include "Client.h"

#include <algorithm>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

int32_t square(int32_t i){
	return i * i;
}

void reverse(char text_inout[42]){
	std::reverse(text_inout, text_inout + strnlen(text_inout, 42));
}

#ifdef __cplusplus
}
#endif /* __cplusplus */

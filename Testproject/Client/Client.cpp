#include "Client.h"
#include <future>

#include <numeric>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

int32_t square(int32_t i){
	return i * i;
}

int32_t test(uint16_t data_inout[42]){
	for (int i = 0; i < 42; ++i)
		data_inout[i] *= data_inout[i];
	return std::accumulate(data_inout, data_inout + 42, 0);
}

#ifdef __cplusplus
}
#endif /* __cplusplus */

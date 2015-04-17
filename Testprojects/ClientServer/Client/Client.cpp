#include "Client.h"

uint32_t pow(uint32_t base, uint8_t exponent){
	auto result = 1;
	while (exponent--)
		result *= base;
	return result;
}

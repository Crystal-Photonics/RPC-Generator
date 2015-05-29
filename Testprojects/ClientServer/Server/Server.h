#include <inttypes.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

#pragma RPC prefix RPC_UART_

int32_t simpleTest(int32_t i);

void arrayTest(char text_inout[42]);

void multiArrayTest(char text_inout[2][3][4]);

void arrayInputTest(char text_in[42]);

void arrayOutputTest(char text_out[42]);

void arrayInputOutputTest(char text_inout[42]);

void emptyTest();

#pragma RPC noanswer noAnswerTest
void noAnswerTest();

void multipleParametersTest(uint8_t p1, uint16_t p2, uint32_t p3);

#pragma RPC ignore ignoreTest
void ignoreTest();

struct TestStruct{
	uint32_t n1;
	int16_t n2;
	char n3;
	uint8_t n4;
	char ar[2];
	char c;
};

void structTest(struct TestStruct s_out[1]);

typedef struct {
	uint16_t n;
	uint8_t ia[42];
	uint8_t iaa[1][2][3][4][5];
} TypedefTestStruct;

void typedefStructTest(TypedefTestStruct s_in[1]);

#ifdef __cplusplus
}
#endif /* __cplusplus */

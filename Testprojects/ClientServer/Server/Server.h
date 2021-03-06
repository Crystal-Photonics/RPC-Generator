#include <inttypes.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

#pragma RPC prefix RPC_UART_

#pragma RPC noanswer setCPS
void setCPS(uint16_t cps);

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
};

void structTest(struct TestStruct s_out[1]);

typedef struct {
	uint16_t n;
	uint8_t ia[42];
	uint8_t iaa[1][2][3];
} TypedefTestStruct;

void typedefStructTest(TypedefTestStruct s_inout[1]);

enum TestEnum{
	TEa, TEb, TEc = -5
};

enum TestEnum2{
	TE2a, TE2b, TE2c = 5, TE2d = TE2c + 1, TE2e = 2 * 2 * 13
};

void enumTest1(enum TestEnum testEnum);
enum TestEnum enumTest2();

typedef enum {
	TTEa, TTEb, TTEc = 5, TTEd = TTEc + 1
}TypedefTestEnum;

void typedefEnumTest1(TypedefTestEnum testEnum);
TypedefTestEnum typedefEnumTest2();

#ifdef __cplusplus
}
#endif /* __cplusplus */

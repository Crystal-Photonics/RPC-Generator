#include <inttypes.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

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

#ifdef __cplusplus
}
#endif /* __cplusplus */

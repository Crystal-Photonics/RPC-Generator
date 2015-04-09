#include <inttypes.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

int32_t square(int32_t i);

void reverse(char text_inout[42]);

#pragma RPC noanswer sayHello
void sayHello();

#pragma RPC noanswer square2
int32_t square2(int32_t i);

#ifdef __cplusplus
}
#endif /* __cplusplus */

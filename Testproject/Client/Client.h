#include <cstdint>

#pragma RPC ignore sendbuffer
int sendbuffer(const void *buffer, uint32_t buffer_size);
#pragma RPC ignore sleep
void sleep();
#pragma RPC ignore wakeup
void wakeup();
#define RPC_BUFFER_SIZE

#define RPC_SEND(BUFFER, SIZE) sendbuffer((BUFFER), (SIZE))
#define RPC_SLEEP() sleep()
#define RPC_WAKEUP() wakeup()

int32_t square(int32_t i);

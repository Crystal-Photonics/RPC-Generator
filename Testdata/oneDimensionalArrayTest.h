#define RPC_SEND(BUFFER, SIZE) (send((BUFFER), (SIZE)))
#define RPC_SLEEP() (aquire_semaphor(send_semaphor) != semaphor_timeout)
#define RPC_WAKEUP() (release_semaphor(send_semaphor))

uint8_t f(uint16_t i, uint8_t singleArrayData_in[1], uint8_t singleArrayData_out[2], uint8_t singleArrayData_inout[3]);

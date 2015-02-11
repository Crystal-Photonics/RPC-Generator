#define RPC_SEND(BUFFER, SIZE) (send((BUFFER), (SIZE)))
#define RPC_SLEEP() (aquire_semaphor(send_semaphor) != semaphor_timeout)
#define RPC_WAKEUP() (release_semaphor(send_semaphor))

uint8_t f(int i);

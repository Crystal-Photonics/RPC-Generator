#include <inttypes.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */
	void bobToAliceTest(void);
	void ping(void);
#pragma RPC noanswer infinitePingpongA
	void infinitePingpongA(void);
	void networkFloodingA(void);
#ifdef __cplusplus
}
#endif /* __cplusplus */

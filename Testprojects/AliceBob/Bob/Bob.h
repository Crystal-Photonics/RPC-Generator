#include <inttypes.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */
	void aliceToBobTest(void);
	void pong(void);
#pragma RPC noanswer infinitePingpongB
	void infinitePingpongB(void);
	void networkFloodingB(void);
#ifdef __cplusplus
}
#endif /* __cplusplus */

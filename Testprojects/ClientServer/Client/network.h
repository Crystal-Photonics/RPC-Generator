#ifndef NETWORK_H
#define NETWORK_H

#include "../SharedSocketCode/socket.h"
#include <memory>

extern std::shared_ptr<Socket> socket; //using shared_ptr for it's thread safety, not for sharing

#endif //!NETWORK_H

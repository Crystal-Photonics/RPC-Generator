#ifndef SOCKET_H
#define SOCKET_H

#include <string>

class Socket{
public:
	static Socket getConnection(const char *ip, unsigned short int port); //connects to given ip:port
	static Socket waitForConnection(unsigned short int port); //listens for connection on given port
	void sendData(const void *buffer, size_t size); //blocks until size bytes have been sent or an error occurs
	void receiveData(void *buffer, size_t size); //blocks until size bytes have been read
	Socket(const Socket &) = delete; //no copying sockets
	//Socket(Socket &&other) = default; //moving is fine
	Socket(Socket &&other);
	~Socket();
private:
	Socket(void *);
	void *implementation;
};

#endif //SOCKET_H

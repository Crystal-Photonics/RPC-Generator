#ifndef SOCKET_H
#define SOCKET_H

#include <string>
#include <chrono>
#include <memory>

class Socket{
public:
	const static unsigned short int serverListenPort = 1192;
	const static unsigned short int serverConnectPort = 1192;
	//if you set serverListenPort and serverConnectPort to different values you can
	//monitor, manipulate and forward data sent between client and server
	static Socket getConnection(
		const char *ip,
		unsigned short int port
		); //connects to given ip:port
	static std::unique_ptr<Socket> waitForConnection(
		const char *ip,
		unsigned short int port,
		const std::chrono::milliseconds &timeout
		);
	//listens for connection on given ip:port with given timeout
	//returns nullptr if a timeout occurs
	void sendData(
		const void *buffer,
		size_t size
		); //blocks until size bytes have been sent or an error occurs
	void receiveData(
		void *buffer,
		size_t size,
		const std::chrono::milliseconds &timeout = std::chrono::milliseconds(1000));
	Socket(
		const Socket &) = delete; //no copying sockets
	/* Socket(
		Socket &&other) = default; *///moving is fine
	Socket(
		Socket &&other);
	~Socket();
	struct ConnectionClosed{}; //exception thrown when trying to send or receive data on closed connection
	struct ConnectionTimeoutException{}; //exception thrown when a timeout occurs
private:
	Socket(
		void *);
	void *implementation;
};

#endif //SOCKET_H

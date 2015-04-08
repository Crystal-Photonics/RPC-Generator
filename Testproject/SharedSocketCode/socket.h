#ifndef SOCKET_H
#define SOCKET_H

#include <string>
#include <chrono>
#include <memory>

class Socket{
public:
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
		size_t size); //blocks until size bytes have been read
	Socket(
		const Socket &) = delete; //no copying sockets
	/* Socket(
		Socket &&other) = default; *///moving is fine
	Socket(
		Socket &&other);
	~Socket();
private:
	Socket(
		void *);
	void *implementation;
};

#endif //SOCKET_H

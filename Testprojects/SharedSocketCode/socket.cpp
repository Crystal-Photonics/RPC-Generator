#ifdef WIN32

//#include <winsock.h>
#include <ws2tcpip.h>
#pragma comment(lib, "Ws2_32.lib")
#include "socket.h"
#include <exception>

struct WsaInit{
	WsaInit(){
		WSADATA wsaData = {};
		if (WSAStartup(MAKEWORD(2, 2), &wsaData))
			throw std::runtime_error("WSAStartup failed with error " + std::to_string(WSAGetLastError()));
	}
	~WsaInit(){
		WSACleanup();
	}
};

class SocketImplementation{
public:
	static SocketImplementation getConnection(const char *ip, unsigned short int port); //connects to given ip:port
	static std::unique_ptr<SocketImplementation> waitForConnection(const char *ip, unsigned short int port, const std::chrono::milliseconds &timeout); //listens for connection on given port
	void sendData(const void *buffer, size_t size); //blocks until size bytes have been sent or an error occurs
	void receiveData(void *buffer, size_t size); //blocks until size bytes have been read
	SocketImplementation(const SocketImplementation &) = delete; //no copying SocketImplementations
	SocketImplementation(SocketImplementation &&other);
	~SocketImplementation();
private:
	static WsaInit wsaInit;
	SOCKET s;
	template <class Function>
	SocketImplementation(const char *ip, unsigned short int port, Function &&connector){
		addrinfo *result = nullptr;
		addrinfo hints = {};
		hints.ai_family = AF_INET;
		hints.ai_socktype = SOCK_STREAM;
		hints.ai_protocol = IPPROTO_TCP;
		if (getaddrinfo(ip, std::to_string(port).c_str(), &hints, &result))
			throw std::runtime_error("getaddrinfo failed with error " + std::to_string(WSAGetLastError()));
		s = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
		try{
			std::forward<Function>(connector)(s, result);
		}
		catch (...){
			freeaddrinfo(result);
			if (closesocket(s))
				throw std::runtime_error("closesocket failed with error " + std::to_string(WSAGetLastError()));
			throw;
		}
	}
	struct ConnectionTimeoutException{};
};

WsaInit SocketImplementation::wsaInit;

Socket Socket::getConnection(const char *ip, unsigned short int port){
	auto s = SocketImplementation::getConnection(ip, port);
	return Socket(new SocketImplementation(std::move(s)));
}
std::unique_ptr<Socket> Socket::waitForConnection(const char *ip, unsigned short int port, const std::chrono::milliseconds &timeout){
	auto socketImpl = SocketImplementation::waitForConnection(ip, port, timeout);
	if (socketImpl){
		Socket socket(socketImpl.release());
		return std::make_unique<Socket>(std::move(socket));
	}
	return nullptr;
}
void Socket::sendData(const void *buffer, size_t size){
	return static_cast<SocketImplementation *>(implementation)->sendData(buffer, size);
}
void Socket::receiveData(void *buffer, size_t size){
	return static_cast<SocketImplementation *>(implementation)->receiveData(buffer, size);
}
Socket::Socket(Socket &&other) : implementation(nullptr){
	using namespace std;
	swap(implementation, other.implementation);
}
Socket::~Socket(){
	delete static_cast<SocketImplementation *>(implementation);
}
Socket::Socket(void *impl) : implementation(impl){}

SocketImplementation SocketImplementation::getConnection(const char *ip, unsigned short int port){
	auto connector = [](SOCKET &s, addrinfo *result){
		if (connect(s, result->ai_addr, result->ai_addrlen) == SOCKET_ERROR)
			throw std::runtime_error("connect failed with error " + std::to_string(WSAGetLastError()));
	};
	return SocketImplementation(ip, port, std::move(connector));
}

std::unique_ptr<SocketImplementation> SocketImplementation::waitForConnection(const char *ip, unsigned short int port, const std::chrono::milliseconds &timeout){
	/*
	TODO: Clean up fishiness: This function uses exceptions to communicate a timeout. Since a timeout is a normal control flow,
	it should be modelled without exceptions.
	*/
	auto connector = [&](SOCKET &s, addrinfo *result){
		if (bind(s, result->ai_addr, result->ai_addrlen) == SOCKET_ERROR)
			throw std::runtime_error("connect failed with error " + std::to_string(WSAGetLastError()));
		if (listen(s, 1) == SOCKET_ERROR)
			throw std::runtime_error("listen failed with error " + std::to_string(WSAGetLastError()));
		timeval selectTimeout;
		selectTimeout.tv_sec = std::chrono::duration_cast<std::chrono::seconds>(timeout).count();
		selectTimeout.tv_usec = std::chrono::duration_cast<std::chrono::microseconds>(timeout).count() % 1000000;
		fd_set fds;
		fds.fd_count = 1;
		fds.fd_array[0] = s;
		switch (select(0, &fds, nullptr, nullptr, &selectTimeout)){
			case 0: //timeout
				throw ConnectionTimeoutException();
			case 1: //ready for accept
				break;
			case SOCKET_ERROR:
				throw std::runtime_error("select failed with error " + std::to_string(WSAGetLastError()));
			default: //no idea what happened
				throw std::runtime_error("select failed with unanticipated behavior");
		}
		SOCKET connection = accept(s, nullptr, nullptr); //never blocks due to check by select
		if (connection == INVALID_SOCKET)
			throw std::runtime_error("accept failed with error " + std::to_string(WSAGetLastError()));
		using namespace std;
		swap(connection, s);
		if (closesocket(connection))
			throw std::runtime_error("closesocket failed with error " + std::to_string(WSAGetLastError()));
	};
	try {
		auto sock = SocketImplementation(ip, port, std::move(connector));
		return std::make_unique<SocketImplementation>(std::move(sock));
	}
	catch (ConnectionTimeoutException){
		return nullptr;
	}
}

void SocketImplementation::sendData(const void *buffer, size_t size){
	if (send(s, static_cast<const char *>(buffer), size, 0) == SOCKET_ERROR)
		throw std::runtime_error("send failed with error " + std::to_string(WSAGetLastError()));
}

void SocketImplementation::receiveData(void *buffer, size_t size){
	auto res = 0;
	do {
		res = recv(s, static_cast<char *>(buffer)+res, size - res, 0);
		if (size == res)
			return;
	} while (res > 0);
	throw Socket::ConnectionClosed();
}


SocketImplementation::SocketImplementation(SocketImplementation &&other) :
s(INVALID_SOCKET){
	using namespace std;
	swap(s, other.s);
}

SocketImplementation::~SocketImplementation(){
	closesocket(s);
}

#else

//TODO: add linux implementaion

#endif //WIN32

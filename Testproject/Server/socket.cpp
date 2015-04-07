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
	static SocketImplementation waitForConnection(unsigned short int port); //listens for connection on given port
	void sendData(const void *buffer, size_t size); //blocks until size bytes have been sent or an error occurs
	void receiveData(void *buffer, size_t size); //blocks until size bytes have been read
	SocketImplementation(SocketImplementation &&other);
	~SocketImplementation();
private:
	static WsaInit wsaInit;
	SOCKET s;
	template <class Function>
	SocketImplementation(const char *ip, unsigned short int port, Function &&connector){
		addrinfo *result = nullptr,
			hints;
		ZeroMemory(&hints, sizeof(hints));
		hints.ai_family = AF_INET;
		hints.ai_socktype = SOCK_STREAM;
		hints.ai_protocol = IPPROTO_TCP;
		if (getaddrinfo(ip, std::to_string(port).c_str(), &hints, &result))
			throw std::runtime_error("getaddrinfo failed with error " + std::to_string(WSAGetLastError()));
		auto s = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
		std::forward<Function>(connector)(s, result);
		freeaddrinfo(result);
	}
	struct ConnectionClosed{};
};

WsaInit SocketImplementation::wsaInit;

Socket Socket::getConnection(const char *ip, unsigned short int port){
	auto s = SocketImplementation::getConnection(ip, port);
	return Socket(new SocketImplementation(std::move(s)));
}
Socket Socket::waitForConnection(unsigned short int port){
	auto s = SocketImplementation::waitForConnection(port);
	return Socket(new SocketImplementation(std::move(s)));
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

SocketImplementation SocketImplementation::waitForConnection(unsigned short int port){
	auto connector = [](SOCKET &s, addrinfo *result){
		if (bind(s, result->ai_addr, result->ai_addrlen) == SOCKET_ERROR)
			throw std::runtime_error("connect failed with error " + std::to_string(WSAGetLastError()));
		if (listen(s, 1) == SOCKET_ERROR)
			throw std::runtime_error("listen failed with error " + std::to_string(WSAGetLastError()));
		SOCKET connection = accept(s, nullptr, nullptr);
		if (connection == INVALID_SOCKET)
			throw std::runtime_error("accept failed with error " + std::to_string(WSAGetLastError()));
		using namespace std;
		swap(connection, s);
		if (closesocket(connection))
			throw std::runtime_error("closesocket failed with error " + std::to_string(WSAGetLastError()));
	};
	return SocketImplementation("127.0.0.1", port, std::move(connector));
}

void SocketImplementation::sendData(const void *buffer, size_t size){
	if (send(s, static_cast<const char *>(buffer), size, 0) == SOCKET_ERROR)
		throw std::runtime_error("send failed with error " + std::to_string(WSAGetLastError()));
}

void SocketImplementation::receiveData(void *buffer, size_t size){
	auto res = 0;
	do {
		res = recv(s, static_cast<char *>(buffer)+res, size - res, 0);
	} while (res > 0);
	if (res == 0)
		throw SocketImplementation::ConnectionClosed();
	throw std::runtime_error("recv failed with error " + std::to_string(WSAGetLastError()));
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

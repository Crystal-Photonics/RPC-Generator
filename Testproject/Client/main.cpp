#include "RPC_service.h"
#include <vector>
#include <fstream>
#include <cassert>
#include <iostream>
#include "../SharedSocketCode/socket.h"

int main(){
	try{
		auto s = Socket::getConnection("127.0.0.1", Socket::serverConnectPort);
		std::vector<unsigned char> buffer;
		for (;;){
			do{
				unsigned char c;
				s.receiveData(&c, 1);
				buffer.push_back(c);
			} while (RPC_get_request_size(buffer.data(), buffer.size()).result != RPC_SUCCESS);
			RPC_parse_request(buffer.data(), buffer.size());
			buffer.clear();
		}
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
}


#include "RPC_service.h"
#include <vector>
#include <fstream>
#include <cassert>
#include <iostream>
#include "network.h"
#include "RPC_Alice.h"

RPC_RESULT handleInput(const std::vector<unsigned char> &v){
	if (v.size() == 0)
		return RPC_COMMAND_INCOMPLETE;
	const bool isRequest = v[0] % 2 == 0;
	const auto result = isRequest ? RPC_get_request_size(&v[0], v.size()) : RPC_get_answer_length(&v[0], v.size());
	if (result.result != RPC_SUCCESS)
		return result.result;
	if (isRequest){
		static int counter = 0;
		std::cout << "Request " << counter++ << ": ";
		RPC_parse_request(&v[0], v.size());
	}
	else
		RPC_parse_answer(&v[0], v.size());
	return RPC_SUCCESS;
}

int main(){
	RPC_Parser_init();

	try{
		for (;;){
			std::cout << "waiting for connection\n";
			socket = Socket::waitForConnection("127.0.0.1", Socket::serverListenPort, std::chrono::minutes(1));
			if (!socket){
				std::cout << "got timeout\n";
				continue;
			}
			std::cout << "connection established\n";
			std::vector<unsigned char> buffer;
			try{
				for (;;){
					unsigned char c;
					socket->receiveData(&c, 1);
					buffer.push_back(c);
					switch (handleInput(buffer)){
						case RPC_COMMAND_INCOMPLETE:
							continue;
						case RPC_COMMAND_UNKNOWN:
							std::cout << "unknown command received: " << std::string(std::begin(buffer), std::end(buffer)) << '\n';
							std::cout << "dropping " << buffer.size() << " bytes of data\n";
							buffer.clear();
							continue;
						case RPC_SUCCESS:
							buffer.clear();
							break;
						default:
							throw std::runtime_error("unknown result from RPC_get_request_size: " + std::to_string(RPC_get_request_size(buffer.data(), buffer.size()).result));
					}
				}
			}
			catch (Socket::ConnectionClosed){
				std::cout << "Connection unexpectedly aborted, dropping " << buffer.size() << " bytes of data\n";
				continue;
			}
		}
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
	RPC_Parser_exit();
}

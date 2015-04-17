#include "RPC_service.h"
#include <vector>
#include <fstream>
#include <cassert>
#include <iostream>
#include "network.h"

int main(){
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
					for (;;){
						unsigned char c;
						socket->receiveData(&c, 1);
						buffer.push_back(c);
						switch (RPC_get_request_size(buffer.data(), buffer.size()).result){
							case RPC_COMMAND_INCOMPLETE:
								continue;
							case RPC_COMMAND_UNKNOWN:
								std::cout << "unknown command received: " << std::string(std::begin(buffer), std::end(buffer)) << '\n';
								std::cout << "dropping " << buffer.size() << " bytes of data\n";
								buffer.clear();
								continue;
							case RPC_SUCCESS:
								break;
							default:
								throw std::runtime_error("unknown result from RPC_get_request_size: " + std::to_string(RPC_get_request_size(buffer.data(), buffer.size()).result));
						}
						break;
					}
					RPC_parse_request(buffer.data(), buffer.size());
					buffer.clear();
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
}

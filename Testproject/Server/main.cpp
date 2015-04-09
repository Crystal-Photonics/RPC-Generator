#include <iostream>
#include "RPC_client.h"
#include <thread>
#include <cassert>
#include <vector>
#include <atomic>
#include "../SharedSocketCode/socket.h"
#include "network.h"

std::atomic<bool> quitParser = false;

void parser(){
	try{
		for (; !quitParser;){
			std::cout << "waiting for connection\n";
			socket = Socket::waitForConnection("127.0.0.1", Socket::serverListenPort, std::chrono::minutes(1));
			if (!socket){
				std::cout << "got timeout\n";
				continue;
			}
			std::cout << "connection established\n";
			std::vector<unsigned char> buffer;
			try{
				for (; !quitParser;){
					for (;;){
						unsigned char c;
						socket->receiveData(&c, 1);
						buffer.push_back(c);
						if (quitParser)
							return;
						switch (RPC_get_answer_length(buffer.data(), buffer.size()).result){
							case RPC_COMMAND_INCOMPLETE:
								continue;
							case RPC_COMMAND_UNKNOWN:
								//+quick hack for testing
								if (buffer.size() == 1){
									if (buffer[0] == 'q'){
										std::cout << "closing connection\n";
										throw Socket::ConnectionClosed();
									}
									else if (buffer[0] == 'Q'){
										exit(0);
									}
								}
								//-quick hack for testing
								std::cout << "unknown command received: " << std::string(std::begin(buffer), std::end(buffer)) << '\n';
								std::cout << "dropping " << buffer.size() << " bytes of data\n";
								buffer.clear();
								continue;
							case RPC_SUCCESS:
								break;
							default:
								throw std::runtime_error("unknown result from RPC_get_answer_length: " + std::to_string(RPC_get_answer_length(buffer.data(), buffer.size()).result));
						}
						break;
					}
					RPC_parse_answer(buffer.data(), buffer.size());
					buffer.clear();
				}
			}
			catch (Socket::ConnectionClosed){
				socket = nullptr;
				std::cout << "Connection unexpectedly aborted, dropping " << buffer.size() << " bytes of data\n";
				continue;
			}
		}
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
}

void logic(){
	try{
		for (;;){
			while (socket == nullptr)
				std::this_thread::sleep_for(std::chrono::milliseconds(100));
			for (;socket;){
				std::cout << "Testing RPC functions:\n";
				int32_t result;
				if (square(&result, 42) == RPC_SUCCESS){
					std::cout << "square of " << 42 << " is " << result << '\n';
				}
				else{
					std::cout << "failed calling function square\n";
				}
				char buffer[42] = "Hello World!";
				if (reverse(buffer) == RPC_SUCCESS){
					std::cout << "reverse of \"Hello World!\" is " << buffer << '\n';
				}
				else{
					std::cout << "failed calling function square\n";
				}
				std::this_thread::sleep_for(std::chrono::seconds(1));
			}
		}
		quitParser = true;
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
}

int main()
{
	try{
		RPC_Parser_init();
		auto logicthread = std::thread(logic);
		parser();
		logicthread.join();
		RPC_Parser_exit();
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
}

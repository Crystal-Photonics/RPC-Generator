#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include "RPC\Alice_to_Bob\specific_include\RPC_Bob.h"
#include <thread>
#include <cassert>
#include <vector>
#include <atomic>
#include "../../SharedSocketCode/socket.h"
#include "network.h"
#include <string>
#include "RPC\Bob_to_Alice\include\RPC_network.h"
#include "RPC\Bob_to_Alice\include\RPC_parser.h"

std::atomic<bool> quitParser = false;

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

void parser(){
	try{
		for (; !quitParser;){
			try{
				auto s = Socket::getConnection("127.0.0.1", Socket::serverConnectPort);
				socket = std::make_shared<Socket>(std::move(s));
			}
			catch (const std::runtime_error &error){
				std::cout << error.what() << '\n';
				continue;
			}
			std::vector<unsigned char> buffer;
			try{
				for (; !quitParser;){
					unsigned char c;
					socket->receiveData(&c, 1);
					buffer.push_back(c);
					if (quitParser)
						return;
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
							throw std::runtime_error("unknown result from RPC_get_answer_length: " + std::to_string(RPC_get_answer_length(buffer.data(), buffer.size()).result));
					}
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
			std::cout << "Testing RPC functions:\n";
			for (; socket;){
				//std::cout << "aliceToBobTest " << (aliceToBobTest() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
				std::cout << "infinitePingpongB " << (infinitePingpongB() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
				return;
				std::this_thread::sleep_for(std::chrono::milliseconds(100));
				continue;

				for (int i = 0; i < 0; ++i){
					std::cout << "Initiating pingpong " << i << '\n';
					std::cout << "infinitePingpongB " << (infinitePingpongB() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
					std::this_thread::sleep_for(std::chrono::milliseconds(250));
				}

				std::cout << "Initiating network flooding\n";
				std::cout << "networkFloodingB " << (networkFloodingB() == RPC_SUCCESS ? "succeeded" : "failed") << '\n';
				std::this_thread::sleep_for(std::chrono::milliseconds(1000));
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

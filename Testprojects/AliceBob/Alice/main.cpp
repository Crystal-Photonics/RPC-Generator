#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include "RPC_bob.h"
#include <thread>
#include <cassert>
#include <vector>
#include <atomic>
#include "../../SharedSocketCode/socket.h"
#include "network.h"
#include <string>

std::atomic<bool> quitParser = false;

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
			for (; socket;){
				std::cout << "Testing RPC functions:\n";

				int32_t retval;
				if (simpleTest(&retval, 17) == RPC_SUCCESS){
					std::cout << "simpleTest succeeded: " << retval << '\n';
				}
				else{
					std::cout << "simpleTest failed\n";
				}

				char testArray[42] = "Hello World!";
				if (arrayTest(testArray) == RPC_SUCCESS){
					std::cout << "arrayTest succeeded: " << std::string(testArray, testArray + strnlen(testArray, 42)) << '\n';
				}
				else{
					std::cout << "arrayTest failed\n";
				}

				char multiArray[2][3][4] = {};
				if (multiArrayTest(multiArray) == RPC_SUCCESS){
					std::cout << "multiArrayTest succeeded\n";
				}
				else{
					std::cout << "multiArrayTest failed\n";
				}

				if (arrayInputTest(testArray) == RPC_SUCCESS){
					std::cout << "arrayInputTest succeeded: " << std::string(testArray, testArray + strnlen(testArray, 42)) << '\n';
				}
				else{
					std::cout << "arrayInputTest failed\n";
				}

				sprintf(testArray, "Heyo Input!");
				if (arrayOutputTest(testArray) == RPC_SUCCESS){
					std::cout << "arrayOutputTest succeeded\n";
				}
				else{
					std::cout << "arrayOutputTest failed\n";
				}

				sprintf(testArray, "Heyo IO!");
				if (arrayInputOutputTest(testArray) == RPC_SUCCESS){
					std::cout << "arrayInputOutputTest succeeded: " << std::string(testArray, testArray + strnlen(testArray, 42)) << '\n';
				}
				else{
					std::cout << "arrayInputOutputTest failed\n";
				}

				if (emptyTest() == RPC_SUCCESS){
					std::cout << "emptyTest succeeded\n";
				}
				else{
					std::cout << "emptyTest failed\n";
				}

				if (noAnswerTest() == RPC_SUCCESS){
					std::cout << "noAnswerTest succeeded\n";
				}
				else{
					std::cout << "noAnswerTest failed\n";
				}

				uint8_t p1 = 11;
				uint16_t p2 = 222;
				uint32_t p3 = 3333;
				if (multipleParametersTest(p1, p2, p3) == RPC_SUCCESS){
					std::cout << "multipleParametersTest succeeded\n";
				}
				else{
					std::cout << "multipleParametersTest failed\n";
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

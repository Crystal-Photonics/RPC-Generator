#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include "RPC/specific_include/RPC_UART_Server.h"
#include "RPC/generic_include/RPC_UART_network.h"
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
						try{
							socket->receiveData(&c, 1);
						}
						catch (const Socket::ConnectionTimeoutException &){
							return;
						}
						buffer.push_back(c);
						if (quitParser)
							return;
						switch (RPC_UART_get_answer_length(buffer.data(), buffer.size()).result){
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
								throw std::runtime_error("unknown result from RPC_get_answer_length: " + std::to_string(RPC_UART_get_answer_length(buffer.data(), buffer.size()).result));
						}
						break;
					}
					RPC_UART_parse_answer(buffer.data(), buffer.size());
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

#define TEST_FUNCTION(FUNCTION, ...)\
if (FUNCTION(__VA_ARGS__) == RPC_SUCCESS)\
std::cout << #FUNCTION << " succeeded\n";\
else{std::cout << #FUNCTION << " failed\n"; __debugbreak(); assert(!#FUNCTION " failed\n");}

void logic(){
	try{
		while (socket == nullptr)
			std::this_thread::sleep_for(std::chrono::milliseconds(100));
		const auto &start = std::chrono::system_clock::now();
		const auto &testduration = std::chrono::seconds(1);
		assert(socket);
		for (; socket && (start + testduration > std::chrono::system_clock::now());){
			std::cout << "Testing RPC functions:\n";

			int32_t retval;
			auto success = simpleTest(&retval, 5);
			assert(retval == 3);
			TEST_FUNCTION(simpleTest, &retval, 17);
			char testArray[42] = "Hello World!";
			TEST_FUNCTION(arrayTest, testArray);
			assert(std::string(testArray, testArray + strnlen(testArray, 42)) == "!dlroW olleH");
			char multiArray[2][3][4] = {};
			TEST_FUNCTION(multiArrayTest, multiArray);
			TEST_FUNCTION(arrayInputTest, testArray);
			sprintf(testArray, "Heyo Input!");
			TEST_FUNCTION(arrayOutputTest, testArray);
			sprintf(testArray, "Heyo IO!");
			TEST_FUNCTION(arrayInputOutputTest, testArray);
			TEST_FUNCTION(emptyTest);
			TEST_FUNCTION(noAnswerTest);
			uint8_t p1 = 11;
			uint16_t p2 = 222;
			uint32_t p3 = 3333;
			TEST_FUNCTION(multipleParametersTest, p1, p2, p3);
			TestStruct s = {};
			TEST_FUNCTION(structTest, &s);
			TypedefTestStruct ts = {};
			ts.n = 42;
			TEST_FUNCTION(typedefStructTest, &ts);
			for (auto &l1 : ts.iaa){
				for (auto &l2 : l1){
					for (auto &l3 : l2){
						std::cout << static_cast<int>(l3) << ' ';
					}
				}
			}
			std::cout << '\n';
			//std::this_thread::sleep_for(std::chrono::seconds(1));
		}
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
	quitParser = true;
}

int main()
{
	try{
		RPC_UART_Parser_init();
		auto logicthread = std::thread(logic);
		parser();
		logicthread.join();
		RPC_UART_Parser_exit();
	}
	catch (const std::runtime_error &error){
		std::cout << error.what() << '\n';
	}
}

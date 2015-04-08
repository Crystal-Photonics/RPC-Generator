#include <iostream>
#include "RPC_client.h"
#include <thread>
#include <cassert>
#include <vector>
#include <atomic>
#include "../SharedSocketCode/socket.h"

std::atomic<bool> quitParser = false;

void parser(){
	for (; !quitParser;){
		auto connection = Socket::waitForConnection("127.0.0.1", Socket::serverListenPort, std::chrono::minutes(1));
		if (!connection)
			continue;
		std::cout << "connection established\n";
		std::vector<unsigned char> buffer;
		for (; !quitParser;){
			do{
				unsigned char c;
				connection->receiveData(&c, 1);
				buffer.push_back(c);
				if (quitParser)
					return;
			} while (RPC_get_answer_length(buffer.data(), buffer.size()).result == RPC_COMMAND_INCOMPLETE);
			RPC_parse_answer(buffer.data(), buffer.size());
			buffer.clear();
		}
	}
}

void logic(){
	for (;;)
		std::this_thread::sleep_for(std::chrono::hours(365));
	for (;;){
		int32_t result;
		if (square(&result, 42) == RPC_SUCCESS){
			std::cout << "square of " << 42 << " is " << result << '\n';
		}
		else{
			std::cout << "failed calling function square\n";
		}
	}
	quitParser = true;
}

int main()
{
	RPC_Parser_init();
	auto logicthread = std::thread(logic);
	parser();
	logicthread.join();
	RPC_Parser_exit();
}

#include <iostream>
#include "RPC_client.h"
#include <thread>
#include <fstream>
#include <cassert>
#include <vector>
#include <atomic>

std::atomic<bool> quitParser = false;

void parser(){
	std::ifstream input("server_in.bin", std::ifstream::binary);
	assert(input.good());
	std::vector<unsigned char> buffer;
	auto sleepUntilRead = [&]{
		while (input.gcount() == 0){
			if (quitParser)
				return;
			std::this_thread::sleep_for(std::chrono::milliseconds(128));
		}
		const auto amount = input.gcount();
		buffer.resize(buffer.size() + amount);
		const auto recieved = input.readsome(reinterpret_cast<char *>(&buffer[buffer.size() - amount]), amount);
		assert(recieved == amount);
	};
	for (; !quitParser;){
		do{
			sleepUntilRead();
			if (quitParser)
				return;
		} while (RPC_get_answer_length(buffer.data(), buffer.size()).result == RPC_COMMAND_INCOMPLETE);
		RPC_parse_answer(buffer.data(), buffer.size());
		buffer.clear();
	}
}

void logic(){
	int32_t result;
	for (int i = 0; i < 10; ++i){
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

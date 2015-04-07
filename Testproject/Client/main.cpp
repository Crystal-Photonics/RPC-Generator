#include "RPC_service.h"
#include <vector>
#include <fstream>
#include <cassert>

int main(){
	std::ifstream input("client_in.bin", std::ofstream::binary | std::ios::in);
	assert(input.good());
	std::vector<char> buffer;
	for (char c = input.get(); input.good(); c = input.get()){
		do{
			input.read
			buffer += read_data();
		} while (RPC_get_request_size(buffer.data(), buffer.size()).result != RPC_SUCCESS);
		RPC_parse_request(buffer.data(), buffer.size());
	}
}


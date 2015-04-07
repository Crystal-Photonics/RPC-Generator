#include "RPC_client.h"
#include <vector>
#include <fstream>
#include <cassert>
#include <mutex>
#include <chrono>

auto timeout = std::chrono::milliseconds(500);
std::vector<unsigned char> buffer;
std::ofstream sendStream("server_out.bin", std::ofstream::binary | std::ofstream::trunc);
std::timed_mutex mutexes[RPC_number_of_mutexes];

extern "C" {
	void RPC_start_message(size_t size){
		/*  This function is called when a new message starts. {size} is the number of
		bytes the message will require. In the implementation you can allocate  a
		buffer or write a preamble. The implementation can be empty if you do not
		need to do that. */
	}

	void RPC_push_byte(unsigned char byte){
		/* Pushes a byte to be sent via network. You should put all the pushed bytes
		into a buffer and send the buffer when RPC_commit is called. If you run
		out of buffer space you can send multiple partial messages as long as the
		other side puts them back together. */
		buffer.push_back(byte);
	}

	RPC_RESULT RPC_commit(void){
		/* This function is called when a complete message has been pushed using
		RPC_push_byte. Now is a good time to send the buffer over the network,
		even if the buffer is not full yet. You may also want to free the buffer that
		you may have allocated in the RPC_start_message function.
		RPC_commit should return RPC_SUCCESS if the buffer has been successfully
		sent and RPC_FAILURE otherwise. */
		assert(sendStream.is_open());
		sendStream.write(reinterpret_cast<const char *>(buffer.data()), buffer.size());
		assert(sendStream.good());
		buffer.clear();
		return RPC_SUCCESS;
	}

	void RPC_mutex_lock(RPC_mutex_id mutex_id){
		/* Locks the mutex. If it is already locked it yields until it can lock the mutex. */
		mutexes[mutex_id].lock();
	}

	void RPC_mutex_unlock(RPC_mutex_id mutex_id){
		/* Unlocks the mutex. The mutex is locked when the function is called. */
		mutexes[mutex_id].unlock();
	}

	char RPC_mutex_lock_timeout(RPC_mutex_id mutex_id){
		/* Tries to lock a mutex. Returns 1 if the mutex was locked and 0 if a timeout
		occured. The timeout length should be the time you want to wait for an answer
		before giving up. If the time is infinite a lost answer will get the calling
		thread stuck indefinitely. */
		return mutexes[mutex_id].try_lock_for(timeout) ? 1 : 0;
	}
}

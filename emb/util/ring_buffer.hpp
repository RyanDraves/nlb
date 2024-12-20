#pragma once

#include <array>
#include <cinttypes>
#include <initializer_list>

namespace emb {
namespace util {

// Fixed-size ring buffer
template <typename T, uint8_t Size> class RingBuffer {
  public:
    RingBuffer() : head_(0), tail_(0), full_(false) {}

    RingBuffer(std::initializer_list<T> init_list)
        : head_(0), tail_(0), full_(false) {
        for (const auto &item : init_list) {
            push(item);
        }
    }

    bool contains(const T &item) {
        for (uint8_t i = tail_; i < tail_ + size(); ++i) {
            if (buffer_[i % Size] == item) {
                return true;
            }
        }
        return false;
    }

    void push(const T &item) {
        buffer_[head_] = item;
        if (full_) {
            tail_ = (tail_ + 1) % Size;
        }
        head_ = (head_ + 1) % Size;
        full_ = head_ == tail_;
    }

    T pop() {
        // NOTE: Not checking if `empty` due to no exceptions
        auto item = buffer_[tail_];
        full_ = false;
        tail_ = (tail_ + 1) % Size;
        return item;
    }

    bool empty() const { return (!full_ && (head_ == tail_)); }

    bool full() const { return full_; }

    uint8_t size() const {
        uint8_t size = Size;
        if (!full_) {
            if (head_ >= tail_) {
                size = head_ - tail_;
            } else {
                size = Size + head_ - tail_;
            }
        }
        return size;
    }

  private:
    std::array<T, Size> buffer_;
    uint8_t head_;
    uint8_t tail_;
    bool full_;
};

}  // namespace util
}  // namespace emb

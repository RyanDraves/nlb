#pragma once

#include <cinttypes>
#include <functional>
#include <sstream>
#include <string>

#include "emb/network/node/node.hpp"
#include "emb/project/base/base_bh.hpp"

namespace emb {
namespace util {

namespace {
// Arbitrary buffer for the logger
uint8_t g_arena[256];
}  // namespace

// Custom static allocator
template <typename T> class StaticAllocator {
  public:
    using value_type = T;

    StaticAllocator() = default;

    template <typename U>
    constexpr StaticAllocator(const StaticAllocator<U> &) noexcept {}

    T *allocate(std::size_t n) {
        // Blindly assume that the size is correct
        return reinterpret_cast<T *>(g_arena);
    }

    void deallocate(T *p, std::size_t) noexcept {
        // Never deallocate the arena
        (void)p;
    }
};

template <typename T, typename U>
bool operator==(const StaticAllocator<T> &, const StaticAllocator<U> &) {
    return true;
}

template <typename T, typename U>
bool operator!=(const StaticAllocator<T> &, const StaticAllocator<U> &) {
    return false;
}

// Singleton Logger class
class Logger {
  public:
    // Get the singleton instance
    static Logger &getInstance() {
        static Logger instance;
        return instance;
    }

    // Delete copy constructor and assignment operator
    Logger(const Logger &) = delete;
    Logger &operator=(const Logger &) = delete;

    void set_publish_function(
        const std::function<
            void(uint8_t, const emb::project::base::LogMessage &)> &func) {
        publish_function_ = func;
    }

    // Overload the << operator to capture log messages
    template <typename T> Logger &operator<<(const T &message) {
        buffer_ << message;
        return *this;
    }

    // Overload the << operator to hanlde the LOG_END manipulator
    Logger &operator<<(Logger &(*manip)(Logger &)) { return manip(*this); }

    // Flush the buffer to the output
    void flush() {
        emb::project::base::LogMessage msg(buffer_.str().c_str());
        publish_function_(emb::project::base::PublishIds::LOG_MESSAGE, msg);
        buffer_.str("");  // Clear the buffer
        buffer_.clear();  // Reset the state flags
    }

  private:
    Logger()
        : buffer_(std::basic_string<char, std::char_traits<char>,
                                    StaticAllocator<char>>()) {}
    ~Logger() = default;

    // By the power of AI, we can make the buffer static and
    // generate comments about how we're using a static buffer
    using StaticString =
        std::basic_string<char, std::char_traits<char>, StaticAllocator<char>>;
    std::basic_ostringstream<char, std::char_traits<char>,
                             StaticAllocator<char>>
        buffer_;

    std::function<void(uint8_t, const emb::project::base::LogMessage &)>
        publish_function_;
};

inline Logger &end_log(Logger &logger) {
    logger.flush();
    return logger;
}

}  // namespace util
}  // namespace emb

// Macros to use the Logger singleton
//
// Usage:
//  LOG << "Hello, world!" << LOG_END;
#define LOG emb::util::Logger::getInstance()
#define LOG_END emb::util::end_log

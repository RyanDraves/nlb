#pragma once

#include <array>
#include <concepts>
#include <functional>
#include <inttypes.h>
#include <span>
#include <string.h>

#include "emb/network/serialize/serializer.hpp"
#include "emb/network/transport/transporter.hpp"

namespace emb {
namespace network {
namespace node {

// A generic server node
template <serialize::SerializerLike S, transport::TransporterLike T,
          class... Project>
class Node {
  protected:
    constexpr static size_t kFrameHeader = 1;

  public:
    Node(S &&serializer, T &&transporter, Project &&...projects)
        : serializer_(std::forward<S>(serializer)),
          transporter_(std::forward<T>(transporter)),
          projects_(std::forward_as_tuple(std::forward<Project>(projects)...)) {
        // Register all the handlers
        std::apply(
            [this](auto &&...project) {
                (project.register_handlers(*this), ...);
            },
            projects_);
    }

    template <typename Recv, typename Send>
    void register_handler(uint8_t request_id,
                          std::function<Send(const Recv &)> handler) {
        message_handlers_[request_id] = [this, request_id,
                                         handler](std::span<uint8_t> buffer) {
            Recv msg = serializer_.template deserialize<Recv>(buffer);

            Send resp = handler(msg);

            // Encode the outgoing message;
            // offset by one to leave room for the message ID
            auto [serialized, frame_padding] = serializer_.serialize(
                resp, std::span(tx_buffer_.data() + 1, tx_buffer_.size() - 1));

            // Add the message ID
            tx_buffer_[frame_padding] = request_id;

            // Add back our + 1 offset
            auto framed = serializer_.frame(
                std::span(tx_buffer_.data(), serialized.size() + 1));
            transporter_.send(framed);

            // // Debug logic to echo the deframed message back
            // // Write `request_id` and `buffer` back into `tx_buffer_`
            // memcpy(tx_buffer_.data() + S::kMaxOverhead + 1, buffer.data(),
            //        buffer.size());
            // tx_buffer_[S::kMaxOverhead] = request_id;
            // auto framed = serializer_.frame(std::span(
            //     tx_buffer_.data(), buffer.size() + S::kMaxOverhead + 1));
            // transporter_.send(framed);
        };
    }

    void receive() {
        auto data = transporter_.receive({rx_buffer_.data(), S::kBufSize});

        if (data.empty()) {
            return;
        }

        // Deframe the incoming message
        auto deframed_data = serializer_.deframe(data);

        auto msg_size = deframed_data.size() - kFrameHeader;

        // Check if the first byte is a valid message ID
        if (msg_size == 0 || message_handlers_.find(deframed_data[0]) ==
                                 message_handlers_.end()) {
            return;
        }

        // Call the appropriate message handler
        message_handlers_.at(deframed_data[0])(
            deframed_data.subspan(kFrameHeader, msg_size));

        // // Debug logic to echo the framed message back
        // rx_buffer_[data.size()] = 0;
        // transporter_.send({rx_buffer_.data(), data.size() + 1});
    }

  private:
    S serializer_;
    T transporter_;

    std::tuple<Project...> projects_;

    // Map message IDs to function pointers
    std::unordered_map<uint8_t, std::function<void(std::span<uint8_t>)>>
        message_handlers_;

    // A neat trick with COBS encoding is that we can write the encoded message
    // in-place, provided that our data is <overhead_bytes> bytes into the
    // buffer; we'll manipulate the buffer to make this true
    std::array<uint8_t, S::kBufSize + S::kMaxOverhead> tx_buffer_;

    // We can write the decoded message in-place as well
    std::array<uint8_t, S::kBufSize> rx_buffer_;

    bool has_tx_message_ = false;
};

}  // namespace node
}  // namespace network
}  // namespace emb

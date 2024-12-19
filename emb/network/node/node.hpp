#pragma once

#include <array>
#include <cinttypes>
#include <concepts>
#include <functional>
#include <span>
#include <string.h>

#include "emb/network/serialize/serializer.hpp"
#include "emb/network/transport/transporter.hpp"

namespace emb {
namespace network {
namespace node {

enum class TransportType : uint8_t { COMMS, LOGGING };

// A generic server node
template <serialize::SerializerLike S, transport::TransporterLike C,
          transport::TransporterLike L, class... Project>
class Node {
  protected:
    constexpr static size_t kFrameHeader = 1;

  public:
    Node(S &&serializer, C &comms, L &logging, Project &&...projects)
        : serializer_(std::forward<S>(serializer)), comms_transporter_(comms),
          log_transporter_(logging),
          projects_(std::forward_as_tuple(std::forward<Project>(projects)...)) {
        // Register all the handlers
        std::apply(
            [this](auto &&...project) {
                (project.register_handlers(*this), ...);
            },
            projects_);
    }

    void initialize() {
        // Initialize the transport layers
        comms_transporter_.initialize();
        log_transporter_.initialize();

        // Initialize the serializer
        serializer_.initialize();

        // Initialize the projects
        std::apply([](auto &&...project) { (project.initialize(), ...); },
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
            comms_transporter_.send(framed);

            // // Debug logic to echo the deframed message back
            // // Write `request_id` and `buffer` back into `tx_buffer_`
            // memcpy(tx_buffer_.data() + S::kMaxOverhead + 1, buffer.data(),
            //        buffer.size());
            // tx_buffer_[S::kMaxOverhead] = request_id;
            // auto framed = serializer_.frame(std::span(
            //     tx_buffer_.data(), buffer.size() + S::kMaxOverhead + 1));
            // comms_transporter_.send(framed);
        };
    }

    void receive() {
        auto data =
            comms_transporter_.receive({rx_buffer_.data(), S::kBufSize});

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
        // comms_transporter_.send({rx_buffer_.data(), data.size() + 1});
    }

    template <typename Send>
    void publish(uint8_t request_id, const Send &msg, TransportType type) {
        auto &buffer =
            type == TransportType::COMMS ? tx_buffer_ : log_tx_buffer_;

        // Encode the outgoing message;
        // offset by one to leave room for the message ID
        auto [serialized, frame_padding] = serializer_.serialize(
            msg, std::span(buffer.data() + 1, buffer.size() - 1));

        // Add the message ID
        buffer[frame_padding] = request_id;

        // Add back our + 1 offset
        auto framed =
            serializer_.frame(std::span(buffer.data(), serialized.size() + 1));
        if (type == TransportType::COMMS) {
            comms_transporter_.send(framed);
        } else {
            log_transporter_.send(framed);
        }
    }

  private:
    S serializer_;
    C &comms_transporter_;
    L &log_transporter_;

    std::tuple<Project...> projects_;

    // Map message IDs to function pointers
    std::unordered_map<uint8_t, std::function<void(std::span<uint8_t>)>>
        message_handlers_;

    // A neat trick with COBS encoding is that we can write the encoded
    // message in-place, provided that our data is <overhead_bytes> bytes
    // into the buffer; we'll manipulate the buffer to make this true
    std::array<uint8_t, S::kBufSize + S::kMaxOverhead> tx_buffer_;

    // Create a separate buffer for logging
    //
    // Note that this only serves to allow logging in the `can_send_handler`
    // method for the BLE transport, after the tx buffer for transmission has
    // been set. It's a simple code space optimization to remove this and
    // disallow logging in that one function.
    std::array<uint8_t, S::kBufSize + S::kMaxOverhead> log_tx_buffer_;

    // We can write the decoded message in-place as well
    std::array<uint8_t, S::kBufSize> rx_buffer_;

    bool has_tx_message_ = false;
};

}  // namespace node
}  // namespace network
}  // namespace emb

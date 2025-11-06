#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "nlb/buffham/testdata/other_bh.hpp"
#include "nlb/buffham/testdata/sample_bh.hpp"

using namespace testing;

namespace nlb {
namespace buffham {

// Test Ping serialization and deserialization
TEST(SampleBhTest, TestPingSerialization) {
    testdata::Ping ping{42};

    // Serialize
    std::array<uint8_t, 256> buffer{};
    auto serialized = ping.serialize(buffer);

    // Deserialize
    auto [deserialized_ping, used_buffer] =
        testdata::Ping::deserialize(serialized);

    // Verify
    ASSERT_THAT(deserialized_ping.ping, Eq(ping.ping));
    ASSERT_THAT(used_buffer.size(), Eq(serialized.size()));
}

// Test FlashPage serialization and deserialization
TEST(SampleBhTest, TestFlashPageSerialization) {
    testdata::FlashPage flash_page{0x1234, {0x9A, 0xBC}, 0x5678};

    // Serialize
    std::array<uint8_t, 256> buffer{};
    auto serialized = flash_page.serialize(buffer);

    // Deserialize
    auto [deserialized_flash_page, used_buffer] =
        testdata::FlashPage::deserialize(serialized);

    // Verify
    ASSERT_THAT(deserialized_flash_page.address, Eq(flash_page.address));
    ASSERT_THAT(deserialized_flash_page.data,
                ElementsAreArray(flash_page.data));
    ASSERT_TRUE(deserialized_flash_page.read_size.has_value());
    ASSERT_THAT(deserialized_flash_page.read_size.value(),
                Eq(flash_page.read_size.value()));
    ASSERT_THAT(used_buffer.size(), Eq(serialized.size()));
}

// Test FlashPage without optional field
TEST(SampleBhTest, TestFlashPageWithoutOptionalSerialization) {
    testdata::FlashPage flash_page{0x1234, {0x9A, 0xBC}, std::nullopt};

    // Serialize
    std::array<uint8_t, 256> buffer{};
    auto serialized = flash_page.serialize(buffer);

    // Deserialize
    auto [deserialized_flash_page, used_buffer] =
        testdata::FlashPage::deserialize(serialized);

    // Verify
    ASSERT_THAT(deserialized_flash_page.address, Eq(flash_page.address));
    ASSERT_THAT(deserialized_flash_page.data,
                ElementsAreArray(flash_page.data));
    ASSERT_FALSE(deserialized_flash_page.read_size.has_value());
    ASSERT_THAT(used_buffer.size(), Eq(serialized.size()));
}

// Test LogMessage serialization and deserialization
TEST(SampleBhTest, TestLogMessageSerialization) {
    testdata::LogMessage log_message{
        "Hello, world!", testdata::Verbosity::MEDIUM, testdata::MyEnum::B};

    // Serialize
    std::array<uint8_t, 256> buffer{};
    auto serialized = log_message.serialize(buffer);

    // Deserialize
    auto [deserialized_log_message, used_buffer] =
        testdata::LogMessage::deserialize(serialized);

    // Verify
    ASSERT_THAT(deserialized_log_message.message, Eq(log_message.message));
    ASSERT_THAT(deserialized_log_message.verbosity, Eq(log_message.verbosity));
    ASSERT_THAT(deserialized_log_message.my_enum, Eq(log_message.my_enum));
    ASSERT_THAT(used_buffer.size(), Eq(serialized.size()));
}

// Test NestedMessage serialization and deserialization
TEST(SampleBhTest, TestNestedMessageSerialization) {
    testdata::LogMessage log_message{
        "Hello, world!", testdata::Verbosity::MEDIUM, testdata::MyEnum::B};
    testdata::Ping ping{42};
    testdata::Pong other_pong{43};

    testdata::NestedMessage nested_message{
        true, log_message, {-1, -2}, ping, other_pong};

    // Serialize
    std::array<uint8_t, 512> buffer{};
    auto serialized = nested_message.serialize(buffer);

    // Deserialize
    auto [deserialized_nested_message, used_buffer] =
        testdata::NestedMessage::deserialize(serialized);

    // Verify
    ASSERT_TRUE(deserialized_nested_message.flag.has_value());
    ASSERT_THAT(deserialized_nested_message.flag.value(),
                Eq(nested_message.flag.value()));
    ASSERT_THAT(deserialized_nested_message.message.message,
                Eq(nested_message.message.message));
    ASSERT_THAT(deserialized_nested_message.message.verbosity,
                Eq(nested_message.message.verbosity));
    ASSERT_THAT(deserialized_nested_message.message.my_enum,
                Eq(nested_message.message.my_enum));
    ASSERT_THAT(deserialized_nested_message.numbers,
                ElementsAreArray(nested_message.numbers));
    ASSERT_THAT(deserialized_nested_message.pong.ping,
                Eq(nested_message.pong.ping));
    ASSERT_THAT(deserialized_nested_message.other_pong.pong,
                Eq(nested_message.other_pong.pong));
    ASSERT_THAT(used_buffer.size(), Eq(serialized.size()));
}

// Test StringLists serialization and deserialization
TEST(SampleBhTest, TestStringListsSerialization) {
    testdata::StringLists string_lists{{"hello", "world"},
                                       {{0x01, 0x02, 0x03}, {0x04, 0x05}}};

    // Serialize
    std::array<uint8_t, 512> buffer{};
    auto serialized = string_lists.serialize(buffer);

    // Deserialize
    auto [deserialized_string_lists, used_buffer] =
        testdata::StringLists::deserialize(serialized);

    // Verify
    ASSERT_THAT(deserialized_string_lists.messages.size(),
                Eq(string_lists.messages.size()));
    for (size_t i = 0; i < string_lists.messages.size(); i++) {
        ASSERT_THAT(deserialized_string_lists.messages[i],
                    Eq(string_lists.messages[i]));
    }
    ASSERT_THAT(deserialized_string_lists.buffers.size(),
                Eq(string_lists.buffers.size()));
    for (size_t i = 0; i < string_lists.buffers.size(); i++) {
        ASSERT_THAT(deserialized_string_lists.buffers[i],
                    ElementsAreArray(string_lists.buffers[i]));
    }
    ASSERT_THAT(used_buffer.size(), Eq(serialized.size()));
}

// Test constants
TEST(SampleBhTest, TestConstants) {
    ASSERT_THAT(testdata::kMyConstant, Eq(4));
    ASSERT_THAT(testdata::kConstantString, Eq("Hello, world!"));
    ASSERT_THAT(testdata::kComposedConstant,
                Eq(2 + testdata::kMyConstant + testdata::kOtherConstant));
}

}  // namespace buffham
}  // namespace nlb

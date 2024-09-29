# Buffham
Buffham is a serialization library. It currently has the following design goals:
- Minimal footprint
- Seamless Bazel integrations
- Maximum code generation (builds upon external infrastructure to create handlers)

These goals are flexible.

# Roadmap
- Support for "published" messages (versus transactions, i.e. log messages)
- Write the parser schemas in Buffham (cool)
- Import support
- Enum support
- Dictionary support
- List of messages support
- File support (read/write to/from text/binary)

# Limitations
- Transaction code expects Python clients and C++ servers
- Transaction codegen cannot be turned off
- C++ generation is not unit tested (just `bh_cobs_test.cc`)
- The items on the roadmap are not done

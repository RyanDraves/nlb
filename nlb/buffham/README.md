# Buffham
Buffham is a serialization library. It currently has the following design goals:
- Minimal footprint
- Seamless Bazel integrations
- Maximum code generation (builds upon external infrastructure to create handlers)

These goals are flexible.

# Roadmap
- Support for "published" messages (versus transactions, i.e. log messages)
- Write the parser schemas in Buffham (cool)
- Dictionary support
- File support (read/write to/from text/binary)
- Editor integrations for language syntax support

# Server methods
Projects can declare extra methods on the generated server class (i.e. the
C++ project class) with `svr_method`:

```
# Poll the button; called from the main loop
svr_method tick;
```

This adds a `void tick();` declaration to the generated class, to be
implemented by the project alongside its transaction handlers — no
free-function workarounds needed for main-loop hooks.

# Limitations
- Transaction code expects Python clients and C++ servers
- Transaction codegen cannot be turned off
- `svr_method`s are `void` and take no arguments
- The items on the roadmap are not done

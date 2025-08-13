# Sharetrace
A Python library & CLI for capturing and sharing comprehensive traceback information.

## Overview

Sharetrace makes it easier to share Python exceptions and tracebacks with others by capturing:

- Full exception details (type, message, traceback)
- Code context around each frame in the stack trace
- Git repository information (if available)
- System information (Python version, platform, etc.)
- Local variable values at each frame

All this information is saved to a cache directory as JSON files that can later be used to generate shareable HTML reports.

## Usage

### Capture Traceback Information

```python
from nlb.sharetrace import st

# Install the exception hook (call this early in your program)
sharetrace.install_exception_hook()

# Now any unhandled exceptions will be captured automatically
raise ValueError("This will be captured!")
```

### Generate Shareable HTML Pages

Just invoke the interactive CLI!

```bash
sharetrace [--open-browser]
```

## Examples

A demo traceback can be created with `sharetrace_demo` and visualized with `sharetrace`.

## Notes

- `KeyboardInterrupt` and `SystemExit` are not captured (they use the default handler)
- If the capture process fails, the original exception is still displayed

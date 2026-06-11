# Buffham VSCode Extension

Language support for [Buffham](../README.md) (`.bh`) message schema files:

- Syntax highlighting for keywords, types, comments, constants, and enum values
- Comment toggling (`#`), bracket matching, and auto-closing pairs
- Snippet completions for `message`, `enum`, `transaction`, `publish`, `constant`,
  field types, and more

The extension is fully declarative (no extension code), packaged with
[`vsce`](https://github.com/microsoft/vscode-vsce) via Bazel.

## Build & install

```bash
bazel build //nlb/buffham/vscode:vsix
code --install-extension bazel-bin/nlb/buffham/vscode/buffham.vsix
```

Then reload VSCode ("Developer: Reload Window").

## Developing

Open this folder in VSCode and press F5 to launch an Extension Development Host
with the extension loaded; edits to the grammar/snippets are picked up on reload
of that window.

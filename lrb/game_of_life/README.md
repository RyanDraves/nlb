# Annoying sequence to update `Cargo.lock`

TODO: Remove me when switching to direct dependencies in `MODULE.bazel`
- `cargo generate-lockfile`
- `Cargo.lock`'s `version = 4` -> `version = 3`
- `CARGO_BAZEL_REPIN=1 bazel sync --enable_workspace --only=crates`

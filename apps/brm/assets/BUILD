# Art + audio assets embedded into the client via `include_bytes!` (so they ship
# in both the native binary and the wasm module with no runtime asset loading).
# Regenerate with gen_powerups.py / gen_sfx.py.
exports_files(["powerups.png"])

filegroup(
    name = "sfx",
    srcs = glob(["sfx/*.wav"]),
    visibility = ["//visibility:public"],
)

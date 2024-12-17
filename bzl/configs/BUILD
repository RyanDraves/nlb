load("@bazel_skylib//rules:common_settings.bzl", "bool_flag", "string_flag")

package(default_visibility = ["//visibility:public"])

# Does the device blink an LED with PIO support?
bool_flag(
    name = "PIO_BLINK",
    build_setting_default = False,
)

string_flag(
    name = "COMMS_PROTOCOL",
    build_setting_default = "zmq",
    values = [
        "ble",
        "serial",
        "zmq",
        "unittest",
    ],
)

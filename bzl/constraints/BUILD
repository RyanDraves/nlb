package(default_visibility = ["//visibility:public"])

constraint_setting(
    name = "host_type",
)

constraint_value(
    name = "unittest",
    constraint_setting = ":host_type",
)

config_setting(
    name = "comms_protocol_ble_enabled",
    flag_values = {"//bzl/configs:COMMS_PROTOCOL": "ble"},
)

config_setting(
    name = "comms_protocol_serial_enabled",
    flag_values = {"//bzl/configs:COMMS_PROTOCOL": "serial"},
)

config_setting(
    name = "comms_protocol_zmq_enabled",
    flag_values = {"//bzl/configs:COMMS_PROTOCOL": "zmq"},
)

config_setting(
    name = "comms_protocol_unittest_enabled",
    flag_values = {"//bzl/configs:COMMS_PROTOCOL": "unittest"},
)

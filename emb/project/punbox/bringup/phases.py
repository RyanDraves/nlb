"""Phase implementations for the punbox carrier bringup procedure.

Executed by the `tofupilot` CLI (not Bazel); see `procedure.yaml` for the
sequence and `plugs.py` for the Bazel runner.
"""

import json
import pathlib
import time

BOOTSEL_DRIVE = pathlib.Path('/Volumes/RPI-RP2')
BOOTSEL_TIMEOUT_S = 60


def _press_count(phase, logs, bazel) -> int:
    rc, output = bazel.run('//emb/project/punbox:state')
    if rc != 0:
        logs.info(output)
        phase.fail('state query failed')
    # The JSON state is the last line of the bazel run output
    return json.loads(output.strip().splitlines()[-1])['press_count']


def bootsel_check(measurements):
    deadline = time.monotonic() + BOOTSEL_TIMEOUT_S
    while time.monotonic() < deadline:
        if BOOTSEL_DRIVE.exists():
            measurements.drive_mounted = True
            return
        time.sleep(1)
    measurements.drive_mounted = False


def provision(measurements, logs, bazel):
    rc, output = bazel.run('//emb/project/bootloader:provision_pico')
    logs.info(output)
    measurements.provision_rc = rc


def flash_punbox(measurements, logs, bazel):
    rc, output = bazel.run('//emb/project/punbox:punbox_flash')
    logs.info(output)
    measurements.flash_rc = rc


def hil_test(measurements, logs, bazel):
    rc, output = bazel.test('//emb/project/punbox:hil_test')
    logs.info(output)
    measurements.hil_rc = rc


def button_baseline(phase, measurements, logs, bazel):
    measurements.baseline_count = _press_count(phase, logs, bazel)


def button_verify(phase, measurements, logs, bazel, button_baseline):
    after = _press_count(phase, logs, bazel)
    measurements.press_delta = after - button_baseline.baseline_count

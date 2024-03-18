---
layout: posts
title:  "Programatically Flashing a Pi Pico Part 1: Serialized Messages"
date:   2024-02-09 19:02:51 -0800
categories: tooling pico
---

I have some Pi Picos lying around and decided to flush out some infrastructure to make it easy to interact and create projects with them. It's definitely a "idea in search of a project" type situation, but the idea is interesting enough, so here goes.

One of the neat things about the Pico is the convenient ways to program it. You can flash it programmatically with the [SWD][about_swd] pins using something like the [Pi debug probe][debug_probe], a J-Link, a try-your-luck AliExpress item, or even [another Pi][pi_openocd]. The BOOTSEL mode on the Pico is also convenient; without any additional hardware, you can boot the Pico as a "USB mass storage device" and either drag-and-drop your image or use [picotool][picotool] to programmatically flash it from that mode. But what would be _really_ nice is to avoid the extra hassle of extra hardware, connecting debug pins, or holding the BOOTSEL button as I power cycle the Pico. The goal is to programatically flash the Pico via the firmware's own logic.

## Step 1: Compile something
The first step is always hello world, so let's start with getting something compiling. Conveniently [rules_pico][rules_pico] exists and provides a simple mechanism for us to pull in the Pico SDK, compile the Pico examples, and start compiling our own images. The repo depends on a non-hermetically installed `arm-none-eabi` toolchain (and `python3` interpreter), so install that from apt for now. Booting into BOOTSEL mode on the Pico and dragging and dropping the UF2 output file from `bazel-bin` will give us our first (non-programmatic) flash.

```c
#include <stdio.h>
#include "pico/stdlib.h"

int main() {
    stdio_init_all();

    while (true) {
        printf("Hello, world!");
        sleep_ms(1000);
    }
}
```

Using [minicom][minicom] installed from apt, we can start listening to our Pico with a simple `minicom -b 115200 -o -D /dev/pico` (my udev rules symlink that device name for me). Next is to switch to our first method of programatically flashing the Pico, using [picotool](https://github.com/raspberrypi/picotool) with the BOOTSEL mode. We'll build from sources and install it into our `$PATH` manually.

```bash
picotool load -v -x bazel-bin/emb/hello.uf2

Loading into Flash: [==============================]  100%
Verifying Flash:    [==============================]  100%
  OK

The device was rebooted to start the application.
```

## Platforms, toolchains, and C++ 23
The next task is to improve the hermeticity of the build and get rid the system toolchain install. To do this we'll use [bazel-arm-none-eabi][bazel_arm_none_eabi] to replace the toolchain setup built into `rules_pico`. At this point this post could diverge into either an educational explainer that would dive into how Bazel platforms and toolchains work, or this could be a simple here's-how-I-did-the-thing. For the number of hours it took me to be familiar enough with Bazel's concepts to get something working and the number of topics I want to cover, we'll have to go with the latter.

Long story short, I ended up defining my own set of platforms and registering the toolchains myself to get more control over the environment, rather than using defaults in `rules_pico` (although I have been working on upstreaming a [hermetic default toolchain][rules_pico_upstream]). This approach gives us more granularity in the constraints the platform sets and the constraints each toolchain provides.

For instance, the next thing I wanted to do to spice up the project was to compile my code with C++23, rather than C. To do that we'll need to switch to a g++ toolchain (thankfully `bazel-arm-none-eabi` had a PR for that ready to go), but to do _that_ we'll have to sort out the Pico SDK again. The Pico SDK uses a lot of C conventions that are incompatible with C++, such as some initialization ordering schemes and implicit void pointer conversions. To use the Pico SDK in the firmware but C++23 for the "application code," we'll need to compile the SDK with gcc and the application code with g++. This makes sense at a high-level; as long as the library headers are compatible with the application's compiler (the SDK is designed for this), we shouldn't really care what compiler was used to build the static or shared library we're linking against. But from Bazel's perspective, swapping compilers in the middle of the build is a tall order.

To implement this, I cobbled together a Bazel rule that [transitions][transitions] a target to use a specific platform. Target goes in, new target goes out with the same providers, input target is now hardwired for the specified target. There's a [proposal][platform_data_proposal] and experimental support for this kind of rule in the standard `bazelbuild/platforms`, but the experimental rule seemed pretty broken. This same idea looks like a useful way to build our binary with one platform and run a flashing program with the host platform, all from one `bazel run` command; we'll keep this in mind for later. (TODO: see if Bazel [configurations][bazel_configurations] handle this automatically.)

The platform transition rule is nice, but it does feel like an anti-pattern of Bazel. Bazel platforms and toolchains are designed so "neither the rule author the target author need to know the complete set of available platforms and toolchains" ([source][bazel_platform_pattern]), and while that's kind of upheld for toolchains, you now have to use (or have a compatible toolchain registered for) _my_ `//bzl/platforms:pico_c` platform. The Bazel docs also make it clear that transitions will [bloat the build graph][bazel_configurations], so it's probably best to minimize this `transition` usage, as neat as it would be to never manually specify a platform.

Now that we have toolchains and platforms setup to enable C++ in our application code, getting C++23 was pretty easy; I just had to update `bazel-arm-none-eabi` to pull in a more recent version of the toolchain that implements a more recent GCC standard. Add a simple compile check and we're done!

```cpp
#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif
```

## Brief detour into the WSL rabbit hole
A minor detour in the process is that I'm using Windows & WSL2 to run all of this, which takes some extra effort to get things working. Windows added support for [passing USB devices to WSL][wsl_usb], but the process of finding the device in an administrator Powershell window and manually re-attaching on each device reboot is quite painful. Enter BOOTSEL mode -> attach -> flash -> attach -> connect to device from WSL. Gross.

First of all, don't do this. Don't use this setup. Just boot from Linux.

Second, I found the [WSL USB GUI][wsl_usb_gui] to be quite helpful here. It lets you manage devices from a GUI and configure them for an auto-attach into WSL. Fantastic! I have found that the Pico in BOOTSEL mode will usually fail to auto-attach and instead requires me to open the GUI and manually attach it, whereas the "normal" boot of the Pico auto-attaches fine. All the more reason to get programmatic flash working and stop using BOOTSEL!

## Building a client
With the most of the firmware tooling out of the way, we can work on replacing `minicom` with a custom client. I'm a big fan of [IPython][ipython] shells (we'll get there), but a good first step would be to get a hermetic interpreter with [rules_python][rules_python] set up and a simple client that listens for our Pico's `"Hello, world!"` messages.

The `rules_python` setup was simple and got a hermetic `3.12` interpreter going right away, but the editor integrations were trickier. I ended up finding [rules_pyvenv][rules_pyvenv] and its setup worked out-of-the-box, despite ~7 months of inactivity. A simple `bazel run //:venv venv` and I have an exported virtual environment for my editor! I also found the `rules_python` wrapper library [aspect_rules_py][aspect_rules_py], and while its rule wrappers look promising, the virtual environment export didn't seem to work. The aspect rules are in active development, so I'll have to check back later.

With that set up, we can get a minimal, good-enough-for-now client going:

```py
import serial
from serial.tools import list_ports
from serial.tools import list_ports_common

PICO_VENDOR_PRODUCT_ID = '2e8a:000a'

def find_pico() -> str:
    devices: list[list_ports_common.ListPortInfo] = list(list_ports.grep(PICO_VENDOR_PRODUCT_ID))
    if not devices:
        raise RuntimeError('Pico not found')
    elif len(devices) > 1:
        raise RuntimeError('Multiple Picos found')
    return devices[0].device


def main() -> None:
    port = find_pico()
    print(f'Pico found at {port}')
    with serial.Serial(port, 115200, timeout=1) as ser:
        while True:
            print(ser.read(100).decode('utf-8'), end='')


if __name__ == '__main__':
    main()
```

This lets us find the Pico, grab it with `pyserial`, and start reading from it. We'll make the reading fancier as we go.

## Serialized transactions

nanpb

## Message framing

cobs

## Using C++ in Python

pybind11

TODO: insert image of the Pico explorer board

[about_swd]: https://community.silabs.com/s/article/serial-wire-debug-swd-x?language=en_US
[aspect_rules_py]: https://github.com/aspect-build/rules_py
[bazel_arm_none_eabi]: https://github.com/hexdae/bazel-arm-none-eabi
[bazel_configurations]: https://github.com/bazelbuild/bazel/blob/a54a393d209ab9c8cf5e80b2a0ef092196c17df3/site/en/extending/rules.md#configurations
[bazel_platform_pattern]: https://github.com/bazelbuild/bazel/blob/13ecdf583301a94484a1ae0eb27c56fcf3248dc5/site/en/extending/toolchains.md
[debug_probe]: https://www.raspberrypi.com/products/debug-probe/
[ipython]: https://ipython.org/
[minicom]: https://help.ubuntu.com/community/Minicom
[picotool]: https://github.com/raspberrypi/picotool
[pi_openocd]: https://iosoft.blog/2019/01/28/raspberry-pi-openocd/
[platform_data_proposal]: https://github.com/bazelbuild/proposals/blob/124b188252d2b4da516898724e1ce6227a1aedaf/designs/2023-06-08-standard-platform-transitions.md
[rules_pico]: https://github.com/dfr/rules_pico
[rules_pico_upstream]: https://github.com/dfr/rules_pico/pull/13
[rules_python]: https://github.com/bazelbuild/rules_python
[rules_pyvenv]: https://github.com/cedarai/rules_pyvenv
[transitions]: https://bazel.build/rules/lib/builtins/transition
[wsl_usb]: https://learn.microsoft.com/en-us/windows/wsl/connect-usb
[wsl_usb_gui]: https://gitlab.com/alelec/wsl-usb-gui/-/tree/v5.2.0?ref_type=tags

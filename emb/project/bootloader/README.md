# About
The pico bootloader is a third stage bootloader that enables programatically flashing the Pi Pico (i.e. over-the-air updates managed by the application code). It draws heavy inspiration from Brian Starkey's [Pico serial bootloader](https://blog.usedbytes.com/2021/12/pico-serial-bootloader/) and [pico-flashloader](https://github.com/rhulme/pico-flashloader).

# Design
Note: This should match comments in `emb/yaal/pico/flash.cc`. Exact numbers can be found in `bootloader.bh`'s constants.

The flash is partitioned into 4 spaces:
- Bootloader
- Image A
- Image B
- Scratchpad sectors

All firmware images are linked to the location of image A, so image B is just a bank waiting to be loaded into image A. The application linker script enforces the image size budget, so an oversized image fails to link.

On boot, the bootloader will:
1. Read the `SystemFlashPage` (defined in `bootloader.bh`) scratchpad sector
2. Increment the boot count
3. Initialize USB serial output
4. Blink a pattern on the LED (a fast-slow alternation, distinct from the application's steady blinking)
5. If `SystemFlashPage.new_image_flashed` is set, swap image A and B:
   - Wait up to ~2s for a host to attach to the USB serial port
   - Emit `FLASH <bytes_done> <bytes_total>` progress lines during the swap, and a final `DONE`
   - Alternate fast and slow LED blinks throughout
6. Write the `SystemFlashPage` back to the scratchpad
7. Jump to image A

The "swap image A and B" sequence is to swap their values in flash. At the end the relevant `SystemFlashPage` values are swapped and `SystemFlashPage.new_image_flashed` is cleared.

Note that this design offers an easy mechanism to revert to the previously flashed image; just set `SystemFlashPage.new_image_flashed` and reset the device.

# Image verification
Application images embed an `ImageStamp` (see `emb/project/base/image_stamp.hpp`): a magic followed by a SHA256 of the image, patched into the `.bin` post-build by `:stamp` (wired into the `pico_project` macro; UF2s are not stamped). On boot the application reports its stamp in `SystemFlashPage.image_hash`, which `flash.py` compares against the local image — along with the boot count, image sizes, and a ping — before declaring a flash successful.

# Bootstrapping
A fresh Pico can be bootstrapped with a couple simple steps:
- Hold the BOOTSEL button and power on the Pico
- `bazel run //emb/project/bootloader:provision_pico` (or `:provision_pico_w`)
- Power cycle the Pico (e.g. `picotool reboot`)
- Done!

This will provision the bootloader, the base image, and initialize the system flash page.

Note that the bootloader itself is not updatable over-the-air. To update just the bootloader on a provisioned board (keeping its images and system page):
- Hold the BOOTSEL button and power on the Pico
- `picotool load bazel-out/.../emb/project/bootloader/bootloader_intermediate.bin`
- `picotool reboot`

Changes to the `SystemFlashPage` layout require a full re-provision, as neither the bootloader nor the application gracefully handle a stale page layout.

# Roadmap
- Allow writing to flash in multiple sectors & increase buffer size of the shuffle
- Include a CRC check before swapping or jumping to an image
  - On the application side, consider skipping the flash if the CRC matches the running image
  - DMA CRC32 https://github.com/usedbytes/rp2040-serial-bootloader/blob/main/main.c#L266
  - Another DMA CRC32 https://github.com/rhulme/pico-flashloader/blob/urloader/flashloader.c#L125
- Point back to the [latest memmap](https://github.com/raspberrypi/pico-sdk/blob/master/src/rp2040/pico_platform/memmap_default.ld) for linking

# Attribution
- `memmap_default.ld` vendored from [pico-sdk 2.2.0](https://github.com/raspberrypi/pico-sdk/blob/a1438dff1d38bd9c65dbd693f0e5db4b9ae91779/src/rp2_common/pico_crt0/rp2040/memmap_default.ld)

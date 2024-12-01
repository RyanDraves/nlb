# About
The pico bootloader is a third stage bootloader that enables programatically flashing the Pi Pico (i.e. over-the-air updates managed by the application code). It draws heavy inspiration from Brian Starkey's [Pico serial bootloader](https://blog.usedbytes.com/2021/12/pico-serial-bootloader/) and [pico-flashloader](https://github.com/rhulme/pico-flashloader).

# Design
Note: This should match comments in `emb/yaal/pico/flash.cc`. Exact numbers can be found in `bootloader.bh`'s constants.

The flash is partitioned into 4 spaces:
- Bootloader
- Image A
- Image B
- Scratchpad sectors

All firmware images are linked to the location of image A, so image B is just a bank waiting to be loaded into image A.

On boot, the bootloader will:
1. Read the `SystemFlashPage` (defined in `bootloader.bh`) scratchpad sector
2. Increment the boot count
3. Blink a pattern on the LED
4. If `SystemFlashPage.new_image_flashed` is set, swap image A and B
5. Write the `SystemFlashPage` back to the scratchpad
6. Jump to image A


The "swap image A and B" sequence is to swap their values in flash, alternating the LED every now and then during this process. At the end the relevant `SystemFlashPage` values are swapped and `SystemFlashPage.new_image_flashed` is cleared.

Note that this design offers an easy mechanism to revert to the previously flashed image; just set `SystemFlashPage.new_image_flashed` and reset the device.

# Bootstrapping
A fresh Pico can be bootstrapped with a couple simple steps:
- Hold the BOOTSEL button and power on the Pico
- `bazel run //emb/project/bootloader:provision`
- Powercycle the Pico
- Done!

This will provision the bootloader, the base image, and initialize the system flash page.

# Roadmap
- Allow writing to flash in multiple sectors & increase buffer size of the shuffle
- Include a CRC check before swapping or jumping to an image
  - On the application side, consider skipping the flash if the CRC matches the running image
  - DMA CRC32 https://github.com/usedbytes/rp2040-serial-bootloader/blob/main/main.c#L266
  - Another DMA CRC32 https://github.com/rhulme/pico-flashloader/blob/urloader/flashloader.c#L125

/* Generously borrowed from
   https://github.com/particle-iot/docs/blob/cb2cd062e4564959970853a5aa220eea8934160e/src/assets/files/projects/rp2040-raspberry-pi-asset-ota/pico/memmap_defines.ld
 */
__BOOTLOADER_START = 0;
__BOOTLOADER_LENGTH = 160 * 1k;
__APPLICATION_START = __BOOTLOADER_START + __BOOTLOADER_LENGTH;

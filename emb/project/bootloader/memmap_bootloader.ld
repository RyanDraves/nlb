/* Generously borrowed from
   https://github.com/particle-iot/docs/blob/cb2cd062e4564959970853a5aa220eea8934160e/src/assets/files/projects/rp2040-raspberry-pi-asset-ota/pico/memmap_flashloader.ld
 */
INCLUDE "memmap_defines.ld"

__FLASH_OFFSET = __BOOTLOADER_START;
__FLASH_LENGTH = __BOOTLOADER_LENGTH;

INCLUDE "memmap_default.ld"

/* Generously borrowed from
   https://github.com/particle-iot/docs/blob/cb2cd062e4564959970853a5aa220eea8934160e/src/assets/files/projects/rp2040-raspberry-pi-asset-ota/pico/memmap_application.ld
 */
INCLUDE "memmap_defines.ld"

__FLASH_OFFSET = __APPLICATION_START;

INCLUDE "memmap_default.ld"

# @generated by Buffham
import dataclasses
from typing import Self, Type

PICO_FLASH_BASE_ADDR = 0x10000000
PICO_FLASH_SIZE = 2 * 1024 * 1024
PICO_BOOTLOADER_SIZE = 160 * 1024
PICO_APP_SIZE = 880 * 1024
PICO_APP_ADDR_A = 160 * 1024
PICO_APP_ADDR_B = PICO_APP_ADDR_A + 880 * 1024
PICO_SCRATCHPAD_ADDR = PICO_APP_ADDR_B + 880 * 1024
PICO_SECTOR_SIZE = 4 * 1024
NUM_SECTORS = 32


@dataclasses.dataclass
class SystemFlashPage:
    # Number of times the device has booted
    boot_count: int
    # Size of the image in bank A
    image_size_a: int
    # Size of the image in bank B
    image_size_b: int
    # Whether a new image has been flashed into bank B
    new_image_flashed: int

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...


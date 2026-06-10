"""Stamp a firmware image with its own SHA256.

The image embeds an `ImageStamp` struct (see `emb/project/base/image_stamp.hpp`):
a 16-byte magic followed by a 32-byte hash field, zeroed in the compiled
binary. The stamp is the SHA256 of the image with the hash field zeroed,
patched into the hash field post-build. The application reports the stamp
in the `SystemFlashPage` so `flash.py` can verify the running image.
"""

import hashlib
import pathlib

import rich_click as click

# NOTE: Must match `g_image_stamp.magic` in `emb/project/base/image_stamp.cc`
MAGIC = b'NLB-IMAGE-STAMP!'
HASH_SIZE = 32


def _hash_offset(image: bytes) -> int:
    """Locate the hash field of the image's stamp."""
    offset = image.find(MAGIC)
    if offset == -1:
        raise ValueError('Image stamp magic not found in image')
    if image.find(MAGIC, offset + 1) != -1:
        raise ValueError('Multiple image stamp magics found in image')
    return offset + len(MAGIC)


def compute_hash(image: bytes) -> bytes:
    """Compute the stamp hash: SHA256 of the image with the hash field zeroed."""
    offset = _hash_offset(image)
    zeroed = image[:offset] + b'\x00' * HASH_SIZE + image[offset + HASH_SIZE :]
    return hashlib.sha256(zeroed).digest()


def read_hash(image: bytes) -> bytes:
    """Read the stamped hash from an image."""
    offset = _hash_offset(image)
    return image[offset : offset + HASH_SIZE]


def stamp_image(image: bytes) -> bytes:
    """Return the image with its stamp hash patched in."""
    offset = _hash_offset(image)
    return image[:offset] + compute_hash(image) + image[offset + HASH_SIZE :]


@click.command()
@click.argument(
    'input_path', type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path)
)
@click.argument('output_path', type=click.Path(dir_okay=False, path_type=pathlib.Path))
def main(input_path: pathlib.Path, output_path: pathlib.Path) -> None:
    output_path.write_bytes(stamp_image(input_path.read_bytes()))


if __name__ == '__main__':
    main()

import logging
import pathlib
from typing import Self, Type

from rich import progress

from emb.project.base import base_bh
from emb.project.bootloader import bootloader_bh
from nlb.buffham import bh


class BaseClient:
    def __init__(self, node: base_bh.BaseNode) -> None:
        self._node = node

        self._app_addr_a = 160 * 1024
        self._app_addr_b = self._app_addr_a + 880 * 1024

    def __enter__(self) -> Self:
        self._node.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._node.stop()

    def ping(self) -> None:
        msg = base_bh.Ping(ping=0)
        resp = base_bh.PING.transact(self._node, msg)
        logging.info(resp.message)

    def _write_flash_image(self, address: int, data: list[int]) -> None:
        msg = base_bh.FlashPage(address=address, read_size=0, data=data)
        resp = base_bh.WRITE_FLASH_IMAGE.transact(self._node, msg)
        assert resp.address == address

    def write_flash_image(self, image: pathlib.Path | str) -> None:
        image = pathlib.Path(image)
        with progress.Progress() as progress_bar:
            address = 0

            task = progress_bar.add_task(
                'Writing flash image', total=image.stat().st_size
            )

            with image.open('rb') as f:
                data = list(f.read(1024))
                while data:
                    self._write_flash_image(address, data)
                    address += len(data)
                    progress_bar.update(task, advance=len(data))
                    data = list(f.read(1024))
        logging.info(f'Flash image written from {image}')

    def _read_flash(self, address: int, size: int) -> base_bh.FlashPage:
        msg = base_bh.FlashPage(address=address, read_size=size, data=[])
        resp = base_bh.READ_FLASH.transact(self._node, msg)
        return resp

    def read_flash_image(
        self,
        outpath: pathlib.Path | str,
        boot_side: int | None = None,
        read_size: int = 880 * 1024,
    ) -> None:
        if boot_side is None:
            boot_side = self.read_system_page().boot_side
        address = self._app_addr_b if boot_side == 0 else self._app_addr_a

        self.read_flash(outpath, address, read_size)

    def read_flash(
        self,
        outpath: pathlib.Path | str,
        address: int = 0,
        read_size: int = 2 * 1024 * 1024,
    ) -> None:
        end_address = address + read_size
        with progress.Progress() as progress_bar:
            task = progress_bar.add_task('Reading flash', total=read_size)

            with pathlib.Path(outpath).open('wb') as f:
                while address < end_address:
                    page = self._read_flash(address, min(1024, end_address - address))
                    if not page.data:
                        break
                    f.write(bytes(page.data))
                    address += len(page.data)
                    progress_bar.update(task, advance=len(page.data))
        logging.info(f'Flash read to {outpath}')

    def _write_flash_sector(self, sector: int, msg: bh.BuffhamLike) -> None:
        resp = base_bh.WRITE_FLASH_SECTOR.transact(
            self._node, base_bh.FlashSector(sector=sector, data=list(msg.serialize()))
        )
        assert resp.sector == sector

    def _read_flash_sector[
        M: bh.BuffhamLike
    ](self, sector: int, msg_class: Type[M]) -> M:
        resp = base_bh.READ_FLASH_SECTOR.transact(
            self._node, base_bh.FlashSector(sector=sector, data=[])
        )
        return msg_class.deserialize(bytes(resp.data))[0]

    def write_system_page(self, page: bootloader_bh.SystemFlashPage) -> None:
        self._write_flash_sector(0, page)

    def read_system_page(self) -> bootloader_bh.SystemFlashPage:
        return self._read_flash_sector(0, bootloader_bh.SystemFlashPage)

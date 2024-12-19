import logging
import pathlib
from typing import Type

from rich import progress

from emb.project import client
from emb.project.base import base_bh
from emb.project.bootloader import bootloader_bh
from nlb.buffham import bh


class BaseClient(client.Client):
    def __init__(self, node: bh.BhNode) -> None:
        super().__init__(node)

        self._node.register_publish_callback(
            base_bh.PublishIds.LOG_MESSAGE.value, self._on_log_msg
        )

        self._emb_logger: logging.Logger | None = None

    def _on_log_msg(self, msg: base_bh.LogMessage) -> None:
        # TODO: Make a more creative / richer logger
        self.emb_logger.info(msg.message)

    @property
    def emb_logger(self) -> logging.Logger:
        if self._emb_logger is None:
            self._emb_logger = logging.getLogger('emb')
        return self._emb_logger

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
        # TODO: Make 1024 for serial
        chunk_size = 256

        with progress.Progress() as progress_bar:
            address = 0

            task = progress_bar.add_task(
                'Writing flash image', total=image.stat().st_size
            )

            with image.open('rb') as f:
                data = list(f.read(chunk_size))
                while data:
                    self._write_flash_image(address, data)
                    address += len(data)
                    progress_bar.update(task, advance=len(data))
                    data = list(f.read(chunk_size))

        system_page = self.read_system_page()
        system_page.image_size_b = image.stat().st_size
        system_page.new_image_flashed = 1
        self.write_system_page(system_page)

        logging.info(f'Flash image written from {image}')

    def _read_flash(self, address: int, size: int) -> base_bh.FlashPage:
        msg = base_bh.FlashPage(address=address, read_size=size, data=[])
        resp = base_bh.READ_FLASH.transact(self._node, msg)
        return resp

    def read_flash_image(
        self,
        outpath: pathlib.Path | str,
        boot_side: int | None = None,
        read_size: int | None = None,
    ) -> None:
        address = (
            bootloader_bh.PICO_APP_ADDR_A
            if not boot_side
            else bootloader_bh.PICO_APP_ADDR_B
        )

        if read_size is None:
            system_page = self.read_system_page()
            read_size = (
                system_page.image_size_a if not boot_side else system_page.image_size_b
            )

        self.read_flash(outpath, address, read_size)

    def read_flash(
        self,
        outpath: pathlib.Path | str,
        address: int = 0,
        read_size: int = bootloader_bh.PICO_FLASH_SIZE,
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

    def reset(self) -> None:
        # Manually transmit the reset message to avoid waiting for a response
        self._node._comms_transporter.send(
            self._node._serializer.serialize(base_bh.Ping(0), base_bh.RESET.request_id)
        )

    def revert_flash(self) -> None:
        # The previous image is stored in the other bank, so we can just tell
        # the bootloader to switch to the other bank
        system_page = self.read_system_page()
        system_page.new_image_flashed = 1
        self.write_system_page(system_page)

        self.reset()

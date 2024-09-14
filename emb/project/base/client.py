import logging
import pathlib
from typing import Self

from rich import progress

from emb.project.base import base_bh


class BaseClient:
    def __init__(self, node: base_bh.BaseNode) -> None:
        self._node = node

    def __enter__(self) -> Self:
        self._node.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._node.stop()

    def ping(self) -> None:
        msg = base_bh.Ping(ping=0)
        resp = base_bh.PING.transact(self._node, msg)
        logging.info(resp.message)

    def _write_flash_page(self, address: int, data: list[int]) -> None:
        msg = base_bh.FlashPage(address=address, read_size=0, data=data)
        resp = base_bh.FLASH_PAGE.transact(self._node, msg)
        logging.info(resp.address)

    def _read_flash_page(self, address: int, size: int) -> base_bh.FlashPage:
        msg = base_bh.FlashPage(address=address, read_size=size, data=[])
        resp = base_bh.READ_FLASH_PAGE.transact(self._node, msg)
        return resp

    def read_flash(self, outpath: pathlib.Path) -> None:
        with progress.Progress() as progress_bar:
            address = 0
            flash_size = 2 * 1024 * 1024

            task = progress_bar.add_task('Reading flash', total=flash_size)

            with outpath.open('wb') as f:
                while address < flash_size:
                    page = self._read_flash_page(address, 1024)
                    if not page.data:
                        break
                    f.write(bytes(page.data))
                    address += len(page.data)
                    progress_bar.update(task, advance=len(page.data))
        logging.info(f'Flash read to {outpath}')

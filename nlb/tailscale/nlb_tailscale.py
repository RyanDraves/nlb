"""Simple CLI wrapper around the Tailscale CLI"""

import datetime
import glob
import json
import pathlib
import shlex
import subprocess

import rich_click as click
from InquirerPy.base import control
from InquirerPy.prompts import filepath
from InquirerPy.prompts import list as list_prompt

from nlb.util import console_utils
from nlb.util import prompt_utils

SCREENSHOT_DIR = pathlib.Path.home() / 'Pictures' / 'Screenshots'


class TailscaleWrapper:
    """A simple wrapper around the `tailscale` process

    (Does not use the actual API)
    """

    def __init__(self, console: console_utils.Console) -> None:
        self._console = console

    def list_devices(self) -> list[str]:
        """List all devices connected to the current Tailscale network"""
        result = self._run_command('tailscale status --json')

        data = json.loads(result.stdout)
        peers = [peer for peer in data['Peer'].values() if peer['Online']]
        return [peer['DNSName'].split('.')[0] for peer in peers]

    def print_devices(self) -> None:
        """Print all devices connected to the current Tailscale network"""
        devices = self.list_devices()
        if not devices:
            self._console.warning('No devices connected to the network')
            return
        self._console.info('Devices connected to the network:')
        for device in devices:
            self._console.print(f'  - [blue]{device}[/]')

    def _prompt_for_device(self) -> str:
        devices = self.list_devices()
        return list_prompt.ListPrompt(
            message='Select a device:', choices=devices
        ).execute()

    def send_files(self) -> None:
        """Send files to a device"""
        device = self._prompt_for_device()
        files = self._prompt_for_files()

        self._run_command(
            f'tailscale file cp {shlex.join([str(f) for f in files])} {device}:'
        )

        files_str = 'Files' if len(files) > 1 else 'File'
        self._console.success(f'{files_str} sent successfully')

    def _prompt_for_files(self) -> list[pathlib.Path]:
        pattern = filepath.FilePathPrompt(
            message='Select a file or glob pattern:',
            default=str(pathlib.Path.cwd()),
            multicolumn_complete=True,
        ).execute()

        # Gracefully add a wildcard to directories;
        # `tailscale file cp` does not support directories
        if pathlib.Path(pattern).is_dir():
            pattern += '/*'

        return [
            pathlib.Path(f) for f in glob.glob(pattern) if pathlib.Path(f).is_file()
        ]

    def send_screenshots(self, hours_ago: int = 1) -> None:
        """Send recent screenshots to a device"""
        device = self._prompt_for_device()
        selected_files = self._prompt_for_screenshots(hours_ago)

        self._run_command(
            f'tailscale file cp {shlex.join([str(f) for f in selected_files])} {device}:'
        )

        files_str = 'Files' if len(selected_files) > 1 else 'File'
        self._console.success(f'{files_str} sent successfully')

    def _prompt_for_screenshots(self, hours_ago: int) -> list[pathlib.Path]:
        files = [
            pathlib.Path(f)
            for f in glob.glob(str(SCREENSHOT_DIR) + '/**/*', recursive=True)
            if pathlib.Path(f).is_file()
        ]
        dates = [datetime.datetime.fromtimestamp(f.stat().st_mtime) for f in files]
        # Sort files and dates together
        sorted_files, dates = zip(
            *sorted(zip(files, dates), key=lambda x: x[1], reverse=True)
        )
        # Filter for files modified in the last `hours_ago` hours
        now = datetime.datetime.now()
        files = [
            f
            for f, d in zip(sorted_files, dates)
            if now - d < datetime.timedelta(hours=hours_ago)
        ]

        if not files:
            # Backup: 5 most recent screenshots
            files = sorted_files[:5]

        if not files:
            self._console.warning('No screenshots found')
            exit(1)

        selected_files: list[pathlib.Path] = list_prompt.ListPrompt(
            message='Select screenshots to send:',
            choices=[
                control.Choice(file, str(file.relative_to(SCREENSHOT_DIR)))
                for file in files
            ],
            multiselect=True,
        ).execute()

        return selected_files

    def receive_files(self) -> None:
        """Receive files from a device"""
        local_path = self._prompt_for_dir()
        self._run_command(f'tailscale file get {local_path}')

        self._console.success('File(s) received successfully')

    def _prompt_for_dir(self) -> pathlib.Path:
        return pathlib.Path(
            filepath.FilePathPrompt(
                message='Select a directory:',
                default=str(pathlib.Path.cwd()),
                multicolumn_complete=True,
                validate=prompt_utils.PathValidator(
                    message='Path must be a directory', is_dir=True, must_exist=True
                ),
                only_directories=True,
            ).execute()
        )

    def _run_command(self, command: str) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(shlex.split(command), capture_output=True, check=False)
        if result.returncode != 0:
            self._console.print(f'Error running command: {result.stderr}')
            exit(1)
        return result


@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Tailscale CLI wrapper"""
    ctx.obj = TailscaleWrapper(console_utils.Console())


@main.command()
@click.pass_obj
def list_devices(tailscale: TailscaleWrapper) -> None:
    tailscale.print_devices()


@main.command()
@click.pass_obj
def send(tailscale: TailscaleWrapper) -> None:
    tailscale.send_files()


@main.command()
@click.pass_obj
def send_screenshot(tailscale: TailscaleWrapper) -> None:
    tailscale.send_screenshots()


@main.command()
@click.pass_obj
def receive(tailscale: TailscaleWrapper) -> None:
    tailscale.receive_files()


if __name__ == '__main__':
    main(prog_name='nlb_tailscale')

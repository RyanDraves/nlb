import dataclasses
import json
import pathlib
import shlex
import subprocess
from typing import TypedDict


@dataclasses.dataclass
class BoardInfo:
    port: str
    protocol: str
    type: str
    board_name: str
    # Fully qualified board name
    fqbn: str
    core: str


class BoardMatch(TypedDict):
    name: str
    fqbn: str


class PortInfo(TypedDict):
    address: str
    label: str
    protocol: str
    protocol_label: str
    # There's a `properties` field but idc about it
    hardware_id: str


class BoardResponse(TypedDict):
    matching_boards: list[BoardMatch]
    port: PortInfo


class BoardListResponse(TypedDict):
    detected_ports: list[BoardResponse]


class CompileResponse(TypedDict):
    compiler_out: str
    compiler_err: str
    # There're a whole bunch of fields we don't care about
    # There's also an `upload_result` field but it seems empty
    success: bool


class UploadResponse(TypedDict):
    stdout: str
    stderr: str
    # There's an `updated_upload_port` field but idc about it


class ArduinoClient:
    """Client for interacting with Arduino CLI."""

    def __init__(self, cli_path: str = 'arduino-cli'):
        self._cli_path = cli_path

    def _run_command(self, args: list[str]) -> tuple[str, str]:
        """Run a command using subprocess and return stdout and stderr."""
        sanitized_args = [shlex.quote(arg) for arg in args]
        command = [self._cli_path] + sanitized_args
        process = subprocess.run(command, capture_output=True, text=True, shell=False)
        return process.stdout, process.stderr

    def get_boards(self) -> list[BoardInfo]:
        """Get a list of available boards."""
        stdout, stderr = self._run_command(['board', 'list', '--json'])
        if stderr:
            raise RuntimeError(f'Error getting boards: {stderr}')

        output: BoardListResponse = json.loads(stdout)

        boards = []
        for board in output['detected_ports']:
            boards.append(
                BoardInfo(
                    port=board['port']['address'],
                    protocol=board['port']['protocol'],
                    type=board['port']['protocol_label'],
                    board_name=board['matching_boards'][0]['name'],
                    fqbn=board['matching_boards'][0]['fqbn'],
                    core=board['matching_boards'][0]['fqbn'].rsplit(':', maxsplit=1)[0],
                )
            )
        return boards

    def compile(self, board: BoardInfo, sketch_path: pathlib.Path) -> CompileResponse:
        """Compile a sketch for a given board."""
        stdout, stderr = self._run_command(
            ['compile', str(sketch_path), '-b', board.fqbn, '--json']
        )
        if stderr:
            raise RuntimeError(f'Error compiling sketch: {stderr}')

        output: CompileResponse = json.loads(stdout)
        return output

    def upload(self, board: BoardInfo, sketch_path: pathlib.Path) -> UploadResponse:
        """Upload a sketch for a given board."""
        stdout, stderr = self._run_command(
            ['upload', str(sketch_path), '-b', board.fqbn, '-p', board.port, '--json']
        )
        if stderr:
            raise RuntimeError(f'Error uploading sketch: {stderr}')

        output: UploadResponse = json.loads(stdout)
        return output

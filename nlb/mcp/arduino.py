import pathlib
from typing import Annotated, Any, Callable

import pydantic
from fastmcp import exceptions

from nlb.arduino import client
from nlb.mcp import util


class ArduinoTool:
    def __init__(self, sandbox_dir: pathlib.Path = util.SANDBOX_DIR):
        self._sandbox_dir = sandbox_dir
        self._sandbox_dir.mkdir(parents=True, exist_ok=True)
        self._client = client.ArduinoClient()

    @property
    def tool_functions(self) -> list[Callable[..., Any]]:
        """Return a list of tool functions for this tool."""
        return [self.arduino_create_sketch, self.arduino_upload]

    def arduino_create_sketch(
        self,
        name: Annotated[
            str,
            pydantic.Field(
                description=(
                    'The name of the sketch to create.'
                    ' A folder and .ino file will be created with this name (e.g. `sketch/sketch.ino`).'
                ),
                min_length=1,
            ),
        ],
        file_text: Annotated[
            str,
            pydantic.Field(
                description='The content to write to the new sketch file.',
                min_length=1,
            ),
        ],
    ) -> None:
        """Create a new Arduino sketch."""
        name = name.strip('/')  # Remove leading slashes
        full_path = (self._sandbox_dir / name / f'{name}.ino').resolve()
        if not full_path.is_relative_to(self._sandbox_dir):
            raise exceptions.ToolError(
                f'Path {name} is not within the sandbox directory.'
            )

        if full_path.exists():
            raise exceptions.ToolError(f'Sketch {name} already exists.')

        # Create the sketch directory
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the sketch file
        full_path.write_text(file_text)

    def arduino_upload(
        self,
        name: Annotated[
            str,
            pydantic.Field(
                description='The name of the sketch to upload.',
                min_length=1,
            ),
        ],
    ) -> str:
        """Upload the Arduino sketch to the board."""
        boards = self._client.get_boards()
        if not boards:
            raise exceptions.ToolError('No Arduino boards found.')
        if len(boards) > 1:
            raise exceptions.ToolError(
                'Multiple Arduino boards found. Please specify one.'
            )

        board = boards[0]

        sketch_path = self._sandbox_dir / name
        if not sketch_path.exists():
            raise exceptions.ToolError(f'Sketch {name} does not exist.')

        # Compile the sketch
        compile_response = self._client.compile(board, sketch_path)
        if not compile_response['success']:
            raise exceptions.ToolError(
                f'Error compiling sketch: {compile_response["compiler_err"]}'
            )

        # Upload the sketch
        upload_response = self._client.upload(board, sketch_path)
        if upload_response['stderr']:
            raise exceptions.ToolError(
                f'Error uploading sketch: {upload_response["stderr"]}'
            )

        return upload_response['stdout'] or 'Sketch uploaded successfully.'

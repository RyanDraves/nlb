import pathlib
import shutil
from typing import Annotated, Any, Callable

import pydantic
from fastmcp import exceptions

from nlb.mcp import util
from nlb.util import semantic_errors


class FileEditTool:
    def __init__(self, sandbox_dir: pathlib.Path = util.SANDBOX_DIR):
        self._sandbox_dir = sandbox_dir
        self._sandbox_dir.mkdir(parents=True, exist_ok=True)

    @property
    def tool_functions(self) -> list[Callable[..., Any]]:
        """Return a list of tool functions for this tool."""
        return [self.file_view, self.file_create, self.file_update, self.file_undo_edit]

    def _resolve_path(self, path: str, should_exist: bool) -> pathlib.Path:
        path = path.strip('/')  # Remove leading slashes
        full_path = (self._sandbox_dir / path).resolve()

        if not full_path.is_relative_to(self._sandbox_dir):
            raise exceptions.ToolError(
                f'Path {path} is not within the sandbox directory.'
            )

        if not should_exist and full_path.exists():
            raise exceptions.ToolError(f'Path {path} already exists.')

        if should_exist and not full_path.exists():
            # Find the best match for the path
            all_files = [f for f in self._sandbox_dir.rglob('**/*') if f.is_file()]
            all_file_names = [f.name for f in all_files]
            path_name = pathlib.Path(path).name

            best_match = semantic_errors.find_best_match(path_name, all_file_names)
            if best_match:
                index = all_file_names.index(best_match)
                match_path = all_files[index].relative_to(self._sandbox_dir)
                raise exceptions.ToolError(
                    f'Path {path} does not exist. Did you mean "{match_path}"?',
                )

            raise exceptions.ToolError(f'Path {path} does not exist.')

        return full_path

    def _backup_file(self, path: pathlib.Path) -> None:
        # Create a backup of the file
        backup_path = path.parent / (path.name + '.bak')
        # Copy the file to the backup path
        shutil.copy(path, backup_path)

    def _backup_exists(self, path: pathlib.Path) -> bool:
        # Check if a backup file exists
        backup_path = path.parent / (path.name + '.bak')
        return backup_path.exists()

    def file_view(
        self,
        path: Annotated[
            str,
            pydantic.Field(
                description='The path to the file or directory to view.', min_length=1
            ),
        ],
        begin_line: Annotated[
            int | None,
            pydantic.Field(
                description=(
                    'The line number to start viewing from (1-indexed).'
                    ' If not specified, the entire file will be viewed.'
                    ' This parameter only applies when viewing files, not directories.'
                ),
                ge=1,
            ),
        ] = None,
        end_line: Annotated[
            int | None,
            pydantic.Field(
                description=(
                    'The line number to stop viewing at (1-indexed, inclusive).'
                    ' If not specified, the entire file will be viewed.'
                    ' If -1, read to the end of the file.'
                    ' This parameter only applies when viewing files, not directories.'
                ),
                ge=-1,
            ),
        ] = None,
    ) -> str:
        """View a file or directory, optionally specifying line numbers to limit the output."""
        full_path = self._resolve_path(path, True)

        if full_path.is_dir():
            return self._view_directory(full_path)

        if begin_line is not None and end_line is not None:
            view_range = (begin_line, end_line)
        else:
            view_range = None

        return self._view_file(full_path, view_range)

    def _view_directory(self, path: pathlib.Path) -> str:
        # Get the list of files and directories in the specified path
        names = []
        for item in path.iterdir():
            # Hide backup files
            if item.suffix == '.bak':
                continue
            # Append a trailing slash for directories
            if item.is_dir():
                names.append(item.name + '/')
            else:
                names.append(item.name)

        return (
            f'{path.relative_to(self._sandbox_dir)} directory contents: '
            + ', '.join(names)
        )

    def _view_file(self, path: pathlib.Path, view_range: tuple[int, int] | None) -> str:
        if view_range is not None:
            # Sanitize the view range
            start, end = view_range
            if start < 1:
                raise exceptions.ToolError('begin_line must be greater than 0.')
            if end != -1 and end < start:
                raise exceptions.ToolError(
                    'end_line must be greater than or equal to begin_line.'
                )

        # Read the file and return the specified lines
        with path.open('r') as f:
            lines = f.readlines()

        # For each line, prepend `line_number: ` to the line
        lines = [f'{i + 1}: {line}' for i, line in enumerate(lines)]

        if view_range is not None:
            start, end = view_range
            if end == -1:
                end = len(lines)
            return ''.join(lines[start - 1 : end])

        return ''.join(lines)

    def file_create(
        self,
        path: Annotated[
            str,
            pydantic.Field(
                description=(
                    'The path where the new file should be created.'
                    ' Missing parent directories will be created automatically.'
                ),
                min_length=1,
            ),
        ],
        file_text: Annotated[
            str,
            pydantic.Field(
                description='The content to write to the new file.', min_length=1
            ),
        ],
    ) -> str:
        """Create a new file with the specified content."""
        full_path = self._resolve_path(path, False)

        # Make sure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_text(file_text)

        return f'File {path} created successfully.'

    def file_update(
        self,
        path: Annotated[
            str,
            pydantic.Field(description='The path to the file to update.', min_length=1),
        ],
        file_text: Annotated[
            str,
            pydantic.Field(
                description='The new content to replace the entire file with.',
                min_length=1,
            ),
        ],
    ) -> None:
        """Update an existing file by replacing its entire content with new text."""
        full_path = self._resolve_path(path, True)

        if not full_path.is_file():
            raise exceptions.ToolError(f'Path {path} is not a file.')

        self._backup_file(full_path)
        full_path.write_text(file_text)

    def file_undo_edit(
        self,
        path: Annotated[
            str,
            pydantic.Field(
                description='The path to the file whose last edit should be undone.',
                min_length=1,
            ),
        ],
    ) -> None:
        """Undo the last edit made to a file, restoring its previous content."""
        full_path = self._resolve_path(path, True)

        if not full_path.is_file():
            raise exceptions.ToolError(f'Path {path} is not a file.')

        if not self._backup_exists(full_path):
            raise exceptions.ToolError(f'No edits to undo for {path}.')

        # Restore the backup file
        backup_path = full_path.parent / (full_path.name + '.bak')
        shutil.copy(backup_path, full_path)

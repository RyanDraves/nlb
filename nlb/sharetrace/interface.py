import dataclasses
import datetime
import pathlib
from typing import Any, cast

import marshmallow_dataclass

TRACE_CACHE_DIR = pathlib.Path.home() / '.cache' / 'sharetrace'
# Browsers don't like file:// URLs with `.` in the path (apparently?)
TRACE_OUTPUT_DIR = pathlib.Path.home() / 'sharetrace'


@dataclasses.dataclass
class GitInfo:
    repository: str | None
    commit: str | None
    branch: str | None
    root: str | None


@dataclasses.dataclass
class LineContext:
    number: int
    content: str
    is_error_line: bool


@dataclasses.dataclass
class CodeContext:
    filename: str
    error_line: int
    context_start: int | None
    context_end: int | None
    lines: list[LineContext]


@dataclasses.dataclass
class SystemInfo:
    platform: str
    python_version: str
    python_implementation: str
    architecture: str
    machine: str
    processor: str
    system: str
    release: str


@dataclasses.dataclass
class StackFrame:
    filename: str
    line_number: int
    function_name: str
    code_context: CodeContext
    locals: dict[str, Any]


@dataclasses.dataclass
class ExceptionData:
    id: str
    timestamp: str
    exception_type: str
    exception_module: str
    exception_message: str
    traceback_text: str
    stack_frames: list[StackFrame]
    system_info: SystemInfo
    git_info: GitInfo | None


def list_cached_exceptions() -> list[pathlib.Path]:
    """List all cached exception files."""
    if not TRACE_CACHE_DIR.exists():
        return []

    return sorted(TRACE_CACHE_DIR.glob('trace_*.json'), reverse=True)


def save_exception_data(exception_data: ExceptionData) -> pathlib.Path:
    """Save exception data to cache directory."""
    # Ensure cache directory exists
    TRACE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp and exception ID
    timestamp = datetime.datetime.fromisoformat(exception_data.timestamp)
    filename = (
        f'trace_{timestamp.strftime("%Y%m%d_%H%M%S")}_{exception_data.id[:8]}.json'
    )
    file_path = TRACE_CACHE_DIR / filename

    # Save the data
    schema = marshmallow_dataclass.class_schema(ExceptionData)()
    with file_path.open('w', encoding='utf-8') as f:
        f.write(schema.dumps(exception_data))

    return file_path


def load_exception_data(file_path: pathlib.Path) -> ExceptionData:
    """Load exception data from a cache file."""
    return cast(
        ExceptionData,
        marshmallow_dataclass.class_schema(ExceptionData)().loads(
            file_path.read_text()
        ),
    )

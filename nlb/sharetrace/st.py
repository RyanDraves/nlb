import datetime
import linecache
import pathlib
import platform
import subprocess
import sys
import traceback
import uuid

from nlb.sharetrace import interface


def _get_git_info(file_path: str) -> interface.GitInfo | None:
    """Get Git information for a file."""
    try:
        # Get the repository root
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=pathlib.Path(file_path).parent,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        repo_root = result.stdout.strip()

        # Get current commit hash
        commit_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_hash = (
            commit_result.stdout.strip() if commit_result.returncode == 0 else None
        )

        # Get current branch
        branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None

        # Get remote URL
        remote_result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        remote_url = (
            remote_result.stdout.strip() if remote_result.returncode == 0 else None
        )

        return interface.GitInfo(
            repository=remote_url,
            commit=commit_hash,
            branch=branch,
            root=repo_root,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None


def _get_code_context(
    filename: str, lineno: int, context_lines: int = 5
) -> interface.CodeContext:
    """Extract code context around the given line."""
    try:
        # Get lines around the error
        start_line = max(1, lineno - context_lines)
        end_line = lineno + context_lines + 1

        lines: list[interface.LineContext] = []
        for line_num in range(start_line, end_line):
            line = linecache.getline(filename, line_num)
            if line:  # linecache returns empty string for non-existent lines
                lines.append(
                    interface.LineContext(
                        number=line_num,
                        content=line.rstrip('\n'),
                        is_error_line=line_num == lineno,
                    )
                )

        return interface.CodeContext(
            filename=filename,
            error_line=lineno,
            context_start=start_line,
            context_end=end_line - 1,
            lines=lines,
        )
    except Exception:
        return interface.CodeContext(
            filename=filename,
            error_line=lineno,
            context_start=None,
            context_end=None,
            lines=[],
        )


def _get_system_info() -> interface.SystemInfo:
    """Collect system information."""
    return interface.SystemInfo(
        platform=platform.platform(),
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        architecture=platform.architecture()[0],
        machine=platform.machine(),
        processor=platform.processor(),
        system=platform.system(),
        release=platform.release(),
    )


def _capture_exception(
    exc_type: type, exc_value: Exception, exc_traceback
) -> interface.ExceptionData:
    """Capture comprehensive exception information."""
    # Generate unique ID for this exception
    exception_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()

    # Extract stack trace information
    stack_frames: list[interface.StackFrame] = []
    git_info = None
    tb = exc_traceback
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        lineno = tb.tb_lineno
        function_name = frame.f_code.co_name

        if git_info is None:
            git_info = _get_git_info(filename)

        filename_relative = (
            filename.removeprefix(git_info.root + '/')
            if git_info and git_info.root
            else filename
        )

        # Get code context for this frame
        code_context = _get_code_context(filename, lineno)

        stack_frames.append(
            interface.StackFrame(
                filename=filename_relative,
                line_number=lineno,
                function_name=function_name,
                code_context=code_context,
                locals={k: repr(v) for k, v in frame.f_locals.items()},
            )
        )

        tb = tb.tb_next

    # Format the full traceback as text
    traceback_text = ''.join(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
    )

    return interface.ExceptionData(
        id=exception_id,
        timestamp=timestamp,
        exception_type=exc_type.__name__,
        exception_module=exc_type.__module__,
        exception_message=str(exc_value),
        traceback_text=traceback_text,
        stack_frames=stack_frames,
        system_info=_get_system_info(),
        git_info=git_info,
    )


def _custom_excepthook(exc_type: type, exc_value: Exception, exc_traceback) -> None:
    """Custom exception hook that captures and saves exception data."""
    # Don't capture KeyboardInterrupt or SystemExit
    if exc_type in (KeyboardInterrupt, SystemExit):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    try:
        # Capture exception data
        exception_data = _capture_exception(exc_type, exc_value, exc_traceback)

        # Save to cache
        cache_file = interface.save_exception_data(exception_data)

        # Print the original traceback
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

        # Inform user about the cached data
        print(
            f'\nException data saved to: \033[96m{cache_file}\033[0m', file=sys.stderr
        )
        print(
            'Use \033[96msharetrace\033[0m to generate a shareable report.',
            file=sys.stderr,
        )
    except Exception as save_error:
        # If something goes wrong with our capturing, still show the original exception
        print(f'Error saving exception data: {save_error}', file=sys.stderr)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


def install_exception_hook() -> None:
    """Install the custom exception hook to capture traceback data."""
    sys.excepthook = _custom_excepthook

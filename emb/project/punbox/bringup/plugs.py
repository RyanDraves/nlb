"""Plugs for the punbox bringup procedure."""

import pathlib
import subprocess

# bringup/ -> punbox -> project -> emb -> repo root
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


class Bazel:
    """Runs the repo's Bazel targets, returning (exit code, combined output)."""

    def _invoke(self, *args: str) -> tuple[int, str, str]:
        result = subprocess.run(
            ['bazel', *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def run(self, target: str, quiet: bool = False) -> tuple[int, str, str]:
        if quiet:
            return self._invoke('run', '--config', 'quiet', target)
        return self._invoke('run', target)

    def test(self, target: str) -> tuple[int, str, str]:
        return self._invoke(
            'test', target, '--nocache_test_results', '--test_output=all'
        )

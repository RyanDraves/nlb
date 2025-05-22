"""Simple CLI tool to create feature branches from GitHub issues."""

import json
import shlex
import subprocess
from typing import TypedDict

import rich_click as click
from InquirerPy.base import control
from InquirerPy.prompts import list as list_prompt

from nlb.util import console_utils


class Issue(TypedDict):
    """Type definition for GitHub issue."""

    number: int
    title: str


class GhIssueWrapper:
    """Wrapper around GitHub CLI for issue operations."""

    def __init__(self, console: console_utils.Console) -> None:
        self._console = console

    def list_issues(self) -> list[Issue]:
        """List open issues using 'gh issue list'."""
        result = self._run_command(
            'gh issue list --state open --limit 100 --json number,title'
        )
        return json.loads(result.stdout)

    def prompt_issue(self, issues: list[Issue]) -> int | str:
        """Prompt user to select an issue or create a new one."""
        choices = [
            control.Choice('create', 'Create new issue'),
        ] + [
            control.Choice(issue['number'], f'#{issue["number"]}: {issue["title"]}')
            for issue in issues
        ]
        return list_prompt.ListPrompt(
            message='Select an issue (or create):', choices=choices
        ).execute()

    def create_issue(self, issues: list[Issue] | None = None) -> int:
        """Create a new issue using 'gh issue create' and return its number."""
        if issues is None:
            issues = self.list_issues()

        # Run interactive create
        self._run_command_interactive('gh issue create')

        # Query the issue list again to find the new issue
        new_issues = self.list_issues()
        new_issue = next((issue for issue in new_issues if issue not in issues), None)
        if new_issue is None:
            self._console.warning('No new issue found')
            exit(1)

        return new_issue['number']

    def develop_issue(self, number: int) -> None:
        """Create and checkout a branch for the given issue."""
        self._run_command(f'gh issue develop {number} -c')
        self._console.success(f'Feature branch for issue #{number} created')

    def _run_command_interactive(self, command: str) -> None:
        """Run a shell command interactively and return the result."""
        result = subprocess.run(command, shell=True, check=False, text=True)
        if result.returncode != 0:
            self._console.print(f'Error running command: {result.stderr}')
            exit(1)

    def _run_command(self, command: str) -> subprocess.CompletedProcess[str]:
        """Run a shell command and return the result."""
        result = subprocess.run(shlex.split(command), capture_output=True, text=True)
        if result.returncode != 0:
            self._console.print(f'Error running command: {result.stderr}')
            exit(1)
        return result


@click.command()
@click.option('--issue', type=int, help='Issue number to develop')
@click.option('--create', 'create_new', is_flag=True, help='Create a new issue')
def main(issue: int, create_new: bool) -> None:
    """CLI for creating feature branches from GitHub issues."""
    console = console_utils.Console()
    wrapper = GhIssueWrapper(console)
    if issue:
        wrapper.develop_issue(issue)
    elif create_new:
        number = wrapper.create_issue()
        wrapper.develop_issue(number)
    else:
        issues = wrapper.list_issues()
        if not issues:
            console.warning('No open issues found')
            exit(0)
        selection = wrapper.prompt_issue(issues)
        if selection == 'create':
            number = wrapper.create_issue()
        else:
            number = int(selection)
        wrapper.develop_issue(number)


if __name__ == '__main__':
    main(prog_name='nlb_gh_feature')

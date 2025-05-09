import os
import pathlib

import rich_click as click
from InquirerPy.prompts import confirm


@click.command()
def main() -> None:
    """Install script for bash-completion in a virtual environment."""
    venv = os.environ.get('VIRTUAL_ENV')
    backup_dir = pathlib.Path.home() / '.local'

    if not venv and backup_dir.exists():
        env_dir = backup_dir
    elif not venv:
        print('Not inside a virtual environment.')
        exit(1)
    else:
        env_dir = pathlib.Path(venv)

    if venv:
        script_path = env_dir / 'bin' / 'activate'
    else:
        script_path = pathlib.Path.home() / '.bashrc'
    completions_dir = env_dir / 'share' / 'completions'

    if not script_path.exists():
        if not venv:
            print('Not inside a virtual environment.')
            exit(1)
        print('Cannot find venv activate script.')
        exit(1)

    if not completions_dir.exists():
        if not venv:
            print('Not inside a virtual environment.')
            exit(1)
        print('No bash completions directory found.')
        exit(1)

    if not venv:
        allow = confirm.ConfirmPrompt(
            message='No virtual environment found. Do you want to proceed installing for ~/.local?',
            default=False,
        ).execute()
        if not allow:
            print('Exiting without changes.')
            exit(1)

    marker = '# Added by venv_completions for completions files'
    bash_block = (
        f'\n{marker}\n'
        f'_completion_dir="{completions_dir}"\n'
        'if [ -d "$_completion_dir" ]; then\n'
        '    for _script in "$_completion_dir"/*; do\n'
        '        [ -f "$_script" ] && source "$_script"\n'
        '    done\n'
        'fi\n'
    )

    activate_text = script_path.read_text()
    if marker not in activate_text:
        with script_path.open('a') as f:
            f.write(bash_block)
        print(f'Patched activate script to source all completions in {completions_dir}')
    else:
        print('Activate script already contains the bash completion sourcing block.')


if __name__ == '__main__':
    main(prog_name='venv_completions')

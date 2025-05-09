import os
import pathlib

import rich_click as click


@click.command()
def main() -> None:
    """Install script for bash-completion in a virtual environment."""
    venv = os.environ.get('VIRTUAL_ENV')
    if not venv:
        print('Not inside a virtual environment.')
        exit(1)

    activate_path = pathlib.Path(venv) / 'bin' / 'activate'
    completions_dir = pathlib.Path(venv) / 'share' / 'completions'

    if not activate_path.exists():
        print('Cannot find venv activate script.')
        exit(1)

    if not completions_dir.exists():
        print('No bash completions directory found.')
        exit(1)

    marker = '# Added by venv_completions.py for completions files'
    bash_block = (
        f'{marker}'
        f'_completion_dir="{completions_dir}"'
        'if [ -d "$_completion_dir" ]; then'
        '    for _script in "$_completion_dir"/*; do'
        '        [ -f "$_script" ] && source "$_script"'
        '    done'
        'fi'
    )

    activate_text = activate_path.read_text()
    if marker not in activate_text:
        with activate_path.open('a') as f:
            f.write(bash_block)
        print(f'Patched activate script to source all completions in {completions_dir}')
    else:
        print('Activate script already contains the bash completion sourcing block.')


if __name__ == '__main__':
    main(prog_name='venv_completions')

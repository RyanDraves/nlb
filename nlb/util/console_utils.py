import os

from rich import console


class Console(console.Console):
    def info(self, msg: str, **kwargs) -> None:
        self.print(f'[cyan]{msg}[/cyan]', **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self.print(f'[red]{msg}[/red]', **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self.print(f'[yellow]{msg}[/yellow]', **kwargs)

    def success(self, msg: str, **kwargs) -> None:
        self.print(f'[green]{msg}[/green]', **kwargs)


class ConsolePanel(Console):
    """Make a console a renderable Panel for live displays.

    https://stackoverflow.com/a/74134595

    TODO: Find a way to add Panel options like a border & such
    """

    def __init__(self, *args, **kwargs):
        console_file = open(os.devnull, 'w')
        super().__init__(record=True, file=console_file, *args, **kwargs)

    def __rich_console__(self, console, options):
        texts = self.export_text(clear=False).split('\n')
        for line in texts[-options.height :]:
            yield line

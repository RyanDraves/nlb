from rich import console


class Console(console.Console):
    def info(self, msg: str) -> None:
        self.print(f'[cyan]{msg}[/cyan]')

    def error(self, msg: str) -> None:
        self.print(f'[red]{msg}[/red]')

    def warning(self, msg: str) -> None:
        self.print(f'[yellow]{msg}[/yellow]')

    def success(self, msg: str) -> None:
        self.print(f'[green]{msg}[/green]')

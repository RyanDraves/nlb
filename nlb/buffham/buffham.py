import enum
import pathlib

import rich_click as click

from nlb.buffham import cpp_generator
from nlb.buffham import parser
from nlb.buffham import py_generator
from nlb.util import click_utils


class Languages(enum.Enum):
    PYTHON = enum.auto()
    PYTHON_STUB = enum.auto()
    CPP = enum.auto()


@click.command()
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Input Buffham file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Output file",
)
@click.option(
    "--language",
    "-l",
    type=click_utils.EnumChoice(Languages),
    required=True,
    help="Output language",
)
def main(input: pathlib.Path, output: pathlib.Path, language: Languages):
    p = parser.Parser()
    buffham = p.parse_file(input)

    match language:
        case Languages.PYTHON:
            py_generator.generate_python(buffham, output, stub=False)
        case Languages.PYTHON_STUB:
            py_generator.generate_python(buffham, output, stub=True)
        case Languages.CPP:
            cpp_generator.generate_cpp(buffham, output)
        case _:
            raise ValueError(f"Unsupported language: {language}")

    print(f"Generated {output}")


if __name__ == '__main__':
    main()

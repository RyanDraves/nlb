import enum
import pathlib

import rich_click as click

from nlb.buffham import cpp_generator
from nlb.buffham import parser
from nlb.buffham import py_generator
from nlb.buffham import template_generator
from nlb.util import click_utils


class Languages(enum.Enum):
    PYTHON = enum.auto()
    CPP = enum.auto()
    TEMPLATE = enum.auto()


@click.command()
@click.option(
    '--input',
    '-i',
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help='Input Buffham file',
)
@click.option(
    '--output',
    '-o',
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    required=True,
    help='Output file',
)
@click.option(
    '--secondary-output',
    '-s',
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    help='Secondary output file (e.g. for Python stubs or .cc files)',
)
@click.option(
    '--template-file',
    '-t',
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    help='Template file',
)
@click.option(
    '--dep',
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    multiple=True,
    help='Dependency buffham file (neccessary for now)',
)
@click.option(
    '--language',
    '-l',
    type=click_utils.EnumChoice(Languages),
    required=True,
    help='Output language',
)
def main(
    input: pathlib.Path,
    output: pathlib.Path,
    secondary_output: pathlib.Path | None,
    template_file: pathlib.Path | None,
    dep: list[pathlib.Path],
    language: Languages,
):
    p = parser.Parser()
    ctx = parser.ParseContext({})

    for d in dep:
        p.parse_file(d, ctx)

    buffham = p.parse_file(input, ctx)

    match language:
        case Languages.PYTHON:
            assert secondary_output is not None
            py_generator.generate_python(ctx, buffham.namespace, output, stub=False)
            py_generator.generate_python(
                ctx, buffham.namespace, secondary_output, stub=True
            )
        case Languages.CPP:
            assert secondary_output is not None
            cpp_generator.generate_cpp(ctx, buffham.namespace, output, hpp=True)
            cpp_generator.generate_cpp(
                ctx, buffham.namespace, secondary_output, hpp=False
            )
        case Languages.TEMPLATE:
            assert template_file is not None
            template_generator.generate_template(
                ctx, buffham.namespace, output, template_file
            )
        case _:
            raise ValueError(f'Unsupported language: {language}')

    print(f'Generated {output}')
    if secondary_output is not None:
        print(f'Generated {secondary_output}')


if __name__ == '__main__':
    main(prog_name='buffham')

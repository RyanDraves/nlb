import pathlib
import re

from nlb.buffham import parser

TEMPLATE_PATTERN = re.compile(r'\{\{ (\w+) \}\}')


def _expanded_constant(buffham: parser.Buffham, constant: parser.Constant) -> str:
    """Expand a constant to its value.

    If the constant references other constants, expand those as well.
    """
    reference_constants = {}
    for reference in constant.references:
        reference_constant = next(
            filter(lambda x: x.name == reference, buffham.constants), None
        )
        assert reference_constant is not None
        reference_constants[reference] = _expanded_constant(buffham, reference_constant)

    value = constant.value.format(**reference_constants)

    return value


def generate_template(
    buffham: parser.Buffham, outfile: pathlib.Path, template_file: pathlib.Path
) -> None:
    """Generate a template file."""
    lines = template_file.read_text().splitlines()

    # Search through the lines of the template file for template patterns
    with outfile.open('w') as fp:
        for line in lines:
            match = TEMPLATE_PATTERN.findall(line)
            if not match:
                fp.write(line + '\n')
                continue

            for m in match:
                # Find the value in the Buffham constants
                constant = next(filter(lambda x: x.name == m, buffham.constants), None)

                if constant is None:
                    raise ValueError(f'Constant {m} not found in {buffham.name} file')

                line = line.replace(
                    f'{{{{ {m} }}}}', _expanded_constant(buffham, constant)
                )

            fp.write(line + '\n')

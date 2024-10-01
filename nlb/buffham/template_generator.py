import pathlib
import re

from nlb.buffham import parser

TEMPLATE_PATTERN = re.compile(r'\{\{ ([\w|\.]+) \}\}')


def _expanded_constant(
    ctx: parser.ParseContext, bh: parser.Buffham, constant: parser.Constant
) -> str:
    """Expand a constant to its value.

    If the constant references other constants, expand those as well.
    """
    reference_constants = {}
    for reference in constant.references:
        reference_constant = next(
            filter(
                lambda x: x.get_relative_name(bh.namespace) == reference,
                ctx.iter_constants(bh.constants),
            ),
            None,
        )
        assert reference_constant is not None, f'Constant {reference} not found'
        reference_constants[reference] = _expanded_constant(ctx, bh, reference_constant)

    value = constant.value
    for ref, val in reference_constants.items():
        value = value.replace(f'{{{ref}}}', val)

    return value


def generate_template(
    ctx: parser.ParseContext,
    primary_namespace: str,
    outfile: pathlib.Path,
    template_file: pathlib.Path,
) -> None:
    """Generate a template file."""
    bh = ctx.buffhams[primary_namespace]

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
                constant = next(
                    filter(lambda x: x.name == m, ctx.iter_constants(bh.constants)),
                    None,
                )

                if constant is None:
                    raise ValueError(f'Constant {m} not found')

                line = line.replace(
                    f'{{{{ {m} }}}}', _expanded_constant(ctx, bh, constant)
                )

            fp.write(line + '\n')

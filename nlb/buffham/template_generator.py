import pathlib
import re

from nlb.buffham import parser

TEMPLATE_PATTERN = re.compile(r'\{\{ ([\w|\.]+) \}\}')


def generate_template(
    ctx: parser.Parser,
    primary_namespace: str,
    outfile: pathlib.Path,
    template_file: pathlib.Path,
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
                constant, _ = next(
                    filter(
                        lambda x: parser.relative_name(x[1], primary_namespace) == m,
                        ctx.iter_constants(),
                    ),
                    (None, None),
                )

                if constant is None:
                    raise ValueError(f'Constant {m} not found')

                line = line.replace(f'{{{{ {m} }}}}', constant.expanded_value)

            fp.write(line + '\n')

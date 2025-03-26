import dataclasses
import inspect
import re
from typing import Callable, Type


@dataclasses.dataclass
class ParsedSignature:
    description: str

    # Arg name -> arg description
    arg_descriptions: dict[str, str]
    arg_types: dict[str, Type]

    return_description: str | None = None
    return_type: Type | None = None


def parse_signature_and_docs(func: Callable) -> ParsedSignature:
    """Parse the docstring of a function into a structured format.

    The docstring should be formatted as this one is, with the description as the header,
    the args in the `Args:` section (tabbed), and an optional `Returns:` section.

    Args:
        func: The function to parse the docstring from.

    Returns:
        A ParsedSignature object containing the description, args, and returns.
    """
    doc = func.__doc__

    if not doc:
        raise ValueError(f'Function {func.__name__} has no docstring.')

    lines = [line.strip() for line in doc.split('\n')]

    # Find `Args:` and `Returns:` sections
    args_start = lines.index('Args:') if 'Args:' in lines else None
    returns_start = lines.index('Returns:') if 'Returns:' in lines else None

    if args_start is None:
        raise ValueError(f'Function {func.__name__} has no Args section.')

    # Extract description
    description = '\n'.join(lines[:args_start]).strip()

    # Extract arg descriptions
    arg_descriptions = {}
    cur_arg = ''
    for line in lines[
        args_start + 1 : returns_start if returns_start is not None else -1
    ]:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'(\w+): (.+)', line)
        if match:
            arg_name, arg_desc = match.groups()
            arg_descriptions[arg_name] = arg_desc
            cur_arg = arg_name
        elif cur_arg:
            # Continuation of the previous arg description
            arg_descriptions[cur_arg] += ' ' + line

    # Extract arg types
    arg_types = {}
    for arg in arg_descriptions.keys():
        param = inspect.signature(func).parameters.get(arg)
        if param and param.annotation is not param.empty:
            arg_types[arg] = param.annotation
        else:
            raise ValueError(
                f'Function {func.__name__} has no type annotation for argument "{arg}".'
            )

    # Extract return description
    return_description = None
    if returns_start is not None:
        return_description = '\n'.join(lines[returns_start + 1 :]).strip()

    # Extract return type
    return_type = None
    if return_description:
        return_param = inspect.signature(func).return_annotation
        if return_param is not inspect.Signature.empty:
            return_type = return_param
        else:
            raise ValueError(f'Function {func.__name__} has no return type annotation.')

    return ParsedSignature(
        description=description,
        arg_descriptions=arg_descriptions,
        arg_types=arg_types,
        return_description=return_description,
        return_type=return_type,
    )

import pathlib
import types
from typing import Callable, Type, get_args, get_origin

from openai.types.beta import assistant_tool_param
from openai.types.beta.realtime import session_update_event_param

from nlb.util import introspection

# Keep file edits in this sandbox
SANDBOX_DIR = pathlib.Path.home() / '.cache' / 'nlb' / 'wizaidry'

TYPE_MAP = {
    str: 'string',
    int: 'integer',
    float: 'number',
    bool: 'boolean',
    type(None): 'null',
}


def _get_arg_type(arg_type: Type) -> dict[str, str | list[dict[str, str]]]:
    if get_origin(arg_type) is types.UnionType:
        return {
            'anyOf': [
                {'type': TYPE_MAP[inner_type]} for inner_type in get_args(arg_type)
            ]
        }

    return {'type': TYPE_MAP[arg_type]}


def get_assistant_tool_schema(
    func: Callable,
) -> assistant_tool_param.AssistantToolParam:
    """Generate the OpenAI Assistant tool schema for a given function.

    This closes follows `openai.pydantic_function_tool`'s behavior on
    a schema analogous to a function spec, but instead generates directly
    from a function signature and docstring.
    """
    signature = introspection.parse_signature_and_docs(func)

    properties = {
        arg: {'description': signature.arg_descriptions[arg], 'title': arg}
        | _get_arg_type(signature.arg_types[arg])
        for arg in signature.arg_descriptions
    }

    return {
        'type': 'function',
        'function': {
            'name': func.__name__,
            'strict': True,
            'parameters': {
                # Skip duplicate description in the parameters field
                # 'description': signature.description,
                'properties': properties,
                # Don't respect None-ness in order to match OpenAI's behavior
                'required': [arg for arg in signature.arg_descriptions],
                # Skip duplicate title in the parameters field
                # 'title': func.__name__,
                'type': 'object',
                'additionalProperties': False,
            },
            'description': signature.description,
        },
    }


def get_realtime_tool_schema(
    func: Callable,
) -> session_update_event_param.SessionTool:
    """Generate the OpenAI Realtime tool schema for a given function.

    This closely follows `pydantic.BaseModel.model_json_schema`'s behavior on
    a schema analogous to a function spec (for the `parameters` field), but instead
    generates directly from a function signature and docstring.
    """
    signature = introspection.parse_signature_and_docs(func)

    properties = {
        arg: {'description': signature.arg_descriptions[arg], 'title': arg}
        | _get_arg_type(signature.arg_types[arg])
        for arg in signature.arg_descriptions
    }

    # Respect None-ness for which args are required
    required = [
        arg
        for arg in signature.arg_descriptions
        if type(None) not in get_args(signature.arg_types[arg])
    ]

    return {
        'type': 'function',
        'name': func.__name__,
        'description': signature.description,
        'parameters': {
            # Skip duplicate description in the parameters field
            # 'description': signature.description,
            'properties': properties,
            'required': required,
            # Skip duplicate title in the parameters field
            # 'title': func.__name__,
            'type': 'object',
        },
    }

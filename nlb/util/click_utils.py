import enum
import logging
from typing import Any, Type

import rich_click as click


class EnumChoice(click.Choice):
    """Use an Enum as choices for a click option

    Borrowed from https://github.com/pallets/click/pull/2210
    """

    def __init__(self, enum_type: Type[enum.Enum], case_sensitive: bool = False):
        super().__init__(
            choices=[element.name for element in enum_type],
            case_sensitive=case_sensitive,
        )
        self.enum_type = enum_type

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> Any:
        if not isinstance(value, str):
            # Assume enum instance
            value = value.value
        value = super().convert(value=value, param=param, ctx=ctx)
        if value is None:
            return None
        return self.enum_type[value]


class MappedChoice[V](click.Choice):
    """Use a mapping as choices for a click option"""

    def __init__(self, mapping: dict[str, V], case_sensitive: bool = False):
        super().__init__(choices=list(mapping.keys()), case_sensitive=case_sensitive)
        self.mapping = mapping

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> V:
        value = super().convert(value=value, param=param, ctx=ctx)
        return self.mapping[value]


class ClassChoice(click.Choice):
    """Select from a list of classes by name"""

    def __init__(self, classes: list[type], case_sensitive: bool = False):
        self.mapping = {clz.__name__: clz for clz in classes}

        super().__init__(
            choices=[clz.__name__ for clz in classes], case_sensitive=case_sensitive
        )

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> type:
        value = super().convert(value=value, param=param, ctx=ctx)
        return self.mapping[value]


log_level = click.option(
    '-l',
    '--log-level',
    type=MappedChoice(
        {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
    ),
    default='INFO',
    help='Log level',
)

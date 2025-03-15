import struct
from typing import Callable, Type

from nlb.buffham import parser
from nlb.util import dataclass


def generate_serializer(
    message: parser.Message,
) -> Callable[[dataclass.DataclassLike], bytes]:
    """Generic serializer generator for a message schema."""

    def serializer(instance: dataclass.DataclassLike) -> bytes:
        buffer = bytes()
        for field in message.fields:
            value = getattr(instance, field.name)

            if field.iterable:
                # Write the size of the value as a uint16_t
                buffer += struct.pack('<H', len(value))

                if field.pri_type is parser.FieldType.LIST:
                    buffer += struct.pack(f'<{len(value)}{field.format}', *value)
                else:
                    if field.pri_type is parser.FieldType.STRING:
                        value = value.encode()
                    buffer += value
            elif field.pri_type is parser.FieldType.MESSAGE:
                assert field.message is not None
                # Turtles all the way down
                buffer += generate_serializer(field.message)(value)
            else:
                buffer += struct.pack(f'<{field.format}', value)

        return buffer

    return serializer


def generate_deserializer[T: dataclass.DataclassLike](
    message: parser.Message, clz: Type[T]
) -> Callable[[bytes], tuple[T, int]]:
    """Generic deserializer generator for a message schema."""

    def deserializer(buffer: bytes) -> tuple[T, int]:
        values = {}

        offset = 0
        for field in message.fields:
            if field.iterable:
                size = struct.unpack_from('<H', buffer, offset)[0]
                offset += 2

                if field.pri_type is parser.FieldType.LIST:
                    values[field.name] = list(
                        struct.unpack_from(f'<{size}{field.format}', buffer, offset)
                    )
                    offset += size * struct.calcsize(field.format)
                else:
                    value = buffer[offset : offset + size]
                    if field.pri_type is parser.FieldType.STRING:
                        value = value.decode()
                    values[field.name] = value
                    offset += size
            elif field.pri_type is parser.FieldType.MESSAGE:
                assert field.message is not None
                values[field.name], size = generate_deserializer(
                    field.message, clz.__dataclass_fields__[field.name].type
                )(buffer[offset:])
                offset += size
            else:
                values[field.name] = struct.unpack_from(
                    f'<{field.format}', buffer, offset
                )[0]
                offset += struct.calcsize(field.format)

        return clz(**values), offset

    return deserializer

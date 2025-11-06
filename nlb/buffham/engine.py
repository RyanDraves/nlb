import struct
import types
from typing import Callable, Type, Union, get_args, get_origin

from nlb.buffham import parser
from nlb.buffham import schema_bh
from nlb.util import dataclass


def split_optional(field_type: Type) -> tuple[Type, bool]:
    """Split a type into its base type and whether it's optional.

    Args:
        field_type: The type annotation from a dataclass field

    Returns:
        Tuple of (base_type, is_optional)
    """
    origin = get_origin(field_type)

    # Check if it's a Union type (which includes Optional/Union/X | None)
    if origin is types.UnionType or origin is Union:
        args = get_args(field_type)
        # Check if None is one of the union members
        if type(None) in args:
            # Filter out None and return the remaining type
            non_none_types = [arg for arg in args if arg is not type(None)]

            if len(non_none_types) == 1:
                return non_none_types[0], True
            else:
                raise ValueError(
                    f'Only single-type Optionals are supported, got: {field_type}'
                )

    # Not optional
    return field_type, False


def generate_serializer(
    message: parser.Message, message_registry: dict[tuple[str, str], parser.Message]
) -> Callable[[dataclass.DataclassLike], bytes]:
    """Generic serializer generator for a message schema."""
    num_optional_fields = sum(1 for f in message.fields if f.is_optional)
    num_optional_bytes = (num_optional_fields + 7) // 8

    def serializer(instance: dataclass.DataclassLike) -> bytes:
        buffer = bytes()

        # Handle optional fields bitfield
        if num_optional_fields > 0:
            bitfield = 0
            optional_idx = 0
            for field in message.fields:
                if field.is_optional:
                    value = getattr(instance, field.name)
                    if value is not None:
                        bitfield |= 1 << optional_idx
                    optional_idx += 1
            buffer += bitfield.to_bytes(length=num_optional_bytes, byteorder='little')

        for field in message.fields:
            value = getattr(instance, field.name)
            field_format = parser.FORMAT_MAP[field.sub_type or field.pri_type]

            if field.is_optional and value is None:
                continue

            if parser.is_field_iterable(field):
                # Write the size of the value as a uint16_t
                buffer += struct.pack('<H', len(value))

                if field.pri_type is schema_bh.FieldType.LIST:
                    if field.sub_type in (
                        schema_bh.FieldType.STRING,
                        schema_bh.FieldType.BYTES,
                    ):
                        for item in value:
                            buffer += struct.pack('<H', len(item))
                            if field.sub_type is schema_bh.FieldType.STRING:
                                item = item.encode()
                            buffer += item
                    else:
                        buffer += struct.pack(f'<{len(value)}{field_format}', *value)
                else:
                    if field.pri_type is schema_bh.FieldType.STRING:
                        value = value.encode()
                    buffer += value
            elif field.pri_type is schema_bh.FieldType.MESSAGE:
                assert field.obj_name is not None
                nested_message = message_registry[
                    (field.obj_name.namespace, field.obj_name.name)
                ]
                # Turtles all the way down
                buffer += generate_serializer(nested_message, message_registry)(value)
            elif field.pri_type is schema_bh.FieldType.ENUM:
                buffer += struct.pack(f'<{field_format}', value.value)
            else:
                buffer += struct.pack(f'<{field_format}', value)

        return buffer

    return serializer


def generate_deserializer[T: dataclass.DataclassLike](
    message: parser.Message,
    message_registry: dict[tuple[str, str], parser.Message],
    clz: Type[T],
) -> Callable[[bytes], tuple[T, int]]:
    """Generic deserializer generator for a message schema."""
    num_optional_fields = sum(1 for f in message.fields if f.is_optional)
    num_optional_bytes = (num_optional_fields + 7) // 8

    def deserializer(buffer: bytes) -> tuple[T, int]:
        values = {}

        # Handle optional fields bitfield
        optional_bitfield = 0
        if num_optional_fields > 0:
            optional_bitfield = int.from_bytes(
                buffer[0:num_optional_bytes], byteorder='little'
            )
            offset = num_optional_bytes
        else:
            offset = 0

        optional_idx = 0
        for field in message.fields:
            field_format = parser.FORMAT_MAP[field.sub_type or field.pri_type]

            if field.is_optional:
                if not optional_bitfield & (1 << optional_idx):
                    values[field.name] = None
                    continue
                optional_idx += 1

            if parser.is_field_iterable(field):
                size = struct.unpack_from('<H', buffer, offset)[0]
                offset += 2

                if field.pri_type is schema_bh.FieldType.LIST:
                    if field.sub_type in (
                        schema_bh.FieldType.STRING,
                        schema_bh.FieldType.BYTES,
                    ):
                        values[field.name] = []
                        for _ in range(size):
                            item_size = struct.unpack_from('<H', buffer, offset)[0]
                            offset += 2
                            item = buffer[offset : offset + item_size]
                            offset += item_size
                            if field.sub_type is schema_bh.FieldType.STRING:
                                item = item.decode()
                            values[field.name].append(item)
                    else:
                        values[field.name] = list(
                            struct.unpack_from(f'<{size}{field_format}', buffer, offset)
                        )
                        offset += size * struct.calcsize(field_format)
                else:
                    value = buffer[offset : offset + size]
                    if field.pri_type is schema_bh.FieldType.STRING:
                        value = value.decode()
                    values[field.name] = value
                    offset += size
            elif field.pri_type is schema_bh.FieldType.MESSAGE:
                assert field.obj_name is not None
                nested_clz, _ = split_optional(
                    clz.__dataclass_fields__[field.name].type
                )
                nested_message = message_registry[
                    (field.obj_name.namespace, field.obj_name.name)
                ]
                # Turtles all the way up
                values[field.name], size = generate_deserializer(
                    nested_message, message_registry, nested_clz
                )(buffer[offset:])
                offset += size
            elif field.pri_type is schema_bh.FieldType.ENUM:
                enum_clz, _ = split_optional(clz.__dataclass_fields__[field.name].type)
                value = struct.unpack_from(f'<{field_format}', buffer, offset)[0]
                values[field.name] = enum_clz(value)
                offset += struct.calcsize(field_format)
            else:
                values[field.name] = struct.unpack_from(
                    f'<{field_format}', buffer, offset
                )[0]
                offset += struct.calcsize(field_format)

        return clz(**values), offset

    return deserializer

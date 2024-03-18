from enum import Enum
from python_bebop import BebopWriter, BebopReader, UnionType, UnionDefinition
from uuid import UUID
import math
import json
from datetime import datetime

class Config:
    _ping: int


    def __init__(self,     ping: int    ):
        self.encode = self._encode
        self._ping = ping

    @property
    def ping(self):
        return self._ping

    def _encode(self):
        """Fake class method for allowing instance encode"""
        writer = BebopWriter()
        Config.encode_into(self, writer)
        return writer.to_list()


    @staticmethod
    def encode(message: "Config"):
        writer = BebopWriter()
        Config.encode_into(message, writer)
        return writer.to_list()


    @staticmethod
    def encode_into(message: "Config", writer: BebopWriter):
        writer.write_uint32(message.ping)

    @classmethod
    def read_from(cls, reader: BebopReader):
        field0 = reader.read_uint32()

        return Config(ping=field0)

    @staticmethod
    def decode(buffer) -> "Config":
        return Config.read_from(BebopReader(buffer))

    def __repr__(self):
        return json.dumps(self, default=lambda o: o.value if isinstance(o, Enum) else dict(sorted(o.__dict__.items())) if hasattr(o, "__dict__") else str(o))




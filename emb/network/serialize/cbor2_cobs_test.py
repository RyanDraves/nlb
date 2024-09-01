import dataclasses
import unittest

from emb.network.serialize import cbor2_cobs
from nlb.datastructure import bidirectional_dict


@dataclasses.dataclass
class Foo:
    bar: int
    baz: str
    qux: list[int]


class TestCbor2Cobs(unittest.TestCase):
    def setUp(self) -> None:
        self.serializer = cbor2_cobs.Cbor2Cobs(
            bidirectional_dict.BidirectionalMap(
                {
                    Foo: 8,
                }
            )
        )

    def test_serialize(self) -> None:
        msg = Foo(bar=1, baz='hello', qux=[1, 2, 3])

        # Painfully curated manual test cases
        self.assertEqual(
            self.serializer.serialize(msg),
            b'\x1a\x08\xa3cbar\x01cbazehellocqux\x83\x01\x02\x03\x00',
        )

    def test_deserialize(self) -> None:
        # Painfully curated manual test cases
        self.assertEqual(
            self.serializer.deserialize(
                b'\x1a\x08\xa3cbar\x01cbazehellocqux\x83\x01\x02\x03\x00'
            ),
            Foo(bar=1, baz='hello', qux=[1, 2, 3]),
        )

    def test_zeroes(self) -> None:
        # Put more zeroes in more places to trip up the COBS encoding
        serializer = cbor2_cobs.Cbor2Cobs(
            bidirectional_dict.BidirectionalMap(
                {
                    Foo: 0,
                }
            )
        )

        msg = Foo(bar=0, baz='', qux=[0, 0, 0])
        self.assertEqual(serializer.deserialize(serializer.serialize(msg)), msg)

    def test_round_trip(self) -> None:
        msg = Foo(bar=1, baz='hello', qux=[1, 2, 3])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

        msg = Foo(bar=0, baz='', qux=[])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

    def test_large_messages(self) -> None:
        # 2e256 is 257 characters long; past the COBS frame size
        msg = Foo(bar=int(2e256), baz='', qux=[])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

        msg = Foo(bar=0, baz='a' * 1000, qux=[])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

        msg = Foo(bar=0, baz='', qux=[4] * 1000)
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

        msg = Foo(bar=0, baz='', qux=[0] * 1000)
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

        # All together now!
        msg = Foo(bar=int(2e256), baz='a' * 1000, qux=[4] * 1000)
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg)), msg
        )

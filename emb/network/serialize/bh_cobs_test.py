import unittest

from emb.network.serialize import bh_cobs
from emb.network.serialize.testdata import test_bh


class TestBhCobs(unittest.TestCase):
    def setUp(self) -> None:
        self.serializer = bh_cobs.BhCobs(
            {
                8: test_bh.Foo,
                9: test_bh.NestedMessage,
            }
        )

    def test_serialize(self) -> None:
        msg = test_bh.Foo(bar=1, baz='hello', qux=[1, 2, 3])

        # Painfully curated manual test cases
        self.assertEqual(
            self.serializer.serialize(msg, 8),
            b'\x03\x08\x01\x01\x01\x02\x05\x07hello\x03\x02\x01\x02\x02\x02\x03\x01\x00',
        )

    def test_deserialize(self) -> None:
        # Painfully curated manual test cases
        self.assertEqual(
            self.serializer.deserialize(
                b'\x03\x08\x01\x01\x01\x02\x05\x07hello\x03\x02\x01\x02\x02\x02\x03\x01\x00'
            ),
            test_bh.Foo(bar=1, baz='hello', qux=[1, 2, 3]),
        )

    def test_zeroes(self) -> None:
        # Put more zeroes in more places to trip up the COBS encoding
        serializer = bh_cobs.BhCobs(
            {
                0: test_bh.Foo,
            }
        )

        msg = test_bh.Foo(bar=0, baz='', qux=[0, 0, 0])
        self.assertEqual(serializer.deserialize(serializer.serialize(msg, 0)), msg)

    def test_round_trip(self) -> None:
        msg = test_bh.Foo(bar=1, baz='hello', qux=[1, 2, 3])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

        msg = test_bh.Foo(bar=0, baz='', qux=[])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

    def test_large_messages(self) -> None:
        # 2e256 is 257 characters long; past the COBS frame size
        msg = test_bh.Foo(bar=2**32 - 1, baz='', qux=[])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

        msg = test_bh.Foo(bar=0, baz='a' * 1000, qux=[])
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

        msg = test_bh.Foo(bar=0, baz='', qux=[4] * 1000)
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

        msg = test_bh.Foo(bar=0, baz='', qux=[0] * 1000)
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

        # All together now!
        msg = test_bh.Foo(bar=2**32 - 1, baz='a' * 1000, qux=[4] * 1000)
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 8)), msg
        )

    def test_nested_messages(self) -> None:
        msg = test_bh.NestedMessage(
            foo=test_bh.Foo(bar=1, baz='hello', qux=[1, 2, 3, 4]), flag=1
        )
        self.assertEqual(
            self.serializer.deserialize(self.serializer.serialize(msg, 9)), msg
        )

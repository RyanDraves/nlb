import unittest

from nlb.datastructure import bidirectional_dict


class TestBidirectionalDict(unittest.TestCase):
    def test_basic(self) -> None:
        d = bidirectional_dict.BidirectionalMap[str, int]()

        d['a'] = 1

        self.assertEqual(d['a'], 1)
        self.assertEqual(d[1], 'a')

        with self.assertRaises(KeyError):
            d['b']

    def test_dict_init(self) -> None:
        d = bidirectional_dict.BidirectionalMap[str, int]({'a': 1})

        self.assertEqual(d['a'], 1)
        self.assertEqual(d[1], 'a')

    def test_update(self) -> None:
        d = bidirectional_dict.BidirectionalMap[str, int]()

        d.update({'a': 1})

        self.assertEqual(d['a'], 1)
        self.assertEqual(d[1], 'a')

        # Can't support kwarg-based update
        with self.assertRaises(AssertionError):
            d.update(b=2)

    def test_overwrite(self) -> None:
        d = bidirectional_dict.BidirectionalMap[str, int]()

        d['a'] = 1
        d['a'] = 2

        self.assertEqual(d['a'], 2)
        self.assertEqual(d[2], 'a')

        with self.assertRaises(KeyError):
            d[1]

    def test_delete(self) -> None:
        d = bidirectional_dict.BidirectionalMap[str, int]()

        d['a'] = 1

        del d['a']

        with self.assertRaises(KeyError):
            d['a']

        with self.assertRaises(KeyError):
            d[1]

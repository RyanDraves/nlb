from typing import TypeVar, overload

_K = TypeVar('_K')
_V = TypeVar('_V')


class BidirectionalMap(dict[_K | _V, _K | _V]):
    """A bijective map that allows for key-value and value-key lookups.

    https://stackoverflow.com/a/13276237 but with better typing and
    `update` works
    """

    @overload
    def __init__(self, dictionary: dict[_K, _V] | None) -> None: ...

    @overload
    def __init__(self, dictionary: dict[_V, _K] | None = None) -> None: ...

    def __init__(
        self, dictionary: dict[_K | _V, _K | _V] | None = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        if dictionary is not None:
            for key, value in dictionary.items():
                # Can't convince it that key and value are different types
                self.__setitem__(key, value)  # type: ignore

    def update(self, *args, **kwargs) -> None:
        """Update the dictionary with the key-value pairs from a mapping object

        Typing an `update` override is impossible(?), so we'll just use `*args`
        """
        assert len(args) == 1, 'update expected 1 argument, got 0'
        assert not kwargs, 'update expected 1 arg, got kwargs'
        m: dict[_K | _V, _K | _V] = args[0]
        for key, value in m.items():
            # Can't convince it that key and value are different types
            self.__setitem__(key, value)  # type: ignore

    @overload
    def __getitem__(self, key: _K) -> _V: ...

    @overload
    def __getitem__(self, key: _V) -> _K: ...

    def __getitem__(self, key: _K | _V) -> _K | _V:
        return super().__getitem__(key)

    @overload
    def __setitem__(self, key: _K, value: _V) -> None: ...

    @overload
    def __setitem__(self, key: _V, value: _K) -> None: ...

    def __setitem__(self, key: _K | _V, value: _K | _V) -> None:
        if key in self:
            del self[key]
        if value in self:
            del self[value]

        super().__setitem__(key, value)
        super().__setitem__(value, key)

    def __delitem__(self, key: _K | _V) -> None:
        super().__delitem__(self[key])
        super().__delitem__(key)

    def __len__(self) -> int:
        """Return the number of key-value pairs."""
        return super().__len__() // 2

from typing import Any, ClassVar, Protocol


class DataclassLike(Protocol):
    """Quack, quack, it's a dataclass"""

    __dataclass_fields__: ClassVar[dict[str, Any]]

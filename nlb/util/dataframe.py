import dataclasses
from typing import Type, TypeVar

import pandas as pd

from nlb.util import dataclass

T = TypeVar('T', bound=dataclass.DataclassLike)


def dataframe_from_type(
    clz: Type[dataclass.DataclassLike], *args, **kwargs
) -> pd.DataFrame:
    """Initialize a DataFrame from a dataclass type."""
    if 'columns' in kwargs:
        raise ValueError('columns must not be provided')
    kwargs['columns'] = [f.name for f in dataclasses.fields(clz)]
    return pd.DataFrame(*args, **kwargs)

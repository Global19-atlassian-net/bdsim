from bdsim.components import ArrayLike as ArrayLike, Block as Block, FunctionBlock as FunctionBlock, Plug as Plug, block as block, ndarray as ndarray
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union
from typing_extensions import Literal as Literal

class Sum(FunctionBlock):
    type: str = ...
    signs: Any = ...
    angles: Any = ...
    def __init__(self, signs: Sequence[Literal['+', '-']], *inputs: Union[Block, Plug], angles: bool=..., **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...

class Prod(FunctionBlock):
    type: str = ...
    ops: Any = ...
    matrix: Any = ...
    def __init__(self, ops: Sequence[Literal['*', '/']], *inputs: Union[Block, Plug], matrix: bool=..., **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...

class Gain(FunctionBlock):
    gain: Any = ...
    type: str = ...
    premul: Any = ...
    def __init__(self, gain: Union[float, ndarray], *inputs: Union[Block, Plug], premul: bool=..., **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...

class Clip(FunctionBlock):
    min: Any = ...
    max: Any = ...
    type: str = ...
    def __init__(self, *inputs: Any, min: Any = ..., max: Any = ..., **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...

class Function(FunctionBlock):
    nin: Any = ...
    type: str = ...
    nout: Any = ...
    func: Any = ...
    userdata: Any = ...
    args: Any = ...
    kwargs: Any = ...
    def __init__(self, func: Union[Callable[..., Sequence[Any]], Sequence[Callable[..., Any]]], *inputs: Union[Block, Plug], nin: int=..., nout: int=..., dict: bool=..., args: Tuple[Any, ...]=..., kwargs: Dict[str, Any]=..., **kwargs_: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...

class Interpolate(FunctionBlock):
    time: Any = ...
    blockclass: str = ...
    f: Any = ...
    x: Any = ...
    def __init__(self, *inputs: Union[Block, Plug], x: Optional[ArrayLike]=..., y: Optional[ArrayLike]=..., xy: Optional[ArrayLike]=..., time: bool=..., kind: Literal[linear, nearest, zero, slinear, quadratic, cubic, previous, next]=..., **kwargs: Any) -> None: ...
    def start(self, **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...

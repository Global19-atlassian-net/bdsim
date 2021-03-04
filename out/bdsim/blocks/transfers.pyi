from bdsim.components import ArrayLike as ArrayLike, Block as Block, Plug as Plug, TransferBlock as TransferBlock, block as block
from math import atan2 as atan2, cos as cos, pi as pi, sin as sin, sqrt as sqrt
from typing import Any, Optional, Union

class Integrator(TransferBlock):
    nstates: Any = ...
    min: Any = ...
    max: Any = ...
    def __init__(self, *inputs: Union[Block, Plug], x0: ArrayLike=..., min: Optional[ArrayLike]=..., max: Optional[ArrayLike]=..., **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...
    def deriv(self): ...

class LTI_SS(TransferBlock):
    type: str = ...
    A: Any = ...
    B: Any = ...
    C: Any = ...
    nstates: Any = ...
    def __init__(self, *inputs: Union[Block, Plug], A: ArrayLike, B: ArrayLike, C: ArrayLike, x0: Optional[ArrayLike]=..., verbose: bool=..., **kwargs: Any) -> None: ...
    def output(self, t: Optional[Any] = ...): ...
    def deriv(self): ...

class LTI_SISO(LTI_SS):
    N: Any = ...
    D: Any = ...
    type: str = ...
    def __init__(self, N: ArrayLike=..., D: ArrayLike=..., *inputs: Union[Block, Plug], x0: Optional[ArrayLike]=..., verbose: bool=..., **kwargs: Any) -> None: ...

"core dimension-with-units logic + coordinate pairs"
# todo: try getting this from a library, maybe pint

from dataclasses import dataclass
from typing import Union, Optional, Literal, Tuple
from .common import LayoutError

@dataclass
class Unit:
    "a number with units. supports some math operations"
    n: Union[int, float]
    unit: Optional[Literal['px', 'in']] # only optional when n=0

    @classmethod
    def zero(cls):
        return cls(0, None)

    @classmethod
    def inch(cls, n, unit: str = 'in'):
        "factory for inches (or any unit I guess; ugh rename this)"
        return cls(n=n, unit=unit)

    def __lt__(self, other):
        assert self.unit == other.unit or self.n == 0 or other.n == 0
        return self.n < other.n

    def __sub__(self, other):
        assert self.unit == other.unit or self.n == 0 or other.n == 0
        return Unit(n=self.n - other.n, unit=self.unit or other.unit)

    def __add__(self, other):
        assert self.unit == other.unit or self.n == 0 or other.n == 0
        return Unit(n=self.n + other.n, unit=self.unit or other.unit)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Unit(n=self.n / other, unit=self.unit)
        assert self.unit == other.unit or self.n == 0 or other.n == 0
        return Unit(n=self.n / other.n, unit=self.unit or other.unit)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Unit(n=self.n * other, unit=self.unit)
        assert self.unit == other.unit or self.n == 0 or other.n == 0
        return Unit(n=self.n * other.n, unit=self.unit or other.unit)

    def __eq__(self, other):
        if self.n == 0 and other.n == 0:
            return True # regardless of units
        return self.n == other.n and self.unit == other.unit

    def to_px(self, dpi):
        "convert to pixels"
        if self.unit == 'px':
            return self
        elif self.unit == 'in':
            return Unit(self.n * dpi, 'px')
        elif self.n == 0:
            return Unit.zero()
        else:
            raise ValueError(f"unk unit {self.unit}")

    def to_in(self, dpi):
        "convert to inches"
        if self.unit == 'in':
            return self
        elif self.unit == 'px':
            return Unit(self.n / dpi, 'in')
        else:
            raise ValueError(f"unk unit {self.unit}")

Direction = Literal['horz', 'vert']

def is_horz(direction: Direction):
    assert direction in Direction.__args__
    return direction == 'horz'

@dataclass
class Dim:
    width: Optional[Unit] = None
    height: Optional[Unit] = None

    def partial(self, direction: Direction, replace=None):
        """return self with main axis nullified; this is used for axis / constraint direction.
        (null axis signals to subcomponents to size according to the cross axis).
        If `replace` is given, this replaces main axis instead of nullifying. (Used in Flex).
        """
        return Dim(width=replace, height=self.height) if is_horz(direction) else Dim(width=self.width, height=replace)

    @classmethod
    def inch(cls, width: Optional[int], height: Optional[int], unit: str = 'in'):
        return cls(width if width is None else Unit.inch(width, unit), height if height is None else Unit.inch(height, unit))

    def __sub__(self, other):
        return Dim(
            width=self.width and other.width and (other.width - self.width),
            height=self.height and other.height and (other.height - self.height),
        )

    def __mul__(self, other):
        return Dim(width=self.width and self.width * other, height=self.height and self.height * other)

    def __truediv__(self, other):
        return Dim(width=self.width and self.width / other, height=self.height and self.height / other)

    def getdir(self, direction: Direction) -> Optional[Unit]:
        return self.width if is_horz(direction) else self.height

    def to_px(self, dpi, factor=4) -> 'Dim':
        return Dim(
            (self.width or self.height * factor).to_px(dpi),
            (self.height or self.width * factor).to_px(dpi),
        )

    def to_in(self, dpi) -> 'Dim':
        return Dim(
            (self.width or self.height).to_in(dpi),
            (self.height or self.width).to_in(dpi),
        )

    def tuple(self) -> Tuple[Optional[int], Optional[int]]:
        return (self.width and int(self.width.n), self.height and int(self.height.n))

    def unit(self):
        "return width / height unit if they agree, else explode"
        assert self.width or self.height
        if self.width and self.height:
            assert self.width.unit == self.height.unit or self.width.n == 0 or self.height.n == 0
        # pylint: disable=consider-using-ternary
        return (self.width and self.width.unit) or self.height.unit

    def nonnegative(self) -> 'Dim':
        "raise a layout error if negative, return self"
        if self.width and self.width.n < 0:
            raise LayoutError('negative width')
        if self.height and self.height.n < 0:
            raise LayoutError('negative height')
        return self

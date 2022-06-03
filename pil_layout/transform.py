import logging
from dataclasses import dataclass
from typing import Literal, List
from .base import Layout
from .renderable import Renderable
from .units import Dim, Unit, Direction
from .common import LayoutError
from .instruction import Instruction, Ilist

logger = logging.getLogger(__name__)

@dataclass
class Transform(Layout):
    "base class for wrappers that transform contents sort of"
    child: Renderable

@dataclass
class Padding(Transform):
    pad: Unit # todo: also percentage

    def inner(self, outer: Dim) -> Dim:
        "compute pad"
        pad2 = self.pad * 2
        return Dim(outer.width - pad2, outer.height - pad2).nonnegative()

    def compute(self, dim: Dim, dpi: int):
        inner = self.inner(dim)
        logger.debug('padding %s - %s = %s', dim, self.pad, inner)
        ilist = self.child.compute(inner, dpi)
        pad2 = Dim(self.pad, self.pad)
        # note: empty full-dim instruction is so the size is correct for equal-layout things. this doesn't work inside partial dim though
        return [inst.offset2(pad2) for inst in ilist] + [Instruction.from_dim(dim, source=self.source())]

StartMiddleEnd = Literal['start', 'middle', 'end']

@dataclass
class AspectRatio(Transform):
    "restrict a viewport to an aspect ratio"
    height_over_width: float # ratio
    halign: StartMiddleEnd = 'start'
    valign: StartMiddleEnd = 'start'

    def inner(self, dim: Dim) -> Dim:
        "given outer dim, return inner dim based on ratio"
        # pylint: disable=no-else-raise
        if dim.width is None and dim.height is None:
            raise LayoutError("AspectRatio needs at least one of width or height")
        elif dim.width is None:
            return Dim(dim.height / self.height_over_width, dim.height)
        elif dim.height is None:
            return Dim(dim.width, Dim.width * self.height_over_width)
        else:
            container_ratio = (dim.height / dim.width).n
            if container_ratio > self.height_over_width:
                return Dim(dim.width, dim.width * self.height_over_width)
            else:
                return Dim(dim.height / self.height_over_width, dim.height)

    def compute(self, dim: Dim, dpi: int):
        inner = self.inner(dim)
        logger.debug('AspectRatio outer %s, inner %s', dim, inner)
        ilist = self.child.compute(inner, dpi)

        if self.halign == 'middle':
            ilist = ilist.align('horz', dim)
        elif self.halign == 'end':
            ilist = ilist.align('horz', dim, middle=False)

        if self.valign == 'middle':
            ilist = ilist.align('vert', dim)
        elif self.valign == 'end':
            ilist = ilist.align('vert', dim, middle=False)

        return ilist

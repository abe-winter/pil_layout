import logging, dataclasses
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from .base import Layout
from .units import Dim, Unit, Direction, is_horz

@dataclass
class Instruction:
    "drawing instruction"
    top: Unit
    left: Unit
    bottom: Unit
    right: Unit
    image: Optional[Image.Image] = None # optional bc of test suite
    source: Optional[Layout] = None # Layout instance that generated this

    @classmethod
    def from_dim(cls, dim: Dim, image: Optional[Image.Image] = None, source: Optional[Layout] = None):
        "factory. construct an Instruction from a Dim, top left at origin"
        return cls(top=Unit.zero(), left=Unit.zero(), bottom=dim.height, right=dim.width, image=image, source=source)

    @classmethod
    def tlbr(cls, top: int, left: int, bottom: int, right: int, unit='in'):
        "convenience factory"
        return cls(Unit(top, unit), Unit(left, unit), Unit(bottom, unit), Unit(right, unit))

    def offset(self, offset: Unit, direction: Direction) -> 'Instruction':
        "return copy offset in direction by offset"
        if is_horz(direction):
            return dataclasses.replace(self, left=self.left + offset, right=self.right + offset)
        else:
            return dataclasses.replace(self, top=self.top + offset, bottom=self.bottom + offset)

    def offset2(self, offset: Dim) -> 'Instruction':
        return dataclasses.replace(
            self,
            left=self.left + offset.width,
            right=self.right + offset.width,
            top=self.top + offset.height,
            bottom=self.bottom + offset.height,
        )

    def topleft(self, dpi: int) -> Tuple[int, int]:
        "for PIL paste"
        return (
            int(self.left.to_px(dpi).n),
            int(self.top.to_px(dpi).n),
        )

    def size(self) -> Dim:
        return Dim(self.right - self.left, self.bottom - self.top)

    def shrink(self, ratio: float, dpi: int):
        "return a copy shrunk by ratio"
        dim = self.size() * ratio
        image = self.image and self.image.resize(dim.to_px(dpi).tuple())
        return dataclasses.replace(self, right=self.left + dim.width, bottom=self.top + dim.height, image=image)

    def box(self, dpi: int) -> Tuple[int, int, int, int]:
        "return LTRB PIL box for paste()"
        # 'left upper right lower' per this:
        # https://pillow.readthedocs.io/en/stable/reference/Image.html?highlight=box#PIL.Image.Image.crop
        return (
            int(self.left.to_px(dpi).n),
            int(self.top.to_px(dpi).n),
            int(self.right.to_px(dpi).n),
            int(self.bottom.to_px(dpi).n),
        )

    def format(self) -> str:
        return f'topleft: {(self.top, self.left)}, dim: {(self.right - self.left), (self.bottom - self.top)}, image size: {self.image and self.image.size}, source: {self.source and self.source.__class__.__name__}'

def render_instructions(im: Image.Image, ilist: List[Instruction], dpi: int):
    "render instructions onto image. get instruction list from .compute() method on your outermost Layout object"
    for inst in ilist:
        if inst.image:
            im.paste(inst.image, box=inst.topleft(dpi))
    return im

def ilist_height(ilist: List[Optional[Instruction]]):
    "height of an instruction list. list members are nullable because of how flex works"
    return max(inst.bottom for inst in ilist if inst) - min(inst.top for inst in ilist if inst)

def ilist_width(ilist: List[Optional[Instruction]]):
    "width of an instruction list"
    return max(inst.right for inst in ilist if inst) - min(inst.left for inst in ilist if inst)

def ilist_dim(direction: Direction):
    return ilist_width if is_horz(direction) else ilist_height

def sum_dim(ilist_list: List[List[Instruction]], direction: Direction) -> Dim:
    "sums sizes of sublists. returns a dim with only one axis, aka a directional length"
    dim_func = ilist_dim(direction)
    dim = sum((dim_func(sublist) for sublist in ilist_list if sublist), Unit.zero())
    return Dim(width=dim) if is_horz(direction) else Dim(height=dim)

def apply_offsets(ilist_list: List[List[Instruction]], direction: Direction, space: Unit) -> List[List[Instruction]]:
    "layout things sequentially rather than on top of each other"
    total_size = Unit.zero()
    dim_func = ilist_dim(direction)
    ret = []
    for i, ilist in enumerate(ilist_list):
        offset = total_size + space * i
        ret.append([inst.offset(offset, direction) for inst in ilist])
        total_size += dim_func(ilist)
    return ret

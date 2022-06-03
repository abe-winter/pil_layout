import logging, dataclasses
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from .base import Layout
from .units import Dim, Unit, Direction, is_horz

logger = logging.getLogger(__name__)

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
        "2-dimensional offset"
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

class Ilist(list):
    "list of Optional[Instruction] with some helper methods"

    @classmethod
    def concat(cls, ilist_list: List['Ilist']) -> 'Ilist':
        "factory. concat sublists into a single Ilist"
        ret = cls()
        for ilist in ilist_list:
            ret.extend(ilist)
        return ret

    def render(self, im: Image.Image, dpi: int):
        "render instructions onto image. get instruction list from .compute() method on your outermost Layout object"
        for inst in self:
            if inst.image:
                im.paste(inst.image, box=inst.topleft(dpi))
        return im

    def height(self) -> Unit:
        "height of an instruction list. list members are nullable because of how flex works"
        return max(inst.bottom for inst in self if inst) - min(inst.top for inst in self if inst)

    def width(self) -> Unit:
        "width of an instruction list"
        return max(inst.right for inst in self if inst) - min(inst.left for inst in self if inst)

    def dim(self, direction: Direction) -> Unit:
        return self.width() if is_horz(direction) else self.height()

    def offset(self, offset: Unit, direction: Direction) -> 'Ilist':
        "apply offset to all items. requires all non-null I think"
        return Ilist(inst.offset(offset, direction) for inst in self)

    def align(self, direction: Direction, container: Dim, middle: bool = True) -> 'Ilist':
        "align at middle/end of space on H or V axis, by offseting it. middle=False means end"
        offset = (container.getdir(direction) - self.dim(direction)) / (2 if middle else 1)
        logger.debug('aligning middle=%s dir=%s container=%s offset=%s', middle, direction, container, offset)
        return self.offset(offset, direction) if offset.n > 0 else self

def sum_dim(ilist_list: List[Ilist], direction: Direction) -> Dim:
    "sums sizes of sublists. returns a dim with only one axis, aka a directional length"
    dim = sum((ilist.dim(direction) for ilist in ilist_list if ilist), Unit.zero())
    return Dim(width=dim) if is_horz(direction) else Dim(height=dim)

def apply_offsets(ilist_list: List[Ilist], direction: Direction, space: Unit) -> List[Ilist]:
    "layout things sequentially rather than on top of each other"
    total_size = Unit.zero()
    ret = []
    for i, ilist in enumerate(ilist_list):
        offset = total_size + space * i
        ret.append(ilist.offset(offset, direction))
        total_size += ilist.dim(direction)
    return ret

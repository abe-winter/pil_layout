import logging
from dataclasses import dataclass
from typing import List, Tuple
from .base import Layout
from .units import Direction, Dim, Unit
from .common import LayoutError, partition
from .renderable import Box
from .instruction import sum_dim, apply_offsets, Instruction, Ilist

logger = logging.getLogger(__name__)

@dataclass
class Axis(Layout):
    "base class"
    direction: Direction
    children: List[Layout]
    expand: bool = False

    def space_ilists(self, dim: Dim, dpi: int, ilist_list: List[Ilist]) -> Tuple[Unit, List[Ilist]]:
        "complex mix of offset spacing (when too narrow) and shrink to fit (when too wide). split out some logic"
        if len(ilist_list) < 2:
            return Unit.zero(), ilist_list
        axis_dim = dim.getdir(self.direction)
        if axis_dim is None:
            return Unit.zero(), ilist_list
        total_dim = sum_dim(ilist_list, self.direction).getdir(self.direction)

        if total_dim > axis_dim or self.expand:
            # todo: I think this double-resizes images. postpone reesizing images until render stage
            shrinkable, fixed = split_shrinkable(self.children)
            shrinkable_dim = sum_dim((ilist_list[i] for i, _ in shrinkable), self.direction).getdir(self.direction)
            fixed_dim = sum_dim((ilist_list[i] for i, _ in fixed), self.direction).getdir(self.direction)
            logger.debug('shrinkable %d %s, fixed %d %s', len(shrinkable), shrinkable_dim, len(fixed), fixed_dim)
            if shrinkable_dim.n == 0:
                logger.debug('no shrinkable elements or zero-size, using default logic which will overlap')
            else:
                fixed_indices = [i for i, _ in fixed]
                ratio = (axis_dim - fixed_dim) / shrinkable_dim
                logger.debug('shrink ratio %s from %s = %s + %s', ratio, total_dim, shrinkable_dim, fixed_dim)
                # todo: don't shrink is_spacer boxes; but the math works out anyway
                ilist_list = [
                    # wow this is way too complicated
                    ilist if i in fixed_indices else Ilist(inst.shrink(ratio, dpi) for inst in ilist)
                    for i, ilist in enumerate(ilist_list)
                ]
                total_dim = sum_dim(ilist_list, self.direction).getdir(self.direction)
        # note: extra_space can be negative; the math still works, objs will overlap
        # todo: fit params to shrink to fit
        # todo: space_between in here, support in all children as well maybe
        extra_space = axis_dim - total_dim
        logger.debug('axis extra_space %s', extra_space)
        return extra_space / (len(ilist_list) - 1), ilist_list

    def compute(self, dim: Dim, dpi: int):
        subdim = dim.partial(self.direction)
        ilist_list = [x.compute(subdim, dpi) for x in self.children]
        between_space, ilist_list = self.space_ilists(dim, dpi, ilist_list)
        offset_children = apply_offsets(ilist_list, self.direction, between_space)
        return Ilist.concat(offset_children)

@dataclass
class Flex(Axis):
    expand: List[bool] # same length as children; alternatively make this just the index of the expanding elt
    # todo: min_size for each section

    def render_flex(self, dim: Dim, dpi):
        "helper for compute"
        if (nexpand := sum(self.expand)) != 1:
            raise LayoutError(f"flex must have exactly one expand child, got {nexpand}")
        if len(self.expand) != len(self.children):
            raise LayoutError(f"len(expand) != len(children) in flex. {len(self.expand)} != {len(self.children)}")

        # render non-expand elements
        # todo: think about clearer rules for whether a thing takes its size from main or cross axis
        subdim = dim.partial(self.direction)
        ilist_list = [
            [] if expand else child.compute(subdim, dpi)
            for expand, child in zip(self.expand, self.children)
        ]

        # compute flex area
        remainder = dim.getdir(self.direction) - sum_dim(ilist_list, self.direction).getdir(self.direction)
        if remainder.n < 0:
            # note: negative size crashes ImageRenderable
            logger.debug('warning: flex remainder < 0, %s', remainder)
        flex_area = dim.partial(self.direction, remainder)
        logger.debug('flex_area %s', flex_area)

        # compute the expanded element
        i_expand = self.expand.index(True)
        # note: from_dim instruction is so axis stretches right
        ilist_list[i_expand] = Ilist(self.children[i_expand].compute(flex_area, dpi) + [Instruction.from_dim(flex_area, source=self.source())])
        return flex_area, ilist_list

    def compute(self, dim: Dim, dpi: int):
        _, ilist_list = self.render_flex(dim, dpi)
        between_space, ilist_list = self.space_ilists(dim, dpi, ilist_list)
        offset_children = apply_offsets(ilist_list, self.direction, between_space)
        return Ilist.concat(offset_children)

def split_shrinkable(children: List[Layout]) -> Tuple[List[Tuple[int, Layout]], List[Tuple[int, Layout]]]:
    "return tuple of lists of (index, Layout) pair; lists are (shrinkable, fixed)"
    return partition(
        enumerate(children),
        lambda pair: isinstance(pair[1], Box) and pair[1].is_spacer,
    )

import pytest
from pil_layout import Axis, Instruction, Unit, Box, Dim, Flex, Unit
from . import base

def test_axis():
    "exercise Axis layout"
    layout = Axis('horz', [Box.inch(1, is_spacer=False), Box.inch(1, is_spacer=False)])
    # zero space case
    assert layout.compute(Dim.inch(2, 1), dpi=1) == [
        Instruction.tlbr(0, 0, 1, 1),
        Instruction.tlbr(0, 1, 1, 2),
    ]
    # shrink height, space between
    assert layout.compute(Dim.inch(2, 0.5), dpi=1) == [
        Instruction.tlbr(0, 0, 0.5, 0.5),
        Instruction.tlbr(0, 1.5, 0.5, 2),
    ]
    # total overlap
    assert layout.compute(Dim.inch(2, 2), dpi=1) == [
        Instruction.tlbr(0, 0, 1, 1),
        Instruction.tlbr(0, 1, 1, 2),
    ]
    # partial overlap
    assert layout.compute(Dim.inch(3, 2), dpi=1) == [
        Instruction.tlbr(0, 0, 1, 1),
        Instruction.tlbr(0, 2, 1, 3),
    ]

    layout = Axis('vert', [Box.inch(1, is_spacer=False), Box.inch(1, is_spacer=False)])
    assert layout.compute(Dim.inch(1, 2), dpi=1) == [
        Instruction.tlbr(0, 0, 1, 1),
        Instruction.tlbr(1, 0, 2, 1),
    ]
    assert layout.compute(Dim.inch(0.5, 2), dpi=1) == [
        Instruction.tlbr(0, 0, 0.5, 0.5),
        Instruction.tlbr(1.5, 0, 2, 0.5),
    ]
    assert layout.compute(Dim.inch(1, 3), dpi=1) == [
        Instruction.tlbr(0, 0, 1, 1),
        Instruction.tlbr(2, 0, 3, 1),
    ]
    assert layout.compute(Dim.inch(1, 1.5), dpi=1) == [
        Instruction.tlbr(0, 0, 0.75, 0.75),
        Instruction.tlbr(0.75, 0, 1.5, 0.75),
    ]

def test_flex():
    # todo: also test horizontal layout
    layout = Flex('vert', [Box(Unit.inch(1), Unit.inch(1))] * 3, [False, True, False])

    # perfect fit
    flex_area, ilist = layout.render_flex(Dim.inch(1, 3), None)
    assert flex_area == Dim.inch(1, 1)
    assert ilist[1][0] == Instruction.from_dim(Dim.inch(1, 1))
    assert len(ilist) == 3

    # extra space
    flex_area, ilist = layout.render_flex(Dim.inch(1, 4), None)
    assert flex_area == Dim.inch(1, 2)
    assert ilist[1][0] == Instruction.from_dim(Dim.inch(1, 1))

    # less space
    flex_area, ilist = layout.render_flex(Dim.inch(1, 2.5), None)
    assert flex_area == Dim.inch(1, 0.5)
    assert ilist[1][0] == Instruction.from_dim(Dim.inch(0.5, 0.5))

    # shrunk cross axis
    flex_area, ilist = layout.render_flex(Dim.inch(0.5, 2), None)
    assert flex_area == Dim.inch(0.5, 1)
    assert ilist[1][0] == Instruction.from_dim(Dim.inch(0.5, 0.5))

@pytest.mark.skip
def test_axis_shrink():
    raise NotImplementedError

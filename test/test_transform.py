from pil_layout import Dim, AspectRatio, Box, Unit, Padding, Instruction
from . import base

def test_aspect_ratio():
    dpi = 10
    args = (Dim.inch(2, 2), dpi)

    # halign
    layout = AspectRatio(height_over_width=0.5, child=Box.inch(1))
    assert layout.compute(*args)[0].box(dpi) == (0, 0, 10, 10)
    layout = AspectRatio(height_over_width=0.5, child=Box.inch(1), halign='middle')
    assert layout.compute(*args)[0].box(dpi) == (5, 0, 15, 10)
    layout = AspectRatio(height_over_width=0.5, child=Box.inch(1), halign='end')
    assert layout.compute(*args)[0].box(dpi) == (10, 0, 20, 10)

    # valign
    layout = AspectRatio(height_over_width=2, child=Box.inch(1))
    assert layout.compute(*args)[0].box(dpi) == (0, 0, 10, 10)
    layout = AspectRatio(height_over_width=2, child=Box.inch(1), valign='middle')
    assert layout.compute(*args)[0].box(dpi) == (0, 5, 10, 15)
    layout = AspectRatio(height_over_width=2, child=Box.inch(1), valign='end')
    assert layout.compute(*args)[0].box(dpi) == (0, 10, 10, 20)

    # shrink
    layout = AspectRatio(height_over_width=2, child=Box.inch(2))
    assert layout.compute(*args)[0].box(dpi) == (0, 0, 10, 10)

def test_padding():
    layout = Padding(Box.inch(1), Unit.inch(0.5))
    assert layout.compute(Dim.inch(2, 2), 100)[0] == Instruction.tlbr(0.5, 0.5, 1.5, 1.5)

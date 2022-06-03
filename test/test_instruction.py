import pytest
from pil_layout import Instruction, Unit, Dim, Ilist
from pil_layout.instruction import sum_dim
from . import base

def test_ilist_wh():
    ilist = Ilist([
        Instruction(top=Unit.inch(0), left=Unit.inch(0.5), bottom=Unit.inch(1), right=Unit.inch(1), image=''),
        Instruction(top=Unit.inch(2), left=Unit.inch(2), bottom=Unit.inch(1.5), right=Unit.inch(2.5), image=''),
    ])
    assert ilist.width() == Unit.inch(2)
    assert ilist.height() == Unit.inch(1.5)
    assert sum_dim([ilist], 'horz') == Dim(width=Unit.inch(2))
    assert sum_dim([ilist, ilist], 'horz') == Dim(width=Unit.inch(4))
    assert sum_dim([ilist], 'vert') == Dim(height=Unit.inch(1.5))
    assert sum_dim([ilist, ilist], 'vert') == Dim(height=Unit.inch(3))

@pytest.mark.skip
def test_align():
    raise NotImplementedError

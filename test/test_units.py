import pytest
from pil_layout import Unit
from . import base

def test_unit_ops():
    units = [Unit.inch(n) for n in (1, 3, 2, 0)]
    assert min(units).n == 0
    assert max(units).n == 3
    assert (units[1] - units[0]).n == 2
    assert (units[2] - units[1]).n == -1
    assert (units[1] + units[0]).n == 4
    assert (units[2] + units[1]).n == 5
    assert units[0] + Unit.zero() == units[0]
    assert units[1] + Unit.zero() == units[1]
    assert Unit.zero() + Unit.zero() == Unit.zero()
    assert Unit.zero() / Unit.inch(1) == Unit.inch(0)
    assert Unit.inch(1) / Unit.inch(2) == Unit.inch(0.5)
    assert Unit.inch(2) * Unit.inch(2) == Unit.inch(4)
    assert Unit.inch(1) * 4 == Unit.inch(4)
    assert Unit.inch(1).to_px(100) == Unit(100, 'px')

@pytest.mark.skip
def test_dim_ops():
    raise NotImplementedError

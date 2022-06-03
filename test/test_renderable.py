import pytest
from pil_layout import TextRenderable, Unit, Dim
from . import base

def test_text_wrap():
    font = '/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf'
    textr = TextRenderable("I caught a tremendous fish and held him beside the boat, half out of water. He didn't fight; he hadn't fought at all.", font, Unit.inch(0.5))
    args = (Dim.inch(8, None), 200)
    _, _, _, strlines = textr.wrap(*args)
    assert strlines == ['I caught a tremendous fish', 'and held him beside the', 'boat, half out of water.', "He didn't fight; he hadn't", 'fought at all.']
    inst, = textr.compute(*args)
    # rounding here bc I'm not sure this will be consistent across machines, approximate is good enough
    assert (round(inst.image.width / 10), round(inst.image.height / 10)) == (156, 52)
    # toggle this on to inspect ye image
    # inst.image.save(open('tmp.png', 'wb'), 'png')

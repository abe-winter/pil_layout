import logging
from dataclasses import dataclass
from typing import List
from PIL import Image, ImageDraw, ImageFont
from .base import Layout
from .units import Dim, Unit
from .instruction import Instruction

logger = logging.getLogger(__name__)

class Renderable(Layout):
    "base class"

    @staticmethod
    def scaled_dim(size: Dim, container: Dim, can_expand: bool = True) -> Dim:
        "return scaled size (fits container, maintains aspect ratio)"
        # todo: rule about whether it's allowed to expand
        if container.width is None and container.height is None:
            return size
        elif container.width is None:
            ratio = container.height / size.height
        elif container.height is None:
            ratio = container.width / size.width
        else:
            ratio = min(container.width / size.width, container.height / size.height)
        if not can_expand:
            ratio = min(ratio, Unit.inch(1, size.unit()))
        return size * ratio

@dataclass
class Box(Renderable):
    "an inivisible box but with size"
    width: Unit
    height: Unit
    can_expand: bool = False
    is_spacer: bool = True # prevents Axis from shrinking it

    def dim(self) -> Dim:
        "return 'native size' (unscaled)"
        return Dim(width=self.width, height=self.height)

    def compute(self, dim: Dim, dpi: int) -> List['Instruction']:
        return [Instruction.from_dim(self.scaled_dim(self.dim(), dim, self.can_expand), source=self.source())]

    @classmethod
    def inch(cls, width, height=None, unit='in', is_spacer: bool = True):
        "factory. if height omitted, make a square"
        return cls(width=Unit.inch(width, unit), height=Unit.inch(width if height is None else height, unit), is_spacer=is_spacer)

@dataclass
class ImageRenderable(Renderable):
    image: Image.Image
    # todo: consider giving these their own DPI, or reading it from the image.info

    def dim(self, dpi: int) -> Dim:
        "return as inches"
        return Dim.inch(self.image.width, self.image.height, unit='px').to_in(dpi)

    def compute(self, dim: Dim, dpi: int) -> List['Instruction']:
        scaled = self.scaled_dim(self.dim(dpi), dim)
        scaled_px = scaled.to_px(dpi)
        return [Instruction.from_dim(scaled, self.image.resize(scaled_px.tuple()), source=self.source())]

@dataclass
class Line:
    "helper for TextRenderable"
    words: List[str]
    total: int = 0

    def add(self, width, word):
        self.total += width
        self.words.append(word)

@dataclass
class TextRenderable(Renderable):
    text: str
    font: str
    size: Unit # font size, not bbox

    def wrap(self, dim: Dim, dpi):
        "helper for compute. broken out so test suite can hit it"
        # todo: respect existing newlines
        # todo: trace timing here
        # todo: support RTL text
        font = ImageFont.truetype(self.font, int(self.size.to_px(dpi).n))
        im = Image.new('RGBA', dim.to_px(dpi).tuple())
        draw = ImageDraw.Draw(im)
        if draw.textlength(self.text, font) > im.width:
            # wrapping logic
            words = self.text.split()
            space = draw.textlength(' ', font)
            widths = [draw.textlength(word, font) for word in words]
            lines: List[Line] = [Line([])]
            for word, width in zip(words, widths):
                if width > im.width:
                    logger.warning('word is wider than line %s %s', width, im.width)
                if lines[-1].total + len(lines[-1].words) * space + width > im.width:
                    lines.append(Line([]))
                lines[-1].add(width, word)
            strlines = [' '.join(line.words) for line in lines if line.words]
        else:
            strlines = [self.text]
        return font, im, draw, strlines

    def compute(self, dim: Dim, dpi: int):
        "render text, including wrap"
        font, im, draw, strlines = self.wrap(dim, dpi)
        multiline = '\n'.join(strlines)
        interline = int(self.size.to_px(dpi).n / 8)
        draw.multiline_text((0, 0), multiline, fill='black', font=font, spacing=interline)
        box = draw.multiline_textbbox((0, 0), multiline, font, spacing=interline)
        im = im.crop(box)
        return [Instruction.from_dim(Dim.inch(im.width, im.height, 'px').to_in(dpi), im, source=self.source())]

"""Generate ASCII shadow banners as .txt and gradient .svg."""

import argparse
from html import escape
from pathlib import Path

import pyfiglet
from PIL import Image, ImageDraw, ImageFont

CHAR_WIDTH = 7.25
LINE_HEIGHT = 16
PADDING = 20
DEFAULT_COLORS = ["#007cf0", "#7b2ff7", "#ff0080"]
CELL_RATIO = LINE_HEIGHT / CHAR_WIDTH
STROKE = 6
FONT_SIZE = 200


def render_text(text: str, font: str = "dos_rebel", chevron: bool = True) -> str:
    art = pyfiglet.figlet_format((">" if chevron else "") + text, font=font, width=10_000)
    return pad_lines(art.splitlines())


def render_bitmap(text: str, rows: int, chevron: bool = True) -> str:
    """Rasterize text on rows lines, shadow cast down-left like dos_rebel."""
    font = ImageFont.load_default(size=FONT_SIZE)
    text = (">" if chevron else "") + text
    gap = 3 * STROKE
    image = Image.new("L", (round(font.getlength(text)) + gap * len(text), 2 * FONT_SIZE))
    draw = ImageDraw.Draw(image)
    x = STROKE
    for char in text:
        draw.text((x, FONT_SIZE // 2), char, font=font, fill=255, stroke_width=STROKE, stroke_fill=255)
        x += font.getlength(char) + gap
    image = image.crop(image.getbbox())
    cols = round(image.width * rows * CELL_RATIO / image.height)
    image = image.resize((cols, rows), Image.Resampling.LANCZOS)
    filled = [[image.getpixel((x, y)) > 127 for x in range(cols)] for y in range(rows)]

    def is_filled(y: int, x: int) -> bool:
        return 0 <= y < rows and 0 <= x < cols and filled[y][x]

    lines = [
        "".join("█" if is_filled(y, x - 1) else "░" if is_filled(y - 1, x) else " " for x in range(cols + 1))
        for y in range(rows + 1)
    ]
    return pad_lines(lines)


def pad_lines(lines: list[str]) -> str:
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()
    width = max(map(len, lines))
    return "\n".join(line.ljust(width) for line in lines) + "\n"


def render_svg(art: str, colors: list[str], display_width: int | None = None) -> str:
    lines = art.splitlines()
    width = round(max(map(len, lines)) * CHAR_WIDTH) + PADDING
    height = len(lines) * LINE_HEIGHT + PADDING // 2
    display_width = display_width or width
    display_height = round(height * display_width / width)
    last = max(len(colors) - 1, 1)
    stops = "\n".join(
        f'      <stop offset="{i * 100 // last}%" stop-color="{escape(c)}" />' for i, c in enumerate(colors)
    )
    tspans = "\n".join(
        f'    <tspan x="50%" y="{(i + 1) * LINE_HEIGHT + 4}">{escape(line)}</tspan>' for i, line in enumerate(lines)
    )
    return f"""<svg width="{display_width}" height="{display_height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
{stops}
    </linearGradient>
  </defs>
  <style>
    .ascii {{
      font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace;
      font-size: 12px;
      fill: url(#grad);
      white-space: pre;
    }}
  </style>
  <text x="50%" text-anchor="middle" class="ascii">
{tspans}
  </text>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn text into a shadowed ASCII banner (.txt and .svg).")
    parser.add_argument("text")
    parser.add_argument("-o", "--out", type=Path, default=Path("."), help="output directory")
    parser.add_argument("-n", "--name", default="banner", help="output file name without extension")
    parser.add_argument("-c", "--colors", nargs="+", default=DEFAULT_COLORS, help="gradient colors")
    parser.add_argument("-f", "--font", default="dos_rebel", help="figlet font")
    parser.add_argument("-r", "--rows", type=int, help="text height in lines, replaces the figlet font")
    parser.add_argument("-w", "--width", type=int, help="svg width in pixels")
    parser.add_argument("--no-chevron", action="store_true", help="remove the leading >")
    args = parser.parse_args()
    if not args.text.strip():
        parser.error("text must not be empty")
    if args.rows is not None and args.rows < 2:
        parser.error("--rows must be at least 2")
    if args.width is not None and args.width < 1:
        parser.error("--width must be positive")

    text, chevron = args.text.upper(), not args.no_chevron
    art = render_bitmap(text, args.rows, chevron) if args.rows else render_text(text, args.font, chevron)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.name}.txt").write_text(art, encoding="utf-8")
    (args.out / f"{args.name}.svg").write_text(render_svg(art, args.colors, args.width), encoding="utf-8")
    print(art, end="")


if __name__ == "__main__":
    main()

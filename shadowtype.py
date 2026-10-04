"""Generate ASCII shadow banners as .txt and gradient .svg."""

import argparse
from html import escape
from pathlib import Path

import pyfiglet
from PIL import Image, ImageDraw, ImageFont

CHAR_WIDTH = 7.25
LINE_HEIGHT = 16
PADDING = 20
PALETTES = {
    "stratos": ["#007cf0", "#7b2ff7", "#ff0080"],
    "aurora": ["#00f5a0", "#00d9f5", "#7b2ff7"],
    "sunset": ["#ff512f", "#f09819", "#ffd200"],
    "fire": ["#ff0000", "#ff7a00", "#ffd000"],
    "candy": ["#ff6ec4", "#7873f5", "#4adede"],
    "rainbow": ["#ff0040", "#ff8c00", "#ffe600", "#00d26a", "#00a3ff", "#8a2be2"],
    "vaporwave": ["#ff71ce", "#01cdfe", "#05ffa1", "#b967ff"],
    "ocean": ["#00c6ff", "#0072ff"],
    "forest": ["#a8e063", "#56ab2f"],
    "peach": ["#ffb88c", "#de6262"],
    "ice": ["#e0f7ff", "#5ab4ff"],
    "gold": ["#f7e27b", "#c79a2c"],
    "midnight": ["#8e9eab", "#2c3e50"],
    "matrix": ["#00ff41"],
    "amber": ["#ffb000"],
    "ruby": ["#e0115f"],
    "snow": ["#f0f0f0"],
    "graphite": ["#6e7681"],
}
DIRECTIONS = {"horizontal": (100, 0), "vertical": (0, 100), "diagonal": (100, 100)}
CELL_RATIO = LINE_HEIGHT / CHAR_WIDTH
STROKE = 6
FONT_SIZE = 200


def render_text(text: str, font: str = "dos_rebel") -> str:
    return pad_lines(pyfiglet.figlet_format(text, font=font, width=10_000).splitlines())


def render_bitmap(text: str, rows: int, ttf: Path | None = None) -> str:
    """Draw text with a TrueType font, then rasterize it."""
    font = ImageFont.truetype(ttf, FONT_SIZE) if ttf else ImageFont.load_default(size=FONT_SIZE)
    stroke = 0 if ttf else STROKE
    gap = 3 * STROKE
    image = Image.new("L", (round(font.getlength(text)) + gap * len(text), 2 * FONT_SIZE))
    draw = ImageDraw.Draw(image)
    x = STROKE
    for char in text:
        draw.text((x, FONT_SIZE // 2), char, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
        x += font.getlength(char) + gap
    return rasterize(image.crop(image.getbbox()), rows)


def render_chevron(rows: int) -> str:
    """Draw a geometric > so it matches any font."""
    width, height = FONT_SIZE // 2, FONT_SIZE
    thickness = width // 3
    image = Image.new("L", (width, height))
    ImageDraw.Draw(image).polygon(
        [
            (0, 0),
            (thickness, 0),
            (width, height // 2),
            (thickness, height),
            (0, height),
            (width - thickness, height // 2),
        ],
        fill=255,
    )
    return rasterize(image, rows)


def rasterize(image: Image.Image, rows: int) -> str:
    """Scale image to rows lines, shadow cast down-left like dos_rebel."""
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


def join_art(left: str, right: str, gap: int) -> str:
    left_lines, right_lines = left.splitlines(), right.splitlines()
    height = max(len(left_lines), len(right_lines))
    left_lines += [""] * (height - len(left_lines))
    right_lines += [""] * (height - len(right_lines))
    width = max(map(len, left_lines)) + gap
    return pad_lines([a.ljust(width) + b for a, b in zip(left_lines, right_lines)])


def pad_lines(lines: list[str]) -> str:
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()
    width = max(map(len, lines))
    return "\n".join(line.ljust(width) for line in lines) + "\n"


def render_svg(art: str, colors: list[str], display_width: int | None = None, direction: str = "horizontal") -> str:
    lines = art.splitlines()
    width = round(max(map(len, lines)) * CHAR_WIDTH) + PADDING
    height = len(lines) * LINE_HEIGHT + PADDING // 2
    display_width = display_width or width
    display_height = round(height * display_width / width)
    x2, y2 = DIRECTIONS[direction]
    last = max(len(colors) - 1, 1)
    stops = "\n".join(
        f'      <stop offset="{i * 100 // last}%" stop-color="{escape(c)}" />' for i, c in enumerate(colors)
    )
    tspans = "\n".join(
        f'    <tspan x="50%" y="{(i + 1) * LINE_HEIGHT + 4}">{escape(line)}</tspan>' for i, line in enumerate(lines)
    )
    return f"""<svg width="{display_width}" height="{display_height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="{x2}%" y2="{y2}%">
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
    parser.add_argument("-c", "--colors", nargs="+", help="one color for solid, two or more for a gradient")
    parser.add_argument("-p", "--palette", choices=PALETTES, default="stratos", help="preset colors, ignored with -c")
    parser.add_argument("-d", "--direction", choices=DIRECTIONS, default="horizontal", help="gradient direction")
    parser.add_argument("-f", "--font", default="dos_rebel", help="figlet font")
    parser.add_argument("-r", "--rows", type=int, help="text height in lines, replaces the figlet font")
    parser.add_argument("-t", "--ttf", type=Path, help="TrueType font file used with --rows")
    parser.add_argument("-g", "--gap", type=int, default=3, help="spaces between the chevron and the text")
    parser.add_argument("-w", "--width", type=int, help="svg width in pixels")
    parser.add_argument("--no-chevron", action="store_true", help="remove the leading >")
    args = parser.parse_args()
    if not args.text.strip():
        parser.error("text must not be empty")
    if args.rows is not None and args.rows < 2:
        parser.error("--rows must be at least 2")
    if args.ttf and not args.rows:
        parser.error("--ttf requires --rows")
    if args.ttf and not args.ttf.is_file():
        parser.error(f"font file not found: {args.ttf}")
    if args.gap < 0:
        parser.error("--gap must not be negative")
    if args.width is not None and args.width < 1:
        parser.error("--width must be positive")

    def render(text: str) -> str:
        return render_bitmap(text, args.rows, args.ttf) if args.rows else render_text(text, args.font)

    art = render(args.text.upper())
    if not args.no_chevron:
        chevron = render_chevron(args.rows) if args.rows else render_text(">", args.font)
        art = join_art(chevron, art, args.gap)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.name}.txt").write_text(art, encoding="utf-8")
    (args.out / f"{args.name}.svg").write_text(
        render_svg(art, args.colors or PALETTES[args.palette], args.width, args.direction), encoding="utf-8"
    )
    print(art, end="")


if __name__ == "__main__":
    main()

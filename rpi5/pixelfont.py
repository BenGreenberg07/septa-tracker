"""A 5x7 LED pixel font for the board's small text, as a Pillow bitmap font.

Antialiased TrueType at 9 px smears on an LED panel: every stroke edge becomes
a half-lit LED, and at that size half the strokes are edges. A 5x7 matrix font
is what real departure boards use because each stroke is either a lit LED or a
dark one. Uppercase only, as on those boards; lowercase is drawn in capitals.

The glyphs are drawn below as text so they can be read and edited here. At
import they are written out as a BDF font, compiled by Pillow into its own
bitmap format in a temp directory, and loaded, so the result is an ordinary
ImageFont that draw.text() and draw.textlength() accept like any other.

    import pixelfont
    FONT = pixelfont.load()
    draw.text((x, y), "3 STOPS", font=FONT, fill=CYAN)

Text drawn at y occupies rows y+2 to y+8, the same rows as the capitals of the
9 px DejaVu it replaces, so layouts built around that font need no changes.
"""

import hashlib
import io
import os
import tempfile

from PIL import BdfFontFile, ImageFont

ADVANCE = 6         # 5 columns of glyph and 1 of space
SPACE_ADVANCE = 4   # a word gap need not be a full cell
TOP = 2             # empty rows above the glyph, to match the old 9 px font

GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    ";": [".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "/": [".....", "....#", "...#.", "..#..", ".#...", "#....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "[": [".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."],
    "]": [".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    '"': [".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "#": [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    "%": ["##...", "##..#", "...#.", "..#..", ".#...", "#..##", "...##"],
    "*": [".....", "..#..", "#.#.#", ".###.", "#.#.#", "..#..", "....."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    "@": [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    "$": ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    "<": ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    ">": [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
}

# Latin-1 look-alikes drawn with an existing glyph. Text outside Latin-1
# (curly quotes, dashes) should be folded to ASCII before it gets here; see
# clean_alert() in the board script.
ALIASES = {"\xa0": " ", "\xb7": "."}


def _bdf():
    chars = {}
    for ch, rows in GLYPHS.items():
        chars[ord(ch)] = rows
        if ch.isalpha():
            chars[ord(ch.lower())] = rows
    for ch, same in ALIASES.items():
        chars[ord(ch)] = GLYPHS[same]

    height = TOP + 7
    out = [
        "STARTFONT 2.1",
        "FONT -septa-led-medium-r-normal--9-90-75-75-c-60-iso8859-1",
        "SIZE 9 75 75",
        f"FONTBOUNDINGBOX 5 {height} 0 0",
        "STARTPROPERTIES 2",
        f"FONT_ASCENT {height}",
        "FONT_DESCENT 0",
        "ENDPROPERTIES",
        f"CHARS {len(chars)}",
    ]
    for code in sorted(chars):
        rows = chars[code]
        advance = SPACE_ADVANCE if code in (0x20, 0xA0) else ADVANCE
        out += [
            f"STARTCHAR U+{code:04X}",
            f"ENCODING {code}",
            f"SWIDTH {advance * 1000 // 9} 0",
            f"DWIDTH {advance} 0",
            f"BBX 5 {height} 0 0",
            "BITMAP",
        ]
        # Each row left-aligned in one byte: "#.#.." is 0b10100000. The blank
        # rows on top are part of the bitmap because Pillow normalises a
        # BBX offset away when it compiles the font.
        out += [f"{int(r.replace('#', '1').replace('.', '0') + '000', 2):02X}"
                for r in ["....."] * TOP + rows]
        out.append("ENDCHAR")
    out.append("ENDFONT")
    return ("\n".join(out) + "\n").encode("ascii")


def load():
    """The font, compiled on first use into a temp directory and reused after."""
    data = _bdf()
    tag = hashlib.sha1(data).hexdigest()[:10]
    base = os.path.join(tempfile.gettempdir(), f"septa-led5x7-{tag}")
    if not (os.path.exists(base + ".pil") and os.path.exists(base + ".pbm")):
        BdfFontFile.BdfFontFile(io.BytesIO(data)).save(base)
    return ImageFont.load(base + ".pil")

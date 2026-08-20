#!/usr/bin/env python3
"""
Turn avatar.png into the ASCII portrait in art.txt.

    pip install pillow
    python3 asciify.py            # then re-run generate.py

Swap in a different avatar.png and re-run. Photos with a clean, evenly lit
background convert best: the background is removed by flood-filling inward
from the border, so anything that background touches gets dropped too.
"""
from collections import deque
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

COLS   = 56      # width of the art, in characters
ASPECT = 0.50    # character cell width / height
CROP   = 0.10    # fraction trimmed off each edge (drops the avatar's ring)
RAMP   = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def load(path="avatar.png", crop=CROP):
    im = Image.open(path).convert("RGBA")
    im = Image.alpha_composite(Image.new("RGBA", im.size, "white"), im).convert("RGB")
    w, h = im.size
    c = int(w * crop)
    return im.crop((c, c, w - c, h - c))


def background(im, sat_max=42, v_min=135):
    """Flood-fill from the border. Background = light, low-saturation pixels."""
    w, h = im.size
    px = im.load()

    def is_bg(x, y):
        r, g, b = px[x, y]
        return max(r, g, b) - min(r, g, b) <= sat_max and max(r, g, b) >= v_min

    seen, q = bytearray(w * h), deque()
    border = [(x, y) for x in range(w) for y in (0, h - 1)]
    border += [(x, y) for y in range(h) for x in (0, w - 1)]
    for x, y in border:
        if is_bg(x, y) and not seen[y * w + x]:
            seen[y * w + x] = 1
            q.append((x, y))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_bg(nx, ny):
                seen[ny * w + nx] = 1
                q.append((nx, ny))
    return Image.frombytes("L", (w, h), bytes(255 if v else 0 for v in seen))


def subject(im, mask, black=0.05, white=0.95, gamma=1.3, contrast=1.5):
    g = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    b, w_ = black * 255, white * 255
    g = g.point([min(255, max(0, int((min(1.0, max(0.0, (i - b) / (w_ - b))) ** gamma) * 255)))
                 for i in range(256)])
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = g.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=2))
    g.paste(Image.new("L", g.size, 255), (0, 0), mask)      # background -> blank
    circle = Image.new("L", g.size, 0)                       # trim stray ring pixels
    ImageDraw.Draw(circle).ellipse((g.size[0] * 0.015, g.size[1] * 0.015,
                                    g.size[0] * 0.985, g.size[1] * 0.985), fill=255)
    out = Image.new("L", g.size, 255)
    out.paste(g, (0, 0), circle)
    return out


def to_ascii(g, cols=COLS, aspect=ASPECT):
    w, h = g.size
    rows = max(1, round(cols * (h / w) * aspect))
    px = g.resize((cols, rows), Image.LANCZOS).load()
    n = len(RAMP) - 1
    return [("".join(RAMP[round(((255 - px[x, y]) / 255) * n) ] for x in range(cols))).rstrip()
            for y in range(rows)]


if __name__ == "__main__":
    im = load()
    art = to_ascii(subject(im, background(im)))
    with open("art.txt", "w") as f:
        f.write("\n".join(art) + "\n")
    print(f"art.txt: {len(art)} rows x {max(len(l) for l in art)} cols")

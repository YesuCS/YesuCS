#!/usr/bin/env python3
"""
Render dark_mode.svg + light_mode.svg for the GitHub profile README.

Reads:  profile.json  (labels, values, stats)
        art.txt       (pre-rendered ASCII portrait)
Writes: dark_mode.svg, light_mode.svg

Standard library only, so the refresh workflow needs no dependencies.
Re-run asciify.py instead if you change avatar.png.
"""
import json
from datetime import date
from xml.sax.saxutils import escape

FS, CW, LH = 13.0, 7.8, 17.0        # font size, char advance, line height
PAD_X, PAD_Y, GAP = 26.0, 24.0, 4   # outer padding, and art->info gap in chars
VALUE_COL, RULE_W = 31, 58          # value column, separator width
FONT = ("'JetBrains Mono','Fira Code','SFMono-Regular',ui-monospace,"
        "'DejaVu Sans Mono',Menlo,Consolas,monospace")

THEMES = {
    "dark":  dict(panel="#0d1117", border="#30363d", art="#adbac7",
                  user="#7ee787", at="#8b949e", host="#79c0ff", rule="#30363d",
                  label="#a371f7", value="#c9d1d9", num="#7ee787",
                  dim="#484f58", section="#f0883e"),
    "light": dict(panel="#ffffff", border="#d0d7de", art="#424a53",
                  user="#1a7f37", at="#6e7781", host="#0969da", rule="#d0d7de",
                  label="#8250df", value="#1f2328", num="#1a7f37",
                  dim="#afb8c1", section="#bc4c00"),
}


def uptime(since):
    a = date.fromisoformat(since)
    b = date.today()
    y, m, d = b.year - a.year, b.month - a.month, b.day - a.day
    if d < 0:
        m -= 1
        pm, py = (b.month - 1) or 12, b.year if b.month > 1 else b.year - 1
        import calendar
        d += calendar.monthrange(py, pm)[1]
    if m < 0:
        y, m = y - 1, m + 12
    plural = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")
    return ", ".join([plural(y, "year"), plural(m, "month"), plural(d, "day")])


def build_info(cfg):
    """Turn profile.json into rows of (text, colour-key) segments."""
    st, rows = cfg["stats"], []

    def kv(label, value, bullet="- "):
        head = f"{bullet}{label}:"
        dots = "." * max(1, VALUE_COL - len(head) - 2)
        segs = value if isinstance(value, list) else [(value, "value")]
        rows.append([(bullet, "dim"), (label + ":", "label"),
                     (" " + dots + " ", "dim"), *segs])

    rows.append([(cfg["shell_user"], "user"), ("@", "at"), (cfg["user"], "host")])
    rows.append([("-" * RULE_W, "rule")])

    for item in cfg["info"]:
        kind = item[0]
        if kind == "gap":
            rows.append([])
        elif kind == "section":
            rows.append([])
            rows.append([("- ", "dim"), (item[1], "section"),
                         (" " + "-" * max(1, RULE_W - len(item[1]) - 3), "rule")])
        elif kind in ("kv", "kv2"):
            val = uptime(cfg["created_at"]) if item[2] == "@uptime" else item[2]
            kv(item[1], val, bullet="- " if kind == "kv" else "  ")
        elif kind == "stats_repos":
            kv("Repos", [(str(st["repos"]), "num"),
                         ("  |  Stars: ", "dim"), (str(st["stars"]), "num")],
               bullet="  ")
        elif kind == "stats_commits":
            kv("Commits", [(str(st["commits"]), "num"),
                           ("  |  Followers: ", "dim"),
                           (str(st["followers"]), "num")], bullet="  ")
        elif kind == "stats_lang":
            kv("Top language", [(st["top_language"], "value"), ("  (", "dim"),
                                (f'{st["top_language_pct"]}%', "num"),
                                (" of repos)", "dim")], bullet="  ")
    return rows


def seg(x, y, text, fill, bold=False):
    weight = ' font-weight="700"' if bold else ""
    return ('<text x="%.1f" y="%.1f" fill="%s" textLength="%.2f"'
            ' lengthAdjust="spacingAndGlyphs" xml:space="preserve"%s>%s</text>'
            % (x, y, fill, len(text) * CW, weight, escape(text)))


def render(art, info, theme, user, out):
    T = THEMES[theme]
    art_cols = max((len(l) for l in art), default=0)
    info_cols = max((sum(len(t) for t, _ in r) for r in info), default=0)
    n_rows = max(len(art), len(info))
    W = (art_cols + GAP + info_cols) * CW + PAD_X * 2
    H = n_rows * LH + PAD_Y * 2
    info_x = PAD_X + (art_cols + GAP) * CW
    art_y0 = PAD_Y + (n_rows - len(art)) / 2 * LH   # centre the portrait
    base = FS * 0.80

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}"'
         f' height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" role="img"'
         f' aria-label="{user} GitHub profile card">',
         f'<title>{user} - GitHub profile</title>',
         f'<rect x="1" y="1" width="{W - 2:.0f}" height="{H - 2:.0f}" rx="10"'
         f' fill="{T["panel"]}" stroke="{T["border"]}" stroke-width="1.5"/>',
         f'<g font-family="{FONT}" font-size="{FS}"'
         f' dominant-baseline="alphabetic">']

    for i, line in enumerate(art):
        if line.strip():
            p.append(seg(PAD_X, art_y0 + i * LH + base, line, T["art"]))

    for i, row in enumerate(info):
        y, off = PAD_Y + i * LH + base, 0
        for text, key in row:
            if text.strip():
                p.append(seg(info_x + off * CW, y, text, T[key],
                             bold=key in ("user", "host", "section")))
            off += len(text)

    p.append("</g></svg>")
    with open(out, "w") as f:
        f.write("\n".join(p) + "\n")
    return W, H


def main():
    cfg = json.load(open("profile.json"))
    art = open("art.txt").read().split("\n")
    while art and not art[-1].strip():
        art.pop()
    info = build_info(cfg)
    for theme in ("dark", "light"):
        W, H = render(art, info, theme, cfg["user"], f"{theme}_mode.svg")
        print(f"{theme}_mode.svg  {W:.0f}x{H:.0f}")


if __name__ == "__main__":
    main()

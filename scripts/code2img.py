#!/usr/bin/env python3
"""Render blog.md fenced code blocks as purple-terminal PNG images.

Every source snippet in the blog becomes a picture that visually matches the
real-machine Ubuntu terminal screenshots (background #300A24, GNOME terminal
bright-palette syntax colors, monospace). build_blog_html.py swaps the fenced
blocks for these images when producing the single-file blog.html.

Rendering = Pygments token stream (color) + Pillow manual glyph drawing so a
single image can mix ASCII (Noto Sans Mono CJK SC covers both) and the Chinese
comments that appear inside the snippets.
"""
from __future__ import annotations
import hashlib, json, os, re, sys
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.token import Token

BLOG = '/home/zhaosiying/codebase/yushuxin-v2-design/blog-output'
OUTDIR = os.path.join(BLOG, 'codeimg')

FONT_CANDIDATES = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansMonoCJK-Regular.ttc',
]
FONT_SIZE = 26
LINE_HEIGHT = 40
PAD = 28
BG = (48, 10, 36)          # #300A24 — same as the terminal screenshots

# GNOME terminal bright palette on purple.
COLORS = {
    Token.Whitespace:      None,                       # transparent -> bg
    Token.Comment:         (173, 127, 168),            # #AD7FA8 plum
    Token.Keyword:         (252, 233, 79),             # #FCE94F butter
    Token.Keyword.Type:    (252, 233, 79),
    Token.String:          (138, 226, 52),             # #8AE234 chameleon
    Token.String.Affix:    (138, 226, 52),
    Token.Number:          (52, 226, 226),             # #34E2E2 cyan
    Token.Operator:        (238, 238, 236),            # #EEEEEC
    Token.Punctuation:     (238, 238, 236),
    Token.Name.Function:   (114, 159, 207),            # #729FCF sky
    Token.Name.Builtin:    (52, 226, 226),
    Token.Name.Class:      (114, 159, 207),
    Token.Name.Attribute:  (138, 226, 52),
    Token.Name.Tag:        (239, 41, 41),              # #EF2929 scarlet
    Token.Literal:         (138, 226, 52),
    Token.Error:           (239, 41, 41),
}
DEFAULT_FG = (238, 238, 236)                            # #EEEEEC


def load_font() -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        for idx in range(8):
            try:
                f = ImageFont.truetype(path, FONT_SIZE, index=idx)
                name = ' '.join(f.getname())
                if 'Mono' in name and 'SC' in name:
                    return f
            except OSError:
                break
    raise RuntimeError('no Noto Sans Mono CJK SC face found')


FONT = None


def token_color(ttype) -> tuple:
    t = ttype
    while t is not None:
        if t in COLORS:
            c = COLORS[t]
            return c if c else DEFAULT_FG
        t = t.parent
    return DEFAULT_FG


def lexer_for(lang: str):
    lang = (lang or '').strip().lower()
    if lang in ('python', 'py'):
        return get_lexer_by_name('python')
    if lang in ('bash', 'sh', 'shell', 'console'):
        return get_lexer_by_name('bash')
    if lang in ('yaml', 'yml'):
        return get_lexer_by_name('yaml')
    if lang == 'llvm':
        try:
            return get_lexer_by_name('llvm')
        except Exception:
            return TextLexer()
    if lang == 'tablegen':
        try:
            return get_lexer_by_name('cpp')            # closest hue for .td
        except Exception:
            return TextLexer()
    return TextLexer()


def render_block(lang: str, code: str) -> Image.Image:
    """Lex once for colors, draw char-by-char (ASCII advance vs CJK advance)."""
    global FONT
    if FONT is None:
        FONT = load_font()
    w_ascii = FONT.getlength('M')                      # mono advance
    w_cjk = FONT.getlength('中')                       # fullwidth

    lines: list[list[tuple[str, tuple]]] = [[]]        # [(char, color)]
    for ttype, text in lex(code, lexer_for(lang)):
        col = token_color(ttype)
        for ch in text:
            if ch == '\n':
                lines.append([])
                continue
            if ch == '\t':
                ch = '    '
            lines[-1].append((ch, col))

    width_px = max((sum(w_cjk if '\u2e80' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f'
                        or '\uff00' <= c <= '\uffef' else w_ascii
                        for c, _ in ln) for ln in lines), default=w_ascii)
    W = int(width_px) + 2 * PAD
    H = LINE_HEIGHT * len(lines) + 2 * PAD
    im = Image.new('RGB', (W, max(H, LINE_HEIGHT + 2 * PAD)), BG)
    d = ImageDraw.Draw(im)
    y = PAD
    for ln in lines:
        x = PAD
        for ch, col in ln:
            wide = '\u2e80' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef'
            if ch != ' ':
                d.text((x, y), ch, font=FONT, fill=col)
            x += w_cjk if wide else w_ascii * len(ch)
        y += LINE_HEIGHT
    return im


def is_wide(ch: str) -> bool:
    return ('\u2e80' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f'
            or '\uff00' <= ch <= '\uffef')


FENCE_RE = re.compile(r'^```(\w*)\n(.*?)^```', re.M | re.S)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    md = open(os.path.join(BLOG, 'blog.md')).read()
    blocks = FENCE_RE.findall(md)
    manifest = []
    for i, (lang, body) in enumerate(blocks):
        png = os.path.join(OUTDIR, f'code_{i:02d}.png')
        digest = hashlib.sha1(f'{lang}\n{body}'.encode()).hexdigest()[:10]
        im = render_block(lang, body)
        im.save(png, optimize=True)
        manifest.append(dict(png=os.path.basename(png), lang=lang or 'text',
                             lines=body.count('\n') + 1, sha=digest,
                             kb=os.path.getsize(png) // 1024))
        print(f"code_{i:02d} lang={lang or 'text':9s} {im.size[0]}x{im.size[1]} "
              f"{manifest[-1]['kb']}KB")
    json.dump(manifest, open(os.path.join(OUTDIR, 'manifest.json'), 'w'),
              indent=1, ensure_ascii=False)
    print(f"rendered {len(blocks)} code images -> {OUTDIR}")


if __name__ == '__main__':
    main()

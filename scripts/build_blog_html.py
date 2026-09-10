#!/usr/bin/env python3
"""Build blog.html: single file, all images inlined (base64 PNG + inline SVG).

Source snippets are NOT rendered as HTML <pre> blocks: they are rendered as
purple-terminal PNG images (scripts/code2img.py) so the whole page shares the
look of the real-machine terminal screenshots. Set CODE_AS_IMAGES=0 in the
environment to fall back to classic text code blocks.
"""
import base64, os, re, sys

BLOG = '/home/zhaosiying/codebase/yushuxin-v2-design/blog-output'
OUT = os.path.join(BLOG, 'blog.html')
CODE_AS_IMAGES = os.environ.get('CODE_AS_IMAGES', '1') != '0'

md = open(os.path.join(BLOG, 'blog.md')).read()

def b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()

FENCE_RE = re.compile(r'^```(\w*)\n(.*?)^```', re.M | re.S)
code_bodies = []

def stash_code(m):
    """Replace a fenced block with a placeholder paragraph."""
    code_bodies.append(m.group(0))
    return f'\n\n@@CODEIMG_{len(code_bodies)-1}@@\n\n'

if CODE_AS_IMAGES:
    md = FENCE_RE.sub(stash_code, md)

def repl_png(m):
    alt, rel = m.group(1), m.group(2)
    p = os.path.join(BLOG, rel)
    if not os.path.exists(p):
        return f'<p><em>[截图待生成: {rel} — 解锁桌面后运行 scripts/make_all_shots.sh]</em></p>'
    return f'<img alt="{alt}" src="data:image/png;base64,{b64(p)}" style="max-width:100%;border:1px solid #555;border-radius:6px"/>'

def repl_svg(m):
    alt, rel = m.group(1), m.group(2)
    p = os.path.join(BLOG, rel)
    if not os.path.exists(p):
        return f'<p><em>[图缺失: {rel}]</em></p>'
    svg = open(p).read()
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
    return f'<div style="max-width:100%">{svg}</div>'

md = re.sub(r'!\[([^\]]*)\]\(([^)]+\.png)\)', repl_png, md)
md = re.sub(r'!\[([^\]]*)\]\(([^)]+\.svg)\)', repl_svg, md)

import markdown
html_body = markdown.markdown(md, extensions=['tables', 'fenced_code', 'toc'])

if CODE_AS_IMAGES:
    def repl_codeimg(m):
        i = int(m.group(1))
        p = os.path.join(BLOG, 'codeimg', f'code_{i:02d}.png')
        if not os.path.exists(p):
            return f'<p><em>[代码图缺失: code_{i:02d}.png — 运行 scripts/code2img.py]</em></p>'
        return (f'<img alt="source snippet {i}" '
                f'src="data:image/png;base64,{b64(p)}" '
                f'style="max-width:100%;border:1px solid #555;border-radius:8px;'
                f'margin:.4rem 0"/>')
    html_body, nsub = re.subn(r'<p>\s*@@CODEIMG_(\d+)@@\s*</p>', repl_codeimg, html_body)
    assert nsub == len(code_bodies), f'codeimg placeholders: {nsub} != {len(code_bodies)}'
    # also catch any placeholder the markdown pass left outside <p> (empty blocks etc.)
    html_body = re.sub(r'@@CODEIMG_(\d+)@@', repl_codeimg, html_body)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>从 RTL 到编译器：gem5 周期级 Profiling 反演 LLVM RISC-V 向量调度模型</title>
<style>
  body {{ font-family: "Noto Sans SC","Segoe UI",system-ui,sans-serif; margin: 0 auto;
         max-width: 60rem; padding: 2rem 1.2rem 5rem; line-height: 1.65; color: #24292f;
         background: #ffffff; }}
  h1 {{ border-bottom: 2px solid #d0d7de; padding-bottom: .4rem; }}
  h2 {{ border-bottom: 1px solid #d8dee4; padding-bottom: .3rem; margin-top: 2.2rem; }}
  code, pre {{ font-family: "Ubuntu Mono","JetBrains Mono",Consolas,monospace; }}
  pre {{ background: #300a24; color: #f2f2f2; padding: .9rem 1rem; border-radius: 8px;
        overflow-x: auto; font-size: .85rem; line-height: 1.45; }}
  code {{ background: #f0e6f0; border-radius: 4px; padding: .08rem .3rem; font-size: .92em; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .88rem; margin: 1rem 0; }}
  th, td {{ border: 1px solid #d0d7de; padding: .32rem .55rem; text-align: left; }}
  th {{ background: #f1f3f6; }}
  blockquote {{ border-left: 4px solid #6b21a8; background: #faf5ff; margin: 1rem 0;
               padding: .6rem 1rem; color: #374151; }}
  img {{ margin: .6rem 0; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
open(OUT, 'w').write(html)
print(f'wrote {OUT} ({os.path.getsize(OUT)//1024} KB)')

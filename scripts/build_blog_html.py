#!/usr/bin/env python3
"""Build blog.html: single file, all images inlined (base64).

blog.md is the PUBLISHING source: every snippet/figure/screenshot is an image
reference (jsDelivr CDN URLs, Zhihu-importable). Block texts are archived in
codeimg/blocks/ so scripts/code2img.py can re-render code images if a snippet
changes. This builder maps each CDN URL back to the local repo file, embeds it
as base64, and never touches the network.
"""
import base64, os, re

BLOG = '/home/zhaosiying/codebase/yushuxin-v2-design/blog-output'
REPO = '/home/zhaosiying/codebase/Profile-InstLatency'
OUT = os.path.join(BLOG, 'blog.html')
CDN = 'https://cdn.jsdelivr.net/gh/zhaosiying12138/Profile-InstLatency@main'

md = open(os.path.join(BLOG, 'blog.md')).read()

def b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()

def to_local(url):
    """CDN URL (or repo-relative path) -> local file path, else None."""
    if url.startswith(CDN + '/'):
        return os.path.join(REPO, url[len(CDN) + 1:])
    p = os.path.join(BLOG, url)
    return p if os.path.exists(p) else None

def repl_img(m):
    alt, url = m.group(1), m.group(2)
    p = to_local(url)
    if p is None or not os.path.exists(p):
        return f'<p><em>[图片缺失: {url}]</em></p>'
    style = ('max-width:100%;border:1px solid #555;border-radius:6px'
             if url.endswith('.png') else 'max-width:100%')
    return (f'<img alt="{alt}" src="data:image/png;base64,{b64(p)}" '
            f'style="{style}"/>')

md = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', repl_img, md)

import markdown
html_body = markdown.markdown(md, extensions=['tables', 'fenced_code', 'toc'])

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

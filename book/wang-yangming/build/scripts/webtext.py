#!/usr/bin/env python3
"""通俗哲学专著格式 · 全文网页阅读页（/books/m/<号>/text/index.html）

用法：python3 webtext.py --config book.json --manuscript 统稿.md --out public/books/m/146/text/index.html
样式与脚本取自 assets/webtext.css、assets/webtext.js（与站上第 104、146 号同一套）。
"""
import argparse, json, os, re, html as H
import markdown
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
md = markdown.Markdown(extensions=['tables', 'sane_lists'])


def conv(t):
    md.reset(); h = md.convert(t)
    h = re.sub(r'<hr\s*/?>', '', h)
    h = re.sub(r'<p>◆ (.*?)</p>', r'<h2 class="sec"><span class="dia">◆</span>\1</h2>', h)
    h = re.sub(r'<p>【(.*?)】</p>', r'<h3>\1</h3>', h)
    h = re.sub(r'<p><strong>编序</strong></p>', '<div class="bianxu">编序</div>', h)
    h = re.sub(r'<blockquote>\s*<p><strong>小账</strong>\s*(<br\s*/?>)?', r'<div class="ledger"><p><span class="lt">小账</span><br>', h)
    out, pos = [], 0
    for m in re.finditer(r'<div class="ledger">', h):
        e = h.find('</blockquote>', m.end()); out.append(h[pos:e] + '</div>'); pos = e + len('</blockquote>')
    out.append(h[pos:]); h = ''.join(out)
    h = re.sub(r'<p><strong>带走的话</strong>：', r'<p class="takeaway"><span class="tk-l">带走的话</span><br>', h)
    h = re.sub(r'(〔[^〕]*待核[^〕]*〕)', r'<span class="hk">\1</span>', h)
    h = h.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--manuscript', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8')); s = open(a.manuscript, encoding='utf-8').read()
    no, v, slug = cfg['number'], cfg['version'], cfg['slug']
    toc, body, n = [], [], [0]

    def nid():
        n[0] += 1; return f's{n[0]}'
    for p in re.split(r'\n(?=# )', '\n' + s):
        p = p.strip()
        if not p: continue
        head, _, text = p.partition('\n'); title = head[2:].strip()
        if title == '后记' and not cfg.get('keep_afterword'): continue
        m = re.match(r'(第[一二三四五六七八九十]+编)　(.*)', title)
        if m:
            i = nid(); toc.append(('p', title, i)); chunks = re.split(r'\n(?=## )', '\n' + text)
            body.append(f'<section class="part" id="{i}"><div class="part-label">{m.group(1)}</div><div class="part-title">{m.group(2)}</div>'
                        f'<div class="rule"></div><div class="part-intro">{conv(chunks[0])}</div></section>')
            for ch in chunks[1:]:
                h2, _, cb = ch.strip().partition('\n'); mm = re.match(r'## (第 ?\d+ ?章)　(.*)', h2)
                j = nid(); toc.append(('c', mm.group(1) + '　' + mm.group(2), j))
                body.append(f'<div class="chapter" id="{j}"><div class="chap-label">{mm.group(1)}</div><h2 class="chap-title">{mm.group(2)}</h2>'
                            f'<div class="rule"></div></div>{conv(cb)}')
            continue
        if title == '附录':
            i = nid(); toc.append(('f', '附录', i)); chunks = re.split(r'\n(?=## )', '\n' + text)
            out = f'<section class="back-sec" id="{i}"><h1 class="front-title">附录</h1><div class="rule"></div>{conv(chunks[0])}'
            for ch in chunks[1:]:
                h2, _, cb = ch.strip().partition('\n'); t2 = h2[3:].strip(); j = nid(); toc.append(('c', t2, j))
                out += f'<h2 class="chap-title appx" id="{j}">{t2}</h2>{conv(cb)}'
            body.append(out + '</section>'); continue
        x, _, y = title.partition('　'); i = nid(); toc.append(('f', title, i))
        cls = 'back-sec' if x in ('结语', '参考书目', '后记') else 'front-sec'
        txt = text.replace('\n## ', '\n### ') if x == '参考书目' else text
        sub = f'<div class="fs-sub">{y}</div>' if y else ''
        body.append(f'<section class="{cls}" id="{i}"><h1 class="front-title">{x}</h1>{sub}<div class="rule"></div>{conv(txt)}</section>')
    li = ''.join(f'<li class="{k}"><a href="#{i}">{H.escape(t)}</a></li>' for k, t, i in toc)
    css = open(os.path.join(A, 'webtext.css'), encoding='utf-8').read()
    js = open(os.path.join(A, 'webtext.js'), encoding='utf-8').read().replace('__KEY__', f'bk{no}')
    pdf = cfg['pdf_print_url']
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>长文网页阅读 · {cfg["title"]} · {cfg["series_label"]}第 {no} 号</title>
<meta name="description" content="《{cfg["title"]}——{cfg["subtitle"]}》全文网页版。">
<meta name="tier" content="L0"><link rel="canonical" href="https://sdeuniverses.com/books/m/{no}/text/">
<style>
{css}</style></head>
<body><div id="prog"></div>
<div class="bar"><a href="/books/m/{no}/">← 书籍详情</a><a href="/books/m/{no}/read.html">在线翻页</a><a href="{pdf}?v={v}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{no}/cover.jpg?v={v}" alt="封面"><h1>{cfg["title"]}</h1><p>{cfg["subtitle"]}</p><p style="color:var(--dim);margin-top:.5rem">{cfg["author"]} 著 · {cfg["series_label"]}第 {no} 号 · ISBN {cfg["isbn"]} · {cfg["wordcount"]}</p></div>
<details class="toc" open><summary>目录（{cfg["structure_short"]}）</summary><ul>{li}</ul></details>
{"".join(body)}
<div class="foot">{cfg["publisher_cn"]} · {cfg["publisher_en"]} · <a href="/books/">专著书架</a> · <a href="/books/m/{no}/">书籍详情</a></div>
</div>
<script>
{js}</script></body></html>
'''
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(page)
    print('wrote', a.out, len(toc), 'toc items')


if __name__ == '__main__':
    main()

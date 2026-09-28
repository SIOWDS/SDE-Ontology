#!/usr/bin/env python3
"""通俗哲学专著格式 · 书籍详情页（/books/m/<号>/index.html）

用法：python3 detail_page.py --config book.json --out public/books/m/146/index.html
内容全部取自 book.json 的 detail 一节（判词、导语两段、口述卡片、五条判决、一根三梁表、保底与死法、
全书结构、注释、页脚链接）。样式取自 assets/detail.css（深色底、金色强调，与第 104、145、146 号同款）。
"""
import argparse, json, os, html as H
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def cards(items):
    return '<div class="cards">' + ''.join(f'<div class="card"><b>{k}</b><span>{v}</span></div>' for k, v in items) + '</div>'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args(); c = json.load(open(a.config, encoding='utf-8')); d = c['detail']
    no, v = c['number'], c['version']; css = open(os.path.join(A, 'detail.css'), encoding='utf-8').read()
    meta = [('著者', c['author']), ('执笔', c['executor']), ('出版', f'{c["publisher_cn"]} · {c["publisher_en"]} · {c.get("publisher_place", "新加坡")}'),
            ('编号', f'{c["series_label"]}第 {no} 号'), ('ISBN', c['isbn']), ('定价', c['price']), ('规模', d['scale']),
            ('系列', d['series']), ('完稿', d['finished'])]
    rows = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in d['beams'])
    vols = ''.join(f'<li><b>{k}</b>　{t}</li>' for k, t in d['structure'])
    foot = ' · '.join(f'<a href="{u}">{t}</a>' for t, u in d['foot_links'])
    desc = H.escape(f'《{c["title"]}——{c["subtitle"]}》· {c["author"]} 著 · 德麦国际 · ISBN {c["isbn"]}。{d["scale_short"]}。{d["line"]}')
    page = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{c["title"]} · {c["series_label"]}第 {no} 号</title>
<meta name="description" content="{desc}">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="source" content="自撰">
<meta name="isbn" content="{c["isbn"]}"><meta name="book_no" content="{no}"><meta name="tier_set_at" content="统稿"><meta name="tier_reason" content="第一刀：通俗解构专著，以判词、判决、承重命题、分离线与推翻条件等主张层为主，无语料与真跑数据；系列各卷均全文公开">
<meta property="og:title" content="{c["title"]} · 德麦国际专著">
<meta property="og:description" content="{H.escape(d["line"])}">
<meta property="og:image" content="https://sdeuniverses.com/books/m/{no}/cover.jpg?v={v}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/{no}/">
<style>
{css}</style></head><body>
<div class="wrap">
<div class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">德麦国际专著</a> · 第 {no} 号 · {c["title"]}</div>
<div class="hero">
  <img src="/books/m/{no}/cover.jpg?v={v}" alt="《{c["title"]}》封面">
  <div>
    <h1>{c["title"]}</h1>
    <p class="sub">{c["subtitle"]}</p>
    <div class="line">{d["line"]}</div>
    {"".join(f"<p>{x}</p>" for x in d["intro"])}
    <div class="meta">{"".join(f'<div><b>{k}</b><span>{x}</span></div>' for k, x in meta)}</div>
    <div class="btns">
      <a class="btn solid" href="/books/m/{no}/read.html">友好阅读 · 在线翻页</a>
      <a class="btn" href="/books/m/{no}/text/">全文网页阅读</a>
      <a class="btn" href="{c["pdf_reader_url"]}?v={v}" target="_blank" rel="noopener">阅读版 PDF（含封面）</a>
      <a class="btn" href="{c["pdf_print_url"]}?v={v}" target="_blank" rel="noopener">印刷版 PDF</a>
    </div>
  </div>
</div>
<h2>{d["oral_title"]}</h2>
{cards(d["oral"])}
<h2>全书的五条判决</h2>
{cards(d["verdicts"])}
<h2>{d["beams_title"]}</h2>
<table><tr><th>他的</th><th>本书的替换</th><th>保留的那一半</th></tr>{rows}</table>
<h2>保底与死法</h2>
<p>{d["floor"]}</p>
<h2>作者简介</h2>
{"".join(f"<p>{x}</p>" for x in d["bio"])}
<h2>全书结构</h2>
<ol class="vols">{vols}</ol>
<p style="color:var(--dim);font-size:.86rem">{d["note"]}</p>
<div class="foot">{c["publisher_cn"]} · {c["publisher_en"]} · Singapore · {foot}</div>
</div></body></html>
'''
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(page); print('wrote', a.out)


if __name__ == '__main__':
    main()

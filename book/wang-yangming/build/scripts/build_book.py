#!/usr/bin/env python3
"""通俗哲学专著格式 · 成书排版（WeasyPrint 矢量 PDF）

用法：
  python3 build_book.py --config book.json --manuscript 统稿.md --outdir out/
产出（outdir 下）：
  <slug>.pdf          印刷版 170x240 mm，扉页起，无封面封底
  <slug>-reader.pdf   阅读版 190x250 mm，封面＋全书＋封底（翻页阅读器用它）
  cover.jpg / backcover.jpg   900x1270，站点与书架用
  build_report.json   页数、导论所在物理页（翻页器 offset）、书签数
依赖：pip install weasyprint markdown python-barcode pypdf pillow --break-system-packages；
      系统需有 Noto Serif/Sans CJK SC 字体与 poppler（pdftoppm）。
"""
import argparse, json, os, re, subprocess, sys, html as H
import markdown, weasyprint
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover

NAVY = '#1d2b4c'; GOLD = '#b8913e'
md = markdown.Markdown(extensions=['tables', 'sane_lists'])
CJ = '\u4e00-\u9fff\u3000-\u303f\uff00-\uffef'


def conv(t):
    md.reset(); h = md.convert(t)
    h = re.sub(r'<hr\s*/?>', '', h)
    h = re.sub(r'<p>◆ (.*?)</p>', r'<h3 class="sec"><span class="dia">◆</span>\1</h3>', h)
    h = re.sub(r'<p>【(.*?)】</p>', r'<h4 class="scene">\1</h4>', h)
    h = re.sub(r'<p><strong>编序</strong></p>', '<div class="label">编　序</div>', h)
    h = re.sub(r'<blockquote>\s*<p><strong>小账</strong>', r'<blockquote class="ledger"><p><strong>小账</strong>', h)
    h = re.sub(r'<p><strong>带走的话</strong>：', r'<p class="takeaway"><span class="tk">带走的话</span>', h)
    h = re.sub(r'(〔[^〕]*待核[^〕]*〕)', r'<span class="tbd">\1</span>', h)
    # 中西文之间的空格换成细空格：两端对齐时 U+0020 会被拉宽，出现「第    4 章」
    h = re.sub(r'(?<=[' + CJ + r']) (?=[0-9A-Za-z$＝])', '\u2009', h)
    h = re.sub(r'(?<=[0-9A-Za-z%$）)]) (?=[' + CJ + r'])', '\u2009', h)
    # 短单元格不折行（「王德生」「2026 年」不被挤成竖排）
    h = re.sub(r'<td>([^<]{1,8})</td>', r'<td class="nw">\1</td>', h)
    return h


def split_top(s):
    out = []
    for p in re.split(r'\n(?=# )', '\n' + s):
        p = p.strip()
        if p:
            head, _, body = p.partition('\n')
            out.append((head[2:].strip(), body))
    return out


def ft(t):
    a, _, b = t.partition('　')
    return a, b


def css(W, Hh, fs, book):
    return f'''
@page {{ size:{W}mm {Hh}mm; margin:20mm 17mm 20mm 19mm; }}
@page :left {{ margin-left:17mm; margin-right:19mm;
  @top-left {{ content:"{book}"; font-family:'Noto Sans CJK SC'; font-size:7.5pt; color:#8a8f9c; }}
  @bottom-left {{ content: counter(page); font-family:'Noto Sans CJK SC'; font-size:8pt; color:#8a8f9c; }} }}
@page :right {{
  @top-right {{ content: string(chap); font-family:'Noto Sans CJK SC'; font-size:7.5pt; color:#8a8f9c; }}
  @bottom-right {{ content: counter(page); font-family:'Noto Sans CJK SC'; font-size:8pt; color:#8a8f9c; }} }}
@page fm:left {{ @top-left{{content:none}} @bottom-left {{ content: counter(page, lower-roman); }} }}
@page fm:right {{ @top-right{{content:none}} @bottom-right {{ content: counter(page, lower-roman); }} }}
@page blank {{ @top-left{{content:none}} @top-right{{content:none}} @bottom-left{{content:none}} @bottom-right{{content:none}} }}
@page coverp {{ margin:0; @top-left{{content:none}} @top-right{{content:none}} @bottom-left{{content:none}} @bottom-right{{content:none}} }}
/* 正文页组：整段正文包在一个 .mainwrap 里，页码在这一组的第一页重置为 1。
   不要在每个 section 上写 page:mn——每个 section 都会开一个新页组，目录页码全变 1。 */
.mainwrap {{ page: mn; }}
@page mn:nth(1 of mn) {{ counter-reset: page 1; }}
html {{ font-family:'Noto Serif CJK SC','Noto Serif CJK JP',serif; font-size:{fs}; color:#1f2430; line-height:1.92; text-align:justify; }}
body {{ margin:0; }}
.coverwrap {{ page: coverp; page-break-after: always; }}
.coverwrap.back {{ page-break-before: always; page-break-after: auto; }}
section.titlepage {{ page: blank; page-break-after: always; }}
.tp1 {{ font-size:15pt; color:{NAVY}; margin-top:40mm; letter-spacing:1pt; }}
.tp2 {{ font-size:40pt; font-weight:700; color:{NAVY}; letter-spacing:6pt; line-height:1.3; }}
.tp3 {{ font-family:'Noto Sans CJK SC'; font-size:9.5pt; color:{GOLD}; margin-top:3mm; }}
.tprule {{ width:22mm; border-top:0.8pt solid {GOLD}; margin-top:6mm; }}
.tp4 {{ font-family:'Noto Sans CJK SC'; font-size:11pt; color:#333; margin-top:30mm; letter-spacing:2pt; }}
.tp5 {{ margin-top:46mm; font-family:'Noto Sans CJK SC'; font-size:8.5pt; color:{NAVY}; font-weight:700; line-height:1.6; }}
.tp5 span {{ font-weight:400; font-size:6pt; letter-spacing:1.6pt; color:#7a8090; }}
section.front {{ page: fm; page-break-before: always; }}
section.mainsec, section.chap, section.part {{ page-break-before: always; }}
h1.ft {{ margin:4mm 0 0 0; line-height:1.3; }}
h1.ft .ftt {{ display:block; font-family:'Noto Serif CJK SC'; font-size:22pt; font-weight:700; color:{NAVY}; letter-spacing:2pt; string-set: chap content(); }}
h1.ft .fts {{ display:block; font-family:'Noto Sans CJK SC'; font-size:9.5pt; font-weight:500; color:{GOLD}; margin-top:2mm; }}
.rule {{ width:16mm; border-top:0.8pt solid {GOLD}; margin:5mm 0 8mm 0; }}
.rule.c {{ margin:6mm auto 10mm auto; }}
.partno {{ text-align:center; font-family:'Noto Sans CJK SC'; font-size:10pt; color:{GOLD}; letter-spacing:4pt; margin-top:26mm; }}
h1.pt {{ text-align:center; font-family:'Noto Serif CJK SC'; font-size:19pt; color:{NAVY}; font-weight:700; margin:5mm 0 0 0; line-height:1.4; string-set: chap content(); }}
.label {{ font-family:'Noto Sans CJK SC'; font-size:9pt; color:{GOLD}; letter-spacing:3pt; text-align:center; margin-bottom:4mm; }}
h2.ch {{ margin:6mm 0 9mm 0; line-height:1.35; }}
h2.ch .chno {{ display:block; font-family:'Noto Sans CJK SC'; font-size:9pt; color:{GOLD}; letter-spacing:1pt; }}
h2.ch .cht {{ display:block; font-family:'Noto Serif CJK SC'; font-size:17pt; color:{NAVY}; font-weight:700; margin-top:2.5mm; string-set: chap content(); }}
h2.ax {{ font-family:'Noto Serif CJK SC'; font-size:14pt; color:{NAVY}; margin:10mm 0 5mm 0; string-set: chap content(); }}
.appxsec {{ page-break-before: always; }}
.appxsec.first {{ page-break-before: auto; }}
h3 {{ font-family:'Noto Sans CJK SC'; font-size:10.5pt; color:{NAVY}; font-weight:700; margin:7mm 0 3mm 0; page-break-after: avoid; line-height:1.5; }}
h3.sec .dia {{ color:{GOLD}; margin-right:2.2mm; }}
h4.scene {{ font-family:'Noto Sans CJK SC'; font-size:10pt; color:{NAVY}; font-weight:700; margin:6mm 0 2mm 0; padding-left:2.5mm; border-left:2pt solid {GOLD}; page-break-after: avoid; }}
p {{ margin:0 0 1.6mm 0; text-indent:2em; orphans:2; widows:2; }}
li p, td p, blockquote p {{ text-indent:0; }}
strong {{ color:{NAVY}; font-weight:700; }}
blockquote {{ margin:4mm 0; padding:2.5mm 4mm; background:#f6f1e6; border-left:2.4pt solid {GOLD}; page-break-inside: avoid; }}
blockquote p {{ margin:0.6mm 0; }}
blockquote.ledger {{ font-family:'Noto Sans CJK SC'; font-size:8.8pt; line-height:1.75; color:#3a3f4c; background:#f3f1ec; border-left-color:{NAVY}; }}
p.takeaway {{ text-indent:0; margin:6mm 0 4mm 0; padding:2.5mm 0 2.5mm 4mm; border-left:2.4pt solid {GOLD}; color:{NAVY}; font-weight:500; page-break-inside: avoid; }}
p.takeaway .tk {{ display:block; font-family:'Noto Sans CJK SC'; font-size:8.5pt; color:{GOLD}; letter-spacing:1pt; margin-bottom:1mm; }}
.tbd {{ font-size:0.86em; color:#8a8378; }}
table {{ width:100%; border-collapse:collapse; margin:4mm 0 5mm 0; font-family:'Noto Sans CJK SC'; font-size:8.2pt; line-height:1.55; text-align:left; }}
th {{ background:{NAVY}; color:#fff; font-weight:500; padding:1.6mm 2mm; border:0.4pt solid {NAVY}; }}
td.nw {{ white-space:nowrap; }}
td {{ padding:1.5mm 2mm; border:0.4pt solid #d8d3c7; vertical-align:top; }}
tr {{ page-break-inside: avoid; }}
table.kv th {{ width:16mm; background:none; color:#6b7080; border:none; border-bottom:0.4pt solid #e2ddd2; font-weight:500; }}
table.kv td {{ border:none; border-bottom:0.4pt solid #e2ddd2; color:#222; }}
section.pub p.note {{ font-family:'Noto Sans CJK SC'; font-size:7.8pt; color:#555a66; line-height:1.7; text-indent:0; margin-top:3mm; }}
ol, ul {{ margin:2mm 0 3mm 0; padding-left:7mm; }}
li {{ margin-bottom:1mm; }}
section.bib ol {{ font-size:8.8pt; line-height:1.7; text-align:left; }}
section.toc ul {{ list-style:none; padding:0; margin:0; font-family:'Noto Sans CJK SC'; font-size:8.8pt; line-height:1.75; }}
section.toc li {{ margin:0; }}
section.toc a {{ color:#222; text-decoration:none; }}
section.toc a::after {{ content: leader('·') target-counter(attr(href), page); color:#8a8f9c; }}
section.toc li.tf a::after {{ content: leader('·') target-counter(attr(href), page, lower-roman); }}
section.toc li.tp {{ margin-top:2.6mm; font-weight:700; }}
section.toc li.tp a {{ color:{NAVY}; }}
section.toc li.tm {{ margin-top:2.2mm; font-weight:700; }}
section.toc li.tc {{ padding-left:6mm; color:#333; }}
a {{ color:inherit; text-decoration:none; }}
h3, h4, .tp1, .tp2 {{ bookmark-level: none; }}
h1.ft, h1.pt {{ bookmark-level: 1; }}
h2.ch, h2.ax {{ bookmark-level: 2; }}
h1.ft, h1.pt, h2.ch, h2.ax {{ bookmark-label: attr(data-bm); }}
'''


def build_html(kind, cfg, text):
    W, Hh = (170, 240) if kind == 'print' else (190, 250)
    fs = '10.5pt' if kind == 'print' else '11.2pt'
    toc, body, n = [], [], [0]

    def nid():
        n[0] += 1
        return f'x{n[0]}'
    author = None
    for title, t in split_top(text):
        if title == '出版信息':
            continue
        if title == '作者介绍':
            author = t; continue
        if title == '后记' and not cfg.get('keep_afterword'):
            continue
        e = H.escape(title)
        if title.startswith(('前言', '导读')):
            a, b = ft(title); i = nid(); toc.append(('front', title, i))
            body.append(f'<section class="front"><h1 class="ft" id="{i}" data-bm="{e}"><span class="ftt">{" ".join(a)}</span>'
                        f'<span class="fts">{b}</span></h1><div class="rule"></div>{conv(t)}</section>')
            continue
        m = re.match(r'(第[一二三四五六七八九十]+编)　(.*)', title)
        if m:
            i = nid(); toc.append(('part', title, i))
            chunks = re.split(r'\n(?=## )', '\n' + t)
            body.append(f'<section class="part"><div class="partno">{" ".join(m.group(1))}</div>'
                        f'<h1 class="pt" id="{i}" data-bm="{e}">{m.group(2)}</h1><div class="rule c"></div>{conv(chunks[0])}</section>')
            for ch in chunks[1:]:
                h2, _, cb = ch.strip().partition('\n')
                mm = re.match(r'## (第 ?\d+ ?章)　(.*)', h2)
                if not mm:
                    raise SystemExit('章标题须写作「## 第 N 章　章名」：' + h2)
                j = nid(); toc.append(('chap', mm.group(1) + '　' + mm.group(2), j))
                body.append(f'<section class="chap"><h2 class="ch" id="{j}" data-bm="{H.escape(mm.group(1) + "　" + mm.group(2))}">'
                            f'<span class="chno">{mm.group(1)}</span><span class="cht">{mm.group(2)}</span></h2>{conv(cb)}</section>')
            continue
        if title == '参考书目':
            i = nid(); toc.append(('main', '参考书目', i))
            body.append(f'<section class="mainsec bib"><h1 class="ft" id="{i}" data-bm="参考书目"><span class="ftt">参 考 书 目</span></h1>'
                        f'<div class="rule"></div>{conv(t.replace(chr(10) + "## ", chr(10) + "### "))}</section>')
            continue
        if title == '附录':
            i = nid(); toc.append(('main', '附录', i))
            chunks = re.split(r'\n(?=## )', '\n' + t)
            out = f'<section class="mainsec appx"><h1 class="ft" id="{i}" data-bm="附录"><span class="ftt">附 录</span></h1><div class="rule"></div>{conv(chunks[0])}'
            for k, ch in enumerate(chunks[1:]):
                h2, _, cb = ch.strip().partition('\n'); t2 = h2[3:].strip(); j = nid(); toc.append(('chap', t2, j))
                out += f'<div class="appxsec{" first" if k == 0 else ""}"><h2 class="ax" id="{j}" data-bm="{H.escape(t2)}">{t2}</h2>{conv(cb)}</div>'
            body.append(out + '</section>'); continue
        # 导论、结语、后记（如保留）及其他一级部分
        a, b = ft(title); i = nid(); toc.append(('main', title, i))
        body.append(f'<section class="mainsec"><h1 class="ft" id="{i}" data-bm="{e}"><span class="ftt">{" ".join(a)}</span>'
                    f'<span class="fts">{b}</span></h1><div class="rule"></div>{conv(t)}</section>')
    if author is None:
        raise SystemExit('书稿缺「# 作者介绍」一节')
    rows = [('书名', f'《{cfg["title"]}——{cfg["subtitle"]}》'), ('著者', cfg['author']), ('执笔', cfg['executor']),
            ('出版', f'{cfg["publisher_cn"]}（{cfg["publisher_en"]}）· {cfg.get("publisher_place", "新加坡")}'),
            ('编号', f'{cfg["series_label"]}第 {cfg["number"]} 号'), ('ISBN', cfg['isbn'] or '待补'), ('定价', cfg['price']),
            ('开本', f'{W} mm × {Hh} mm'), ('字数', cfg['wordcount']), ('版次', cfg['edition'])]
    notes = ''.join(f'<p class="note">{x}</p>' for x in cfg.get('pub_notes', []))
    pub = ('<section class="front pub"><h1 class="ft" data-bm="出版信息"><span class="ftt">出 版 信 息</span></h1><div class="rule"></div>'
           '<table class="kv">' + ''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a, b in rows) + '</table>' + notes + '</section>')
    auth = f'<section class="front"><h1 class="ft" id="author" data-bm="作者介绍"><span class="ftt">作 者 介 绍</span></h1><div class="rule"></div>{conv(author)}</section>'
    toc.insert(0, ('front', '作者介绍', 'author'))
    tp = (f'<section class="titlepage"><div class="tp1">{cfg["title_small"]}</div><div class="tp2">{cfg["title_big"]}</div>'
          f'<div class="tp3">{cfg["subtitle"]}</div><div class="tprule"></div><div class="tp4">{cfg["author"]}　著</div>'
          f'<div class="tp5">{cfg["publisher_cn"]}<br/><span>{cfg["publisher_en"].upper()}</span></div></section>')
    cls = {'front': 'tf', 'main': 'tm', 'part': 'tp', 'chap': 'tc'}
    li = ''.join(f'<li class="{cls[k]}"><a href="#{i}">{H.escape(t)}</a></li>' for k, t, i in toc)
    tochtml = f'<section class="front toc"><h1 class="ft" data-bm="目录"><span class="ftt">目 录</span></h1><div class="rule"></div><ul>{li}</ul></section>'
    fronts = [b for b in body if b.startswith('<section class="front">')]
    mains = [b for b in body if not b.startswith('<section class="front">')]
    cf = cb = ''
    if kind == 'reader':
        cf = f'<div class="coverwrap">{cover.front_cover(W, Hh, cfg)}</div>'
        cb = f'<div class="coverwrap back">{cover.back_cover(W, Hh, cfg)}</div>'
    return (f'<html><head><meta charset="utf-8"><title>{cfg["title"]}——{cfg["subtitle"]}</title><style>{css(W, Hh, fs, cfg["title"])}</style></head><body>'
            + cf + tp + pub + auth + ''.join(fronts) + tochtml + '<div class="mainwrap">' + ''.join(mains) + '</div>' + cb + '</body></html>')


def render(kind, cfg, text, path):
    doc = weasyprint.HTML(string=build_html(kind, cfg, text)).render()
    doc.metadata.title = f'{cfg["title"]}——{cfg["subtitle"]}'
    doc.metadata.authors = [cfg['author']]
    doc.metadata.description = f'{cfg["series_label"]}第 {cfg["number"]} 号'
    doc.write_pdf(path)
    return len(doc.pages)


def cover_jpgs(cfg, outdir):
    from PIL import Image
    for name, fn in [('cover', cover.front_cover), ('backcover', cover.back_cover)]:
        pdf = os.path.join(outdir, f'_{name}.pdf')
        weasyprint.HTML(string=f'<html><head><style>@page{{size:170mm 240mm;margin:0}}body{{margin:0}}</style></head>'
                                f'<body>{fn(170, 240, cfg)}</body></html>').write_pdf(pdf)
        png = os.path.join(outdir, f'_{name}')
        subprocess.run(['pdftoppm', '-r', '134.5', '-png', '-singlefile', pdf, png], check=True)
        Image.open(png + '.png').convert('RGB').resize((900, 1270), Image.LANCZOS).save(os.path.join(outdir, name + '.jpg'), quality=90)
        os.remove(pdf); os.remove(png + '.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--manuscript', required=True)
    ap.add_argument('--outdir', required=True); ap.add_argument('--only', choices=['print', 'reader', 'covers'])
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(a.config))
    if cfg.get('cover', {}).get('art_svg') and not os.path.isabs(cfg['cover']['art_svg']):
        cfg['cover']['art_svg'] = os.path.join(base, cfg['cover']['art_svg'])
    text = open(a.manuscript, encoding='utf-8').read()
    os.makedirs(a.outdir, exist_ok=True)
    rep = {}
    if a.only in (None, 'print'):
        rep['print_pages'] = render('print', cfg, text, os.path.join(a.outdir, cfg['slug'] + '.pdf'))
    if a.only in (None, 'reader'):
        rp = os.path.join(a.outdir, cfg['slug'] + '-reader.pdf')
        rep['reader_pages'] = render('reader', cfg, text, rp)
        import pypdf
        r = pypdf.PdfReader(rp); marks = []

        def walk(o):
            for x in o:
                walk(x) if isinstance(x, list) else marks.append((str(x.title), r.get_destination_page_number(x) + 1))
        walk(r.outline)
        rep['bookmarks'] = len(marks)
        rep['reader_offset'] = next((g for t, g in marks if t.startswith('导论')), None)
    if a.only in (None, 'covers'):
        cover_jpgs(cfg, a.outdir); rep['covers'] = ['cover.jpg', 'backcover.jpg']
    json.dump(rep, open(os.path.join(a.outdir, 'build_report.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))


if __name__ == '__main__':
    main()

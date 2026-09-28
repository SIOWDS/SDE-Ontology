#!/usr/bin/env python3
"""通俗哲学专著格式 · 成书体检（书稿＋PDF）

用法：
  python3 check_book.py --config book.json --manuscript 统稿.md [--outdir out/]
书稿检查：部件次序、章号连续、前言字数、正文加粗数、每章「带走的话」与「小账」、每章◆节数、
          内部标记残留（交接卡、接续说明、待裁）、书名用字、判词各处一字不差、〔待核〕清单。
PDF 检查（给了 outdir 时）：页数、字体全部嵌入、封面封底页无渐变（Shading/Pattern）、书签、目录页码不全是 1。
退出码：有「错误」为 1，只有「提醒」为 0。
"""
import argparse, json, os, re, subprocess, sys

ERR, WARN = [], []
def err(x): ERR.append(x)
def warn(x): WARN.append(x)
def allc(t): return len(re.sub(r'\s', '', t))
def han(t): return len(re.findall(r'[\u4e00-\u9fff]', t))


def check_md(cfg, s):
    tops = [l[2:].strip() for l in s.splitlines() if l.startswith('# ')]
    heads = [t.split('　')[0] for t in tops]
    want = ['作者介绍', '前言', '导读', '导论']
    for w in want:
        if w not in heads: err(f'缺一级部分：{w}')
    for w in ['结语', '参考书目', '附录']:
        if w not in heads: err(f'缺一级部分：{w}')
    if '后记' in heads and not cfg.get('keep_afterword'):
        warn('书稿里有「后记」；本格式默认不设后记，排版时会跳过（要保留请在 book.json 写 keep_afterword: true）')
    idx = {h: i for i, h in enumerate(heads)}
    order = ['前言', '导读', '导论']
    if all(o in idx for o in order) and not (idx['前言'] < idx['导读'] < idx['导论']):
        err('次序应为：前言 → 导读 → 导论')
    chs = [int(x) for x in re.findall(r'^## 第 ?(\d+) ?章　', s, flags=re.M)]
    if chs != list(range(1, len(chs) + 1)): err(f'章号不连续：{chs[:5]}…')
    # 前言字数
    m = re.search(r'\n# 前言.*?(?=\n# )', '\n' + s, flags=re.S)
    if m:
        tgt = cfg.get('preface_target', 4000); h = han(m.group(0)); c = allc(m.group(0))
        if not (tgt * 0.85 <= h <= tgt * 1.15) and not (tgt * 0.9 <= c <= tgt * 1.15):
            warn(f'前言字数：汉字 {h}，含标点 {c}，目标约 {tgt}')
    # 正文加粗（到附录为止，不含标签）
    body = s[:s.find('\n# 附录')] if '\n# 附录' in s else s
    bolds = [b for b in re.findall(r'\*\*(.+?)\*\*', body) if b not in ('带走的话', '小账', '编序')]
    if len(bolds) > cfg.get('bold_max', 32): warn(f'正文加粗 {len(bolds)} 处，超过上限 {cfg.get("bold_max", 32)}')
    # 每章结构
    for m in re.finditer(r'\n## (第 ?\d+ ?章　[^\n]*)\n(.*?)(?=\n## |\n# |\Z)', s, flags=re.S):
        t, b = m.group(1), m.group(2)
        if '**带走的话**' not in b: warn(f'{t[:20]}：缺「带走的话」')
        if '**小账**' not in b: warn(f'{t[:20]}：缺「小账」')
        k = len(re.findall(r'^◆ ', b, flags=re.M))
        if k > 9: warn(f'{t[:20]}：◆ 节 {k} 个，超过 9')
    # 残留
    for mark in ['【交接卡】', '> 接续说明', '待裁：']:
        if mark in s: err(f'内部标记残留：{mark}')
    # 书名用字
    for alt in ['普通人都能懂的', '普通人都能明白的', '普通人都能读懂的']:
        if alt != cfg['title_small'] and (alt + cfg['title_big']) in s: err(f'书名用字不一：出现「{alt}{cfg["title_big"]}」')
    # 判词
    v = cfg.get('verdict')
    if v:
        n = s.count(v)
        if n < cfg.get('verdict_min', 3): warn(f'判词原文只出现 {n} 次（前言、导读、总解构、结语应一字不差）')
    tb = re.findall(r'〔[^〕]*待核[^〕]*〕', s)
    return {'parts': heads, 'chapters': len(chs), 'bold_body': len(bolds), 'tbd': len(tb), 'chars': allc(s), 'han': han(s)}


def check_pdf(cfg, outdir):
    import pypdf
    rep = {}
    for kind, fn in [('print', cfg['slug'] + '.pdf'), ('reader', cfg['slug'] + '-reader.pdf')]:
        p = os.path.join(outdir, fn)
        if not os.path.exists(p): warn(f'找不到 {fn}'); continue
        r = pypdf.PdfReader(p); rep[kind + '_pages'] = len(r.pages)
        f = subprocess.run(['pdffonts', p], capture_output=True, text=True).stdout.splitlines()[2:]
        bad = [l for l in f if l.split()[-5:-4] != ['yes']] if f else []
        if any(' no ' in (' ' + l + ' ') for l in f): err(f'{fn}：有未嵌入的字体')
        if not r.outline: err(f'{fn}：没有书签（翻页器目录要靠它）')
        if kind == 'reader':
            for i in (0, len(r.pages) - 1):
                res = r.pages[i].get('/Resources', {})
                for key in ('/Shading', '/Pattern'):
                    if key in res and len(res[key]) > 0:
                        err(f'{fn} 第 {i + 1} 页用了渐变（{key}）：PDF.js 矢量翻页会整页发白，改成纯色')
        txt = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout.split('\f')
        tocp = next((t for t in txt if t.strip().startswith('目 录')), '')
        nums = re.findall(r'·\s*(\d+)\s*$', tocp, flags=re.M)
        if nums and len(set(nums)) <= 1: err(f'{fn}：目录页码全是 {nums[0]}（页组重置写错了）')
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--manuscript', required=True); ap.add_argument('--outdir')
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8')); s = open(a.manuscript, encoding='utf-8').read()
    rep = check_md(cfg, s)
    if a.outdir: rep.update(check_pdf(cfg, a.outdir))
    print(json.dumps(rep, ensure_ascii=False))
    for x in ERR: print('✗ 错误：', x)
    for x in WARN: print('△ 提醒：', x)
    print('体检通过' if not ERR else f'体检不通过：{len(ERR)} 处错误')
    sys.exit(1 if ERR else 0)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""把 chapters/ 下十四个分编文件合成一份统稿 full.md，并转成排版脚本认的 Markdown 约定。

各编写作时用的是「阅读友好」的标题写法（### ◆ 一、…），排版脚本 build_book.py
认的是另一套（◆ 一、… 独占一段）。这个脚本做四件事：

1. 去掉各编文末的工作清单（〔待核〕、新造案例、汉字数、禁令自查）——那是写作工序的记录，
   不是书的内容；它们的内容已由结语编汇总进附录四。
2. 把 `### ◆ X` / `## ◆ X` 转成独占一段的 `◆ X`；参考书目下的 `## ◆ 一、` 转成条目标题 `## 一、`。
3. 把 `### ◆ 带走的话` ＋ 其后的引用段，转成 `**带走的话**：…`。
4. 把 `## 编序` 转成 `**编序**`；补上 `# 作者介绍`；给前言与导读补副题；去掉包装用的一级标题。

用法：python3 assemble.py [--chapters ../chapters] [--out full.md]
"""
import argparse
import pathlib
import re
import sys

ORDER = [
    '00-前置', '01-一个人', '02-接手的题', '03-总纲', '04-母题上', '05-母题中',
    '06-母题下', '07-钉子', '08-相遇', '09-总解构', '10-身后', '11-AI',
    '12-用得上', '13-结语与附录',
]

# 各编文末的工作清单从这里开始，一律切掉
TAIL = re.compile(
    r'^#{1,4}\s*(?:[一二三四五]、)?\s*'
    r'(?:本编|附录·本编交稿附件|交稿附件|三条禁令落实自查)')
# 只用来包住一个文件的一级标题，不是书的部件
WRAPPER = re.compile(r'^#\s*(?:前置|结语·参考书目·附录)\b')
DIAMOND = re.compile(r'^#{2,3}\s*◆\s*(.+?)\s*$')
TAKEAWAY = re.compile(r'^#{2,3}\s*◆\s*(?:[一二三四五六七八九十]+、)?\s*带走的话\s*$')
PART = re.compile(r'^#\s*第[一二三四五六七八九十]+编(?:\s|　)')
BIBITEM = re.compile(r'^##\s*◆\s*((?:[一二三四五六七八九十]+)、.+?)\s*$')

AUTHOR_BIO = """# 作者介绍

王德生，博士，SIO 本体论与 SDE 发生学的创立者。

他的思想走过四站：三视角（知识的结构和体系）、321 智慧系统、SIO 本体论、SDE 本体论。
第四站里又分两段：三元组先作「结构、差异、纠缠」，后来只换一个词，结构改读为显露——
显露、差异、纠缠。结构不是显露的沉淀物，是显露的稳定态。

他把这套本体论用到教育、语言、管理、法律、心理与文明史上，写成德麦国际专著系列；
「普通人都能读懂的」哲学家解构系列，是其中一条支线：用七个大白话词，
把一位思想家拆开，再重新装一遍。
"""

SUBTITLES = {'# 前言': '# 前言　这一次，给他一整本书', '# 导读': '# 导读　这本书怎么用'}

# 兜底：编号偶尔写成阿拉伯数字（`# 第 5 编`），排版脚本只认中文数字
CN = '零一二三四五六七八九十十一十二'.split()
ARABIC_PART = re.compile(r'^#\s*第\s*(\d+)\s*编(\s|　)')


def _cn_num(n: int) -> str:
    return ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
            '十一', '十二', '十三', '十四', '十五'][n]


def clean(text: str) -> str:
    lines = text.split('\n')
    # 切掉文末工作清单
    for i, ln in enumerate(lines):
        if TAIL.match(ln):
            lines = lines[:i]
            break
    out, in_bib, i = [], False, 0
    while i < len(lines):
        ln = lines[i]
        if WRAPPER.match(ln):
            i += 1
            continue
        if ln.startswith('# 参考书目'):
            in_bib = True
        elif ln.startswith('# ') and not ln.startswith('# 参考书目'):
            in_bib = False
        m = ARABIC_PART.match(ln)
        if m:
            ln = re.sub(r'第\s*\d+\s*编', '第' + _cn_num(int(m.group(1))) + '编', ln, count=1)
        if ln.strip() in SUBTITLES:
            out.append(SUBTITLES[ln.strip()])
            i += 1
            continue
        if ln.strip() == '## 编序':
            out.append('**编序**')
            i += 1
            continue
        if PART.match(ln):
            out.append(ln)
            # 有几编的编序直接跟在编题后面，没写标题；补一个，排版脚本才认得出
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].lstrip().startswith(('#', '**编序**')):
                out.append('')
                out.append('**编序**')
            i += 1
            continue
        if TAKEAWAY.match(ln):
            # 跳过标题与空行，把随后的引用段收成一行
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            body = []
            while j < len(lines) and lines[j].startswith('>'):
                body.append(lines[j].lstrip('>').strip())
                j += 1
            out.append('**带走的话**：' + ''.join(x for x in body if x))
            i = j
            continue
        if in_bib:
            m = BIBITEM.match(ln)
            if m:
                out.append('## ' + m.group(1))
                i += 1
                continue
        m = DIAMOND.match(ln)
        if m:
            out.append('◆ ' + m.group(1))
            i += 1
            continue
        if ln.strip() == '---':
            i += 1
            continue
        out.append(ln)
        i += 1
    # 压掉连续空行
    res, blank = [], 0
    for ln in out:
        if not ln.strip():
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        res.append(ln)
    return '\n'.join(res).strip() + '\n'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapters', default='../chapters')
    ap.add_argument('--out', default='full.md')
    a = ap.parse_args()
    src = pathlib.Path(a.chapters)
    parts, missing = [], []
    for name in ORDER:
        p = src / f'{name}.md'
        if not p.exists():
            missing.append(name)
            continue
        body = clean(p.read_text(encoding='utf-8'))
        if name == '00-前置':
            body = AUTHOR_BIO + '\n' + body
        parts.append(body)
    if missing:
        print('缺文件：' + '、'.join(missing), file=sys.stderr)
        return 1
    text = '\n\n'.join(parts)
    pathlib.Path(a.out).write_text(text, encoding='utf-8')
    han = len(re.findall(r'[一-鿿]', text))
    chaps = len(re.findall(r'^## 第 \d+ 章', text, re.M))
    books = len(re.findall(r'^# 第[一二三四五六七八九十]+编', text, re.M))
    print(f'{a.out}：{han:,} 汉字 · {books} 编 · {chaps} 章')
    for pat, label in [(r'^# (.+)$', '一级部件')]:
        for m in re.finditer(pat, text, re.M):
            if not m.group(1).startswith('第'):
                print('  ·', m.group(1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

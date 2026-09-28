"""通俗哲学专著格式 · 封面与封底（HTML 片段，交给 WeasyPrint 排成整页）

坐标系：统一用 900 x 1270 的设计稿坐标（= 170x240 mm 的比例），按页面尺寸等比缩放居中（meet）。
底色：64 条纯色横带拼出竖向渐变——不要用 CSS/SVG 渐变。PDF.js 的矢量翻页（SVGGraphics）不认
渐变（Shading/Pattern），封面会整页发白（第 146 号踩过）。WeasyPrint 的内联 SVG 渐变也不稳定。
插图：书各自不同，放在一个只用纯色填充的 SVG 片段文件里（坐标同上），由配置 cover.art_svg 指定。
"""
import base64, io

NAVY_TOP = '#0c1830'; NAVY_BOT = '#1b2b52'; CREAM = '#f1e9d6'; GOLD = '#d4a84b'; TEAL = '#3fb8c6'
SANS = "'Noto Sans CJK SC','Noto Sans CJK JP',sans-serif"
SERIF = "'Noto Serif CJK SC','Noto Serif CJK JP',serif"


def _geom(W, H):
    s = min(W / 900, H / 1270)
    return s, (W - 900 * s) / 2, (H - 1270 * s) / 2


def _bands(W, H, n=64):
    hx = lambda c: tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    a, b = hx(NAVY_TOP), hx(NAVY_BOT)
    out = ''
    for k in range(n):
        t = k / (n - 1)
        col = '#%02x%02x%02x' % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
        out += (f'<div style="position:absolute;left:0;top:{H * k / n:.3f}mm;width:{W}mm;'
                f'height:{H / n + 0.05:.3f}mm;background:{col}"></div>')
    return out


def _svg_layer(ring, art=''):
    cx, cy, r = ring
    dots = ''.join(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#ffffff" fill-opacity="0.05"/>'
                   for x in range(30, 900, 36) for y in range(30, 1270, 36))
    rings = ''.join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" '
                    f'stroke-opacity="{op}" stroke-width="{w}"/>'
                    for w, op in [(46, .025), (30, .04), (18, .06), (9, .10), (3, .30)])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1270" preserveAspectRatio="xMidYMid meet" '
            'style="position:absolute;left:0;top:0;width:100%;height:100%">' + dots + rings + art + '</svg>')


def _txt(W, H, x, y, size, text, color=CREAM, font='serif', weight=700, ls=0):
    s, ox, oy = _geom(W, H)
    fam = SERIF if font == 'serif' else SANS
    return (f'<div style="position:absolute;left:{ox + x * s:.2f}mm;top:{oy + y * s:.2f}mm;font-family:{fam};'
            f'font-size:{size * s:.2f}mm;font-weight:{weight};color:{color};letter-spacing:{ls * s:.2f}mm;'
            f'line-height:1;white-space:nowrap">{text}</div>')


def _rule(W, H, x, y, w, opacity=.55):
    s, ox, oy = _geom(W, H)
    return (f'<div style="position:absolute;left:{ox + x * s:.2f}mm;top:{oy + y * s:.2f}mm;width:{w * s:.2f}mm;'
            f'border-top:{1.2 * s:.2f}mm solid rgba(241,233,214,{opacity})"></div>')


def _wrap(W, H, parts):
    return (f'<div class="cover" style="position:relative;width:{W}mm;height:{H}mm;overflow:hidden;'
            f'background:{NAVY_BOT}">' + ''.join(parts) + '</div>')


def front_cover(W, H, cfg):
    c = cfg['cover']
    art = open(c['art_svg'], encoding='utf-8').read() if c.get('art_svg') else ''
    parts = [_bands(W, H), _svg_layer(c.get('ring', [640, 760, 300]), art)]
    parts.append(_txt(W, H, 60, 168, 46, cfg['title_small']))
    big = cfg['title_big']
    parts.append(_txt(W, H, 54, 238, 124 if len(big) <= 4 else 96, big, ls=6))
    parts.append(_txt(W, H, 62, 404, 25, cfg['subtitle'], color=GOLD, font='sans', weight=500))
    parts.append(_rule(W, H, 60, 1040, 250))
    parts.append(_txt(W, H, 60, 1072, 34, cfg['author'] + '　著', font='sans', weight=500, ls=4))
    parts.append(_txt(W, H, 60, 1168, 24, cfg['publisher_cn'], font='sans', weight=500, ls=2))
    parts.append(_txt(W, H, 60, 1204, 15, cfg['publisher_en'], font='sans', weight=400, ls=2.6, color='#c9c2b0'))
    return _wrap(W, H, parts)


def _ean_svg(isbn):
    import barcode
    from barcode.writer import SVGWriter
    code = isbn.replace('-', '')
    buf = io.BytesIO()
    barcode.get_barcode_class('ean13')(code, writer=SVGWriter()).write(buf, options={
        'module_width': 0.33, 'module_height': 16, 'font_size': 7, 'text_distance': 3.5,
        'quiet_zone': 2, 'background': 'white', 'foreground': 'black'})
    return buf.getvalue().decode('utf-8')


def back_cover(W, H, cfg):
    b = cfg['back_cover']
    parts = [_bands(W, H), _svg_layer(b.get('ring', [720, 250, 230]))]
    y = 120
    for l in b['verdict_lines']:
        parts.append(_txt(W, H, 70, y, 31, l, color='#ffffff', font='sans', weight=500)); y += 52
    y += 40
    for l in b['blurb_lines']:
        parts.append(_txt(W, H, 70, y, 25, l, color='#e9e4d6', font='sans', weight=400)); y += 44
    y += 50
    parts.append(_txt(W, H, 70, y, 24, b['quote'], color=GOLD, font='sans', weight=500))
    parts.append(_rule(W, H, 70, 1085, 360, .5))
    parts.append(_txt(W, H, 70, 1112, 19, f"{cfg['publisher_cn']} · {cfg['publisher_en']}", color='#e9e4d6', font='sans', weight=400))
    parts.append(_txt(W, H, 70, 1146, 19, f"{cfg['series_label']}第 {cfg['number']} 号", color='#e9e4d6', font='sans', weight=400))
    parts.append(_txt(W, H, 70, 1180, 19, f"定价：{cfg['price_back']}", color='#e9e4d6', font='sans', weight=400))
    s, ox, oy = _geom(W, H)
    if cfg.get('isbn'):
        b64 = base64.b64encode(_ean_svg(cfg['isbn']).encode()).decode()
        bx, by, bw, bh = 600, 1040, 240, 190
        parts.append(f'<div style="position:absolute;left:{ox + bx * s:.2f}mm;top:{oy + by * s:.2f}mm;width:{bw * s:.2f}mm;'
                     f'height:{bh * s:.2f}mm;background:#fff;box-sizing:border-box;padding:{8 * s:.2f}mm {10 * s:.2f}mm">'
                     f'<div style="font-family:{SANS};font-size:{13 * s:.2f}mm;color:#000;text-align:center;line-height:1.2">'
                     f'ISBN {cfg["isbn"]}</div><img src="data:image/svg+xml;base64,{b64}" '
                     f'style="display:block;width:100%;height:{140 * s:.2f}mm;object-fit:contain"/></div>')
    return _wrap(W, H, parts)

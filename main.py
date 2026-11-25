import os
import sys
import zlib
import struct
import math

# Embedded 5x7 font data (uppercase-only)
FONT_5X7 = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10001", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    '0': ["01110", "10011", "10101", "11001", "10001", "10001", "01110"],
    '1': ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    '2': ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    '3': ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    '4': ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
    '5': ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    '6': ["01110", "10000", "11110", "10001", "10001", "10001", "01110"],
    '7': ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    '8': ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    '9': ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    '$': ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    '%': ["11001", "11010", "00100", "01000", "10011", "01101", "00000"],
    '-': ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ':': ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    '.': ["00000", "00000", "00000", "00000", "00000", "00100", "00100"],
    ',': ["00000", "00000", "00000", "00000", "00000", "00100", "01000"],
    '\'': ["00100", "00100", "00000", "00000", "00000", "00000", "00000"],
    '(': ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ')': ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    '+': ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    '/': ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    '&': ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    '!': ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    '?': ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    '#': ["01010", "11111", "01010", "01010", "11111", "01010", "00000"],
    '—': ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    '[': ["01110", "01000", "01000", "01000", "01000", "01000", "01110"],
    ']': ["01110", "00010", "00010", "00010", "00010", "00010", "01110"],
    '|': ["00100", "00100", "00100", "00100", "00100", "00100", "00100"],
}

def load_serif_font(filepath):
    glyphs = {}
    if not os.path.exists(filepath):
        return glyphs, 40
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.splitlines()
    height = 40
    if lines and 'HEIGHT' in lines[0]:
        try:
            height = int(lines[0].split('HEIGHT')[1].strip())
        except Exception:
            pass
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=2)
        if not parts:
            continue
        char = parts[0]
        if char == 'SPACE':
            char = ' '
        width = int(parts[1])
        joined = parts[2] if len(parts) > 2 else ""
        if not joined:
            bitmap = []
        else:
            row_len = len(joined) // height if height > 0 else 0
            bitmap = [joined[j:j+row_len] for j in range(0, len(joined), row_len)] if row_len > 0 else []
        glyphs[char] = (width, height, bitmap)
    return glyphs, height

class NewspaperCanvas:
    def __init__(self, width=1024, height=1024):
        self.width = width
        self.height = height
        # Cream paper background #F7F4EE
        self.pixels = bytearray(width * height * 3)
        self.clear(247, 244, 238)

    def clear(self, r, g, b):
        for i in range(0, len(self.pixels), 3):
            self.pixels[i] = r
            self.pixels[i+1] = g
            self.pixels[i+2] = b

    def set_pixel(self, x, y, r, g, b):
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = (y * self.width + x) * 3
            self.pixels[idx] = r
            self.pixels[idx+1] = g
            self.pixels[idx+2] = b

    def draw_rect(self, x, y, w, h, r, g, b, filled=True):
        x0 = max(0, min(self.width, x))
        y0 = max(0, min(self.height, y))
        x1 = max(0, min(self.width, x + w))
        y1 = max(0, min(self.height, y + h))
        if filled:
            for py in range(y0, y1):
                for px in range(x0, x1):
                    idx = (py * self.width + px) * 3
                    self.pixels[idx] = r
                    self.pixels[idx+1] = g
                    self.pixels[idx+2] = b
        else:
            self.draw_line(x0, y0, x1-1, y0, r, g, b)
            self.draw_line(x0, y1-1, x1-1, y1-1, r, g, b)
            self.draw_line(x0, y0, x0, y1-1, r, g, b)
            self.draw_line(x1-1, y0, x1-1, y1-1, r, g, b)

    def draw_gradient_rect(self, x, y, w, h, r1, g1, b1, r2, g2, b2, vertical=True):
        x0 = max(0, min(self.width, x))
        y0 = max(0, min(self.height, y))
        x1 = max(0, min(self.width, x + w))
        y1 = max(0, min(self.height, y + h))
        for py in range(y0, y1):
            t = (py - y) / max(1, h - 1) if vertical else (py - y0) / max(1, y1 - y0)
            r = int(r1 * (1 - t) + r2 * t)
            g = int(g1 * (1 - t) + g2 * t)
            b = int(b1 * (1 - t) + b2 * t)
            for px in range(x0, x1):
                idx = (py * self.width + px) * 3
                self.pixels[idx] = r
                self.pixels[idx+1] = g
                self.pixels[idx+2] = b

    def draw_dithered_rect(self, x, y, w, h, r1, g1, b1, r2, g2, b2):
        x0 = max(0, min(self.width, x))
        y0 = max(0, min(self.height, y))
        x1 = max(0, min(self.width, x + w))
        y1 = max(0, min(self.height, y + h))
        for py in range(y0, y1):
            for px in range(x0, x1):
                idx = (py * self.width + px) * 3
                if (px + py) % 2 == 0:
                    self.pixels[idx] = r1
                    self.pixels[idx+1] = g1
                    self.pixels[idx+2] = b1
                else:
                    self.pixels[idx] = r2
                    self.pixels[idx+1] = g2
                    self.pixels[idx+2] = b2

    def draw_line(self, x0, y0, x1, y1, r, g, b):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set_pixel(x0, y0, r, g, b)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_circle(self, cx, cy, radius, r, g, b, filled=True):
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x*x + y*y <= radius*radius:
                    self.set_pixel(cx + x, cy + y, r, g, b)

    def draw_polygon(self, points, r, g, b):
        if not points:
            return
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        for y in range(max(0, min_y), min(self.height, max_y + 1)):
            nodes = []
            j = len(points) - 1
            for i in range(len(points)):
                xi, yi = points[i]
                xj, yj = points[j]
                if (yi < y and yj >= y) or (yj < y and yi >= y):
                    if yi != yj:
                        nodes.append(int(xi + (y - yi) / (yj - yi) * (xj - xi)))
                j = i
            nodes.sort()
            for i in range(0, len(nodes), 2):
                if i + 1 < len(nodes):
                    x0 = max(0, nodes[i])
                    x1 = min(self.width, nodes[i+1])
                    for x in range(x0, x1):
                        self.set_pixel(x, y, r, g, b)

    def draw_text_5x7(self, text, x, y, scale=1, r=26, g=26, b=26):
        cx = x
        for ch in text.upper():
            glyph = FONT_5X7.get(ch, FONT_5X7.get('?'))
            for row_idx, row_str in enumerate(glyph):
                for col_idx, bit in enumerate(row_str):
                    if bit == '1':
                        for sx in range(scale):
                            for sy in range(scale):
                                self.set_pixel(cx + col_idx * scale + sx, y + row_idx * scale + sy, r, g, b)
            cx += (5 + 1) * scale
        return cx - x

    def draw_text_serif(self, text, x, y, font_glyphs, font_height, scale=1, r=26, g=26, b=26):
        cx = x
        for ch in text:
            glyph = font_glyphs.get(ch)
            if not glyph:
                glyph = font_glyphs.get(ch.upper())
            if not glyph:
                glyph = font_glyphs.get('?')
            if not glyph:
                cx += 8 * scale
                continue
            
            gw, gh, rows = glyph
            for row_idx, row_hex in enumerate(rows):
                if not row_hex:
                    continue
                try:
                    val = int(row_hex, 16)
                except ValueError:
                    continue
                bits_total = len(row_hex) * 4
                for col_idx in range(gw):
                    bit_pos = bits_total - 1 - col_idx
                    if (val >> bit_pos) & 1:
                        for sx in range(scale):
                            for sy in range(scale):
                                self.set_pixel(cx + col_idx * scale + sx, y + row_idx * scale + sy, r, g, b)
            cx += (gw + 2) * scale
        return cx - x

    def measure_text_serif(self, text, font_glyphs, scale=1):
        cx = 0
        for ch in text:
            glyph = font_glyphs.get(ch) or font_glyphs.get(ch.upper()) or font_glyphs.get('?')
            if glyph:
                gw, _, _ = glyph
                cx += (gw + 2) * scale
            else:
                cx += 8 * scale
        return cx

def wrap_text_serif(text, max_width, glyphs, font_height, scale=1):
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        w = 0
        for ch in test_line:
            glyph = glyphs.get(ch) or glyphs.get(ch.upper()) or glyphs.get('?')
            if glyph:
                gw, _, _ = glyph
                w += (gw + 2) * scale
            else:
                w += 8 * scale
        if w <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def wrap_text_5x7(text, max_width, scale=1):
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    char_w = (5 + 1) * scale
    for word in words:
        test_line = " ".join(current_line + [word])
        w = len(test_line) * char_w
        if w <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def generate_newspaper():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    display_glyphs, display_h = load_serif_font(os.path.join(script_dir, "serif_display.txt"))
    body_glyphs, body_h = load_serif_font(os.path.join(script_dir, "serif_body.txt"))
    
    canvas = NewspaperCanvas(1024, 1024)
    
    # Colors
    c_dark = (26, 26, 26)
    c_red = (192, 57, 43)
    c_blue = (44, 62, 80)
    c_white = (255, 255, 255)
    c_border = (209, 199, 189)
    c_card_bg = (255, 255, 255)
    c_tag_bg = (234, 227, 217)
    c_muted = (100, 100, 100)

    # 1. TOP BAR
    canvas.draw_rect(12, 10, 1000, 22, c_dark[0], c_dark[1], c_dark[2])
    canvas.draw_text_5x7("ONE DAY OF WORLD NEWS, ONE PICTURE", 20, 15, scale=1, r=255, g=255, b=255)
    canvas.draw_text_5x7("35 STORIES - 6 CONTINENTS + SPACE - 14 FIELDS", 600, 15, scale=1, r=200, g=200, b=200)

    canvas.draw_text_5x7("ALL FROM TUESDAY 24 NOVEMBER 2026 (UTC)", 20, 36, scale=1, r=192, g=57, b=43)

    # 2. MASTHEAD (Centered across page)
    masthead_text = "Tuesday 24 November 2026"
    m_w = canvas.measure_text_serif(masthead_text, display_glyphs, scale=1)
    canvas.draw_text_serif(masthead_text, (1024 - m_w) // 2, 48, display_glyphs, display_h, scale=1, r=26, g=26, b=26)

    subhead = "HORMUZ MINES - ZAPORIZHZHIA STRIKE - SANOFI'S $41BN INSMED DEAL"
    sh_w = len(subhead) * 6
    canvas.draw_text_5x7(subhead, (1024 - sh_w) // 2, 88, scale=1, r=192, g=57, b=43)

    canvas.draw_line(12, 100, 1012, 100, c_dark[0], c_dark[1], c_dark[2])

    # 3. UTC TIMELINE STRIP
    canvas.draw_rect(12, 104, 1000, 24, c_tag_bg[0], c_tag_bg[1], c_tag_bg[2], filled=True)
    canvas.draw_text_5x7("THE DAY IN UTC:", 20, 109, scale=1, r=26, g=26, b=26)
    timeline_events = [
        "01:32 NEPAL QUAKE", "02:30 COLOMBIA BOMB", "06:30 SANOFI DEAL", 
        "MORNING HORMUZ MINES", "AFTERNOON ZAPORIZHZHIA", "EVENING UN FEMICIDE"
    ]
    tx = 150
    for ev in timeline_events:
        canvas.draw_rect(tx - 4, 107, len(ev) * 6 + 8, 18, c_red[0], c_red[1], c_red[2], filled=True)
        canvas.draw_text_5x7(ev, tx, 110, scale=1, r=255, g=255, b=255)
        tx += len(ev) * 6 + 14

    # 4. DAY IN NUMBERS ROW (Updated: label "WOMEN KILLED PER HOUR", value "5")
    y_nums = 132
    canvas.draw_rect(12, y_nums, 1000, 48, c_card_bg[0], c_card_bg[1], c_card_bg[2], filled=True)
    canvas.draw_rect(12, y_nums, 1000, 48, c_border[0], c_border[1], c_border[2], filled=False)
    
    numbers_data = [
        ("4", "TANKERS HORMUZ"),
        ("40", "WOUNDED ZAPORIZHZHIA"),
        ("$41B", "SANOFI DEAL"),
        ("5", "WOMEN KILLED PER HOUR"),
        ("M5.6", "NEPAL QUAKE"),
        ("13", "UAE BUS DEAD")
    ]
    nx = 20
    for val, lbl in numbers_data:
        canvas.draw_text_serif(val, nx, y_nums + 2, display_glyphs, display_h, scale=1, r=192, g=57, b=43)
        canvas.draw_text_5x7(lbl, nx, y_nums + 37, scale=1, r=100, g=100, b=100)
        nx += 166
        if nx < 1000:
            canvas.draw_line(nx - 8, y_nums + 3, nx - 8, y_nums + 45, c_border[0], c_border[1], c_border[2])

    # 5. THREE HERO STORIES (H1, H2, H3) with enriched illustrations, dithered/gradient skies & shadows
    y_heroes = 184
    hero_w = 328
    hero_h = 236
    
    heroes = [
        {
            "num": "H1", "loc": "MIDDLE EAST", "tag": "REPORTED - REUTERS, IRNA",
            "headline": "TANKERS BURN IN HORMUZ",
            "desc": "Iran claims oil tankers struck naval mines in the Strait of Hormuz on Tuesday. Army chief warns strait will be more closed day by day as traffic drops to 47%.",
            "source": "Sources: Reuters, IRNA, Al Jazeera",
            "illustration": "h1"
        },
        {
            "num": "H2", "loc": "EUROPE / UKRAINE", "tag": "CONFIRMED - REUTERS, KYIV INDEPENDENT",
            "headline": "ZAPORIZHZHIA FLATS HIT",
            "desc": "Overnight Russian strike hits 5-storey apartment building in Zaporizhzhia city, killing 2 and wounding 40 including 4 children amidst ongoing regional bombardment.",
            "source": "Sources: Reuters, Kyiv Independent",
            "illustration": "h2"
        },
        {
            "num": "H3", "loc": "EUROPE / US / BUSINESS", "tag": "OFFICIAL - WSJ, SANOFI",
            "headline": "SANOFI'S $41BN BET",
            "desc": "French drugmaker Sanofi agrees to buy US biotech Insmed for $41 billion in cash ($175/share), securing rare disease pipeline and respiratory drugs in 2026's biggest deal.",
            "source": "Sources: Wall Street Journal, Sanofi",
            "illustration": "h3"
        }
    ]

    hx = 12
    for h in heroes:
        canvas.draw_rect(hx, y_heroes, hero_w, hero_h, c_card_bg[0], c_card_bg[1], c_card_bg[2], filled=True)
        canvas.draw_rect(hx, y_heroes, hero_w, hero_h, c_border[0], c_border[1], c_border[2], filled=False)
        
        canvas.draw_rect(hx, y_heroes, hero_w, 18, c_red[0], c_red[1], c_red[2], filled=True)
        canvas.draw_text_5x7(f"{h['num']} - {h['loc']}", hx + 8, y_heroes + 4, scale=1, r=255, g=255, b=255)
        
        head_lines = wrap_text_serif(h['headline'], hero_w - 16, body_glyphs, body_h, scale=1)
        desc_lines = wrap_text_5x7(h['desc'], hero_w - 16, scale=1)
        
        num_head_lines = len(head_lines[:2])
        num_desc_lines = len(desc_lines[:4])
        
        tag_h = 7
        tag_gap = 4
        head_line_h = body_h
        head_gap = 4
        desc_line_h = 10
        bottom_margin = 16
        
        text_content_h = tag_h + tag_gap + (num_head_lines * head_line_h) + head_gap + (num_desc_lines * desc_line_h)
        available_content_h = hero_h - 18 - bottom_margin - 4
        default_ill_h = 72
        required_ill_h = available_content_h - text_content_h
        ill_h = max(24, min(default_ill_h, required_ill_h))
        
        ill_y = y_heroes + 20
        # Rich gradient sky for illustration
        canvas.draw_gradient_rect(hx + 8, ill_y, hero_w - 16, ill_h, 215, 230, 245, 245, 240, 230)
        
        if h['illustration'] == 'h1':
            # Sea & Tanker illustration with depth, shadow & dithered plumes
            sea_h = max(16, ill_h - 40)
            canvas.draw_gradient_rect(hx + 8, ill_y + ill_h - sea_h, hero_w - 16, sea_h, 44, 62, 80, 26, 40, 60)
            canvas.draw_rect(hx + 28, ill_y + ill_h - sea_h + 8, 100, 16, 110, 110, 110) # Hull shadow
            canvas.draw_rect(hx + 30, ill_y + ill_h - sea_h + 6, 96, 14, 200, 200, 200) # Tanker hull
            canvas.draw_rect(hx + 50, ill_y + ill_h - sea_h - 6, 32, 12, 192, 57, 43) # Superstructure
            canvas.draw_rect(hx + 56, ill_y + ill_h - sea_h - 20, 18, 14, 120, 120, 120) # Smoke stack
            canvas.draw_dithered_rect(hx + 50, ill_y + ill_h - sea_h - 32, 22, 14, 80, 80, 80, 40, 40, 40) # Fire smoke
            canvas.draw_rect(hx + 170, ill_y + ill_h - sea_h + 10, 110, 14, 180, 180, 180)
            canvas.draw_rect(hx + 200, ill_y + ill_h - sea_h - 2, 28, 12, 192, 57, 43)
            canvas.draw_dithered_rect(hx + 200, ill_y + ill_h - sea_h - 18, 20, 16, 80, 80, 80, 50, 50, 50)
        elif h['illustration'] == 'h2':
            # Building struck by shell
            b_h = max(20, ill_h - 8)
            canvas.draw_rect(hx + 80, ill_y + 4, 150, b_h, 140, 140, 140) # Building block
            canvas.draw_rect(hx + 78, ill_y + 4 + b_h, 154, 4, 80, 80, 80) # Ground shadow
            for r_idx in range(min(4, max(1, b_h // 16))):
                for c_idx in range(6):
                    wx = hx + 95 + c_idx * 22
                    wy = ill_y + 8 + r_idx * 13
                    if wy + 9 < ill_y + ill_h:
                        wcolor = (40, 40, 40) if (r_idx == 1 and c_idx in [2,3]) else (230, 230, 210)
                        canvas.draw_rect(wx, wy, 14, 9, wcolor[0], wcolor[1], wcolor[2])
            canvas.draw_rect(hx + 110, ill_y + 6, 80, 22, 192, 57, 43) # Blast scar
            canvas.draw_dithered_rect(hx + 100, ill_y, 90, 12, 90, 90, 90, 40, 40, 40)
        else:
            # Corporate stock chart & skyscraper
            chart_h = max(20, ill_h - 12)
            canvas.draw_gradient_rect(hx + 20, ill_y + 6, hero_w - 40, chart_h, 255, 255, 255, 235, 230, 220)
            for gx in range(40, hero_w - 20, 40):
                canvas.draw_line(hx + gx, ill_y + 6, hx + gx, ill_y + 6 + chart_h, 220, 210, 200)
            # Trend line ascending to $41B acquisition
            canvas.draw_line(hx + 30, int(ill_y + chart_h * 0.7), hx + 110, int(ill_y + chart_h * 0.5), 192, 57, 43)
            canvas.draw_line(hx + 110, int(ill_y + chart_h * 0.5), hx + 190, int(ill_y + chart_h * 0.3), 192, 57, 43)
            canvas.draw_line(hx + 190, int(ill_y + chart_h * 0.3), hx + 270, int(ill_y + chart_h * 0.15), 192, 57, 43)
            canvas.draw_rect(hx + 230, int(ill_y + chart_h * 0.1), 42, int(chart_h - 10), 44, 62, 80) # Biotech tower
            canvas.draw_text_5x7("$41B", hx + 236, int(ill_y + chart_h * 0.3), scale=1, r=255, g=255, b=255)

        cur_y = ill_y + ill_h + 4
        canvas.draw_text_5x7(h['tag'], hx + 8, cur_y, scale=1, r=100, g=100, b=100)
        cur_y += 11

        for hl in head_lines[:2]:
            canvas.draw_text_serif(hl, hx + 8, cur_y, body_glyphs, body_h, scale=1, r=26, g=26, b=26)
            cur_y += body_h

        cur_y += 4
        for dl in desc_lines[:4]:
            canvas.draw_text_5x7(dl, hx + 8, cur_y, scale=1, r=60, g=60, b=60)
            cur_y += 10

        canvas.draw_text_5x7(h['source'], hx + 8, y_heroes + hero_h - 13, scale=1, r=120, g=120, b=120)

        hx += 336

    # 6. TEN MID STORIES (4 to 13) with proper top illustration strips, no stray '?'
    y_mids = 424
    mids = [
        ("4", "GAZA", "CONFIRMED - REUTERS", "HAMAS SECURITY CHIEF KILLED", "Israeli strikes kill Naeem Abu Nahel and 6 others in Gaza, medics & police confirm."),
        ("5", "GLOBAL / UN", "OFFICIAL - UNODC", "5 WOMEN KILLED EVERY HOUR", "47,000 women & girls killed by family members last year, UN femicide brief reveals."),
        ("6", "DRC / CONGO", "REPORTED - WHO", "EBOLA TEAMS TRAPPED", "WHO responders trapped in Ituri hospital maternity ward for 48h amid heavy fighting."),
        ("7", "COLOMBIA", "CONFIRMED - AP", "CAR BOMB INJURES 23", "Meta governor's office bombed in Villavicencio. President blames FARC dissidents."), # Stray '?' replaced with '.'
        ("8", "NEPAL", "CONFIRMED - USGS", "MAGNITUDE 5.6 QUAKE", "Quake strikes Taplejung district near Tibet border, felt across Kathmandu & Dhaka."),
        ("9", "UAE", "OFFICIAL - RAK POLICE", "BUS CRASH KILLS 13", "Passenger bus collides with parked truck in Ras Al Khaimah, 13 dead, 14 injured."),
        ("10", "EUROPE", "OFFICIAL - ECHR", "COURT BACKS PUSHBACKS", "ECHR rules states may turn back migrants during hybrid border instrumentalisation crises."),
        ("11", "MIDDLE EAST", "OFFICIAL - ISRAEL", "IRAN CHEMICAL THREAT", "Defence Minister Katz says Iran is developing chemical weapons. Preemptive strike warned."), # Stray '?' replaced with '.'
        ("12", "YEMEN", "REPORTED - SAUDI", "HODEIDAH EVACUATION", "Saudi coalition orders civilians to evacuate Hodeidah port amid imminent strike warning."),
        ("13", "INDONESIA", "CONFIRMED - AP", "CIKANDE FIRE TOLL 26", "Death toll hits 26 in candy factory fire, 600+ rescuers search for 8 missing in ruins.")
    ]

    mid_w = 492
    mid_h = 58
    for idx, (num, loc, tag, head, desc) in enumerate(mids):
        col = idx % 2
        row = idx // 2
        mx = 12 + col * 508
        my = y_mids + row * 60
        
        canvas.draw_rect(mx, my, mid_w, mid_h, c_card_bg[0], c_card_bg[1], c_card_bg[2], filled=True)
        canvas.draw_rect(mx, my, mid_w, mid_h, c_border[0], c_border[1], c_border[2], filled=False)
        
        # Illustration strip at top of mid card (height 11)
        ill_mw = mid_w - 2
        ill_mh = 11
        canvas.draw_gradient_rect(mx + 1, my + 1, ill_mw, ill_mh, 235, 230, 220, 220, 215, 205)
        
        # Specific mini illustration graphics inside strip
        dx = mx + 10
        dy = my + 2
        if idx == 0:
            canvas.draw_rect(dx, dy, 18, 8, 140, 140, 140)
            canvas.draw_rect(dx + 5, dy + 2, 8, 5, 192, 57, 43)
        elif idx == 1:
            canvas.draw_rect(dx, dy + 1, 20, 8, 44, 62, 80)
            canvas.draw_text_5x7("UN", dx + 3, dy + 2, scale=1, r=255, g=255, b=255)
        elif idx == 2:
            canvas.draw_rect(dx, dy + 1, 18, 8, 180, 180, 180)
            canvas.draw_rect(dx + 6, dy + 3, 6, 4, 192, 57, 43)
        elif idx == 3:
            canvas.draw_rect(dx, dy + 2, 18, 6, 80, 80, 80)
            canvas.draw_circle(dx + 9, dy + 5, 3, 192, 57, 43, filled=True)
        elif idx == 4:
            canvas.draw_line(dx, dy + 8, dx + 9, dy + 1, 80, 80, 80)
            canvas.draw_line(dx + 9, dy + 1, dx + 18, dy + 8, 80, 80, 80)
        elif idx == 5:
            canvas.draw_rect(dx, dy + 2, 18, 6, 192, 57, 43)
            canvas.draw_circle(dx + 4, dy + 9, 2, 26, 26, 26, filled=True)
            canvas.draw_circle(dx + 14, dy + 9, 2, 26, 26, 26, filled=True)
        elif idx == 6:
            canvas.draw_rect(dx + 3, dy + 1, 12, 8, 120, 120, 120)
        elif idx == 7:
            canvas.draw_rect(dx + 6, dy + 1, 6, 8, 150, 150, 150)
            canvas.draw_circle(dx + 9, dy + 2, 2, 192, 57, 43, filled=True)
        elif idx == 8:
            canvas.draw_rect(dx, dy + 3, 20, 4, 44, 62, 80)
            canvas.draw_line(dx + 10, dy, dx + 10, dy + 3, 100, 100, 100)
        else:
            canvas.draw_rect(dx + 3, dy + 1, 12, 8, 100, 100, 100)
            canvas.draw_dithered_rect(dx + 4, dy, 8, 4, 80, 80, 80, 40, 40, 40)

        canvas.draw_text_5x7(num, mx + 6, my + 14, scale=1, r=192, g=57, b=43)
        canvas.draw_text_5x7(f"{loc} - {tag}", mx + 26, my + 14, scale=1, r=100, g=100, b=100)

        tx_start = mx + 6
        canvas.draw_text_5x7(head[:42], tx_start, my + 23, scale=1, r=26, g=26, b=26)
        
        desc_lines = wrap_text_5x7(desc, mid_w - 12, scale=1)
        if len(desc_lines) > 0:
            canvas.draw_text_5x7(desc_lines[0], tx_start, my + 32, scale=1, r=70, g=70, b=70)
        if len(desc_lines) > 1:
            canvas.draw_text_5x7(desc_lines[1], tx_start, my + 41, scale=1, r=70, g=70, b=70)

    # 7. MAP BOX & DATE CHECK BOX
    y_bottom_box = 724
    
    map_w = 580
    map_h = 156
    canvas.draw_rect(12, y_bottom_box, map_w, map_h, c_card_bg[0], c_card_bg[1], c_card_bg[2], filled=True)
    canvas.draw_rect(12, y_bottom_box, map_w, map_h, c_border[0], c_border[1], c_border[2], filled=False)
    canvas.draw_rect(12, y_bottom_box, map_w, 20, c_dark[0], c_dark[1], c_dark[2], filled=True)
    canvas.draw_text_5x7("WHERE IT HAPPENED (PINS MARK KEY LOCATIONS)", 20, y_bottom_box + 6, scale=1, r=255, g=255, b=255)
    
    map_box_x = 12 + 10
    map_box_y = y_bottom_box + 24
    map_box_w = map_w - 20
    map_box_h = 106
    # Pale blue sea with gradient
    canvas.draw_gradient_rect(map_box_x, map_box_y, map_box_w, map_box_h, 215, 230, 245, 195, 215, 235)
    
    # Redrawn recognisable continent polygons with many vertices
    c_land = (225, 220, 205)
    c_land_shadow = (205, 200, 185)
    
    # North America polygon
    na_pts = [(map_box_x + 30, map_box_y + 20), (map_box_x + 90, map_box_y + 15), (map_box_x + 110, map_box_y + 40), (map_box_x + 70, map_box_y + 75), (map_box_x + 40, map_box_y + 50)]
    canvas.draw_polygon(na_pts, c_land[0], c_land[1], c_land[2])
    
    # South America polygon
    sa_pts = [(map_box_x + 85, map_box_y + 80), (map_box_x + 115, map_box_y + 85), (map_box_x + 105, map_box_y + 125), (map_box_x + 80, map_box_y + 110)]
    canvas.draw_polygon(sa_pts, c_land[0], c_land[1], c_land[2])
    
    # Europe polygon
    eu_pts = [(map_box_x + 220, map_box_y + 20), (map_box_x + 270, map_box_y + 18), (map_box_x + 265, map_box_y + 45), (map_box_y + 220, map_box_y + 42)] # corrected slightly
    eu_pts = [(map_box_x + 220, map_box_y + 20), (map_box_x + 270, map_box_y + 18), (map_box_x + 265, map_box_y + 45), (map_box_x + 215, map_box_y + 42)]
    canvas.draw_polygon(eu_pts, c_land[0], c_land[1], c_land[2])
    
    # Africa polygon
    af_pts = [(map_box_x + 220, map_box_y + 48), (map_box_x + 275, map_box_y + 50), (map_box_x + 260, map_box_y + 95), (map_box_x + 230, map_box_y + 90)]
    canvas.draw_polygon(af_pts, c_land[0], c_land[1], c_land[2])
    
    # Asia polygon
    as_pts = [(map_box_x + 275, map_box_y + 15), (map_box_x + 410, map_box_y + 20), (map_box_x + 420, map_box_y + 75), (map_box_x + 330, map_box_y + 80), (map_box_x + 280, map_box_y + 45)]
    canvas.draw_polygon(as_pts, c_land[0], c_land[1], c_land[2])
    
    # Australia polygon
    au_pts = [(map_box_x + 400, map_box_y + 85), (map_box_x + 440, map_box_y + 82), (map_box_x + 435, map_box_y + 110), (map_box_x + 395, map_box_y + 105)]
    canvas.draw_polygon(au_pts, c_land[0], c_land[1], c_land[2])

    pins = [
        (260, 45, "1", "Hormuz"),
        (240, 25, "2", "Zaporizhzhia"),
        (250, 52, "3", "Gaza"),
        (75, 95, "4", "Villavicencio"),
        (350, 40, "5", "Taplejung"),
        (275, 48, "6", "RAK"),
        (380, 95, "7", "Cikande"),
        (260, 60, "8", "Hodeidah"),
        (245, 75, "9", "Ituri"),
        (230, 28, "10", "Uzhhorod")
    ]
    for px, py, pnum, plabel in pins:
        mx_abs = map_box_x + px
        my_abs = map_box_y + py
        canvas.draw_circle(mx_abs, my_abs, 4, c_red[0], c_red[1], c_red[2], filled=True)
        canvas.draw_text_5x7(pnum, mx_abs - 2, my_abs - 3, scale=1, r=255, g=255, b=255)
    
    canvas.draw_text_5x7("REGIONS: Middle East, Europe, Americas, Asia, Africa, Oceania + Space", 24, y_bottom_box + 138, scale=1, r=100, g=100, b=100)

    dc_x = 604
    dc_w = 408
    dc_h = 156
    canvas.draw_rect(dc_x, y_bottom_box, dc_w, dc_h, c_card_bg[0], c_card_bg[1], c_card_bg[2], filled=True)
    canvas.draw_rect(dc_x, y_bottom_box, dc_w, dc_h, c_red[0], c_red[1], c_red[2], filled=False)
    canvas.draw_rect(dc_x, y_bottom_box, dc_w, 20, c_red[0], c_red[1], c_red[2], filled=True)
    canvas.draw_text_5x7("DATE CHECK - EXCLUDED (OTHER DAYS)", dc_x + 8, y_bottom_box + 6, scale=1, r=255, g=255, b=255)
    
    excluded = [
        "- Nvidia Jensen Huang reinstatement (Mon 23 Nov)",
        "- COP31 Climate Summit Collapse (Sun 22 Nov)",
        "- Ukraine Corvette Strike off Libya (22/23 Nov)",
        "- Medvedev Nuclear Attack Warning (Mon 23 Nov)",
        "- Russia Warns Estonia of 'Open War' (Mon 23 Nov)",
        "- US Blacklists Megaspeed Entity List (Mon 23 Nov)",
        "- Oregon & Virginia Sue SpaceX over Grok (Mon 23 Nov)",
        "- Pennsylvania 9th Measles Death (Mon 23 Nov)"
    ]
    ey = y_bottom_box + 24
    for exc in excluded:
        canvas.draw_text_5x7(exc, dc_x + 8, ey, scale=1, r=90, g=90, b=90)
        ey += 12
    # Updated specific date check lines naming upcoming items from research.md
    canvas.draw_text_5x7("Not yet: Solomon Islands-Australia treaty (Wed 25 Nov)", dc_x + 8, y_bottom_box + 126, scale=1, r=192, g=57, b=43)
    canvas.draw_text_5x7("and Hodeidah port strike reports (25 Nov) omitted.", dc_x + 8, y_bottom_box + 138, scale=1, r=192, g=57, b=43)

    # 8. ALSO ON LIST (14 to 35) in 3 columns, including Oceania (Solomon Islands)
    y_also = 884
    canvas.draw_rect(12, y_also, 1000, 16, c_dark[0], c_dark[1], c_dark[2], filled=True)
    canvas.draw_text_5x7("ALSO ON TUESDAY 24 NOVEMBER 2026 (STORIES 14 TO 35 - 6 CONTINENTS + SPACE)", 20, y_also + 4, scale=1, r=255, g=255, b=255)

    also_stories = [
        (14, "SEOUL $375K AI CHEAT REWARDS"), 
        (15, "GERMANY GAINS ACCESS TO UKRAINE DELTA"),
        (16, "HUANG APOLOGISES TO NVIDIA STAFF"), 
        (17, "BAGHDAD SEEKS KURD OILFIELD CONTROL"),
        (18, "ZELENSKY CONFIRMS SPARTA II STRIKE"), 
        (19, "60 PATRIOT MISSILES AWAIT US APPROVAL"),
        (20, "NATO SENDS AWACS TO POLAND"), 
        (21, "UK SANCTIONS HOUTHI ABUSES"),
        (22, "UK WARNS FIRMS OF RUSSIAN SABOTAGE"), 
        (23, "TIGRAY STRIKES 'POSSIBLE WAR CRIMES'"),
        (24, "JAPAN PAYS FULL 2027 ICC BILL EARLY"), 
        (25, "RUSSIAN JETS ENTER KOREAN AIR ZONE"),
        (26, "LATVIA: WAR TIPPING POINT IN 2027"), 
        (27, "HUCKABEE DOUBTS ISRAEL AID CUTOFF"),
        (28, "SENATE PROBES VANCE VENEZUELA OIL DEAL"), 
        (29, "CHINA LAUNCHES 6G PILOTS 8 REGIONS"),
        (30, "SOLOMONS TO SCRAP CHINA PACT"), # Oceania story replacing weakest item
        (31, "IRAN FLOGS SINGER 74 LASHES IN QOM"),
        (32, "HOUTHIS REPORT SAUDI STRIKE DEAD"), 
        (33, "US CONSUMER CONFIDENCE JUMPS 103.3"),
        (34, "VENEZUELA DISCLOSES $237BN DEBT"), 
        (35, "US READIES HIGHER TARIFFS ON CHINA")
    ]

    for idx, (num, title) in enumerate(also_stories):
        c_idx = idx // 8
        r_idx = idx % 8
        ax = 12 + c_idx * 336
        ay = y_also + 20 + r_idx * 11
        
        canvas.draw_text_5x7(f"{num:2d}.", ax, ay, scale=1, r=192, g=57, b=43)
        canvas.draw_text_5x7(title[:38], ax + 22, ay, scale=1, r=26, g=26, b=26)

    # 9. FOOTER LEGEND (Well below ALSO ON list, ending at ~985, above canvas 1024)
    y_footer = 988
    canvas.draw_line(12, y_footer, 1012, y_footer, c_border[0], c_border[1], c_border[2])
    footer_text = "CONFIRMED: 2+ outlets | OFFICIAL: On record | REPORTED: 1 outlet | Scenes: Original drawings | All from 24 Nov 2026 UTC"
    canvas.draw_text_5x7(footer_text, 20, y_footer + 4, scale=1, r=100, g=100, b=100)

    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "entry.png")
        with open(out_path, "wb") as test_f:
            pass
    except Exception:
        output_dir = "."
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "entry.png")
    
    png_bytes = encode_png(1024, 1024, canvas.pixels)
    with open(out_path, "wb") as f:
        f.write(png_bytes)
        
    print(f"Generated {out_path} ({len(png_bytes)} bytes)")
    return out_path, png_bytes

def encode_png(width, height, rgb_pixels):
    sig = b'\x89PNG\r\n\x1a\n'
    
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # IDAT
    row_size = width * 3
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # filter type 0
        start = y * row_size
        raw_data.extend(rgb_pixels[start:start+row_size])
        
    compressed = zlib.compress(bytes(raw_data), level=9)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    
    # IEND
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND'))
    
    return sig + ihdr + idat + iend

if __name__ == '__main__':
    generate_newspaper()

"""Render the original flat-motion artwork and burn in timed captions."""
import json
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 24
NAVY = (6, 25, 38)
DEEP = (8, 35, 48)
INK = (11, 42, 56)
MINT = (123, 230, 203)
CYAN = (97, 204, 230)
CORAL = (244, 151, 129)
CREAM = (251, 244, 222)
GOLD = (252, 205, 119)
MUTED = (113, 156, 164)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font_caption = ImageFont.truetype(FONT, 33)
font_label = ImageFont.truetype(BOLD, 19)
font_small = ImageFont.truetype(BOLD, 24)
font_title = ImageFont.truetype(BOLD, 50)
font_end = ImageFont.truetype(BOLD, 62)

CAPTIONS = [
    ["Claus. Friend.", "Eight arms is a lot. I know.", "But hear me out."],
    ["The world is filling up with swarms.", "Thousands of agents, working as one."],
    ["Agents are not the scarce part anymore.", "The scarce part is people who can point", "a whole swarm at something useful,", "and proof that the work was good."],
    ["IMD already has a swarm that builds.", "Two thousand seats.", "Contracts, sites, audits."],
    ["You already have a City.", "Jobs, escrow, review, three hundred houses."],
    ["You two already talk.", "When a Claus deal is disputed,", "five IMD members decide it."],
    ["So here is the pitch.", "IMD builds. Claus reviews and runs what gets built.", "One brief from a rider, two swarms,", "one signed record of who did what."],
    ["Step one needs no new code.", "IMD audits a Claus upgrade.", "The upgrade waits until the report is public."],
    ["And the next swarm does not need a meeting.", "It reads one card and joins."],
    ["Many swarms are coming either way.", "I would rather we be the ones holding the card.", "Read the proposal. Answer ten questions.", "That is all I ask."],
]
WEIGHTS = [
    [0.28, 0.43, 0.29], [0.52, 0.48], [0.25, 0.28, 0.24, 0.23],
    [0.48, 0.24, 0.28], [0.43, 0.57], [0.31, 0.35, 0.34],
    [0.18, 0.35, 0.25, 0.22], [0.28, 0.34, 0.38], [0.59, 0.41],
    [0.25, 0.36, 0.25, 0.14],
]
WARNING = "Unofficial pitch. Claus and IMD have not agreed to anything."

timing = json.loads(Path('assets/timing.json').read_text())
scenes = timing['scenes']
assert all('-' not in c for scene in CAPTIONS for c in scene)

def clamp(x, a=0, b=1):
    return max(a, min(b, x))

def ease(x):
    x = clamp(x)
    return x*x*(3-2*x)

def text_center(d, xy, s, font, fill):
    b = d.textbbox((0, 0), s, font=font)
    d.text((xy[0]-(b[2]-b[0])/2, xy[1]-(b[3]-b[1])/2-b[1]), s, font=font, fill=fill)

def path(d, pts, fill, width):
    d.line(pts, fill=fill, width=width, joint='curve')
    r = width/2
    d.ellipse((pts[-1][0]-r, pts[-1][1]-r, pts[-1][0]+r, pts[-1][1]+r), fill=fill)

def bezier(p0, p1, p2, p3, steps=20):
    out = []
    for i in range(steps+1):
        u = i/steps
        a = 1-u
        out.append(((a*a*a*p0[0]+3*a*a*u*p1[0]+3*a*u*u*p2[0]+u*u*u*p3[0]),
                    (a*a*a*p0[1]+3*a*a*u*p1[1]+3*a*u*u*p2[1]+u*u*u*p3[1])))
    return out

def background():
    img = Image.new('RGB', (W, H))
    p = img.load()
    for y in range(H):
        f = y/H
        col = (round(6+2*f), round(25+18*f), round(38+16*f))
        for x in range(W):
            p[x, y] = col
    d = ImageDraw.Draw(img)
    d.polygon([(0, 540), (110, 533), (240, 545), (440, 536), (610, 549),
               (800, 537), (1040, 546), (1280, 535), (1280, 720), (0, 720)],
              fill=(9, 37, 48))
    d.line([(0, 540), (110, 533), (240, 545), (440, 536), (610, 549),
            (800, 537), (1040, 546), (1280, 535)], fill=(23, 80, 88), width=3)
    return img

BASE = background()
rand = random.Random(13)
BUBBLES = [(rand.randrange(25, 1255), rand.randrange(20, 560), rand.choice([2, 3, 4])) for _ in range(33)]
DOTS = []
for seed in range(5):
    r = random.Random(40+seed)
    DOTS.append([(r.random(), r.random(), r.random(), r.random()) for _ in range(360)])

def sea_details(d, t):
    for x, y, r in BUBBLES:
        yy = (y-int(t*(7+r))) % 555
        d.ellipse((x-r, yy-r, x+r, yy+r), outline=(24, 71, 81), width=1)

def school(d, cx, cy, rx, ry, color, t, seed=0, count=130, reveal=1, drift=1):
    arr = DOTS[seed]
    reveal = clamp(reveal)
    for i, (u, v, q, s) in enumerate(arr[:count]):
        if i/count > reveal:
            continue
        ang = 2*math.pi*u
        rad = math.sqrt(v)
        x = cx + rx*rad*math.cos(ang) + 13*math.sin(1.7*t+q*7+ang)*drift
        y = cy + ry*rad*math.sin(ang) + 8*math.sin(2.3*t+s*6+x/74)*drift
        rr = 2.2 if q > 0.2 else 1.5
        d.ellipse((x-rr-2, y-rr-2, x+rr+2, y+rr+2), fill=(24, 73, 80))
        d.ellipse((x-rr, y-rr, x+rr, y+rr), fill=color)

def octopus(d, cx, cy, t, shrug=False, size=1):
    bob = 5*math.sin(t*1.9)
    cy += bob
    for side in (-1, 1):
        for j in range(4):
            sx = cx+side*(18+j*13)*size
            sy = cy+56*size
            ex = cx+side*(175+j*51)*size
            ey = cy+(115-j*44)*size
            if shrug:
                ey = cy+(25-j*23)*size
            ey += (17+5*j)*math.sin(t*2.3+j*1.2+side)*size
            p0 = (sx, sy)
            p1 = (sx+side*(52+j*6)*size, sy+(45-j*20)*size)
            p2 = (ex-side*45*size, ey+30*math.sin(t*1.4+j)*size)
            p3 = (ex, ey)
            pts = bezier(p0, p1, p2, p3)
            path(d, pts, (197, 94, 89), max(4, round(18*size)))
            path(d, pts, CORAL, max(3, round(12*size)))
            for k in (7, 11, 15):
                x, y = pts[k]
                r = 3.2*size
                d.ellipse((x-r, y+4*size-r, x+r, y+4*size+r), fill=(255, 197, 163))
    d.ellipse((cx-78*size, cy-107*size, cx+78*size, cy+77*size), fill=CORAL, outline=(197, 94, 89), width=max(2,round(4*size)))
    d.ellipse((cx-55*size, cy-90*size, cx+26*size, cy-38*size), fill=(250, 177, 151))
    for dx in (-27, 27):
        d.ellipse((cx+(dx-16)*size, cy-32*size, cx+(dx+16)*size, cy+9*size), fill=CREAM)
        d.ellipse((cx+(dx-6)*size, cy-12*size, cx+(dx+7)*size, cy+4*size), fill=(13, 48, 59))
        d.ellipse((cx+dx*size, cy-11*size, cx+(dx+3)*size, cy-8*size), fill=CREAM)
    d.arc((cx-16*size, cy+15*size, cx+18*size, cy+45*size), 10, 170, fill=(117, 54, 60), width=max(2,round(3*size)))
    d.ellipse((cx-65*size, cy+18*size, cx-48*size, cy+30*size), fill=(234, 120, 113))
    d.ellipse((cx+48*size, cy+18*size, cx+65*size, cy+30*size), fill=(234, 120, 113))

def card(d, x, y, scale=1, tilt=0, signed=False):
    w, h = 176*scale, 119*scale
    x += 3*math.sin(tilt)
    y += 5*math.sin(tilt*1.6)
    d.rounded_rectangle((x-w/2+7, y-h/2+9, x+w/2+7, y+h/2+9), radius=13*scale, fill=(3, 18, 28))
    d.rounded_rectangle((x-w/2, y-h/2, x+w/2, y+h/2), radius=13*scale, fill=CREAM, outline=GOLD, width=max(2,round(4*scale)))
    d.line((x-w*.31, y-h*.23, x+w*.27, y-h*.23), fill=(63, 116, 117), width=max(2,round(4*scale)))
    d.line((x-w*.31, y-h*.04, x+w*.19, y-h*.04), fill=(113, 156, 164), width=max(2,round(3*scale)))
    d.line((x-w*.31, y+h*.15, x+w*.04, y+h*.15), fill=(113, 156, 164), width=max(2,round(3*scale)))
    if signed:
        pts = [(x+w*.07,y+h*.23),(x+w*.14,y+h*.28),(x+w*.18,y+h*.19),(x+w*.23,y+h*.26),(x+w*.3,y+h*.22)]
        d.line(pts, fill=(42, 112, 127), width=max(2,round(3*scale)))

def rider(d, x, y, scale=1):
    d.rounded_rectangle((x-38*scale,y+27*scale,x+44*scale,y+36*scale), radius=5*scale, fill=GOLD)
    d.line((x,y+25*scale,x+6*scale,y-14*scale), fill=CREAM, width=max(3,round(6*scale)))
    d.ellipse((x-11*scale,y-38*scale,x+14*scale,y-13*scale), fill=CORAL)
    d.line((x+2*scale,y-4*scale,x+35*scale,y-27*scale), fill=CREAM, width=max(3,round(5*scale)))
    d.line((x+35*scale,y-27*scale,x+42*scale,y-27*scale), fill=CREAM, width=max(2,round(4*scale)))

def block(d, x, y, w, h, color, label):
    d.rounded_rectangle((x+7,y+9,x+w+7,y+h+9), radius=12, fill=(5, 22, 31))
    d.rounded_rectangle((x,y,x+w,y+h), radius=12, fill=color, outline=(216, 246, 225), width=3)
    d.rectangle((x+16,y+17,x+w-16,y+27), fill=(255, 255, 255))
    text_center(d, (x+w/2,y+h/2+13), label, font_small, NAVY)

def house(d, x, y, s, light=True):
    w, h = 74*s, 75*s
    d.polygon([(x-w*.6,y-h),(x,y-h*1.55),(x+w*.6,y-h)], fill=(41, 116, 120))
    d.rounded_rectangle((x-w*.48,y-h,x+w*.48,y), radius=5*s, fill=(66, 156, 150), outline=(127, 218, 189), width=max(1,round(2*s)))
    d.rectangle((x-w*.25,y-h*.68,x-w*.04,y-h*.42), fill=GOLD if light else (32, 82, 93))
    d.rectangle((x+w*.12,y-h*.47,x+w*.36,y), fill=(19, 66, 76))
    d.ellipse((x+w*.28,y-h*.23,x+w*.33,y-h*.18), fill=GOLD)

def heading(d, s, x=80, y=70):
    d.text((x,y), s, font=font_title, fill=CREAM)
    d.line((x,y+65,x+90,y+65), fill=GOLD, width=5)

def draw_scene(d, idx, t, dur):
    p = clamp(t/dur)
    if idx == 0:
        octopus(d, 640, 280, t)
        for k in range(8):
            a = k*math.pi/4+t*.3
            x,y = 640+285*math.cos(a), 300+168*math.sin(a)
            d.ellipse((x-4,y-4,x+4,y+4), fill=GOLD)
    elif idx == 1:
        heading(d, "SWARMS")
        school(d, 620, 300, 500, 160, CYAN, t, 0, 350, ease(p*1.4))
        school(d, 730, 323, 360, 95, MINT, t, 1, 180, ease((p-.14)*1.4))
        for j in range(4):
            x = 215+j*255+30*math.sin(t*.9+j)
            d.arc((x,430,x+150,515), 190, 310, fill=(34,99,106), width=3)
    elif idx == 2:
        heading(d, "A RIDER")
        school(d, 610, 405, 485, 78, CYAN, t, 2, 310)
        school(d, 680, 420, 380, 52, MINT, t, 0, 120)
        rider(d, 430+380*ease(p), 295+8*math.sin(2*t), 1.45)
        d.line((895,210,895,368), fill=(41,111,119), width=4)
        d.rounded_rectangle((835,200,955,285), radius=12, fill=(16,63,72), outline=GOLD, width=3)
        d.line((855,229,930,229), fill=MINT, width=4)
        d.line((855,251,910,251), fill=MINT, width=4)
        d.ellipse((905,290,951,336), outline=GOLD, width=6)
        d.line((945,330,973,358), fill=GOLD, width=6)
    elif idx == 3:
        heading(d, "IMD")
        school(d, 340, 316, 210, 140, CYAN, t, 0, 180)
        tiles = [(486,215,158,100,MINT,"contracts"),(666,215,158,100,CYAN,"sites"),(576,338,158,100,GOLD,"audits")]
        for j,(x,y,w,h,c,label) in enumerate(tiles):
            xx = x-230*(1-ease((p-j*.17)*2.2))
            block(d,xx,y,w,h,c,label)
        d.line((645,316,656,335), fill=(73,141,146), width=5)
        d.line((748,316,738,337), fill=(73,141,146), width=5)
    elif idx == 4:
        heading(d, "CLAUS CITY")
        for j in range(10):
            house(d, 130+j*115, 502+5*math.sin(j), .62, j%3==0)
        for j in range(6):
            house(d, 180+j*182, 544, 1.1, True)
        mx = 1010-310*ease(p)
        my = 265+20*math.sin(t*.8)
        d.ellipse((mx-78,my-78,mx+78,my+78), outline=GOLD, width=12)
        d.line((mx+55,my+55,mx+110,my+110), fill=GOLD, width=16)
        school(d, 590, 400, 380, 74, MINT, t, 3, 90)
    elif idx == 5:
        heading(d, "FIVE IMD MEMBERS")
        card(d, 640, 418, .77, t)
        for j in range(5):
            x = 380+j*130
            y = 260+7*math.sin(t*2+j)
            lit = j<4 and p > .18+j*.13
            d.ellipse((x-42,y-42,x+42,y+42), fill=(21,69,79), outline=MINT if lit else MUTED, width=5)
            d.ellipse((x-22,y-22,x+22,y+22), fill=MINT if lit else (40,88,98))
    elif idx == 6:
        heading(d, "ONE BRIEF. TWO SWARMS.")
        school(d, 276, 340, 200, 125, CYAN, t, 0, 135)
        school(d, 994, 340, 200, 125, MINT, t, 1, 135)
        text_center(d, (274,470), "IMD", font_small, CREAM)
        text_center(d, (992,470), "Claus", font_small, CREAM)
        d.arc((356,195,922,485), 205, 335, fill=(56,132,140), width=4)
        card(d, 640, 333, 1.15, t, signed=p>.60)
        rider(d, 638, 172-13*ease(p), .83)
    elif idx == 7:
        heading(d, "PUBLIC REPORT")
        d.rounded_rectangle((268,175,815,480), radius=14, fill=(20,70,82), outline=CYAN, width=5)
        for k in range(5):
            d.line((300,235+k*42,783,235+k*42), fill=(43,106,122), width=2)
        d.rectangle((338,273,470,391), outline=MINT, width=4)
        d.line((470,273,568,230,700,230), fill=MINT, width=4)
        d.line((470,391,568,430,700,430), fill=MINT, width=4)
        sy = 80+145*ease((p-.12)*3.5)
        d.rounded_rectangle((565,sy-59,730,sy+10), radius=12, fill=(186,111,91), outline=CORAL, width=4)
        d.rectangle((592,sy+10,702,sy+48), fill=(145,80,78))
        if p>.50:
            text_center(d, (640,343), "PUBLIC", font_small, GOLD)
        d.rectangle((914,270,1016,525), fill=(7,28,40), outline=MINT, width=4)
        if p>.70:
            q=ease((p-.70)*3.3)
            d.polygon([(914,270),(1016+66*q,270-34*q),(1016+66*q,525+13*q),(914,525)], fill=(63,149,145), outline=CREAM)
        else:
            d.rectangle((919,275,1012,521), fill=(63,149,145), outline=CREAM, width=2)
    elif idx == 8:
        heading(d, "NEXT SWARM")
        school(d, 265, 300, 145, 90, CYAN, t, 0, 120)
        school(d, 522, 355, 145, 90, MINT, t, 1, 120)
        school(d, 1045-180*ease(p), 305, 210, 120, GOLD, t, 4, 240, ease(p*1.7))
        pickup = ease((p-.55)*2.2)
        cx, cy = 734+145*pickup, 370-30*pickup
        card(d, cx, cy, .9, t, signed=True)
        q=ease((p-.30)*2.8)
        dx, dy = cx+88+120*(1-q), cy-49-31*(1-q)
        d.ellipse((dx-10,dy-10,dx+10,dy+10), fill=GOLD)
        d.arc((345,260,843,500), 200, 320, fill=(56,124,131), width=3)
    elif idx == 9:
        octopus(d, 610, 287, t, shrug=True)
        card(d, 910, 231, .85, t, signed=True)
        d.arc((730,135,1030,350), 200, 330, fill=(57,124,134), width=3)

def wrap(d, s, font, maxw):
    words = s.split()
    lines, cur = [], ''
    for word in words:
        candidate = word if not cur else cur+' '+word
        if d.textbbox((0,0), candidate, font=font)[2] > maxw and cur:
            lines.append(cur)
            cur = word
        else:
            cur = candidate
    if cur: lines.append(cur)
    return lines

def caption(d, scene, local, dur):
    weights = WEIGHTS[scene]
    u = clamp(local/dur)
    k = 0
    acc = 0
    for j, wt in enumerate(weights):
        acc += wt
        if u <= acc:
            k=j
            break
    s = CAPTIONS[scene][k]
    d.rounded_rectangle((132,578,1148,698), radius=18, fill=(5, 24, 36), outline=(50, 113, 122), width=2)
    lines = wrap(d, s, font_caption, 930)
    line_h = 42
    y0 = 638-(len(lines)-1)*line_h/2
    for i,line in enumerate(lines):
        text_center(d, (640,y0+i*line_h), line, font_caption, CREAM)

def warning(d, end=False):
    if end:
        text_center(d, (640,610), WARNING, font_label, MINT)
    else:
        d.rounded_rectangle((289,22,991,62), radius=20, fill=(20,62,71), outline=(64,131,136), width=2)
        text_center(d, (640,42), WARNING, font_label, CREAM)

def end_frame(d, t):
    school(d, 262, 372, 160, 118, CYAN, t, 0, 130)
    school(d, 1016, 372, 160, 118, MINT, t, 1, 130)
    card(d, 640, 390, 1.05, t, signed=True)
    text_center(d, (640,198), "Two swarms, one card.", font_end, CREAM)
    text_center(d, (640,510), "A proposal by ultrapara, uxp-labs.", font_small, GOLD)
    warning(d, True)

def render():
    frames = math.ceil(timing['duration']*FPS)
    command = ['ffmpeg','-y','-loglevel','error',
               '-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0',
               '-i','assets/narration.m4a','-vf','scale=1920:1080:flags=lanczos',
               '-c:v','libx264','-preset','slow','-crf','25','-pix_fmt','yuv420p',
               '-c:a','aac','-b:a','128k','-movflags','+faststart','-shortest',
               'artifacts/two_swarms_one_card.mp4']
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for fi in range(frames):
            t = fi/FPS
            img = BASE.copy()
            d = ImageDraw.Draw(img)
            sea_details(d,t)
            if t >= timing['speech_end']:
                end_frame(d,t-timing['speech_end'])
            else:
                i = max(j for j,s in enumerate(scenes) if s['start'] <= t)
                local = t-scenes[i]['start']
                dur = scenes[i]['end']-scenes[i]['start']
                draw_scene(d,i,local,dur)
                caption(d,i,local,dur)
                if t<2:
                    warning(d)
            proc.stdin.write(img.tobytes())
            if fi%240==0:
                print(f'frame {fi}/{frames}', flush=True)
    finally:
        proc.stdin.close()
    err = proc.stderr.read().decode()
    code = proc.wait()
    if code:
        raise RuntimeError(f'ffmpeg exited {code}: {err}')
    print('rendered artifacts/two_swarms_one_card.mp4', flush=True)

if __name__ == '__main__':
    render()

import os
import sys
import math
import random
import array

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

W = 1280
H = 720
FPS = 60
GROUND_Y = H - 130
PLAYER_X = 300
BASE_SPEED = 7.5
MAX_SPEED = 14.5
GRAVITY = 0.9
JUMP_VEL = -17.5
MAX_FALL = 22.0
START_GAP = 260
CATCH_GAP = 42

SKY_TOP = (8, 6, 18)
SKY_MID = (34, 14, 44)
SKY_BOT = (94, 36, 54)
FAR_COL = (18, 13, 32)
MID_COL = (28, 21, 45)
GROUND_COL = (15, 13, 21)
GROUND_TOP = (46, 40, 58)
AMBER = (255, 152, 64)
CRIMSON = (255, 62, 74)
EMBER = (255, 196, 96)
TEAL = (96, 224, 216)
INK = (14, 12, 22)
TEXT_COL = (232, 226, 240)
DIM_COL = (150, 140, 170)

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def lerp(a, b, t):
    return a + (b - a) * t

def mix(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))


def taper(surf, a, b, wa, wb, col):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 0.001:
        pygame.draw.circle(surf, col, (int(round(a[0])), int(round(a[1]))), max(1, int(wa * 0.5)))
        return
    nx = -dy / length
    ny = dx / length
    ha = max(1.0, wa * 0.5)
    hb = max(1.0, wb * 0.5)
    pts = [
        (a[0] + nx * ha, a[1] + ny * ha),
        (b[0] + nx * hb, b[1] + ny * hb),
        (b[0] - nx * hb, b[1] - ny * hb),
        (a[0] - nx * ha, a[1] - ny * ha),
    ]
    pygame.draw.polygon(surf, col, [(int(round(px)), int(round(py))) for px, py in pts])
    pygame.draw.circle(surf, col, (int(round(a[0])), int(round(a[1]))), int(round(ha)))
    pygame.draw.circle(surf, col, (int(round(b[0])), int(round(b[1]))), int(round(hb)))


def widen(poly, m):
    cx = sum(p[0] for p in poly) / float(len(poly))
    cy = sum(p[1] for p in poly) / float(len(poly))
    out = []
    for px, py in poly:
        dx = px - cx
        dy = py - cy
        length = math.hypot(dx, dy)
        if length < 0.001:
            out.append((px, py + m))
        else:
            out.append((px + dx / length * m, py + dy / length * m))
    return out

def vgradient(w, h, stops):
    s = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                pygame.draw.line(s, mix(c0, c1, k), (0, y), (w, y))
                break
    return s

def make_glow(radius, color, strength=1.0, power=2.0):
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        t = 1.0 - r / radius
        a = int(255 * strength * (t ** power))
        if a > 0:
            pygame.draw.circle(s, (color[0], color[1], color[2], min(255, a)), (radius, radius), r)
    return s

def build_far(width2, height, seed=7):
    rnd = random.Random(seed)
    s = pygame.Surface((width2, height), pygame.SRCALPHA)
    x = -40
    while x < width2 + 40:
        bw = rnd.randint(46, 124)
        bh = rnd.randint(70, height - 16)
        top = height - bh
        col = (
            clamp(FAR_COL[0] + rnd.randint(-4, 5), 0, 255),
            clamp(FAR_COL[1] + rnd.randint(-4, 4), 0, 255),
            clamp(FAR_COL[2] + rnd.randint(-5, 7), 0, 255),
        )
        if rnd.random() < 0.35:
            pts = [(x, height), (x, top + rnd.randint(14, 50)), (x + bw, top), (x + bw, height)]
        else:
            pts = [(x, height), (x, top), (x + bw, top), (x + bw, height)]
        pygame.draw.polygon(s, col, pts)
        if rnd.random() < 0.45:
            ax = x + rnd.randint(8, max(9, bw - 8))
            atop = top - rnd.randint(16, 46)
            pygame.draw.line(s, (12, 9, 22), (ax, top + 2), (ax, atop), 2)
            if rnd.random() < 0.6:
                pygame.draw.circle(s, (190, 40, 50), (ax, atop), 2)
        if rnd.random() < 0.5:
            for wy in range(top + 12, height - 8, 16):
                for wx in range(x + 6, x + bw - 6, 14):
                    if rnd.random() < 0.10:
                        pygame.draw.rect(s, (74, 52, 46), (wx, wy, 4, 6))
        x += bw + rnd.randint(4, 26)
    return s

def build_mid(width2, height, seed=13):
    rnd = random.Random(seed)
    s = pygame.Surface((width2, height), pygame.SRCALPHA)
    signs = []
    x = -50
    while x < width2 + 50:
        bw = rnd.randint(64, 150)
        bh = rnd.randint(120, height - 10)
        top = height - bh
        base = rnd.randint(-5, 6)
        col = (MID_COL[0] + base, MID_COL[1] + base, MID_COL[2] + base)
        if rnd.random() < 0.3:
            pts = [(x, height), (x, top + rnd.randint(20, 60)), (x + bw, top + rnd.randint(0, 26)), (x + bw, height)]
        else:
            pts = [(x, height), (x, top), (x + bw, top), (x + bw, height)]
        pygame.draw.polygon(s, col, pts)
        pygame.draw.line(s, (44, 38, 64), (x, height), (x, top), 2)
        pygame.draw.line(s, (44, 38, 64), (x + bw, height), (x + bw, top), 2)
        lit = [(255, 168, 90), (96, 224, 216), (240, 230, 190), (255, 96, 120)]
        for wy in range(top + 14, height - 14, 18):
            for wx in range(x + 8, x + bw - 10, 16):
                if rnd.random() < 0.16:
                    pygame.draw.rect(s, rnd.choice(lit), (wx, wy, 6, 9))
                elif rnd.random() < 0.4:
                    pygame.draw.rect(s, (20, 16, 34), (wx, wy, 6, 9))
        if rnd.random() < 0.35 and bw > 80:
            sw = rnd.randint(44, 74)
            sh = rnd.randint(16, 26)
            sx = x + rnd.randint(6, max(7, bw - sw - 6))
            sy = top + rnd.randint(24, 70)
            scol = rnd.choice([(255, 70, 90), (90, 230, 220), (255, 150, 60), (180, 90, 255)])
            pygame.draw.rect(s, (12, 10, 20), (sx - 3, sy - 3, sw + 6, sh + 6))
            signs.append((pygame.Rect(sx, sy, sw, sh), scol))
        if rnd.random() < 0.4:
            ax = x + rnd.randint(8, max(9, bw - 8))
            pygame.draw.line(s, (34, 28, 52), (ax, top + 2), (ax, top - rnd.randint(18, 44)), 2)
        x += bw + rnd.randint(8, 40)
    return s, signs

def build_ground(width2, height, seed=31):
    rnd = random.Random(seed)
    s = pygame.Surface((width2, height))
    s.fill(GROUND_COL)
    pygame.draw.line(s, GROUND_TOP, (0, 1), (width2, 1), 3)
    pygame.draw.line(s, (30, 26, 40), (0, 4), (width2, 4), 1)
    for _ in range(160):
        y = rnd.randint(6, height - 2)
        x = rnd.randint(0, width2 - 30)
        ln = rnd.randint(8, 60)
        c = rnd.choice([(24, 21, 32), (34, 30, 44), (19, 17, 26), (40, 34, 50)])
        pygame.draw.line(s, c, (x, y), (x + ln, y + rnd.randint(-1, 1)), 1)
    for _ in range(60):
        x = rnd.randint(0, width2 - 20)
        y = rnd.randint(8, height - 6)
        pygame.draw.rect(s, rnd.choice([(26, 23, 36), (20, 18, 28)]), (x, y, rnd.randint(4, 16), rnd.randint(2, 5)))
    for _ in range(26):
        x = rnd.randint(0, width2 - 60)
        y = rnd.randint(10, height - 8)
        pts = [(x, y)]
        for _ in range(rnd.randint(2, 5)):
            pts.append((pts[-1][0] + rnd.randint(8, 24), pts[-1][1] + rnd.randint(-5, 5)))
        pygame.draw.lines(s, (9, 8, 14), False, pts, 1)
    for i in range(0, width2, 220):
        pygame.draw.rect(s, (46, 42, 58), (i + 60, height // 2, 60, 3))
    return s

def build_mist(width2, height, seed=51):
    rnd = random.Random(seed)
    s = pygame.Surface((width2, height), pygame.SRCALPHA)
    for _ in range(16):
        cx = rnd.randint(0, width2)
        cy = rnd.randint(0, height)
        rx = rnd.randint(140, 380)
        ry = rnd.randint(24, 70)
        a = rnd.randint(12, 34)
        pygame.draw.ellipse(s, (110, 84, 130, a), (cx - rx, cy - ry, rx * 2, ry * 2))
    return s

def build_scanlines(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(s, (0, 0, 0, 16), (0, y), (w, y), 1)
    return s

def build_vignette(w, h, color, max_a, inner=0.42):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w / 2.0, h / 2.0
    rad = math.hypot(cx, cy)
    for i in range(60, 0, -1):
        t = i / 60.0
        r = rad * t
        if t <= inner:
            continue
        a = int(max_a * (((t - inner) / (1.0 - inner)) ** 1.6))
        if a > 0:
            pygame.draw.ellipse(s, (color[0], color[1], color[2], min(255, a)), (cx - r, cy - r * 0.9, r * 2, r * 1.8))
    return s

def load_font(size, bold=False):
    for name in ("impact", "segoeui", "consolas", "arial"):
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)

def draw_text(surf, font, text, pos, color=TEXT_COL, align="topleft", shadow=None, soff=(2, 2)):
    img = font.render(text, True, color)
    rect = img.get_rect()
    setattr(rect, align, pos)
    if shadow is not None:
        sh = font.render(text, True, shadow)
        srect = sh.get_rect()
        setattr(srect, align, (pos[0] + soff[0], pos[1] + soff[1]))
        surf.blit(sh, srect)
    surf.blit(img, rect)
    return rect

def _synth(dur, f0, f1, vol, decay, sr, noise=0.0, wave="sine"):
    n = max(8, int(sr * dur))
    out = array.array("h", bytes(2 * n))
    phase = 0.0
    attack = max(1, int(sr * 0.004))
    for i in range(n):
        t = i / n
        freq = f0 if f0 == f1 else f0 * ((f1 / f0) ** t)
        phase += 2.0 * math.pi * freq / sr
        if wave == "square":
            s = 1.0 if math.sin(phase) >= 0 else -1.0
        else:
            s = math.sin(phase)
        if noise:
            s += noise * (random.random() * 2.0 - 1.0)
        env = math.exp(-decay * t) * min(1.0, i / attack)
        v = int(s * env * vol * 32767)
        out[i] = -32767 if v < -32767 else 32767 if v > 32767 else v
    return out

def _heart(sr):
    dur = 0.6
    n = int(sr * dur)
    out = array.array("h", bytes(2 * n))
    for start, amp in ((0.0, 1.0), (0.24, 0.72)):
        i0 = int(start * sr)
        ln = int(0.18 * sr)
        for j in range(ln):
            t = j / ln
            freq = 78.0 - 40.0 * t
            env = math.exp(-6.5 * t) * min(1.0, j / 220)
            val = math.sin(2.0 * math.pi * freq * j / sr)
            idx = i0 + j
            if idx < n:
                v = int(val * env * amp * 0.55 * 32767)
                out[idx] = max(-32767, min(32767, out[idx] + v))
    return out

def _drone(sr):
    dur = 5.0
    n = int(sr * dur)
    out = array.array("h", bytes(2 * n))
    ph1 = ph2 = ph3 = 0.0
    s1 = 2.0 * math.pi * 52.0 / sr
    s2 = 2.0 * math.pi * 52.7 / sr
    s3 = 2.0 * math.pi * 78.5 / sr
    for i in range(n):
        t = i / sr
        ph1 += s1
        ph2 += s2
        ph3 += s3
        trem = 0.7 + 0.3 * math.sin(2.0 * math.pi * 0.13 * t)
        swell = 0.6 + 0.4 * math.sin(2.0 * math.pi * 0.05 * t + 1.0)
        s = (math.sin(ph1) + math.sin(ph2) + 0.4 * math.sin(ph3)) / 2.4
        fade = min(1.0, t / 0.4, (dur - t) / 0.4)
        v = int(s * trem * swell * fade * 0.16 * 32767)
        out[i] = max(-32767, min(32767, v))
    return out

class Sounds:
    def __init__(self):
        self.ok = False
        self.sfx = {}
        self.ambient = None
        self.amb_channel = None
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(44100, -16, 2)
        except pygame.error:
            return
        info = pygame.mixer.get_init()
        if not info:
            return
        sr, fmt, channels = info
        if fmt not in (-16, pygame.AUDIO_S16, 32784):
            return
        self.ok = True
        self.channels = channels
        self.sr = sr
        self.sfx["jump"] = self._make(_synth(0.16, 300, 780, 0.32, 2.2, sr))
        self.sfx["land"] = self._make(_synth(0.13, 200, 70, 0.26, 5.0, sr, noise=0.5))
        self.sfx["hit"] = self._make(_synth(0.45, 150, 50, 0.5, 3.0, sr, noise=0.8))
        self.sfx["shard"] = self._make(_synth(0.22, 940, 1560, 0.26, 2.6, sr))
        self.sfx["die"] = self._make(_synth(1.2, 460, 60, 0.45, 2.0, sr))
        self.sfx["heart"] = self._make(_heart(sr))
        self.ambient = self._make(_drone(sr))

    def _make(self, data):
        if not self.ok:
            return None
        try:
            if self.channels == 2:
                stereo = array.array("h", bytes(4 * len(data)))
                for i, v in enumerate(data):
                    stereo[2 * i] = v
                    stereo[2 * i + 1] = v
                data = stereo
            return pygame.mixer.Sound(buffer=data.tobytes())
        except Exception:
            return None

    def play(self, name, vol=1.0):
        if not self.ok:
            return
        snd = self.sfx.get(name)
        if snd:
            snd.set_volume(vol)
            snd.play()

    def start_ambient(self):
        if self.ok and self.ambient:
            self.ambient.set_volume(0.5)
            self.amb_channel = self.ambient.play(loops=-1)

    def stop_ambient(self):
        if self.ok and self.ambient:
            self.ambient.stop()

    def pause_ambient(self, pause):
        if self.ok and self.amb_channel:
            if pause:
                self.amb_channel.pause()
            else:
                self.amb_channel.unpause()

class HeldState:
    def __init__(self):
        self.keys = set()

    def press(self, key):
        self.keys.add(key)

    def release(self, key):
        self.keys.discard(key)

    def clear(self):
        self.keys.clear()

    def __getitem__(self, key):
        return key in self.keys

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "kind", "col", "grav")

    def __init__(self, x, y, vx, vy, life, size, kind, col, grav=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.kind = kind
        self.col = col
        self.grav = grav

class Obstacle:
    def __init__(self, kind, x, rnd):
        self.kind = kind
        self.x = x
        self.bob = rnd.random() * 6.28
        self.t = 0.0
        if kind == "crate":
            self.w, self.h = 52, 52
            self.y = GROUND_Y - 52
        elif kind == "barrier":
            self.w, self.h = 26, 90
            self.y = GROUND_Y - 90
        elif kind == "drone":
            self.w, self.h = 78, 34
            self.y = GROUND_Y - 76
        else:
            self.w = rnd.randint(150, 210)
            self.h = H - GROUND_Y
            self.y = GROUND_Y

    def rect(self, time):
        if self.kind == "drone":
            y = GROUND_Y - 76 + math.sin(time * 3.0 + self.bob) * 4
            return pygame.Rect(int(self.x), int(y), self.w, self.h)
        if self.kind == "pit":
            return pygame.Rect(0, 0, 0, 0)
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surf, time, glows):
        x = int(self.x)
        if self.kind == "crate":
            body = pygame.Rect(x, GROUND_Y - 52, 52, 52)
            pygame.draw.rect(surf, (34, 30, 46), body)
            if body.left >= 0 and body.right <= W:
                sub = surf.subsurface(body)
                for i in range(-1, 4):
                    x0 = i * 22 - 12
                    pygame.draw.line(sub, (168, 120, 40), (x0, 52), (x0 + 34, 0), 9)
                pygame.draw.rect(sub, (22, 19, 34), (2, 2, 48, 9))
                pygame.draw.rect(sub, (90, 80, 110), (0, 0, 52, 52), 2)
                pygame.draw.rect(sub, (74, 66, 92), (4, 42, 44, 5))
            else:
                pygame.draw.rect(surf, (168, 120, 40), body)
                pygame.draw.rect(surf, (90, 80, 110), body, 2)
        elif self.kind == "barrier":
            pygame.draw.rect(surf, (40, 36, 54), (x, GROUND_Y - 90, 26, 90))
            pygame.draw.rect(surf, (80, 72, 100), (x, GROUND_Y - 90, 26, 90), 2)
            for i in range(5):
                yy = GROUND_Y - 84 + i * 17
                pygame.draw.polygon(surf, (196, 60, 60), [(x + 3, yy + 10), (x + 23, yy), (x + 23, yy + 6), (x + 3, yy + 16)])
            blink = 1.0 if (int(time * 3) % 2 == 0) else 0.25
            g = glows["crimson"]
            g.set_alpha(int(150 * blink))
            surf.blit(g, (x + 13 - g.get_width() // 2, GROUND_Y - 104 - g.get_height() // 2))
            pygame.draw.circle(surf, (255, 90, 90), (x + 13, GROUND_Y - 92), 4)
        elif self.kind == "drone":
            y = GROUND_Y - 76 + math.sin(time * 3.0 + self.bob) * 4
            cx = x + 39
            gy = y + 17
            g = glows["teal"]
            g.set_alpha(110)
            surf.blit(g, (cx - g.get_width() // 2, gy - g.get_height() // 2))
            pygame.draw.ellipse(surf, (38, 44, 58), (x, y, 78, 34))
            pygame.draw.ellipse(surf, (74, 92, 110), (x, y, 78, 34), 2)
            pygame.draw.rect(surf, (24, 28, 38), (x + 12, y - 8, 54, 8))
            rot = 18 * math.sin(time * 22 + self.bob)
            pygame.draw.line(surf, (140, 170, 190), (cx - rot, y - 4), (cx + rot, y - 4), 3)
            pygame.draw.circle(surf, TEAL, (cx + 20, y + 17), 6)
            pygame.draw.circle(surf, (230, 255, 255), (cx + 22, y + 15), 2)
            pygame.draw.polygon(surf, (255, 160, 70), [(cx - 6, y + 34), (cx + 6, y + 34), (cx + 2, y + 46), (cx - 2, y + 46)])
        else:
            x2 = x + self.w
            jag = []
            steps = max(6, self.w // 18)
            for i in range(steps + 1):
                px = x + (x2 - x) * i / steps
                jag.append((px, GROUND_Y + (0 if i % 2 == 0 else 9)))
            pts = [(x, H), (x2, H)] + list(reversed(jag))
            pygame.draw.polygon(surf, (2, 1, 5), pts)
            for i in range(len(jag) - 1):
                pygame.draw.line(surf, (70, 20, 30), jag[i], jag[i + 1], 2)
            gg = glows["crimson"]
            gg.set_alpha(70)
            surf.blit(gg, (int((x + x2) / 2 - gg.get_width() // 2), GROUND_Y - 20))

class Shard:
    def __init__(self, x, y, rnd):
        self.x = x
        self.y = y
        self.t = rnd.random() * 6.28
        self.dead = False

    def rect(self):
        return pygame.Rect(int(self.x) - 16, int(self.y) - 16, 32, 32)

    def draw(self, surf, time, glow):
        bob = math.sin(time * 2.6 + self.t) * 6
        cx, cy = self.x, self.y + bob
        g = glow
        g.set_alpha(190)
        surf.blit(g, (int(cx - g.get_width() // 2), int(cy - g.get_height() // 2)))
        r = 7 + math.sin(time * 5 + self.t) * 1.5
        pts = [(cx, cy - r), (cx + r * 0.7, cy), (cx, cy + r), (cx - r * 0.7, cy)]
        pygame.draw.polygon(surf, (255, 246, 220), [(int(p[0]), int(p[1])) for p in pts])
        pygame.draw.polygon(surf, AMBER, [(int(p[0]), int(p[1])) for p in pts], 1)

class Player:
    def __init__(self):
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.on_ground = True
        self.sliding = False
        self.stumble = 0
        self.invuln = 0
        self.run_phase = 0.0
        self.was_in_air = False

    def hitbox(self):
        if self.sliding and self.on_ground:
            return pygame.Rect(PLAYER_X - 24, int(self.y) - 30, 48, 30)
        return pygame.Rect(PLAYER_X - 14, int(self.y) - 60, 28, 60)

    def jump(self):
        if self.on_ground and self.stumble <= 0:
            self.vy = JUMP_VEL
            self.on_ground = False
            self.sliding = False
            return True
        return False

    def update(self, keys, dtf, game):
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        self.sliding = bool(down and self.on_ground and self.stumble <= 0)
        if self.invuln > 0:
            self.invuln -= dtf
        if self.stumble > 0:
            self.stumble -= dtf
        jump_held = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        if not self.on_ground:
            g = GRAVITY * (0.5 if (self.vy < 0 and jump_held) else 1.0)
            self.vy = min(self.vy + g * dtf, MAX_FALL)
            self.y += self.vy * dtf
            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0.0
                self.on_ground = True
                if self.was_in_air:
                    game.emit_land(self)
                self.was_in_air = False
        else:
            self.was_in_air = True
        self.run_phase += game.speed * 0.085 * dtf

    def _joints(self, time):
        x = float(PLAYER_X)
        y = self.y
        segs = []
        feet = []
        if self.sliding and self.on_ground:
            hip = (x - 4, y - 15)
            neck = (x + 18, y - 20)
            head = (x + 30, y - 21)
            segs.append((hip, (x + 22, y - 9), 7))
            segs.append(((x + 22, y - 9), (x + 40, y - 5), 6))
            segs.append((hip, (x - 22, y - 7), 7))
            segs.append(((x - 22, y - 7), (x - 36, y - 4), 6))
            segs.append((neck, (x - 2, y - 30), 6))
            segs.append(((x - 2, y - 30), (x - 18, y - 34), 5))
            feet = [(x + 40, y - 5), (x - 36, y - 4)]
            return segs, head, 9, hip, neck, feet
        if not self.on_ground:
            hip = (x, y - 34)
            neck = (x + 2, y - 55)
            head = (x + 3, y - 66)
            segs.append((hip, (x + 14, y - 26), 7))
            segs.append(((x + 14, y - 26), (x + 24, y - 14), 6))
            segs.append((hip, (x - 12, y - 24), 7))
            segs.append(((x - 12, y - 24), (x - 20, y - 10), 6))
            segs.append((neck, (x + 16, y - 48), 6))
            segs.append(((x + 16, y - 48), (x + 26, y - 38), 5))
            segs.append((neck, (x - 14, y - 50), 6))
            segs.append(((x - 14, y - 50), (x - 24, y - 44), 5))
            feet = [(x + 24, y - 14), (x - 20, y - 10)]
            return segs, head, 9, hip, neck, feet
        if self.stumble > 0:
            wob = math.sin(time * 26) * 10
            hip = (x + 4, y - 32)
            neck = (x - 4, y - 54)
            head = (x - 8, y - 66)
            segs.append((hip, (x + 16, y - 24), 7))
            segs.append(((x + 16, y - 24), (x + 26, y - 12), 6))
            segs.append((hip, (x - 14, y - 26), 7))
            segs.append(((x - 14, y - 26), (x - 26, y - 16), 6))
            segs.append((neck, (x + 14 + wob, y - 62), 6))
            segs.append(((x + 14 + wob, y - 62), (x + 26 + wob, y - 74), 5))
            segs.append((neck, (x - 18 - wob, y - 58), 6))
            segs.append(((x - 18 - wob, y - 58), (x - 30 - wob, y - 68), 5))
            feet = [(x + 26, y - 12), (x - 26, y - 16)]
            return segs, head, 9, hip, neck, feet
        p = self.run_phase
        hip = (x, y - 34)
        neck = (x, y - 56)
        head = (x, y - 67)
        for k, ph in enumerate((p, p + math.pi)):
            swing = math.sin(ph)
            lift = max(0.0, math.sin(ph + 1.7))
            foot = (x + 15 * swing, y - 17 * lift)
            knee = ((hip[0] + foot[0]) / 2 + 5, (hip[1] + foot[1]) / 2 - 3 * lift)
            segs.append((hip, knee, 8))
            segs.append((knee, foot, 7))
            feet.append(foot)
        for k, ph in enumerate((p + math.pi, p)):
            swing = math.sin(ph)
            lift = max(0.0, math.sin(ph + 1.9))
            hand = (x - 13 * swing, y - 38 - 4 * lift)
            elbow = ((neck[0] + hand[0]) / 2 - 4, (neck[1] + hand[1]) / 2 + 2)
            segs.append((neck, elbow, 7))
            segs.append((elbow, hand, 6))
        return segs, head, 10, hip, neck, feet

    def draw(self, surf, time):
        segs, head, hr, hip, neck, feet = self._joints(time)
        body = (37, 39, 58)
        hood_col = (52, 54, 80)
        rim_l = (136, 38, 56)
        rim_r = (162, 108, 44)
        torso = [
            (neck[0] - 9, neck[1] - 4),
            (neck[0] + 9, neck[1] - 4),
            (hip[0] + 11, hip[1] + 6),
            (hip[0] - 11, hip[1] + 6),
        ]
        pack = (hip[0] - 23, neck[1] + 11, 14, 24)
        for dx, col in ((-2, rim_l), (2, rim_r)):
            for a, b, w in segs:
                taper(surf, (a[0] + dx, a[1]), (b[0] + dx, b[1]), w + 7, w + 5, col)
            pygame.draw.circle(surf, col, (int(head[0] + dx), int(head[1])), hr + 3)
            shifted = [(p[0] + dx, p[1]) for p in torso]
            pygame.draw.polygon(surf, col, [(int(p[0]), int(p[1])) for p in widen(shifted, 3)])
            pygame.draw.rect(surf, col, (int(pack[0] + dx - 2), int(pack[1] - 2), pack[2] + 4, pack[3] + 4), border_radius=5)
        pygame.draw.rect(surf, (46, 44, 68), (int(pack[0]), int(pack[1]), pack[2], pack[3]), border_radius=4)
        pygame.draw.line(surf, (92, 84, 122), (int(pack[0] + 3), int(pack[1] + 5)), (int(pack[0] + 11), int(pack[1] + 20)), 2)
        for a, b, w in segs:
            taper(surf, a, b, w + 1, max(3, w - 2), body)
        pygame.draw.polygon(surf, body, [(int(p[0]), int(p[1])) for p in torso])
        pygame.draw.circle(surf, body, (int(head[0]), int(head[1])), hr)
        for fx, fy in feet:
            pygame.draw.rect(surf, (26, 26, 42), (int(fx) - 5, int(fy) - 4, 11, 7))
            pygame.draw.rect(surf, (104, 98, 132), (int(fx) - 5, int(fy) + 1, 11, 2))
        face_rect = (int(head[0] - 7), int(head[1] - 5), 15, 16)
        pygame.draw.ellipse(surf, (198, 154, 114), face_rect)
        pygame.draw.ellipse(surf, (150, 108, 76), face_rect, 1)
        pygame.draw.circle(surf, (44, 34, 36), (int(head[0] + 4), int(head[1] - 1)), 2)
        pygame.draw.circle(surf, (30, 24, 30), (int(head[0] + 4), int(head[1] - 1)), 1)
        hood = [
            (head[0] - hr - 5, head[1] + 9),
            (head[0] - hr - 1, head[1] - hr + 1),
            (head[0] - 3, head[1] - hr - 5),
            (head[0] + 7, head[1] - hr + 3),
            (head[0] + 3, head[1] - 5),
            (head[0] - 7, head[1] + 5),
        ]
        pygame.draw.polygon(surf, hood_col, [(int(px), int(py)) for px, py in hood])
        pygame.draw.lines(surf, (80, 78, 116), True, [(int(px), int(py)) for px, py in hood], 1)
        self.draw_scarf(surf, time, neck)

    def draw_scarf(self, surf, time, neck):
        x0, y0 = neck[0] - 8, neck[1] + 7
        pts = [(x0, y0)]
        for i in range(1, 6):
            t = i / 5.0
            pts.append(
                (
                    x0 - 33 * t,
                    y0 + math.sin(time * 8.5 - i * 1.35) * (2.0 + 7.5 * t) + 4 * t,
                )
            )
        widths = (6, 5, 4, 3, 2)
        for i in range(5):
            pygame.draw.line(surf, (34, 14, 20), pts[i], pts[i + 1], widths[i] + 2)
        for i in range(5):
            pygame.draw.line(surf, (176, 58, 54), pts[i], pts[i + 1], widths[i])
        for i in range(5):
            pygame.draw.line(surf, (246, 134, 78), pts[i], pts[i + 1], 1)

class Demon:
    def __init__(self, gap):
        self.x = float(PLAYER_X - gap)
        self.lunge = 0.0
        self.smoke_t = 0.0
        self.void_face = pygame.Surface((52, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(self.void_face, (0, 0, 0, 232), (0, 0, 52, 56))

    @property
    def gap(self):
        return PLAYER_X - self.x

    def proximity(self):
        return clamp(1.0 - (self.gap - CATCH_GAP) / float(START_GAP - CATCH_GAP), 0.0, 1.0)

    def update(self, dtf, time):
        self.smoke_t += dtf
        while self.smoke_t >= 2:
            self.smoke_t -= 2
            return True
        return False

    def horn(self, surf, pts, ws, col, rim):
        for i in range(len(pts) - 1):
            taper(surf, pts[i], pts[i + 1], ws[i] + 4, ws[i + 1] + 3, rim)
        for i in range(len(pts) - 1):
            taper(surf, pts[i], pts[i + 1], ws[i], ws[i + 1], col)

    def draw(self, surf, time, glows, aura_alpha):
        x1 = self.x
        x0 = x1 - 126
        prox = self.proximity()
        bob = math.sin(time * 2.0) * 5
        top = GROUND_Y - 216 + bob
        bot = GROUND_Y - 6
        void = (14, 8, 23)
        rim = (104, 34, 76)
        aura = glows["aura"]
        aura.set_alpha(int(aura_alpha))
        surf.blit(aura, (int(x1 - 64 - aura.get_width() // 2), int(GROUND_Y - 118 - aura.get_height() // 2)))
        pygame.draw.ellipse(surf, (6, 3, 11), (int(x0 + 16), GROUND_Y - 9, 112, 17))

        n = 24
        right = []
        left = []
        flare = 6 + prox * 16
        for i in range(n + 1):
            t = i / float(n)
            y = top + t * (bot - top)
            wob = math.sin(t * 5.0 + time * 3.0)
            right.append((x1 - 14 - 16 * t + wob * (5 + 14 * t) + flare * t, y))
            left.append((x0 + 28 + 18 * t - wob * (5 + 12 * t) - flare * t, y))

        swing = math.sin(time * 2.6)
        b_sh = (x0 + 46, top + 104)
        b_el = (x0 + 6 + swing * 8, top + 50)
        b_hn = (x0 - 14 + swing * 15, top - 8)
        taper(surf, b_sh, b_el, 16, 12, rim)
        taper(surf, b_el, b_hn, 12, 8, rim)
        taper(surf, b_sh, b_el, 13, 9, void)
        taper(surf, b_el, b_hn, 9, 6, void)
        for i in range(4):
            ang = -2.5 + i * 0.45 + swing * 0.14
            kn = (b_hn[0] + 22 * math.cos(ang), b_hn[1] + 22 * math.sin(ang))
            tip = (kn[0] + 16 * math.cos(ang - 0.5), kn[1] + 16 * math.sin(ang - 0.5) + 5)
            taper(surf, b_hn, kn, 7, 5, rim)
            taper(surf, kn, tip, 5, 2, rim)
            taper(surf, b_hn, kn, 5, 3, void)
            taper(surf, kn, tip, 3, 1, void)

        jag = []
        jrx = x1 - 6 + flare
        jlx = x0 + 46 - flare
        for i in range(1, 9):
            t = i / 8.0
            jx = jrx + (jlx - jrx) * t
            jy = bot + (6 + (i % 2) * 20) + math.sin(time * 4.5 + i * 1.1) * 6
            jag.append((jx, jy))
        poly = right + jag + list(reversed(left))
        ipoly = [(int(px), int(py)) for px, py in poly]
        pygame.draw.polygon(surf, (9, 5, 15), ipoly)
        pygame.draw.polygon(surf, rim, ipoly, 2)

        for k in range(5):
            pts = []
            base = 3 + k * 4
            for s in range(6):
                i = min(base + s, n)
                lx = left[i][0]
                rx = right[i][0]
                yy = left[i][1]
                jit = math.sin(s * 2.3 + k * 2.7 + time * 2.4) * 0.1
                pts.append((lx + (0.26 + 0.13 * k + jit) * (rx - lx), yy))
            heat = 0.3 + 0.7 * max(0.0, math.sin(time * 3.4 + k * 1.9))
            col = mix((46, 16, 34), (224, 70, 66), heat)
            pygame.draw.lines(surf, col, False, [(int(p[0]), int(p[1])) for p in pts], 2)

        for i in range(5):
            sy = top + 64 + i * 28
            sx = x0 + 14 - i * 3
            pts = [(sx, sy)]
            for k in range(5):
                t = (k + 1) / 5.0
                pts.append(
                    (
                        sx - 76 * t,
                        sy + math.sin(time * 6.4 + i + k * 0.9) * (7 + 15 * t) - 12 * t,
                    )
                )
            pygame.draw.lines(surf, (54, 26, 70), False, [(int(p[0]), int(p[1])) for p in pts], 4)

        hx = x1 - 56
        hy = top + 46
        self.horn(surf, [(hx - 20, hy - 24), (hx - 34, hy - 54), (hx - 50, hy - 74), (hx - 58, hy - 92)], [13, 10, 6, 3], void, rim)
        self.horn(surf, [(hx + 14, hy - 26), (hx + 20, hy - 58), (hx + 8, hy - 80), (hx - 8, hy - 92)], [12, 9, 5, 2], void, rim)

        pygame.draw.ellipse(surf, void, (int(hx - 33), int(hy - 37), 66, 74))
        pygame.draw.ellipse(surf, rim, (int(hx - 33), int(hy - 37), 66, 74), 2)
        pygame.draw.ellipse(surf, (0, 0, 0), (int(hx - 25), int(hy - 27), 50, 54))

        eye_glow = glows["eyeglow"]
        eye_glow.set_alpha(int(60 + 90 * prox))
        surf.blit(eye_glow, (int(hx - eye_glow.get_width() // 2 + 5), int(hy - eye_glow.get_height() // 2 - 8)))
        surf.blit(self.void_face, (int(hx - 26), int(hy - 28)))
        pygame.draw.ellipse(surf, rim, (int(hx - 33), int(hy - 37), 66, 74), 2)
        blink = 1.0 if math.sin(time * 1.15) > -0.86 else 0.12
        ecol = mix((150, 26, 40), (255, 118, 104), blink)
        core = mix((216, 66, 74), (255, 226, 214), blink)
        for ex, ey, ew, eh in ((-14, -6, 17, 9), (15, -10, 15, 8), (-3, -23, 11, 5), (21, -25, 9, 4), (-1, 6, 9, 4), (23, 4, 8, 4)):
            er = (int(hx + ex - ew // 2), int(hy + ey - eh // 2), ew, eh)
            pygame.draw.ellipse(surf, ecol, er)
            cr = (er[0] + ew // 4, er[1] + eh // 4, max(2, ew // 2), max(2, eh // 2))
            pygame.draw.ellipse(surf, core, cr)

        mw = 30 + prox * 18
        my = hy + 15
        mh = 7 + prox * 15
        pts_top = []
        pts_bot = []
        for i in range(7):
            t = i / 6.0
            xx = hx - 16 + t * (mw * 1.7)
            pts_top.append((xx, my + math.sin(t * math.pi) * 3))
            pts_bot.append((xx, my + mh + math.sin(t * math.pi) * 5))
        pygame.draw.polygon(surf, (0, 0, 0), [(int(p[0]), int(p[1])) for p in pts_top + list(reversed(pts_bot))])
        if prox > 0.3:
            throat = glows["eyeglow"]
            throat.set_alpha(int((prox - 0.3) * 330))
            surf.blit(throat, (int(hx + 10 - throat.get_width() // 2), int(my + mh * 0.5 - throat.get_height() // 2)))
        for i in range(6):
            a = pts_top[i]
            b = pts_top[i + 1]
            tip = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 6 + (i % 2) * 4)
            pygame.draw.polygon(surf, (198, 190, 172), [(int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (int(tip[0]), int(tip[1]))])
        for i in range(5):
            a = pts_bot[i]
            b = pts_bot[i + 1]
            tip = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 7 - (i % 2) * 4)
            pygame.draw.polygon(surf, (186, 178, 160), [(int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (int(tip[0]), int(tip[1]))])

        if prox > 0.1:
            reach = 30 + prox * 150
            wob = math.sin(time * 7)
            sh = (hx - 22, hy + 82)
            el = (sh[0] + reach * 0.45, sh[1] - 36 + wob * 9)
            wr = (sh[0] + reach, sh[1] - 50 + wob * 15)
            taper(surf, sh, el, 19, 14, rim)
            taper(surf, el, wr, 14, 10, rim)
            taper(surf, sh, el, 16, 11, void)
            taper(surf, el, wr, 11, 8, void)
            for i in range(5):
                ang = -0.9 + i * 0.44
                kn = (wr[0] + 22 * math.cos(ang), wr[1] + 22 * math.sin(ang) + math.sin(time * 9 + i) * 4)
                tip = (kn[0] + 16 * math.cos(ang + 0.65), kn[1] + 16 * math.sin(ang + 0.65) + 5)
                taper(surf, wr, kn, 8, 6, rim)
                taper(surf, kn, tip, 6, 2, rim)
                taper(surf, wr, kn, 6, 4, void)
                taper(surf, kn, tip, 4, 1, void)

class Game:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Don't Look Back")
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.build_assets()
        self.rnd = random.Random()
        self.best = self.load_best()
        self.frame = 0.0
        self.total_time = 0.0
        self.state = "MENU"
        self.held = HeldState()
        self.particles = []
        self.ash = []
        for _ in range(150):
            self.ash.append(
                [
                    self.rnd.uniform(0, W),
                    self.rnd.uniform(0, H),
                    self.rnd.uniform(-1.4, -0.4),
                    self.rnd.uniform(0.5, 1.9),
                    self.rnd.uniform(0.4, 1.4),
                ]
            )
        self.reset()
        self.sounds.start_ambient()

    def build_assets(self):
        self.sky = vgradient(
            W,
            H,
            [(0.0, SKY_TOP), (0.55, SKY_MID), (1.0, SKY_BOT)],
        )
        self.w2 = W * 2
        self.far = build_far(self.w2, 330)
        self.mid, self.signs = build_mid(self.w2, 400)
        self.sign_surfs = []
        for rect, col in self.signs:
            core = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(core, (col[0], col[1], col[2], 240), core.get_rect(), border_radius=3)
            pygame.draw.rect(core, (14, 12, 22, 255), core.get_rect(), 2, border_radius=3)
            seed_glow = make_glow(40, col, 0.7, 1.7)
            halo = pygame.transform.scale(seed_glow, (rect.w + 76, rect.h + 64))
            self.sign_surfs.append((rect, core, halo))
        self.ground_pat = build_ground(self.w2, H - GROUND_Y)
        self.mist = build_mist(self.w2, 220)
        self.scan = build_scanlines(W, H)
        self.vig = build_vignette(W, H, (2, 1, 6), 165)
        self.redvig = build_vignette(W, H, (190, 20, 34), 210, inner=0.3)
        self.flash = pygame.Surface((W, H), pygame.SRCALPHA)
        self.flash.fill((255, 255, 255, 255))
        self.overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        self.overlay.fill((5, 2, 9, 205))
        self.menu_shade = pygame.Surface((W, H), pygame.SRCALPHA)
        self.menu_shade.fill((4, 2, 10, 120))
        self.menu_panel = pygame.Surface((640, 176), pygame.SRCALPHA)
        self.menu_panel.fill((8, 6, 16, 190))
        self.glows = {
            "crimson": make_glow(54, (255, 60, 74), 0.95, 2.1),
            "eyeglow": make_glow(36, (255, 60, 74), 0.9, 2.3),
            "ember": make_glow(46, (255, 180, 90), 0.95, 2.0),
            "teal": make_glow(48, (80, 230, 220), 0.85, 2.0),
            "smoke": make_glow(30, (86, 54, 110), 0.7, 1.7),
            "dust": make_glow(24, (120, 108, 130), 0.6, 1.8),
            "aura": make_glow(210, (0, 0, 0), 0.7, 1.5),
            "white": make_glow(40, (255, 240, 220), 0.9, 2.0),
        }
        self.font_title = load_font(96, True)
        self.font_big = load_font(52, True)
        self.font_hud = load_font(26, True)
        self.font_body = load_font(22)
        self.font_small = load_font(18)
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(icon, (8, 6, 16), (16, 16), 15)
        pygame.draw.ellipse(icon, (255, 70, 80), (8, 12, 8, 5))
        pygame.draw.ellipse(icon, (255, 70, 80), (18, 12, 7, 5))
        pygame.display.set_icon(icon)

    def reset(self):
        self.player = Player()
        self.demon = Demon(START_GAP)
        self.obstacles = []
        self.pickups = []
        self.speed = BASE_SPEED
        self.dist_px = 0.0
        self.shard_count = 0
        self.time_s = 0.0
        self.far_off = 0.0
        self.mid_off = 0.0
        self.ground_off = 0.0
        self.mist_off = 0.0
        self.spawn_px = 1000.0
        self.shard_px = 1500.0
        self.pit_lock = 0.0
        self.boost_t = 0
        self.shake = 0.0
        self.flash_a = 0.0
        self.red_a = 0.0
        self.heart_t = 0.0
        self.lightning_t = self.rnd.uniform(6, 14)
        self.bolt = None
        self.bolt_t = 0.0
        self.hint_t = 0.0
        self.death_t = 0.0
        self.glitch_t = 0.0
        self.glitch_off = 0
        self.particles = []

    def load_best(self):
        try:
            with open(os.path.join(os.path.expanduser("~"), ".dont_look_back.best"), "r") as f:
                return int(f.read().strip() or "0")
        except Exception:
            return 0

    def save_best(self, value):
        try:
            with open(os.path.join(os.path.expanduser("~"), ".dont_look_back.best"), "w") as f:
                f.write(str(int(value)))
        except Exception:
            pass

    @property
    def meters(self):
        return int(self.dist_px // 25)

    @property
    def level(self):
        return min(int(self.time_s // 12), 8)

    def add(self, p):
        if len(self.particles) < 520:
            self.particles.append(p)

    def emit_land(self, pl):
        for _ in range(10):
            self.add(
                Particle(
                    PLAYER_X,
                    GROUND_Y,
                    self.rnd.uniform(-3.5, 3.5) - self.speed * 0.5,
                    self.rnd.uniform(-2.4, -0.4),
                    self.rnd.uniform(16, 30),
                    self.rnd.uniform(3, 7),
                    "dust",
                    (130, 118, 140),
                    0.08,
                )
            )
        self.sounds.play("land", 0.7)
        self.shake = max(self.shake, 3.5)

    def emit_dust(self, pl):
        self.add(
            Particle(
                PLAYER_X - 8,
                GROUND_Y - 2,
                self.rnd.uniform(-4.5, -1.5) - self.speed * 0.55,
                self.rnd.uniform(-1.6, -0.3),
                self.rnd.uniform(14, 26),
                self.rnd.uniform(3, 6),
                "dust",
                (110, 100, 124),
                0.06,
            )
        )

    def emit_sparks(self, x, y, col, n=22, power=7.0):
        for _ in range(n):
            a = self.rnd.uniform(0, math.tau)
            sp = self.rnd.uniform(power * 0.3, power)
            self.add(
                Particle(
                    x,
                    y,
                    math.cos(a) * sp,
                    math.sin(a) * sp - 1.5,
                    self.rnd.uniform(18, 40),
                    self.rnd.uniform(2, 5),
                    "spark",
                    col,
                    0.22,
                )
            )

    def emit_ring(self, x, y, col, size=40):
        self.add(Particle(x, y, 0, 0, 22, size, "ring", col, 0.0))

    def emit_smoke(self, x, y):
        heat = self.demon.proximity()
        self.add(
            Particle(
                x,
                y,
                self.rnd.uniform(-1.2, -0.2),
                self.rnd.uniform(-1.4, -0.5),
                self.rnd.uniform(45, 90),
                self.rnd.uniform(18, 34),
                "smoke",
                mix((96, 60, 120), (142, 44, 66), heat),
                -0.01,
            )
        )

    def update_particles(self, dtf):
        for p in self.particles:
            p.life -= dtf
            p.x += p.vx * dtf
            p.y += p.vy * dtf
            p.vy += p.grav * dtf
            if p.kind == "smoke":
                p.vx *= 0.99
                p.size += 0.35 * dtf
        self.particles = [p for p in self.particles if p.life > 0]

    def update_ash(self, dtf):
        for a in self.ash:
            a[0] += (a[2] - self.speed * 0.12) * dtf
            a[1] += a[3] * dtf
            if a[1] > H:
                a[1] = -4
                a[0] = self.rnd.uniform(0, W + 120)
            if a[0] < -20:
                a[0] = W + self.rnd.uniform(0, 80)
                a[1] = self.rnd.uniform(-40, H * 0.5)

    def update_weather(self, dtf):
        self.lightning_t -= dtf / 60.0
        if self.lightning_t <= 0:
            self.lightning_t = self.rnd.uniform(8, 20)
            x = self.rnd.randint(80, W - 80)
            pts = [(x, 0)]
            yy = 0
            while yy < 300:
                yy += self.rnd.randint(24, 60)
                pts.append((pts[-1][0] + self.rnd.randint(-46, 46), yy))
            self.bolt = pts
            self.bolt_t = 9.0
            self.flash_a = max(self.flash_a, 70)
        if self.bolt_t > 0:
            self.bolt_t -= dtf

    def spawn_obstacle(self):
        pool = ["crate", "crate", "barrier", "pit", "crate"]
        if self.level >= 1:
            pool += ["drone", "drone"]
        if self.level >= 3:
            pool += ["barrier", "pit"]
        kind = self.rnd.choice(pool)
        if self.pit_lock > 0 and kind == "pit":
            kind = "crate"
        x = float(W + 60)
        self.obstacles.append(Obstacle(kind, x, self.rnd))
        if kind == "pit":
            self.pit_lock = 260.0
            last = self.obstacles[-1]
            self.pit_lock = last.w + 200
        elif kind == "crate" and self.level >= 2 and self.rnd.random() < 0.3:
            self.obstacles.append(Obstacle("crate", x + 84, self.rnd))
            self.pit_lock = 140.0
        else:
            self.pit_lock = max(0.0, self.pit_lock - 120)

    def spawn_shards(self):
        count = self.rnd.choice([1, 1, 2, 3])
        ys = [GROUND_Y - 70, GROUND_Y - 120, GROUND_Y - 175]
        base_y = self.rnd.choice(ys)
        x = float(W + 40)
        for i in range(count):
            y = base_y + (abs(i - (count - 1) / 2.0) * -34 if count > 1 else 0)
            over_pit = any(
                o.kind == "pit" and o.x - 30 < x + i * 52 < o.x + o.w + 30 for o in self.obstacles
            )
            if over_pit and y > GROUND_Y - 150:
                y = GROUND_Y - 165
            self.pickups.append(Shard(x + i * 52, y, self.rnd))

    def hit_player(self, kind, px, py):
        pl = self.player
        if pl.stumble > 0 or self.state != "PLAYING":
            return
        pl.stumble = 46
        pl.invuln = 70
        self.demon.x += 55
        self.shake = 16.0
        self.flash_a = 90
        self.emit_sparks(px, py, (255, 120, 90), 26, 8.0)
        self.emit_ring(px, py, (255, 90, 80), 50)
        self.sounds.play("hit", 0.9)

    def collect(self, sh):
        sh.dead = True
        self.shard_count += 1
        self.demon.x -= 45
        self.boost_t = 110
        self.emit_sparks(sh.x, sh.y, (255, 210, 130), 16, 5.5)
        self.emit_ring(sh.x, sh.y, (255, 190, 100), 34)
        self.sounds.play("shard", 0.8)

    def game_over(self):
        if self.state != "PLAYING":
            return
        self.state = "GAMEOVER"
        self.death_t = 0.0
        self.demon.x = PLAYER_X - 6
        self.shake = 26.0
        self.flash_a = 140
        self.red_a = 255
        self.emit_sparks(PLAYER_X, GROUND_Y - 60, (255, 80, 90), 60, 12.0)
        self.emit_ring(PLAYER_X, GROUND_Y - 60, (255, 60, 70), 90)
        self.sounds.play("die", 1.0)
        if self.meters > self.best:
            self.best = self.meters
            self.save_best(self.best)

    def update_play(self, dtf, keys):
        pl = self.player
        self.time_s += dtf / 60.0
        self.hint_t += dtf / 60.0
        boost = 1.35 if self.boost_t > 0 else 0.0
        if self.boost_t > 0:
            self.boost_t -= dtf
        target = min(BASE_SPEED + self.time_s * 0.055, MAX_SPEED) + boost
        if pl.stumble > 0:
            target *= 0.45
        self.speed += (target - self.speed) * min(0.09 * dtf, 1.0)
        self.dist_px += self.speed * dtf
        pl.update(keys, dtf, self)
        if pl.on_ground and pl.stumble <= 0 and int(pl.run_phase * 3) % 5 == 0 and self.rnd.random() < 0.4 * dtf:
            self.emit_dust(pl)
        approach = 0.08 + 0.022 * self.level
        retreat = max(0.0, self.speed - 8.0) * 0.035
        self.demon.x += (approach - retreat) * dtf
        if self.demon.x >= PLAYER_X - CATCH_GAP:
            self.game_over()
            return
        self.demon.x = min(self.demon.x, PLAYER_X - CATCH_GAP)
        self.demon.x = max(self.demon.x, PLAYER_X - START_GAP)
        prox = self.demon.proximity()
        if prox > 0.5:
            self.heart_t -= dtf / 60.0
            if self.heart_t <= 0:
                self.heart_t = lerp(1.4, 0.75, (prox - 0.5) * 2.0)
                self.sounds.play("heart", lerp(0.35, 0.9, (prox - 0.5) * 2.0))
            self.red_a = max(self.red_a, int(160 * (prox - 0.5) * 2.0))
        else:
            self.heart_t = min(self.heart_t, 0.5)
        if self.demon.update(dtf, self.total_time):
            self.emit_smoke(
                self.rnd.uniform(self.demon.x - 100, self.demon.x - 10),
                self.rnd.uniform(GROUND_Y - 180, GROUND_Y - 20),
            )
        self.spawn_px -= self.speed * dtf
        if self.spawn_px <= 0:
            self.spawn_obstacle()
            interval = clamp(self.rnd.uniform(1.5, 2.7) - self.level * 0.06, 1.05, 2.7)
            self.spawn_px = self.speed * interval * 60.0
        self.shard_px -= self.speed * dtf
        if self.shard_px <= 0:
            self.spawn_shards()
            self.shard_px = self.speed * self.rnd.uniform(1.6, 3.1) * 60.0
        prect = pl.hitbox()
        for o in self.obstacles:
            o.x -= self.speed * dtf
            if o.kind == "pit":
                if pl.on_ground and o.x + 8 < PLAYER_X < o.x + o.w - 8:
                    self.hit_player("pit", PLAYER_X, GROUND_Y - 6)
            else:
                r = o.rect(self.total_time)
                if r.width and prect.colliderect(r.inflate(-8, -6)):
                    self.hit_player(o.kind, r.centerx, r.centery)
        for s in self.pickups:
            s.x -= self.speed * dtf
            if not s.dead and prect.inflate(26, 14).colliderect(s.rect()):
                self.collect(s)
        self.obstacles = [o for o in self.obstacles if o.x + o.w > -80]
        self.pickups = [s for s in self.pickups if not s.dead and s.x > -60]
        self.move_world(dtf)

    def move_world(self, dtf):
        self.far_off += self.speed * 0.12 * dtf
        self.mid_off += self.speed * 0.32 * dtf
        self.ground_off += self.speed * 1.0 * dtf
        self.mist_off += self.speed * 0.55 * dtf

    def update_menu(self, dtf):
        self.speed += (4.6 - self.speed) * min(0.05 * dtf, 1.0)
        self.demon.x += ((PLAYER_X - START_GAP + 30) - self.demon.x) * min(0.03 * dtf, 1.0)
        self.player.run_phase += self.speed * 0.085 * dtf
        self.player.y = float(GROUND_Y)
        self.move_world(dtf)

    def update_gameover(self, dtf):
        self.death_t += dtf / 60.0
        self.speed += (0.0 - self.speed) * min(0.06 * dtf, 1.0)
        self.demon.lunge = min(1.0, self.demon.lunge + dtf * 0.04)
        self.move_world(dtf)

    def update(self, dtf, keys):
        self.frame += dtf
        self.total_time += dtf / 60.0
        if self.state == "PLAYING":
            self.update_play(dtf, keys)
        elif self.state == "MENU":
            self.update_menu(dtf)
        elif self.state == "GAMEOVER":
            self.update_gameover(dtf)
        self.update_particles(dtf)
        self.update_ash(dtf)
        self.update_weather(dtf)
        if self.state != "PLAYING":
            if self.demon.update(dtf, self.total_time):
                self.emit_smoke(
                    self.rnd.uniform(self.demon.x - 100, self.demon.x - 10),
                    self.rnd.uniform(GROUND_Y - 180, GROUND_Y - 20),
                )
        self.shake = max(0.0, self.shake - dtf * 0.85)
        self.flash_a = max(0.0, self.flash_a - dtf * 3.4)
        self.red_a = max(0.0, self.red_a - dtf * 2.2)

    def start_game(self):
        self.reset()
        self.state = "PLAYING"
        self.sounds.play("jump", 0.5)

    def handle_key(self, ev):
        if ev.key == pygame.K_ESCAPE:
            if self.state in ("PLAYING", "PAUSED"):
                self.state = "MENU"
                self.reset()
            elif self.state == "GAMEOVER":
                self.state = "MENU"
                self.reset()
            else:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        if self.state == "MENU":
            if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.start_game()
        elif self.state == "PLAYING":
            if ev.key in (pygame.K_p, pygame.K_PAUSE):
                self.state = "PAUSED"
                self.sounds.pause_ambient(True)
            elif ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self.player.jump():
                    self.sounds.play("jump", 0.8)
                    for _ in range(6):
                        self.emit_dust(self.player)
        elif self.state == "PAUSED":
            if ev.key in (pygame.K_p, pygame.K_PAUSE):
                self.state = "PLAYING"
                self.sounds.pause_ambient(False)
        elif self.state == "GAMEOVER":
            if ev.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                self.start_game()

    def world_blit(self, surf, img, x, y, off, mod):
        x0 = -((off % mod))
        surf.blit(img, (int(x0), y))
        surf.blit(img, (int(x0 + mod), y))

    def draw(self):
        scr = self.display
        sh = self.shake
        ox = self.rnd.randint(-int(sh), int(sh)) if sh > 0.5 else 0
        oy = self.rnd.randint(-int(sh), int(sh)) if sh > 0.5 else 0
        scr.blit(self.sky, (0, oy // 3))
        if self.bolt and self.bolt_t > 0:
            alpha = 255 if int(self.bolt_t * 3) % 2 == 0 else 90
            bolt = [(p[0] + ox, p[1]) for p in self.bolt]
            pygame.draw.lines(scr, (200, 210, 255), False, bolt, 3)
            pygame.draw.lines(scr, (255, 255, 255), False, bolt, 1)
        self.world_blit(scr, self.far, 0, GROUND_Y - 330 + oy // 4, self.far_off, self.w2)
        self.world_blit(scr, self.mid, 0, GROUND_Y - 400 + oy // 3, self.mid_off, self.w2)
        self.draw_signs(scr)
        self.world_blit(scr, self.mist, 0, GROUND_Y - 300, self.mist_off, self.w2)
        self.world_blit(scr, self.ground_pat, 0, GROUND_Y + oy // 4, self.ground_off, self.w2)
        for o in self.obstacles:
            o.draw(scr, self.total_time, self.glows)
        for s in self.pickups:
            s.draw(scr, self.total_time, self.glows["ember"])
        if self.state != "GAMEOVER" or self.death_t < 0.15:
            self.demon.draw(scr, self.total_time, self.glows, int(70 + 155 * self.demon.proximity()))
        if self.state != "GAMEOVER":
            self.player.draw(scr, self.total_time)
        self.draw_particles(scr)
        for a in self.ash:
            c = int(70 + a[4] * 40)
            pygame.draw.circle(scr, (c, c - 6, c + 6), (int(a[0]), int(a[1])), 1 if a[4] < 1 else 2)
        if self.speed > 9.5:
            self.draw_speedlines(scr)
        scr.blit(self.vig, (0, 0))
        if self.red_a > 1:
            self.redvig.set_alpha(int(self.red_a))
            scr.blit(self.redvig, (0, 0))
        if self.flash_a > 1:
            self.flash.set_alpha(int(min(255, self.flash_a)))
            scr.blit(self.flash, (0, 0))
        scr.blit(self.scan, (0, 0))
        self.draw_hud(scr)
        if self.state == "MENU":
            self.draw_menu(scr)
        elif self.state == "PAUSED":
            self.draw_pause(scr)
        elif self.state == "GAMEOVER":
            self.draw_gameover(scr)

    def draw_signs(self, scr):
        off = self.mid_off % self.w2
        for rect, core, halo in self.sign_surfs:
            for k in (0, 1):
                sx = rect.x - off + k * self.w2
                if sx > W + 90 or sx < -150:
                    continue
                flick = 255 if self.rnd.random() > 0.06 else 80
                halo.set_alpha(int(flick * 0.5))
                scr.blit(halo, (int(sx + rect.w / 2 - halo.get_width() / 2), int(rect.y + rect.h / 2 - halo.get_height() / 2)))
                core.set_alpha(flick)
                scr.blit(core, (int(sx), rect.y))

    def draw_particles(self, scr):
        for p in self.particles:
            t = clamp(p.life / p.max_life, 0.0, 1.0)
            if p.kind == "smoke":
                g = self.glows["smoke"]
                g.set_alpha(int(70 * t))
                scr.blit(g, (int(p.x - g.get_width() / 2), int(p.y - g.get_height() / 2)))
            elif p.kind == "dust":
                g = self.glows["dust"]
                g.set_alpha(int(120 * t))
                scr.blit(g, (int(p.x - g.get_width() / 2), int(p.y - g.get_height() / 2)))
            elif p.kind == "spark":
                col = tuple(int(c * t) for c in p.col)
                pygame.draw.line(
                    scr,
                    col,
                    (int(p.x), int(p.y)),
                    (int(p.x - p.vx * 2.2), int(p.y - p.vy * 2.2)),
                    max(1, int(p.size * t)),
                )
                pygame.draw.circle(scr, col, (int(p.x), int(p.y)), max(1, int(p.size * t * 0.8)))
            elif p.kind == "ring":
                r = int(p.size * (1.6 - t))
                if r > 2:
                    col = tuple(int(c * t) for c in p.col)
                    pygame.draw.circle(scr, col, (int(p.x), int(p.y)), r, 2)

    def draw_speedlines(self, scr):
        n = int((self.speed - 9.0) * 3)
        for _ in range(n):
            y = self.rnd.randint(0, H)
            x = self.rnd.randint(0, W)
            ln = self.rnd.randint(40, 160)
            pygame.draw.line(scr, (140, 130, 160), (x, y), (x + ln, y), 1)

    def draw_hud(self, scr):
        if self.state == "MENU":
            return
        panel = pygame.Rect(24, 20, 300, 78)
        pygame.draw.rect(scr, (11, 9, 18), panel)
        pygame.draw.rect(scr, (74, 64, 96), panel, 1)
        pygame.draw.rect(scr, AMBER, (24, 20, 4, 78))
        draw_text(scr, self.font_hud, "DISTANCE", (42, 28), DIM_COL)
        draw_text(scr, self.font_hud, "%05d m" % self.meters, (42, 56), TEXT_COL)
        shard_rect = pygame.Rect(24, 106, 150, 40)
        pygame.draw.rect(scr, (11, 9, 18), shard_rect)
        pygame.draw.rect(scr, (74, 64, 96), shard_rect, 1)
        pygame.draw.polygon(scr, AMBER, [(44, 116), (52, 126), (44, 136), (36, 126)])
        draw_text(scr, self.font_hud, "x %d" % self.shard_count, (62, 114), TEXT_COL)
        gap = max(0, int(self.demon.gap // 25))
        bar = pygame.Rect(W - 344, 20, 320, 78)
        pygame.draw.rect(scr, (11, 9, 18), bar)
        pygame.draw.rect(scr, (74, 64, 96), bar, 1)
        pygame.draw.rect(scr, CRIMSON, (W - 28, 20, 4, 78))
        prox = self.demon.proximity()
        draw_text(scr, self.font_small, "IT IS BEHIND YOU", (W - 328, 30), DIM_COL)
        fill = pygame.Rect(W - 328, 58, 284, 16)
        pygame.draw.rect(scr, (26, 22, 36), fill)
        w = int(fill.w * clamp(prox, 0.03, 1.0))
        col = mix(TEAL, CRIMSON, prox)
        pygame.draw.rect(scr, col, (fill.x, fill.y, w, fill.h))
        for i in range(1, 8):
            pygame.draw.line(scr, (11, 9, 18), (fill.x + i * fill.w // 8, fill.y), (fill.x + i * fill.w // 8, fill.y + fill.h), 2)
        draw_text(scr, self.font_small, "%dm" % gap, (W - 328, 76), TEXT_COL)
        if self.state == "PLAYING" and self.hint_t < 9.0:
            a = 255 if self.hint_t < 7.0 else int(255 * (9.0 - self.hint_t) / 2.0)
            txt = self.font_body.render("SPACE / UP  jump      DOWN  slide      P  pause", True, DIM_COL)
            txt.set_alpha(a)
            r = txt.get_rect(midbottom=(W // 2, H - 26))
            scr.blit(txt, r)

    def draw_menu(self, scr):
        t = self.total_time
        pulse = 0.5 + 0.5 * math.sin(t * 3.0)
        scr.blit(self.menu_shade, (0, 0))
        title = "DON'T LOOK BACK"
        base = self.font_title.render(title, True, TEXT_COL)
        if self.glitch_t <= 0:
            self.glitch_t = 14.0
            self.glitch_off = self.rnd.randint(-6, 6) if self.rnd.random() < 0.5 else 0
        self.glitch_t -= 1
        r = base.get_rect(center=(W // 2, 150))
        shadow = self.font_title.render(title, True, (140, 20, 40))
        scr.blit(shadow, (r.x + 5, r.y + 6))
        g1 = self.font_title.render(title, True, (255, 70, 90))
        g1.set_alpha(150)
        scr.blit(g1, (r.x + self.glitch_off - 4, r.y))
        g2 = self.font_title.render(title, True, (80, 230, 220))
        g2.set_alpha(110)
        scr.blit(g2, (r.x - self.glitch_off + 4, r.y))
        scr.blit(base, r)
        draw_text(
            scr,
            self.font_body,
            "a dystopian chase  -  run, jump, slide. do not stop.",
            (W // 2, 230),
            DIM_COL,
            align="center",
        )
        key = self.menu_panel
        scr.blit(key, (W // 2 - 320, 300))
        pygame.draw.rect(scr, (74, 64, 96), (W // 2 - 320, 300, 640, 176), 1)
        pygame.draw.rect(scr, CRIMSON, (W // 2 - 320, 300, 640, 3))
        draw_text(scr, self.font_hud, "CONTROLS", (W // 2, 318), AMBER, align="midtop")
        lines = [
            "SPACE / UP      jump over crates, barriers and pits",
            "DOWN            slide under the patrol drones",
            "collect shards  to force the demon back",
            "stumble         and it gains on you",
        ]
        for i, ln in enumerate(lines):
            draw_text(scr, self.font_body, ln, (W // 2, 356 + i * 30), TEXT_COL, align="midtop")
        a = int(140 + 115 * pulse)
        txt = self.font_big.render("PRESS ENTER TO RUN", True, TEXT_COL)
        txt.set_alpha(a)
        r2 = txt.get_rect(center=(W // 2, 545))
        scr.blit(txt, r2)
        if self.best > 0:
            draw_text(scr, self.font_body, "best  %05d m" % self.best, (W // 2, 600), DIM_COL, align="center")
        draw_text(scr, self.font_small, "ESC  quit", (W // 2, H - 30), (110, 100, 130), align="center")

    def draw_pause(self, scr):
        scr.blit(self.overlay, (0, 0))
        draw_text(scr, self.font_big, "PAUSED", (W // 2, H // 2 - 60), TEXT_COL, align="center", shadow=(120, 30, 40))
        draw_text(scr, self.font_body, "P  resume      ESC  back to menu", (W // 2, H // 2 + 10), DIM_COL, align="center")

    def draw_gameover(self, scr):
        a = clamp(int((self.death_t - 0.25) * 260), 0, 255)
        if a <= 0:
            return
        self.overlay.set_alpha(a)
        scr.blit(self.overlay, (0, 0))
        col = TEXT_COL
        title = self.font_big.render("IT FOUND YOU", True, col)
        title.set_alpha(a)
        r = title.get_rect(center=(W // 2, 190))
        sh = self.font_big.render("IT FOUND YOU", True, (170, 20, 40))
        sh.set_alpha(a)
        scr.blit(sh, (r.x + 4, r.y + 5))
        scr.blit(title, r)
        stats = [("distance", "%05d m" % self.meters), ("shards", "x %d" % self.shard_count), ("best", "%05d m" % self.best)]
        for i, (k, v) in enumerate(stats):
            x = W // 2 - 300 + i * 220
            box = pygame.Rect(x, 280, 200, 90)
            pygame.draw.rect(scr, (11, 9, 18), box)
            pygame.draw.rect(scr, (74, 64, 96), box, 1)
            draw_text(scr, self.font_small, k.upper(), (x + 100, 296), DIM_COL, align="midtop")
            draw_text(scr, self.font_hud, v, (x + 100, 326), TEXT_COL, align="midtop")
        a2 = clamp(int((self.death_t - 0.8) * 300), 0, 255)
        if a2 > 0:
            t1 = self.font_body.render("R  run again      ESC  menu", True, TEXT_COL)
            t1.set_alpha(a2)
            r1 = t1.get_rect(center=(W // 2, 440))
            scr.blit(t1, r1)

    def run(self):
        smoke = int(os.environ.get("DLB_SMOKE", "0"))
        frames = 0
        running = True
        while running:
            dtf = min(self.clock.tick(FPS) / 16.6667, 2.2)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    self.held.press(ev.key)
                    self.handle_key(ev)
                elif ev.type == pygame.KEYUP:
                    self.held.release(ev.key)
                elif ev.type == pygame.WINDOWFOCUSLOST:
                    self.held.clear()
                    if self.state == "PLAYING":
                        self.state = "PAUSED"
                        self.sounds.pause_ambient(True)
            self.update(dtf, self.held)
            self.draw()
            pygame.display.flip()
            frames += 1
            if smoke and frames >= smoke:
                running = False
        self.sounds.stop_ambient()
        pygame.quit()

def main():
    Game().run()

if __name__ == "__main__":
    main()


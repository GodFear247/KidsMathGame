import pygame
import random
import os
import math
import tempfile
import hashlib
import threading
import asyncio
import edge_tts
import sys
import json
import wave
import struct

# ===============================
# Resource & Sound Helpers
# ===============================
def get_resource_path(relative_path):
    """ PyInstaller ဖြင့် App ထုတ်သောအခါ ဖိုင်လမ်းကြောင်းမှန်ကန်စေရန် """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_save_file_path(filename="save_data.json"):
    """ Save data file path """
    return os.path.join(os.path.abspath("."), filename)

def generate_bgm_if_missing():
    """ Generate a cheerful, bouncy Kids Marimba Melody WAV file """
    bgm_path = get_save_file_path("bgm_kids.wav")
    if not os.path.exists(bgm_path):
        try:
            sample_rate = 22050
            # Playful 8-bar Kids Nursery Melody (Twinkle / Playground style in C Major)
            C3, E3, G3, F3, A3 = 130.81, 164.81, 196.00, 174.61, 220.00
            C4, D4, E4, F4, G4, A4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00

            melody = [
                C4, C4, G4, G4, A4, A4, G4, 0,
                F4, F4, E4, E4, D4, D4, C4, 0,
                G4, G4, F4, F4, E4, E4, D4, 0,
                G4, G4, F4, F4, E4, E4, D4, 0,
                C4, C4, G4, G4, A4, A4, G4, 0,
                F4, F4, E4, E4, D4, D4, C4, 0
            ]
            bass = [
                C3, G3, C3, G3, F3, A3, C3, G3,
                F3, C3, E3, C3, G3, D3, C3, G3,
                C3, G3, F3, A3, C3, G3, G3, D3,
                C3, G3, F3, A3, C3, G3, G3, D3,
                C3, G3, C3, G3, F3, A3, C3, G3,
                F3, C3, E3, C3, G3, D3, C3, G3
            ]

            step_len = int(sample_rate * 0.28) # Bouncy, upbeat 280ms tempo
            num_samples = len(melody) * step_len

            with wave.open(bgm_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                frames = bytearray()
                for i in range(num_samples):
                    step_idx = i // step_len
                    t_step = (i % step_len) / sample_rate
                    
                    # Bright Marimba Lead
                    freq_m = melody[step_idx]
                    lead_val = 0
                    if freq_m > 0:
                        env_m = math.exp(-t_step * 10.0) # Crisp marimba decay
                        lead_val = (math.sin(2 * math.pi * freq_m * t_step) + 0.35 * math.sin(4 * math.pi * freq_m * t_step)) * env_m * 0.20
                    
                    # Bouncy Bassline
                    freq_b = bass[step_idx]
                    env_b = math.exp(-t_step * 6.0)
                    bass_val = math.sin(2 * math.pi * freq_b * t_step) * env_b * 0.12

                    sample_val = lead_val + bass_val
                    sample_int = int(max(-1.0, min(1.0, sample_val)) * 32767)
                    frames.extend(struct.pack('<h', sample_int))
                
                wav_file.writeframes(frames)
        except Exception as e:
            print("BGM Generation Error:", e)
    return bgm_path


# ===============================
# Voice Manager
# ===============================
class VoiceManager:
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            self.enabled = False

        self.cache_dir = os.path.join(tempfile.gettempdir(), "kids_math_voice_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.lang = "EN"
        self.voices = {
            "EN": "en-US-AriaNeural",
            "MM": "my-MM-NilarNeural"
        }

    def filename(self, text, lang):
        h = hashlib.md5((text + lang + "_custom_speed_v4").encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, h + ".mp3")

    def create_voice(self, text, path, lang):
        async def make():
            if lang == "MM":
                # Faster Burmese Female Voice (+22% speed)
                tts = edge_tts.Communicate(text=text, voice="my-MM-NilarNeural", rate="+22%", pitch="+10%")
            else:
                # Original English Female Voice (+10% speed)
                tts = edge_tts.Communicate(text=text, voice="en-US-AriaNeural", rate="+10%", pitch="+5%")
            await tts.save(path)
        asyncio.run(make())

    def speak(self, text):
        if not self.enabled:
            return

        current_lang = self.lang
        def worker():
            path = self.filename(text, current_lang)
            if not os.path.exists(path):
                try:
                    self.create_voice(text, path, current_lang)
                except Exception as e:
                    print(f"TTS Error: {e}")
                    return
            try:
                pygame.mixer.Sound(path).play()
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()


# ===============================
# Font helper
# ===============================
def load_font(candidates, size, bold=False):
    available = pygame.font.get_fonts()
    for name in candidates:
        key = name.lower().replace(" ", "")
        if key in available:
            return pygame.font.SysFont(name, size, bold=bold)
    return pygame.font.Font(None, size + (4 if bold else 0))


# ===============================
# Question Generator (Updated with Difficulty)
# ===============================
def generate_questions(total=10, allowed_ops=["+"], difficulty="EASY"):
    result = []
    used = set()
    while len(result) < total:
        op = random.choice(allowed_ops)
        
        if op == "+":
            if difficulty == "EASY":
                a, b = random.randint(1, 10), random.randint(1, 10)
            elif difficulty == "MEDIUM":
                a, b = random.randint(10, 50), random.randint(10, 50)
            else: # HARD
                a, b = random.randint(50, 100), random.randint(50, 100)
            ans = a + b
            display_op = "+"
            
        elif op == "-":
            if difficulty == "EASY":
                a, b = random.randint(1, 10), random.randint(1, 1)
            elif difficulty == "MEDIUM":
                a, b = random.randint(10, 50), random.randint(10, 50)
            else:
                a, b = random.randint(50, 100), random.randint(50, 100)
                
            if a < b: a, b = b, a 
            ans = a - b
            display_op = "-"
            
        elif op == "*":
            if difficulty == "EASY":
                a, b = random.randint(1, 5), random.randint(1, 5)
            elif difficulty == "MEDIUM":
                a, b = random.randint(2, 10), random.randint(2, 10)
            else:
                a, b = random.randint(5, 15), random.randint(5, 15)
            ans = a * b
            display_op = "x"
            
        elif op == "/":
            if difficulty == "EASY":
                b = random.randint(1, 5)
                ans = random.randint(1, 5)
            elif difficulty == "MEDIUM":
                b = random.randint(2, 10)
                ans = random.randint(2, 10)
            else:
                b = random.randint(3, 12)
                ans = random.randint(5, 15)
            a = b * ans 
            display_op = "÷"

        key = f"{a}{op}{b}"
        if key in used:
            continue
        used.add(key)

        wrong = set()
        while len(wrong) < 3:
            if op in ["*", "/"]:
                offset = random.choice([-2, -1, 1, 2, b, -b])
                if offset == 0: offset = 1
                x = ans + offset
            else:
                if difficulty == "EASY":
                    offset = random.randint(-4, 4)
                elif difficulty == "MEDIUM":
                    offset = random.randint(-10, 10)
                else:
                    offset = random.randint(-20, 20)
                    
                if offset == 0: offset = 2
                x = ans + offset
                
            if x >= 0 and x != ans:
                wrong.add(x)

        options = list(wrong)
        options.append(ans)
        random.shuffle(options)

        result.append({
            "a": a, "b": b, "op": op, "display_op": display_op,
            "q_str": f"{a} {display_op} {b}",
            "answer": ans,
            "options": options
        })
    return result


# ===============================
# Visual helpers
# ===============================
def make_vertical_gradient(size, top_color, bottom_color):
    w, h = size
    surf = pygame.Surface(size)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = top_color[0] + (bottom_color[0] - top_color[0]) * t
        g = top_color[1] + (bottom_color[1] - top_color[1]) * t
        b = top_color[2] + (bottom_color[2] - top_color[2]) * t
        pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (w, y))
    return surf

def draw_soft_shadow(surface, rect, radius=20, offset=(0, 8), alpha=45):
    shadow_surf = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(20, 20, rect.width, rect.height)
    for i in range(6, 0, -1):
        a = int(alpha * (i / 6))
        grown = shadow_rect.inflate(i * 3, i * 3)
        pygame.draw.rect(shadow_surf, (30, 30, 60, a), grown, border_radius=radius + i)
    surface.blit(shadow_surf, (rect.x - 20 + offset[0], rect.y - 20 + offset[1]))

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_star(surface, center, size, color, rotation=0):
    points = []
    for i in range(10):
        angle = math.pi / 5 * i + rotation
        r = size if i % 2 == 0 else size * 0.45
        points.append((center[0] + r * math.sin(angle), center[1] - r * math.cos(angle)))
    pygame.draw.polygon(surface, color, points)


# ===============================
# Custom Avatar & Coin Vector Surface Renderer
# ===============================
AVATAR_MAP = {
    "😊": "smile",
    "🐶": "dog",
    "🐱": "cat",
    "🐼": "panda",
    "🦄": "unicorn",
    "smile": "smile",
    "dog": "dog",
    "cat": "cat",
    "panda": "panda",
    "unicorn": "unicorn"
}

SURFACE_CACHE = {}

def create_avatar_surface(avatar_key, size=60):
    avatar_key = AVATAR_MAP.get(avatar_key, "smile")
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    radius = size // 2
    cx, cy = radius, radius
    
    if avatar_key == "smile":
        pygame.draw.circle(surf, (255, 214, 51), (cx, cy), radius - 2)
        pygame.draw.circle(surf, (230, 180, 20), (cx, cy), radius - 2, 2)
        eye_r = max(2, size // 10)
        pygame.draw.circle(surf, (40, 40, 40), (cx - size // 4, cy - size // 8), eye_r)
        pygame.draw.circle(surf, (40, 40, 40), (cx + size // 4, cy - size // 8), eye_r)
        rect = pygame.Rect(cx - size // 4, cy - size // 6, size // 2, int(size // 2.2))
        pygame.draw.arc(surf, (40, 40, 40), rect, math.pi * 1.1, math.pi * 1.9, max(2, size // 15))

    elif avatar_key == "dog":
        ear_w, ear_h = int(size * 0.28), int(size * 0.45)
        ear_l = pygame.Rect(int(cx - size * 0.45), int(cy - size * 0.25), ear_w, ear_h)
        ear_r = pygame.Rect(int(cx + size * 0.45 - ear_w), int(cy - size * 0.25), ear_w, ear_h)
        pygame.draw.ellipse(surf, (140, 80, 30), ear_l)
        pygame.draw.ellipse(surf, (140, 80, 30), ear_r)
        pygame.draw.circle(surf, (215, 150, 75), (cx, cy + size // 15), int(radius * 0.82))
        snout_w, snout_h = int(size * 0.45), int(size * 0.35)
        snout_rect = pygame.Rect(cx - snout_w // 2, cy, snout_w, snout_h)
        pygame.draw.ellipse(surf, (255, 245, 230), snout_rect)
        nose_r = max(3, size // 12)
        pygame.draw.circle(surf, (40, 30, 25), (cx, cy + size // 12), nose_r)
        tongue_w, tongue_h = int(size * 0.16), int(size * 0.2)
        tongue_rect = pygame.Rect(cx - tongue_w // 2, cy + size // 5, tongue_w, tongue_h)
        pygame.draw.ellipse(surf, (255, 120, 150), tongue_rect)
        eye_r = max(2, size // 12)
        pygame.draw.circle(surf, (30, 25, 20), (cx - size // 4, cy - size // 8), eye_r)
        pygame.draw.circle(surf, (30, 25, 20), (cx + size // 4, cy - size // 8), eye_r)

    elif avatar_key == "cat":
        pts_left = [(cx - size * 0.38, cy - size * 0.05), (cx - size * 0.4, cy - size * 0.45), (cx - size * 0.1, cy - size * 0.3)]
        pts_right = [(cx + size * 0.38, cy - size * 0.05), (cx + size * 0.4, cy - size * 0.45), (cx + size * 0.1, cy - size * 0.3)]
        pygame.draw.polygon(surf, (255, 160, 80), pts_left)
        pygame.draw.polygon(surf, (255, 160, 80), pts_right)
        pygame.draw.circle(surf, (255, 170, 90), (cx, cy + size // 20), int(radius * 0.8))
        snout_w, snout_h = int(size * 0.35), int(size * 0.25)
        pygame.draw.ellipse(surf, (255, 245, 235), (cx - snout_w // 2, cy + 2, snout_w, snout_h))
        eye_w, eye_h = int(size * 0.18), int(size * 0.22)
        pygame.draw.ellipse(surf, (60, 200, 130), (cx - size // 4 - eye_w // 2, cy - size // 8, eye_w, eye_h))
        pygame.draw.ellipse(surf, (60, 200, 130), (cx + size // 4 - eye_w // 2, cy - size // 8, eye_w, eye_h))

    elif avatar_key == "panda":
        ear_r = int(radius * 0.35)
        pygame.draw.circle(surf, (35, 35, 40), (cx - int(radius * 0.65), cy - int(radius * 0.65)), ear_r)
        pygame.draw.circle(surf, (35, 35, 40), (cx + int(radius * 0.65), cy - int(radius * 0.65)), ear_r)
        pygame.draw.circle(surf, (250, 250, 252), (cx, cy), int(radius * 0.82))
        patch_w, patch_h = int(size * 0.26), int(size * 0.32)
        patch_l = pygame.Surface((patch_w, patch_h), pygame.SRCALPHA)
        patch_r = pygame.Surface((patch_w, patch_h), pygame.SRCALPHA)
        pygame.draw.ellipse(patch_l, (35, 35, 40), (0, 0, patch_w, patch_h))
        pygame.draw.ellipse(patch_r, (35, 35, 40), (0, 0, patch_w, patch_h))
        rot_l = pygame.transform.rotate(patch_l, 15)
        rot_r = pygame.transform.rotate(patch_r, -15)
        surf.blit(rot_l, rot_l.get_rect(center=(cx - size // 4, cy - size // 12)))
        surf.blit(rot_r, rot_r.get_rect(center=(cx + size // 4, cy - size // 12)))

    elif avatar_key == "unicorn":
        pygame.draw.circle(surf, (255, 140, 200), (cx - size // 4, cy - size // 4), int(radius * 0.4))
        pygame.draw.circle(surf, (250, 245, 255), (cx, cy + size // 20), int(radius * 0.78))
        horn_pts = [(cx, cy - int(size * 0.48)), (cx - int(size * 0.1), cy - int(size * 0.22)), (cx + int(size * 0.1), cy - int(size * 0.22))]
        pygame.draw.polygon(surf, (255, 215, 0), horn_pts)

    return surf

def create_coin_surface(size=36):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    radius = size // 2
    cx, cy = radius, radius
    pygame.draw.circle(surf, (200, 130, 0), (cx + 1, cy + 2), radius - 2)
    pygame.draw.circle(surf, (255, 195, 0), (cx, cy), radius - 2)
    pygame.draw.circle(surf, (255, 235, 120), (cx, cy), radius - 2, 2)
    pygame.draw.circle(surf, (255, 170, 0), (cx, cy), radius - 6)
    draw_star(surf, (cx, cy), int(size * 0.22), (255, 255, 220))
    return surf

def get_avatar_surface(avatar_key, size=60):
    cache_key = (f"avatar_{avatar_key}", size)
    if cache_key not in SURFACE_CACHE:
        SURFACE_CACHE[cache_key] = create_avatar_surface(avatar_key, size)
    return SURFACE_CACHE[cache_key]

def get_coin_surface(size=36):
    cache_key = ("coin", size)
    if cache_key not in SURFACE_CACHE:
        SURFACE_CACHE[cache_key] = create_coin_surface(size)
    return SURFACE_CACHE[cache_key]


# ===============================
# UI Components
# ===============================
class Confetti:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-15, -5)
        self.color = random.choice([
            (255, 99, 132), (99, 209, 128), (99, 168, 255),
            (255, 221, 89), (255, 159, 28), (198, 129, 255)
        ])
        self.size = random.randint(6, 12)
        self.shape = random.choice(['circle', 'rect'])
        self.timer = 80
        self.max_timer = 80
        self.spin = random.uniform(-8, 8)
        self.angle = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.6
        self.angle += self.spin
        self.timer -= 1

    def draw(self, surface):
        if self.timer <= 0: return
        fade = max(0, min(255, int(255 * (self.timer / self.max_timer))))
        if self.shape == 'circle':
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, fade), (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))
        else:
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(s, (*self.color, fade), (0, 0, self.size, self.size), border_radius=2)
            rotated = pygame.transform.rotate(s, self.angle)
            surface.blit(rotated, rotated.get_rect(center=(self.x, self.y)))

class Button:
    def __init__(self, x, y, w, h, text, font, bg_color, hover_color, text_color, radius=16, emoji_font=None, emoji_text=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.emoji_font = emoji_font
        self.emoji_text = emoji_text
        self.base_color = bg_color
        self.hover_color = hover_color
        self.current_color = bg_color
        self.text_color = text_color
        self.state = "normal"
        self.custom_color = None
        self.radius = radius
        self.hover_progress = 0.0

    def update(self, offset_x=0, offset_y=0):
        pos = pygame.mouse.get_pos()
        draw_rect = self.rect.move(offset_x, offset_y)
        target = 1.0 if (self.state == "normal" and draw_rect.collidepoint(pos)) else 0.0
        self.hover_progress += (target - self.hover_progress) * 0.25

    def draw(self, surface, offset_x=0, offset_y=0):
        draw_rect = self.rect.move(offset_x, offset_y)
        lift = int(self.hover_progress * 4)
        raised_rect = draw_rect.move(0, -lift)

        draw_soft_shadow(surface, raised_rect, radius=self.radius, offset=(0, 6 - lift), alpha=35)
        self.current_color = self.custom_color if self.custom_color else lerp_color(self.base_color, self.hover_color, self.hover_progress)

        pygame.draw.rect(surface, self.current_color, raised_rect, border_radius=self.radius)
        pygame.draw.rect(surface, (255, 255, 255), raised_rect, width=2, border_radius=self.radius)

        if self.emoji_font and self.emoji_text:
            em_surf = self.emoji_font.render(self.emoji_text, True, self.text_color)
            txt_surf = self.font.render(self.text, True, self.text_color)
            
            total_w = em_surf.get_width() + 10 + txt_surf.get_width()
            start_x = raised_rect.centerx - total_w // 2
            
            surface.blit(em_surf, (start_x, raised_rect.centery - em_surf.get_height() // 2))
            surface.blit(txt_surf, (start_x + em_surf.get_width() + 10, raised_rect.centery - txt_surf.get_height() // 2))
        else:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=raised_rect.center)
            surface.blit(text_surf, text_rect)

    def is_clicked(self, event, offset_x=0, offset_y=0):
        if self.state == "normal" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.move(offset_x, offset_y).collidepoint(event.pos):
                return True
        return False

class Slider:
    def __init__(self, x, y, w, h, initial_val=0.5):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = initial_val
        self.dragging = False
        self.knob_radius = int(h * 1.3)
        if self.knob_radius < 8: self.knob_radius = 8

    def update(self, event):
        hit_rect = self.rect.inflate(self.knob_radius*4, self.knob_radius*4)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hit_rect.collidepoint(event.pos):
                self.dragging = True
                self._set_val(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._set_val(event.pos[0])
                return True
        return False

    def _set_val(self, mouse_x):
        rel_x = mouse_x - self.rect.x
        self.val = max(0, min(1, rel_x / self.rect.w))
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.val * 0.4)
        except Exception:
            pass

    def draw(self, surface):
        pygame.draw.rect(surface, (230, 210, 190), self.rect, border_radius=self.rect.h//2)
        fill_w = int(self.val * self.rect.w)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            pygame.draw.rect(surface, (142, 223, 178), fill_rect, border_radius=self.rect.h//2)
        knob_x = self.rect.x + fill_w
        knob_y = self.rect.centery
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, knob_y), self.knob_radius)
        pygame.draw.circle(surface, (180, 180, 180), (knob_x, knob_y), self.knob_radius, 1)


# ===============================
# Math Game Pygame Main Class
# ===============================
class MathGamePygame:
    BG_TOP = (255, 244, 214)
    BG_BOTTOM = (255, 223, 186)
    CARD = (255, 255, 255)
    PRIMARY = (255, 145, 77)
    CARD_BORDER = (255, 199, 130)
    BUTTON_BG = (255, 214, 128)
    BUTTON_HOVER = (255, 179, 71)
    GREEN = (142, 223, 178)
    RED = (255, 158, 158)
    TEXT = (55, 61, 92)
    SCORE_TEXT = (42, 157, 143)
    BTN_BLUE = (173, 216, 255)
    BTN_BLUE_HOVER = (140, 195, 255)

    DIALOGUE = {
        "WELCOME": {"EN": "Choose a game mode to start!", "MM": "ကစားမယ့်ပုံစံကို ရွေးချယ်ပေးပါ!"},
        "SELECT_DIFF": {"EN": "Select a difficulty level.", "MM": "အခက်အခဲ အဆင့်ကို ရွေးချယ်ပေးပါ!"},
        "CORRECT": {"EN": "Correct! Great job!", "MM": "မှန်ပါတယ်။ အရမ်းတော်တာပဲ!"},
        "WRONG":   {"EN": "Oops! Try again.", "MM": "မှားနေပါတယ်။ ထပ်ကြိုးစားကြည့်ပါဦးနော်။"},
        "GREET_EN": {"EN": "English voice activated.", "MM": "Hello!"},
        "GREET_MM": {"EN": "Burmese voice activated.", "MM": "မြန်မာအသံ ပြောင်းလိုက်ပါပြီ။"}
    }

    FONT_CANDIDATES = ["comicsansms", "comic sans ms", "chalkboardse", "verdana", "arial", "dejavusans"]
    EMOJI_CANDIDATES = ["segoeuiemoji", "notocoloremoji", "applecoloremoji", "symbola", "segoe ui emoji"]

    def __init__(self):
        pygame.init()
        self.save_file = get_save_file_path("save_data.json")
        self.load_data()
        self.earned_coins = 0
        self.width, self.height = 700, 880
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Kids Math Game")
        self.clock = pygame.time.Clock()

        self.title_font = load_font(self.FONT_CANDIDATES, 42, bold=True)
        self.ui_font = load_font(self.FONT_CANDIDATES, 22, bold=True)
        self.ui_font_large = load_font(self.FONT_CANDIDATES, 30, bold=True)
        
        self.emoji_font = load_font(self.EMOJI_CANDIDATES, 30)
        self.emoji_large = load_font(self.EMOJI_CANDIDATES, 45)
        
        self.math_font = load_font(self.FONT_CANDIDATES, 72, bold=True)
        self.btn_font = load_font(self.FONT_CANDIDATES, 36, bold=True)

        self.background = make_vertical_gradient((self.width, self.height), self.BG_TOP, self.BG_BOTTOM)
        self.voice = VoiceManager()
        self.voice_on = True
        self.total_questions = 10
        self.current_ops = ["+"]
        self.combo = 0
        
        # Load or generate playful Kids Marimba BGM
        music_path = get_resource_path("bgm.mp3")
        if not os.path.exists(music_path):
            music_path = generate_bgm_if_missing()

        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.25)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print("BGM Playback Error:", e)

        self.setup_header_ui()
        self.setup_menu_ui()
        self.setup_difficulty_ui()
        self.setup_shop_ui()

        self.time_elapsed = 0
        self.shake_amount = 0  
        
        self.state = "MENU"
        self.speak_dialogue("WELCOME")
        self.confetti_particles = []

    def load_data(self):
        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                self.save_data = json.load(f)
        except Exception:
            self.save_data = {
                "coins": 0,
                "unlocked_avatars": ["😊"],
                "equipped_avatar": "😊"
            }

    def save_game_data(self):
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(self.save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Save error:", e)

    def setup_header_ui(self):
        self.btn_home = Button(20, 25, 55, 45, "🏠", self.emoji_font, self.BUTTON_BG, self.BUTTON_HOVER, self.TEXT, radius=20)
        self.music_slider = Slider(130, 42, 100, 10, initial_val=0.3)
        self.btn_lang = Button(520, 25, 60, 45, "EN", self.ui_font, self.BUTTON_BG, self.BUTTON_HOVER, self.TEXT, radius=20)
        self.btn_voice = Button(600, 25, 60, 45, "🔊", self.emoji_font, self.BUTTON_BG, self.BUTTON_HOVER, self.TEXT, radius=20)

    def setup_menu_ui(self):
        btn_w, btn_h = 300, 70
        cx = self.width // 2 - btn_w // 2
        
        self.btn_menu_add = Button(cx, 250, btn_w, btn_h, "Addition", self.ui_font_large, self.GREEN, (100, 200, 150), self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="➕")
        self.btn_menu_sub = Button(cx, 340, btn_w, btn_h, "Subtraction", self.ui_font_large, self.RED, (220, 120, 120), self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="➖")
        self.btn_menu_mul = Button(cx, 430, btn_w, btn_h, "Multiplication", self.ui_font_large, self.BTN_BLUE, self.BTN_BLUE_HOVER, self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="✖️")
        self.btn_menu_div = Button(cx, 520, btn_w, btn_h, "Division", self.ui_font_large, (220, 180, 255), (190, 150, 230), self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="➗")
        self.btn_menu_mix = Button(cx, 610, btn_w, btn_h, "Mix All", self.ui_font_large, self.PRIMARY, self.BUTTON_HOVER, (255,255,255), radius=25, emoji_font=self.emoji_font, emoji_text="🎲")
        self.btn_menu_shop = Button(self.width - 150, 85, 120, 50, "Shop", self.ui_font, (255, 214, 100), (230, 190, 80), self.TEXT, radius=20, emoji_font=self.emoji_font, emoji_text="🛒")
    
    def setup_shop_ui(self):
        self.btn_shop_back = Button(self.width // 2 - 90, 750, 180, 60, "Back", self.ui_font_large, self.BUTTON_BG, self.BUTTON_HOVER, self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="🔙")
        
        self.shop_items = [
            {"emoji": "🐶", "price": 20, "name": "Dog"},
            {"emoji": "🐱", "price": 50, "name": "Cat"},
            {"emoji": "🐼", "price": 100, "name": "Panda"},
            {"emoji": "🦄", "price": 200, "name": "Unicorn"}
        ]
        
        self.shop_buy_btns = []
        for i in range(len(self.shop_items)):
            btn = Button(self.width - 200, 230 + (i * 120), 140, 60, "Buy", self.ui_font, self.BTN_BLUE, self.BTN_BLUE_HOVER, self.TEXT, radius=20)
            self.shop_buy_btns.append(btn)

    def setup_difficulty_ui(self):
        btn_w, btn_h = 300, 80
        cx = self.width // 2 - btn_w // 2
        
        self.btn_diff_easy = Button(cx, 280, btn_w, btn_h, "Easy", self.ui_font_large, self.GREEN, (100, 200, 150), self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="🟢")
        self.btn_diff_med = Button(cx, 390, btn_w, btn_h, "Medium", self.ui_font_large, (255, 214, 100), (230, 190, 80), self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="🟡")
        self.btn_diff_hard = Button(cx, 500, btn_w, btn_h, "Hard", self.ui_font_large, self.RED, (220, 120, 120), self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="🔴")
        
        self.btn_diff_back = Button(cx + 60, 620, 180, 60, "Back", self.ui_font_large, self.BUTTON_BG, self.BUTTON_HOVER, self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="🔙")

    def select_mode(self, ops):
        self.current_ops = ops
        self.state = "DIFFICULTY"
        self.speak_dialogue("SELECT_DIFF")

    def start_game(self, difficulty):
        self.difficulty = difficulty
        self.questions = generate_questions(self.total_questions, self.current_ops, self.difficulty)
        self.index = 0
        self.score = 0
        self.combo = 0
        self.state = "PLAYING"
        self.wait_timer = 0
        self.confetti_particles = []
        self.shake_amount = 0
        self.msg_text = ""
        self.msg_emoji = ""
        self.msg_color = self.TEXT
        self.msg_scale_timer = 0 

        self.setup_game_ui()
        if self.voice.lang == "EN":
            self.voice.speak(f"Starting {self.difficulty} mode! Let's go!")
        else:
            self.voice.speak("စတင်လိုက်ရအောင်!")

    def setup_game_ui(self):
        self.btn_read = Button(230, 450, 240, 50, "Read Question", self.ui_font, self.BTN_BLUE, self.BTN_BLUE_HOVER, self.TEXT, radius=25, emoji_font=self.emoji_font, emoji_text="🔈")
        self.btn_restart = Button(150, 600, 180, 60, "Play Again", self.ui_font_large, self.GREEN, (100, 200, 150), self.TEXT, radius=30, emoji_font=self.emoji_font, emoji_text="🔄")
        self.btn_back_menu = Button(370, 600, 180, 60, "Menu", self.ui_font_large, self.PRIMARY, (230, 130, 15), (255, 255, 255), radius=30, emoji_font=self.emoji_font, emoji_text="🏠")
        self.setup_answer_buttons()

    def setup_answer_buttons(self):
        self.ans_buttons = []
        if self.index >= len(self.questions): return
        options = self.questions[self.index]["options"]
        btn_w, btn_h = 160, 100
        start_x = (self.width // 2) - btn_w - 20
        start_y = 570
        for i in range(4):
            row, col = i // 2, i % 2
            x = start_x + (col * (btn_w + 40))
            y = start_y + (row * (btn_h + 30))
            btn = Button(x, y, btn_w, btn_h, str(options[i]), self.btn_font, self.BUTTON_BG, self.BUTTON_HOVER, self.TEXT, radius=20)
            self.ans_buttons.append(btn)

    def toggle_voice(self):
        self.voice_on = not self.voice_on
        self.btn_voice.text = "🔊" if self.voice_on else "🔇"

    def toggle_lang(self):
        if self.voice.lang == "EN":
            self.voice.lang = "MM"
            self.btn_lang.text = "MM"
            self.speak_dialogue("GREET_MM")
        else:
            self.voice.lang = "EN"
            self.btn_lang.text = "EN"
            self.speak_dialogue("GREET_EN")

    def speak_dialogue(self, key):
        if self.voice_on:
            self.voice.speak(self.DIALOGUE[key][self.voice.lang])

    def read_question(self):
        if not self.voice_on: return
        q = self.questions[self.index]
        a, b, op = str(q["a"]), str(q["b"]), q["op"]
        
        if self.voice.lang == "EN":
            op_words = {"+": "plus", "-": "minus", "*": "times", "/": "divided by"}
            text = f"What is {a} {op_words[op]} {b}"
        else:
            op_words = {"+": "အပေါင်း", "-": "အနုတ်", "*": "အမြှောက်", "/": "အစား"}
            text = f"{a} {op_words[op]} {b} ညီမျှခြင်း ဘယ်လောက်လဲ"
            
        self.voice.speak(text)

    def check_answer(self, choice_index):
        if self.state != "PLAYING": return
        q = self.questions[self.index]
        selected = q["options"][choice_index]
        answer = q["answer"]

        for btn in self.ans_buttons:
            btn.state = "disabled"

        self.msg_scale_timer = pygame.time.get_ticks()

        if selected == answer:
            self.score += 1
            self.combo += 1
            self.ans_buttons[choice_index].custom_color = self.GREEN
            
            if self.combo == 2:
                self.msg_text = "Double Correct! x2"
                self.msg_emoji = "🚀"
            elif self.combo == 3:
                self.msg_text = "Combo x3! Amazing!"
                self.msg_emoji = "🔥"
            elif self.combo > 3:
                self.msg_text = f"On Fire! x{self.combo}!"
                self.msg_emoji = "🎇"
            else:
                self.msg_text = "Awesome! Correct!"
                self.msg_emoji = "🌟"
                
            self.msg_color = self.SCORE_TEXT
            btn_center = self.ans_buttons[choice_index].rect.center
            
            confetti_amount = 40 + (self.combo * 15) 
            for _ in range(confetti_amount):
                self.confetti_particles.append(Confetti(btn_center[0], btn_center[1]))
            self.speak_dialogue("CORRECT")
        else:
            self.combo = 0
            self.ans_buttons[choice_index].custom_color = self.RED
            self.msg_text = "Oops! Try again."
            self.msg_emoji = "🤔"
            self.msg_color = (214, 40, 40)
            self.shake_amount = 15
            for i, val in enumerate(q["options"]):
                if val == answer:
                    self.ans_buttons[i].custom_color = self.GREEN
            self.speak_dialogue("WRONG")

        self.state = "WAITING"
        self.wait_timer = pygame.time.get_ticks()

    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            self.time_elapsed = current_time / 1000.0
            shake_x, shake_y = 0, 0
            if self.shake_amount > 0:
                shake_x = random.randint(-self.shake_amount, self.shake_amount)
                shake_y = random.randint(-self.shake_amount, self.shake_amount)
                self.shake_amount -= 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                self.music_slider.update(event)
                if self.btn_voice.is_clicked(event): self.toggle_voice()
                if self.btn_lang.is_clicked(event): self.toggle_lang()

                if self.state != "MENU":
                    if self.btn_home.is_clicked(event):
                        self.state = "MENU"
                        self.speak_dialogue("WELCOME")

                if self.state == "MENU":
                    if self.btn_menu_add.is_clicked(event): self.select_mode(["+"])
                    if self.btn_menu_sub.is_clicked(event): self.select_mode(["-"])
                    if self.btn_menu_mul.is_clicked(event): self.select_mode(["*"])
                    if self.btn_menu_div.is_clicked(event): self.select_mode(["/"])
                    if self.btn_menu_mix.is_clicked(event): self.select_mode(["+", "-", "*", "/"])
                    if self.btn_menu_shop.is_clicked(event): self.state = "SHOP"
                    
                elif self.state == "DIFFICULTY":
                    if self.btn_diff_easy.is_clicked(event): self.start_game("EASY")
                    if self.btn_diff_med.is_clicked(event): self.start_game("MEDIUM")
                    if self.btn_diff_hard.is_clicked(event): self.start_game("HARD")
                    if self.btn_diff_back.is_clicked(event):
                        self.state = "MENU"
                        self.speak_dialogue("WELCOME")

                elif self.state == "PLAYING":
                    if self.btn_read.is_clicked(event, shake_x, shake_y):
                        self.read_question()
                    for i, btn in enumerate(self.ans_buttons):
                        if btn.is_clicked(event, shake_x, shake_y):
                            self.check_answer(i)

                elif self.state == "RESULT":
                    if self.btn_restart.is_clicked(event):
                        self.start_game(self.difficulty)
                    if self.btn_back_menu.is_clicked(event):
                        self.state = "MENU"
                        self.speak_dialogue("WELCOME")

                elif self.state == "SHOP":
                    if self.btn_shop_back.is_clicked(event):
                        self.state = "MENU"
                    
                    for i, btn in enumerate(self.shop_buy_btns):
                        if btn.is_clicked(event):
                            item = self.shop_items[i]
                            if item["emoji"] in self.save_data["unlocked_avatars"]:
                                self.save_data["equipped_avatar"] = item["emoji"]
                                self.save_game_data()
                            else:
                                if self.save_data["coins"] >= item["price"]:
                                    self.save_data["coins"] -= item["price"]
                                    self.save_data["unlocked_avatars"].append(item["emoji"])
                                    self.save_data["equipped_avatar"] = item["emoji"]
                                    self.save_game_data()
                                    if self.voice_on: self.voice.speak("Item unlocked!")

            if self.state == "WAITING":
                if current_time - self.wait_timer > 1500:
                    self.index += 1
                    self.msg_text = ""
                    self.msg_emoji = ""
                    self.confetti_particles.clear()
                    if self.index >= len(self.questions):
                        self.state = "RESULT"
                        self.earned_coins = (self.score * 5) + (self.combo * 2)
                        self.save_data["coins"] += self.earned_coins
                        self.save_game_data()

                        if self.voice_on:
                            if self.voice.lang == "EN":
                                self.voice.speak(f"Game Finished! Your score is {self.score}")
                            else:
                                self.voice.speak(f"ဂိမ်းပြီးသွားပါပြီ။ သင့်ရမှတ်ကတော့ {self.score} မှတ်ပါ။")
                    else:
                        self.state = "PLAYING"
                        self.setup_answer_buttons()

            # Hover updates
            self.btn_voice.update()
            self.btn_lang.update()
            if self.state != "MENU":
                self.btn_home.update()
                
            if self.state == "MENU":
                self.btn_menu_add.update()
                self.btn_menu_sub.update()
                self.btn_menu_mul.update()
                self.btn_menu_div.update()
                self.btn_menu_mix.update()
                self.btn_menu_shop.update()
            elif self.state == "DIFFICULTY":
                self.btn_diff_easy.update()
                self.btn_diff_med.update()
                self.btn_diff_hard.update()
                self.btn_diff_back.update()
            elif self.state == "PLAYING":
                self.btn_read.update(shake_x, shake_y)
                for btn in self.ans_buttons: btn.update(shake_x, shake_y)
            elif self.state == "RESULT":
                self.btn_restart.update()
                self.btn_back_menu.update()
            elif self.state == "SHOP":
                self.btn_shop_back.update()

            # Drawing
            self.screen.blit(self.background, (0, 0))
            self.draw_header()

            if self.state == "MENU":
                self.draw_menu_screen()
            elif self.state == "SHOP":
                self.draw_shop_screen()
            elif self.state == "DIFFICULTY":
                self.draw_difficulty_screen()
            elif self.state == "RESULT":
                self.draw_result_screen()
            else:
                self.draw_game_screen(shake_x, shake_y)

            for particle in self.confetti_particles[:]:
                particle.update()
                particle.draw(self.screen)
                if particle.timer <= 0:
                    self.confetti_particles.remove(particle)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def draw_header(self):
        if self.state != "MENU":
            self.btn_home.draw(self.screen)
            
        music_icon = self.emoji_font.render("🎵", True, self.TEXT)
        self.screen.blit(music_icon, (90, 30))
        self.music_slider.draw(self.screen)
        self.btn_lang.draw(self.screen)
        self.btn_voice.draw(self.screen)

    def draw_menu_screen(self):
        bounce = math.sin(self.time_elapsed * 2) * 5
        title = self.math_font.render("Math Game", True, self.PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 130 + bounce)))
        
        subtitle = self.ui_font_large.render("Choose a Game Mode", True, self.TEXT)
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 200)))

        self.btn_menu_add.draw(self.screen)
        self.btn_menu_sub.draw(self.screen)
        self.btn_menu_mul.draw(self.screen)
        self.btn_menu_div.draw(self.screen)
        self.btn_menu_mix.draw(self.screen)
        
        self.btn_menu_shop.draw(self.screen)

        # Vector Surface Equipped Avatar & Coin
        eq_av = self.save_data.get('equipped_avatar', '😊')
        av_surf = get_avatar_surface(eq_av, 46)
        self.screen.blit(av_surf, (30, 85))

        coin_surf = get_coin_surface(32)
        self.screen.blit(coin_surf, (85, 92))

        coins_count = self.save_data.get('coins', 0)
        coin_txt = self.ui_font_large.render(f"{coins_count}", True, (255, 145, 0))
        self.screen.blit(coin_txt, (123, 92))

    def draw_difficulty_screen(self):
        bounce = math.sin(self.time_elapsed * 2) * 5
        title = self.math_font.render("Difficulty", True, self.PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 150 + bounce)))
        
        subtitle = self.ui_font_large.render("Select your level:", True, self.TEXT)
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 220)))
        
        self.btn_diff_easy.draw(self.screen)
        self.btn_diff_med.draw(self.screen)
        self.btn_diff_hard.draw(self.screen)
        self.btn_diff_back.draw(self.screen)

    def draw_game_screen(self, offset_x=0, offset_y=0):
        bounce = math.sin(self.time_elapsed * 2) * 4
        
        title_em = self.emoji_large.render("🧮", True, self.PRIMARY)
        title_txt = self.title_font.render(" Let's Play Math!", True, self.PRIMARY)
        self.screen.blit(title_em, (35, 75 + bounce))
        self.screen.blit(title_txt, (35 + title_em.get_width(), 80 + bounce))

        prog_text = self.ui_font.render(f"Question {self.index + 1}/{self.total_questions}", True, self.TEXT)
        self.screen.blit(prog_text, (40, 145))

        score_txt = self.ui_font.render(f" Score: {self.score}", True, self.SCORE_TEXT)
        score_em = self.emoji_font.render("⭐", True, self.SCORE_TEXT)
        total_w = score_em.get_width() + score_txt.get_width()
        start_x = self.width - 40 - total_w
        self.screen.blit(score_em, (start_x, 142))
        self.screen.blit(score_txt, (start_x + score_em.get_width(), 145))

        if hasattr(self, 'combo') and self.combo > 1:
            streak_bounce = math.sin(self.time_elapsed * 8) * 3
            combo_color = (255, 100, 50)
            combo_em = self.emoji_font.render("🔥", True, combo_color)
            combo_txt = self.ui_font.render(f"Streak x{self.combo}", True, combo_color)
            
            c_w = combo_em.get_width() + combo_txt.get_width()
            c_x = self.width // 2 - c_w // 2
            c_y = 142 + streak_bounce
            self.screen.blit(combo_em, (c_x, c_y))
            self.screen.blit(combo_txt, (c_x + combo_em.get_width(), c_y + 3))

        bar_x, bar_y, bar_w, bar_h = 40, 180, self.width - 80, 18
        pygame.draw.rect(self.screen, (255, 235, 210), (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        fill_w = int((self.index / self.total_questions) * bar_w)
        if fill_w > 0:
            fill_color = lerp_color(self.BUTTON_HOVER, self.SCORE_TEXT, self.index / self.total_questions)
            pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=9)

        card_rect = pygame.Rect((self.width - 480) // 2 + offset_x, 230 + offset_y, 480, 180)
        draw_soft_shadow(self.screen, card_rect, radius=24, offset=(0, 10), alpha=40)
        pygame.draw.rect(self.screen, self.CARD, card_rect, border_radius=24)
        pygame.draw.rect(self.screen, self.CARD_BORDER, card_rect, width=4, border_radius=24)

        q_str = self.questions[self.index]["q_str"] + " = ?"
        q_surf = self.math_font.render(q_str, True, self.TEXT)
        q_rect = q_surf.get_rect(center=card_rect.center)
        self.screen.blit(q_surf, q_rect)

        self.btn_read.draw(self.screen, offset_x, offset_y)
        for btn in self.ans_buttons:
            btn.draw(self.screen, offset_x, offset_y)

        if self.msg_text:
            age = pygame.time.get_ticks() - self.msg_scale_timer
            scale = min(1.0, age / 150) if age >= 0 else 1.0
            scale = 0.7 + 0.3 * scale
            
            em_surf = self.emoji_large.render(self.msg_emoji, True, self.msg_color)
            txt_surf = self.ui_font_large.render(self.msg_text, True, self.msg_color)
            
            w = em_surf.get_width() + 10 + txt_surf.get_width()
            h = max(em_surf.get_height(), txt_surf.get_height())
            
            msg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            msg_surf.blit(em_surf, (0, (h - em_surf.get_height())//2))
            msg_surf.blit(txt_surf, (em_surf.get_width() + 10, (h - txt_surf.get_height())//2))

            if scale != 1.0:
                msg_surf = pygame.transform.smoothscale(msg_surf, (max(1, int(w * scale)), max(1, int(h * scale))))
            msg_rect = msg_surf.get_rect(center=(self.width // 2, 520))
            self.screen.blit(msg_surf, msg_rect)

    def draw_result_screen(self):
        if self.score > 0 and random.random() < 0.2:
            self.confetti_particles.append(Confetti(random.randint(50, self.width - 50), -20))

        pct = self.score / self.total_questions
        if pct == 1:
            emoji, msg, star_count = "🏆", "Perfect! Amazing Job!", 3
        elif pct >= 0.7:
            emoji, msg, star_count = "🎉", "Great job!", 2
        elif pct >= 0.4:
            emoji, msg, star_count = "💪", "Good effort!", 1
        else:
            emoji, msg, star_count = "💪", "Keep practicing!", 0

        card_rect = pygame.Rect((self.width - 520) // 2, 140, 520, 520)
        draw_soft_shadow(self.screen, card_rect, radius=32, offset=(0, 12), alpha=45)
        pygame.draw.rect(self.screen, self.CARD, card_rect, border_radius=32)
        pygame.draw.rect(self.screen, self.CARD_BORDER, card_rect, width=4, border_radius=32)

        em1 = self.emoji_large.render(emoji, True, self.PRIMARY)
        em2 = self.emoji_large.render(emoji, True, self.PRIMARY)
        txt = self.title_font.render(" Game Finished ", True, self.PRIMARY)
        
        tot_w = em1.get_width() + txt.get_width() + em2.get_width()
        st_x = (self.width - tot_w) // 2
        
        self.screen.blit(em1, (st_x, 190))
        self.screen.blit(txt, (st_x + em1.get_width(), 195))
        self.screen.blit(em2, (st_x + em1.get_width() + txt.get_width(), 190))

        star_y = 300
        gap = 70
        start_x = self.width // 2 - gap
        for i in range(3):
            pop = max(0.0, min(1.0, (self.time_elapsed * 2 - i * 0.3)))
            size = 26 * (0.6 + 0.4 * pop)
            wobble = math.sin(self.time_elapsed * 3 + i) * 3 if i < star_count else 0
            color = (255, 196, 61) if i < star_count else (225, 220, 210)
            draw_star(self.screen, (start_x + i * gap, star_y + wobble), size, color)

        score_disp = self.math_font.render(f"{self.score} / {self.total_questions}", True, self.SCORE_TEXT)
        self.screen.blit(score_disp, score_disp.get_rect(center=(self.width // 2, 400)))

        msg_disp = self.ui_font_large.render(msg, True, self.TEXT)
        self.screen.blit(msg_disp, msg_disp.get_rect(center=(self.width // 2, 470)))
        
        if self.earned_coins > 0:
            coin_surf = get_coin_surface(30)
            coin_disp = self.ui_font_large.render(f"+ {self.earned_coins} Earned!", True, (255, 165, 0))
            tot_w = coin_disp.get_width() + 8 + coin_surf.get_width()
            st_x = self.width // 2 - tot_w // 2
            self.screen.blit(coin_disp, (st_x, 510))
            self.screen.blit(coin_surf, (st_x + coin_disp.get_width() + 8, 508))

        self.btn_restart.draw(self.screen)
        self.btn_back_menu.draw(self.screen)

    def draw_shop_screen(self):
        title = self.math_font.render("Avatar Shop", True, self.PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 100)))
        
        coin_surf = get_coin_surface(36)
        coin_txt = self.ui_font_large.render(f"Your Coins: {self.save_data.get('coins', 0)}", True, (255, 145, 0))
        tot_w = coin_txt.get_width() + 10 + coin_surf.get_width()
        st_x = self.width // 2 - tot_w // 2
        self.screen.blit(coin_txt, (st_x, 160))
        self.screen.blit(coin_surf, (st_x + coin_txt.get_width() + 10, 157))
        
        for i, item in enumerate(self.shop_items):
            y_pos = 230 + (i * 120)
            
            box_rect = pygame.Rect(40, y_pos - 15, self.width - 80, 90)
            pygame.draw.rect(self.screen, (255, 255, 255), box_rect, border_radius=15)
            pygame.draw.rect(self.screen, (220, 220, 220), box_rect, width=2, border_radius=15)
            
            av_surf = get_avatar_surface(item["emoji"], 65)
            self.screen.blit(av_surf, (55, y_pos - 3))
            
            name = self.ui_font_large.render(item["name"], True, self.TEXT)
            self.screen.blit(name, (135, y_pos - 5))
            
            p_coin = get_coin_surface(24)
            price_txt = self.ui_font.render(f"{item['price']}", True, (255, 145, 0))
            self.screen.blit(price_txt, (135, y_pos + 32))
            self.screen.blit(p_coin, (135 + price_txt.get_width() + 6, y_pos + 30))
            
            btn = self.shop_buy_btns[i]
            equipped = self.save_data.get("equipped_avatar", "😊")
            unlocked = self.save_data.get("unlocked_avatars", ["😊"])
            
            if item["emoji"] == equipped or AVATAR_MAP.get(item["emoji"]) == AVATAR_MAP.get(equipped):
                btn.text = "Equipped"
                btn.base_color = self.GREEN
            elif item["emoji"] in unlocked or AVATAR_MAP.get(item["emoji"]) in unlocked:
                btn.text = "Equip"
                btn.base_color = self.BUTTON_BG
            else:
                btn.text = "Buy"
                btn.base_color = self.BTN_BLUE
                
            btn.update()
            btn.draw(self.screen)
            
        self.btn_shop_back.update()
        self.btn_shop_back.draw(self.screen)


if __name__ == "__main__":
    game = MathGamePygame()
    game.run()

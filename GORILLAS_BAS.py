# This is a Pygame port of the classic QBasic Gorillas.bas game.
# This is relatively close to the original using the EGA part.

import pygame
import math
import random
import sys
import struct
import numpy as np
import time
import threading

# Set up for sounds
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
NOTE_TABLE = [
    0,   # N0 = rest
    65.41, 69.30, 73.42, 77.78, 82.41, 87.31,
    92.50, 98.00, 103.83, 110.00, 116.54, 123.47,
    130.81, 138.59, 146.83, 155.56, 164.81, 174.61,
    185.00, 196.00, 207.65, 220.00, 233.08, 246.94,
    261.63, 277.18, 293.66, 311.13, 329.63, 349.23,
    369.99, 392.00, 415.30, 440.00, 466.16, 493.88,
    523.25, 554.37, 587.33, 622.25, 659.25, 698.46,
    739.99, 783.99, 830.61, 880.00, 932.33, 987.77
]

NOTE_OFFSET = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

def _read_number(s, i):
    n = ""
    while i < len(s) and s[i].isdigit():
        n += s[i]
        i += 1
    return (int(n) if n else 0), i

def _play_square(freq, duration, volume):
    if freq <= 0:
        time.sleep(duration)
        return

    sample_rate = 44100
    n = max(1, int(sample_rate * duration))
    t = np.linspace(0, duration, n, False)
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    audio = (wave * 32767).astype(np.int16)

    # Match mixer channels
    channels = pygame.mixer.get_init()[2]
    if channels == 2:
        audio = np.column_stack((audio, audio))

    snd = pygame.sndarray.make_sound(audio)
    snd.set_volume(volume)
    snd.play()
    time.sleep(duration)
    snd.stop()

def PLAY(play_string, volume=0.4):
    s = play_string.upper()
    background = s.startswith("MB")

    def player():
        octave = 4
        length = 4
        tempo = 120
        staccato = False
        i = 0
        while i < len(s):
            ch = s[i]
            # MODE
            if ch == 'M' and i + 1 < len(s):
                i += 2
                continue
            # TEMPO
            if ch == 'T':
                tempo, i = _read_number(s, i + 1)
                continue
            # OCTAVE
            if ch == 'O':
                octave, i = _read_number(s, i + 1)
                continue
            if ch == '>':
                octave += 1
                i += 1
                continue
            if ch == '<':
                octave -= 1
                i += 1
                continue
            # LENGTH
            if ch == 'L':
                length, i = _read_number(s, i + 1)
                length = max(1, length)
                continue
            # PAUSE
            if ch == 'P':
                dur = 60 / tempo * (4 / length)
                time.sleep(dur)
                i += 1
                continue
            # NOTE NUMBER (N)
            if ch == 'N':
                note, i = _read_number(s, i + 1)
                freq = NOTE_TABLE[note] if note < len(NOTE_TABLE) else 0
                dur = 60 / tempo * (4 / length)
                _play_square(freq, dur, volume)
                continue
            # LETTER NOTE
            if ch in NOTE_OFFSET:
                semi = NOTE_OFFSET[ch]
                i += 1
                if i < len(s) and s[i] in '+#':
                    semi += 1
                    i += 1
                elif i < len(s) and s[i] == '-':
                    semi -= 1
                    i += 1
                note_num = octave * 12 + semi + 1
                freq = NOTE_TABLE[note_num] if note_num < len(NOTE_TABLE) else 0
                dur = 60 / tempo * (4 / length)
                if i < len(s) and s[i] == '.':
                    dur *= 1.5
                    i += 1
                _play_square(freq, dur, volume)
                continue

            i += 1

    if background:
        threading.Thread(target=player, daemon=True).start()
    else:
        player()

# Constants from GORILLAS.BAS
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 350
SCALE = 2  # Window scaling for modern displays
FPS = 60

# EGA 16-color palette
EGA_PALETTE = [
    (0, 0, 0),         # 0 - Black
    (0, 0, 170),       # 1 - Blue
    (0, 170, 0),       # 2 - Green
    (0, 170, 170),     # 3 - Cyan
    (170, 0, 0),       # 4 - Red
    (170, 0, 170),     # 5 - Magenta
    (170, 85, 0),      # 6 - Brown
    (170, 170, 170),   # 7 - Light Gray
    (85, 85, 85),      # 8 - Dark Gray
    (85, 85, 255),     # 9 - Light Blue
    (85, 255, 85),     # 10 - Light Green
    (85, 255, 255),    # 11 - Light Cyan
    (255, 85, 85),     # 12 - Light Red
    (255, 85, 255),    # 13 - Light Magenta
    (255, 255, 85),    # 14 - Yellow
    (255, 255, 255),   # 15 - White
]

# Color constants
BACKATTR = 1  # Blue background
OBJECTCOLOR = 6  # Brown for gorillas
WINDOWCOLOR = 14  # Yellow windows
SUNATTR = 14  # Yellow
EXPLOSION_COLOR = 4  # Red explosion

# Banana DATA from EGABanana section
BANANA_LEFT = [458758, 202116096, 471604224, 943208448, 943208448, 943208448, 471604224, 202116096, 0]
BANANA_DOWN = [262153, -2134835200, -2134802239, -2130771968, -2130738945, 8323072, 8323199, 4063232, 4063294]
BANANA_UP = [262153, 4063232, 4063294, 8323072, 8323199, -2130771968, -2130738945, -2134835200, -2134802239]
BANANA_RIGHT = [458758, -1061109760, -522133504, 1886416896, 1886416896, 1886416896, -522133504, -1061109760, 0]

class QBasicGorillas:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((SCREEN_WIDTH * SCALE, SCREEN_HEIGHT * SCALE))
        pygame.display.set_caption("QBasic Gorillas")
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("couriernew", 14, bold=True)
        self.player_font = pygame.font.SysFont("couriernew", 18, bold=True)
        self.small_font = pygame.font.SysFont("couriernew", 16, bold=True)
        
        # Game state
        self.player1_name = ""
        self.player2_name = ""
        self.num_games = 3
        self.gravity = 9.8
        self.buildings = []
        self.city_surf = None  # damageable city bitmap
        self.gorilla_x = [0, 0]
        self.gorilla_y = [0, 0]
        self.wind = 0
        self.scores = [0, 0]
        self.sun_hit = False
        self.gorilla_alive = [True, True]
        
        # Load banana sprites
        self.banana_sprites = self.load_banana_sprites()
        
        # Gorilla sprite storage
        self.gorilla_images = self.create_gorilla_images()
    
    def decode_put_array(self, data):
        # Decode QBasic SCREEN 9 PUT array format
        # Convert signed 32-bit integers to unsigned bytes
        byte_list = []
        for x in data:
            # Handle negative numbers by converting to unsigned 32-bit
            if x < 0:
                x = x & 0xFFFFFFFF
            # Pack as 4 bytes little-endian
            byte_list.extend([
                x & 0xFF,
                (x >> 8) & 0xFF,
                (x >> 16) & 0xFF,
                (x >> 24) & 0xFF
            ])
        byte_data = bytes(byte_list)
        
        # First 2 words are dimensions
        width = struct.unpack_from('<H', byte_data, 0)[0] + 1
        height = struct.unpack_from('<H', byte_data, 2)[0] + 1
        
        # Rest is pixel data in 4 bitplanes
        pixel_data = byte_data[4:]
        
        # Create image array
        image = [[0 for _ in range(width)] for _ in range(height)]
        
        bytes_per_line = (width + 7) // 8
        
        for y in range(height):
            for plane in range(4):
                offset = y * bytes_per_line * 4 + plane * bytes_per_line
                for x in range(width):
                    byte_idx = x // 8
                    bit_idx = 7 - (x % 8)
                    if offset + byte_idx < len(pixel_data):
                        byte_val = pixel_data[offset + byte_idx]
                        if byte_val & (1 << bit_idx):
                            image[y][x] |= (1 << plane)
        
        return image
    
    def create_surface_from_array(self, array):
        # Convert pixel array to pygame surface
        height = len(array)
        width = len(array[0]) if height > 0 else 0
        surface = pygame.Surface((width, height))
        surface.set_colorkey((0, 0, 0))
        
        for y in range(height):
            for x in range(width):
                color_idx = array[y][x]
                if color_idx != 0:
                    surface.set_at((x, y), EGA_PALETTE[color_idx])    
        return surface
    
    def load_banana_sprites(self):
        # Load all banana rotation sprites
        left_array = self.decode_put_array(BANANA_LEFT)
        down_array = self.decode_put_array(BANANA_DOWN)
        up_array = self.decode_put_array(BANANA_UP)
        right_array = self.decode_put_array(BANANA_RIGHT)
        
        return {
            0: self.create_surface_from_array(left_array),
            1: self.create_surface_from_array(up_array),
            2: self.create_surface_from_array(down_array),
            3: self.create_surface_from_array(right_array)
        }
    
    def draw_gorilla(self, x, y, arms_up=0):
        # Draw a gorilla (arms: 0=down, 1=right up, 2=left up)
        surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        color = EGA_PALETTE[OBJECTCOLOR]
        
        # Head (slightly smaller)
        pygame.draw.rect(surface, color, (10, 1, 11, 7))
        pygame.draw.rect(surface, color, (9, 3, 13, 3))

        # Brow
        pygame.draw.line(surface, EGA_PALETTE[0], (11, 2), (19, 2), 1)

        # Eyes
        surface.set_at((12, 4), EGA_PALETTE[0])
        surface.set_at((13, 4), EGA_PALETTE[0])
        surface.set_at((16, 4), EGA_PALETTE[0])
        surface.set_at((17, 4), EGA_PALETTE[0])

        # Neck
        pygame.draw.line(surface, color, (9, 8), (21, 8), 1)
        
        # Body
        pygame.draw.rect(surface, color, (6, 9, 19, 8))
        pygame.draw.rect(surface, color, (8, 17, 14, 6))
        
        # Legs
        for i in range(5):
            pygame.draw.arc(surface, color, (7 + i, 18, 20, 20), 
                          3 * math.pi / 4, 9 * math.pi / 8, 1)
            pygame.draw.arc(surface, color, (i, 18, 20, 20),
                          15 * math.pi / 8, math.pi / 4, 1)
        
        # Chest circles
        pygame.draw.arc(surface, (0, 0, 0), (5, 7, 10, 10),
                       3 * math.pi / 2, 2 * math.pi, 1)
        pygame.draw.arc(surface, (0, 0, 0), (15, 7, 10, 10),
                       math.pi, 3 * math.pi / 2, 1)
        
        # Arms
        for i in range(5):
            if arms_up == 1:  # Right arm up
                pygame.draw.arc(surface, color, (2 + i, 6, 18, 18),
                              3 * math.pi / 4, 5 * math.pi / 4, 1)
                pygame.draw.arc(surface, color, (7 + i, -1, 18, 18),
                              7 * math.pi / 4, math.pi / 4, 1)
            elif arms_up == 2:  # Left arm up
                pygame.draw.arc(surface, color, (2 + i, -1, 18, 18),
                              3 * math.pi / 4, 5 * math.pi / 4, 1)
                pygame.draw.arc(surface, color, (7 + i, 6, 18, 18),
                              7 * math.pi / 4, math.pi / 4, 1)
            else:  # Both arms down
                pygame.draw.arc(surface, color, (2 + i, 6, 18, 18),
                              3 * math.pi / 4, 5 * math.pi / 4, 1)
                pygame.draw.arc(surface, color, (7 + i, 6, 18, 18),
                              7 * math.pi / 4, math.pi / 4, 1)
     
        return surface
    
    def create_gorilla_images(self):
        # Pre-render gorilla images
        return {
            'down': self.draw_gorilla(0, 0, 0),
            'left': self.draw_gorilla(0, 0, 2),
            'right': self.draw_gorilla(0, 0, 1)
        }
    
    def center_text(self, text, y, color=7):
        # Center text on screen
        surf = self.font.render(text, True, EGA_PALETTE[color])
        x = (SCREEN_WIDTH - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))
    
    
    def draw_input_history(self):
        # Draw previously-entered setup lines (prompt + value) so they persist on later screens.
        if not hasattr(self, "input_lines"):
            return
        for prompt, value, y_pos in self.input_lines:
            line = f"{prompt} {value}"
            self.center_text(line, y_pos, 7)

    def draw_sparkle_border(self, frame):
        # Draw animated star border like original
        star_pattern = "*    *    *    *    *    *    *    *    *    *    *    *    *    *    *    "
        offset = frame % 5
        
        # Top and bottom borders
        for i, x in enumerate(range(0, SCREEN_WIDTH, 8)):
            if (i + offset) % 5 == 0:
                surf = self.small_font.render("*", True, EGA_PALETTE[4])
                self.screen.blit(surf, (x, 5))
                self.screen.blit(surf, (x, SCREEN_HEIGHT - 20))
        
        # Side borders
        for i, y in enumerate(range(20, SCREEN_HEIGHT - 20, 8)):
            if (i + offset) % 5 == 0:
                surf = self.small_font.render("*", True, EGA_PALETTE[4])
                self.screen.blit(surf, (5, y))
                self.screen.blit(surf, (SCREEN_WIDTH - 15, y))
    
    def intro_screen(self):
        # Display intro screen
        frame = 0
        waiting = True
        PLAY("MBT160O1L8CDEDCDL4ECC")
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    waiting = False
            
            self.screen.fill(EGA_PALETTE[0])
            self.draw_sparkle_border(frame)
            
            self.center_text("'Q B a s i c'   G O R I L L A S", 60, 15)
            self.center_text("Copyright (C) Microsoft Corporation 1990", 90, 7)
            
            y = 120
            lines = [
                "Your mission is to hit your opponent with the exploding",
                "banana by varying the angle and power of your throw, taking",
                "into account wind speed, gravity, and the city skyline.",
                "The wind speed is shown by a directional arrow at the bottom",
                "of the playing field, its length relative to its strength."
            ]
            
            for line in lines:
                self.center_text(line, y, 7)
                y += 20
            
            self.center_text("Press any key to continue", SCREEN_HEIGHT - 40, 7)
            
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            self.clock.tick(15)
            frame += 1
        
        return True
    
    def get_input(self, prompt, default, y_pos, numeric=False):
        # Get user input (QBasic-style): keep previous lines on screen.
        # - No default shown while typing (blank input line)
        # - ENTER with empty input uses default
        # - Cursor blink does not shift text horizontally
        text = ""
        cursor_visible = True
        cursor_timer = 0

        if not hasattr(self, "input_lines"):
            self.input_lines = []  # list of (prompt, value, y_pos)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return text if text else default
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    else:
                        char = event.unicode
                        if numeric:
                            if char in "0123456789.":
                                text += char
                        else:
                            if char.isprintable() and len(text) < 20:
                                text += char

            # Redraw full screen each frame, but include previous completed lines
            self.screen.fill(EGA_PALETTE[0])
            self.draw_input_history()

            # Render the current prompt + current typed text as one centered line
            live = text  # do NOT show defaults while typing
            line = f"{prompt} {live}".rstrip()

            line_surf = self.font.render(line, True, EGA_PALETTE[7])
            x = (SCREEN_WIDTH - line_surf.get_width()) // 2
            self.screen.blit(line_surf, (x, y_pos))

            # Draw blinking cursor separately so centering never changes
            if cursor_visible:
                cursor_surf = self.font.render("_", True, EGA_PALETTE[15])
                self.screen.blit(cursor_surf, (x + line_surf.get_width(), y_pos))

            cursor_timer += 1
            if cursor_timer > 20:
                cursor_visible = not cursor_visible
                cursor_timer = 0

            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            self.clock.tick(30)

    def get_inputs(self):
        # Get all game inputs
        self.screen.fill(EGA_PALETTE[0])
        self.input_lines = []
        
        result = self.get_input("Name of Player 1 (Default = 'Player 1'):", "Player 1", 80)
        if result is None:
            return False
        self.player1_name = result[:10]
        self.input_lines.append(("Name of Player 1 (Default = 'Player 1'):", self.player1_name, 80))
        
        result = self.get_input("Name of Player 2 (Default = 'Player 2'):", "Player 2", 110)
        if result is None:
            return False
        self.player2_name = result[:10]
        self.input_lines.append(("Name of Player 2 (Default = 'Player 2'):", self.player2_name, 110))
        
        result = self.get_input("Play to how many total points (Default = 3)?", "3", 140, True)
        if result is None:
            return False
        try:
            self.num_games = max(1, int(result))
        except:
            self.num_games = 3
        self.input_lines.append(("Play to how many total points (Default = 3)?", str(self.num_games), 140))
        
        result = self.get_input("Gravity in Meters/Sec (Earth = 9.8)?", "9.8", 170, True)
        if result is None:
            return False
        try:
            self.gravity = float(result) if result else 9.8
        except:
            self.gravity = 9.8
        self.input_lines.append(("Gravity in Meters/Sec (Earth = 9.8)", str(self.gravity), 170))
        
        return True
    
    def gorilla_intro(self):
        # Display gorilla intro with V/P choice
        waiting = True

        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False, False
                if event.type == pygame.KEYDOWN:
                    if event.unicode.upper() == 'V':
                        return True, True
                    elif event.unicode.upper() == 'P':
                        return True, False
                    elif event.key == pygame.K_ESCAPE:
                        return False, False
            
            self.screen.fill(EGA_PALETTE[0])
            self.draw_input_history()
            self.center_text("--------------", 190, 7)
            self.center_text("V = View Intro", 220, 7)
            self.center_text("P = Play Game", 240, 7)
            self.center_text("Your Choice?", 270, 15)
            
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            self.clock.tick(30)
    
    def view_intro(self):
            # View animated gorilla intro - matches QBasic original
            self.screen.fill(EGA_PALETTE[BACKATTR])
            
            # Title and starring text
            self.center_text("Q B A S I C   G O R I L L A S", 30, 15)
            self.center_text("STARRING:", 80, 7)
            player_text = f"{self.player1_name} AND {self.player2_name}"
            self.center_text(player_text, 110, 7)
            
            # Draw gorillas side by side in center
            x = SCREEN_WIDTH // 2 - 50
            y = 160
            
            # Initial draw - both arms down
            self.screen.blit(self.gorilla_images['down'], (x, y))
            self.screen.blit(self.gorilla_images['down'], (x + 70, y))
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(1000)
            
            # Animated sequence - 4 times
            for i in range(4):
                # Left arm up, right arm up
                self.screen.fill(EGA_PALETTE[BACKATTR])
                self.center_text("Q B A S I C   G O R I L L A S", 30, 15)
                self.center_text("STARRING:", 80, 7)
                self.center_text(player_text, 110, 7)
                
                self.screen.blit(self.gorilla_images['left'], (x, y))
                self.screen.blit(self.gorilla_images['right'], (x + 70, y))
                self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
                pygame.display.flip()
                
                PLAY("t120o1l16b9n0baan0bn0bn0baaan0b9n0baan0b")
                pygame.time.wait(300)
                
                # Right arm up, left arm up
                self.screen.fill(EGA_PALETTE[BACKATTR])
                self.center_text("Q B A S I C   G O R I L L A S", 30, 15)
                self.center_text("STARRING:", 80, 7)
                self.center_text(player_text, 110, 7)
                
                self.screen.blit(self.gorilla_images['right'], (x, y))
                self.screen.blit(self.gorilla_images['left'], (x + 70, y))
                self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
                pygame.display.flip()
                
                PLAY("o2l16e-9n0e-d-d-n0e-n0e-n0e-d-d-d-n0e-9n0e-d-d-n0e-")
                pygame.time.wait(300)
            
            # Final flourish - rapid alternation
            for i in range(8):
                self.screen.fill(EGA_PALETTE[BACKATTR])
                self.center_text("Q B A S I C   G O R I L L A S", 30, 15)
                self.center_text("STARRING:", 80, 7)
                self.center_text(player_text, 110, 7)
                
                if i % 2 == 0:
                    self.screen.blit(self.gorilla_images['left'], (x, y))
                    self.screen.blit(self.gorilla_images['right'], (x + 70, y))
                else:
                    self.screen.blit(self.gorilla_images['right'], (x, y))
                    self.screen.blit(self.gorilla_images['left'], (x + 70, y))
                
                self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
                pygame.display.flip()
                PLAY("T160O0L32EFGEFDC")
                pygame.time.wait(100)
            
            pygame.time.wait(1000)
    
    def make_cityscape(self):
        # Generate random cityscape
        self.buildings = []
        x = 2
        slope = random.randint(1, 6)
        
        if slope == 1:
            new_ht = 15
        elif slope == 2:
            new_ht = 130
        elif slope <= 5:
            new_ht = 15
        else:
            new_ht = 130
        
        while x < SCREEN_WIDTH - 10:
            # Update height based on slope
            if slope == 1:
                new_ht += 10
            elif slope == 2:
                new_ht -= 10
            elif slope <= 5:
                if x > SCREEN_WIDTH // 2:
                    new_ht -= 20
                else:
                    new_ht += 20
            else:
                if x > SCREEN_WIDTH // 2:
                    new_ht += 20
                else:
                    new_ht -= 20
            
            width = random.randint(37, 74)
            if x + width > SCREEN_WIDTH:
                width = SCREEN_WIDTH - x - 2
            
            height = random.randint(0, 120) + new_ht
            height = max(10, min(height, 200))
            
            color = random.choice([4, 5, 6, 7])
            
            bottom = SCREEN_HEIGHT - 5
            top = bottom - height
            windows = []
            wx = x + 3
            while wx < x + width - 3:
                wy = top + 3
                while wy < bottom - 3:
                    win_color = WINDOWCOLOR if random.randint(1, 4) > 1 else 8
                    windows.append((wx, wy, win_color))
                    wy += 15
                wx += 10

            self.buildings.append({
                'x': x,
                'width': width,
                'height': height,
                'color': color,
                'windows': windows
            })
            
            x += width + 2
        
        # Set wind
        self.wind = random.randint(-10, 10)
        if random.randint(1, 3) == 1:
            if self.wind > 0:
                self.wind += random.randint(1, 10)
            else:
                self.wind -= random.randint(1, 10)
        # Build damageable city bitmap for persistent building damage
        self.rebuild_city_surface()

    
    def draw_buildings(self):
        #Draw all buildings with windows
        for bldg in self.buildings:
            bottom = SCREEN_HEIGHT - 5
            top = bottom - bldg['height']
            
            # Draw building
            pygame.draw.rect(self.screen, EGA_PALETTE[bldg['color']],
                           (bldg['x'], top, bldg['width'], bldg['height']))
            
            # Draw windows
            for (wx, wy, win_color) in bldg.get('windows', []):
                pygame.draw.rect(self.screen, EGA_PALETTE[win_color], (wx, wy, 3, 6))


    def rebuild_city_surface(self):
        # Render buildings onto a damageable transparent surface.
        #
        # This surface is blitted each frame instead of redrawing pristine building rectangles,
        # so explosion holes remain visible and affect collision checks.
        
        self.city_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for bldg in self.buildings:
            bottom = SCREEN_HEIGHT - 5
            top = bottom - bldg['height']

            # Building body (opaque)
            col = EGA_PALETTE[bldg['color']]
            pygame.draw.rect(
                self.city_surf,
                (col[0], col[1], col[2], 255),
                (bldg['x'], top, bldg['width'], bldg['height'])
            )

            # Windows (opaque) – skip bottom row
            windows = bldg.get('windows', [])
            if windows:
                # Find the lowest row (largest y value)
                max_wy = max(wy for (_, wy, _) in windows)

                for (wx, wy, win_color) in windows:
                    # Skip the bottom-most row
                    if wy == max_wy:
                        continue

                    wcol = EGA_PALETTE[win_color]
                    pygame.draw.rect(
                        self.city_surf,
                        (wcol[0], wcol[1], wcol[2], 255),
                        (wx, wy, 3, 6)
                    )
 
    def draw_sun(self, shocked=False):
        # Draw the sun
        cx = SCREEN_WIDTH // 2
        cy = 40
        
        # Body
        pygame.draw.circle(self.screen, EGA_PALETTE[SUNATTR], (cx, cy), 12)
        
        # Rays
        for angle in range(0, 360, 18):
            rad = math.radians(angle)
            x1 = cx + int(math.cos(rad) * 15)
            y1 = cy + int(math.sin(rad) * 15)
            x2 = cx + int(math.cos(rad) * 20)
            y2 = cy + int(math.sin(rad) * 20)
            pygame.draw.line(self.screen, EGA_PALETTE[SUNATTR], (x1, y1), (x2, y2), 1)
        
        # Face
        pygame.draw.circle(self.screen, EGA_PALETTE[0], (cx - 3, cy - 2), 1)
        pygame.draw.circle(self.screen, EGA_PALETTE[0], (cx + 3, cy - 2), 1)
        
        if shocked:
            # O mouth
            pygame.draw.circle(self.screen, EGA_PALETTE[0], (cx, cy + 5), 3, 2)
        else:
            # Smile
            pygame.draw.circle(self.screen, EGA_PALETTE[0], (cx, cy + 5), 6, 2)
            pygame.draw.rect(self.screen, EGA_PALETTE[SUNATTR], (cx - 6, cy - 1, 12, 7))
                               
    def draw_wind_arrow(self):
        # Draw wind indicator arrow
        cy = SCREEN_HEIGHT - 10
        cx = SCREEN_WIDTH // 2
        wind_line = self.wind * 3
        pygame.draw.rect(self.screen, EGA_PALETTE[1], (cx-60, cy-20, 125, 30))
        if wind_line != 0:
            pygame.draw.line(self.screen, EGA_PALETTE[4],
                           (cx, cy), (cx + wind_line, cy), 2)
            
            arrow_dir = -2 if wind_line > 0 else 2
            end_x = cx + wind_line
            pygame.draw.line(self.screen, EGA_PALETTE[4],
                           (end_x, cy), (end_x + arrow_dir, cy - 2), 2)
            pygame.draw.line(self.screen, EGA_PALETTE[4],
                           (end_x, cy), (end_x + arrow_dir, cy + 2), 2)
    
    def place_gorillas(self):
        # Place gorillas on buildings
        # Left gorilla on 2nd or 3rd building
        left_idx = random.randint(1, 2)
        left_bldg = self.buildings[left_idx]
        self.gorilla_x[0] = left_bldg['x'] + left_bldg['width'] // 2 - 15
        self.gorilla_y[0] = SCREEN_HEIGHT - 5 - left_bldg['height'] - 30
        
        # Right gorilla on 2nd or 3rd from end
        right_idx = len(self.buildings) - random.randint(2, 3)
        right_bldg = self.buildings[right_idx]
        self.gorilla_x[1] = right_bldg['x'] + right_bldg['width'] // 2 - 15
        self.gorilla_y[1] = SCREEN_HEIGHT - 5 - right_bldg['height'] - 30
    
    def draw_scene(self):
        #Draw complete game scene
        self.screen.fill(EGA_PALETTE[BACKATTR])
        if self.city_surf is not None:
            self.screen.blit(self.city_surf, (0, 0))
        else:
            self.draw_buildings()
        self.draw_sun(self.sun_hit)
        self.draw_wind_arrow()
        
        # Draw gorillas (skip ones that have been hit)
        if self.gorilla_alive[0]:
            self.screen.blit(self.gorilla_images['down'], (self.gorilla_x[0], self.gorilla_y[0]))
        if self.gorilla_alive[1]:
            self.screen.blit(self.gorilla_images['down'], (self.gorilla_x[1], self.gorilla_y[1]))

        # Draw scores
        score_text = f"{self.scores[0]} > Score < {self.scores[1]}"
        self.center_text(score_text, SCREEN_HEIGHT - 30, 15)
    
    def get_shot_input(self, player_num):
        #Get angle and velocity from player
        # Get angle
        angle = self.get_number_input("Angle:", player_num, 0, True)
        if angle is None:
            return None, None
        
        # Get velocity
        velocity = self.get_number_input("Velocity:", player_num, 1, True)
        if velocity is None:
            return None, None
        
        return angle, velocity
    
    def get_number_input(self, prompt, player_num, input_num, redraw):
        #Get numeric input during gameplay
        text = ""
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        try:
                            val = float(text) if text else 45
                            return min(val, 360) if input_num == 0 else val
                        except:
                            return 45 if input_num == 0 else 50
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.unicode in '0123456789.':
                        text += event.unicode
            if redraw:
                self.draw_scene()
            
            # Draw player names
            name_surf = self.player_font.render(self.player1_name, True, EGA_PALETTE[15])
            self.screen.blit(name_surf, (5, 5))
            name_surf = self.player_font.render(self.player2_name, True, EGA_PALETTE[15])
            self.screen.blit(name_surf, (SCREEN_WIDTH - name_surf.get_width() - 5, 5))
            
            # Draw prompt
            x_pos = 5 if player_num == 0 else SCREEN_WIDTH - 150
            y_pos = 30 + input_num * 20
            prompt_surf = self.small_font.render(f"{prompt} {text}_", True, EGA_PALETTE[15])
            self.screen.blit(prompt_surf, (x_pos, y_pos))
            
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            self.clock.tick(30)
    
    def do_explosion(self, x, y):
        # Create explosion animation.
        # The city skyline is drawn from a damageable bitmap, so any holes punched into
        # self.city_surf remain after the animation.

        PLAY("MBO0L32EFGEFDC")
        x_i, y_i = int(x), int(y)

        # Expanding ring
        for radius in range(2, 20, 2):
            self.draw_scene()
            pygame.draw.circle(self.screen, EGA_PALETTE[EXPLOSION_COLOR], (x_i, y_i), radius, 2)
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(20)

        # Contracting ring
        for radius in range(20, 0, -2):
            self.draw_scene()
            pygame.draw.circle(self.screen, EGA_PALETTE[EXPLOSION_COLOR], (x_i, y_i), radius, 2)
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(20)
    
    def check_collision(self, x, y, shooter=None):
        # Check if shot hits building or gorilla
        # Check gorillas
        for i in range(2):
            # Ignore collision with the gorilla who just threw the banana
            if shooter is not None and i == shooter:
                continue
            if (self.gorilla_x[i] <= x <= self.gorilla_x[i] + 30 and
                self.gorilla_y[i] <= y <= self.gorilla_y[i] + 30):
                return 'gorilla', i
        # Check buildings (pixel-accurate against the damageable city surface)
        ix, iy = int(x), int(y)
        if self.city_surf is not None and 0 <= ix < SCREEN_WIDTH and 0 <= iy < SCREEN_HEIGHT:
            if self.city_surf.get_at((ix, iy)).a > 0:
                return 'building', None
        elif self.city_surf is None:
            # Fallback: rectangle tests
            for bldg in self.buildings:
                bottom = SCREEN_HEIGHT - 5
                top = bottom - bldg['height']
                if (bldg['x'] <= x <= bldg['x'] + bldg['width'] and
                    top <= y <= bottom):
                    return 'building', None
        
        # Check sun
        cx = SCREEN_WIDTH // 2
        cy = 40
        if math.sqrt((x - cx)**2 + (y - cy)**2) < 12:
            return 'sun', None
        
        return None, None
    
    def plot_shot(self, player_num, angle, velocity):
        # Animate banana shot
        # Adjust angle for player 2
        if player_num == 1:
            angle = 180 - angle
        
        angle_rad = math.radians(angle)
        
        # Starting position
        start_x = self.gorilla_x[player_num] + (25 if player_num == 0 else 5)
        start_y = self.gorilla_y[player_num] + 8
        
        # Show throwing animation
        throw_img = self.gorilla_images['left' if player_num == 0 else 'right']
        
        # Initial velocity components
        init_xvel = math.cos(angle_rad) * velocity
        init_yvel = math.sin(angle_rad) * velocity
        
        t = 0
        x, y = start_x, start_y
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
            
            # Physics calculation
            x = start_x + (init_xvel * t) + (0.5 * (self.wind / 5) * t * t)
            y = start_y + ((-1 * init_yvel * t) + (0.5 * self.gravity * t * t)) * (SCREEN_HEIGHT / 350)
            
            # Check bounds
            if x < -50 or x > SCREEN_WIDTH + 50 or y > SCREEN_HEIGHT + 50:
                return None
            
            if y > 0:
                # Check collision
                coll_type, coll_data = self.check_collision(int(x), int(y), shooter=player_num)
                
                if coll_type == 'sun':
                    self.sun_hit = True
                elif coll_type == 'building':
                    # Punch a transparent hole in the city bitmap so damage persists
                    if self.city_surf is not None:
                        pygame.draw.circle(self.city_surf, (0, 0, 0, 0), (int(x), int(y)), 14)
                    self.do_explosion(x, y)
                    return None
                elif coll_type == 'gorilla':
                    # Hide the gorilla so it doesn't get redrawn during the explosion
                    self.gorilla_alive[coll_data] = False
                    self.draw_scene()
                    self.explode_gorilla(coll_data)
                    return coll_data
                
                # Draw scene
                self.draw_scene()
                
                # Draw player names
                name_surf = self.font.render(self.player1_name, True, EGA_PALETTE[15])
                self.screen.blit(name_surf, (5, 5))
                name_surf = self.font.render(self.player2_name, True, EGA_PALETTE[15])
                self.screen.blit(name_surf, (SCREEN_WIDTH - name_surf.get_width() - 5, 5))
                
                # Draw banana
                rot = int((t * 10) % 4)
                banana = self.banana_sprites[rot]
                self.screen.blit(banana, (int(x), int(y)))
                
                self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
                pygame.display.flip()
            
            t += 0.1
            self.clock.tick(FPS)
    
    def explode_gorilla(self, player_num):
        # Gorilla explosion animation
        PLAY("MBO0L16EFGEFDC")
        gx = self.gorilla_x[player_num] + 15
        gy = self.gorilla_y[player_num] + 15
        # Expanding circles
        for i in range(1, 25, 2):
            self.draw_scene()
            pygame.draw.circle(self.screen, EGA_PALETTE[EXPLOSION_COLOR],
                             (gx, gy), i)
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(30)
        # Contracting circles
        for i in range(24, 0, -2):
            self.draw_scene()
            pygame.draw.circle(self.screen, EGA_PALETTE[EXPLOSION_COLOR],(gx, gy), i)
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(30)
    
    def victory_dance(self, player_num):
        # Winning gorilla dance
        self.gorilla_alive = [False, False]
        for i in range(4):
            PLAY("MFO0L32EFGEFDC")
            self.draw_scene()
            self.screen.blit(self.gorilla_images['left'],
                           (self.gorilla_x[player_num], self.gorilla_y[player_num]))
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(200)
            
            self.draw_scene()
            self.screen.blit(self.gorilla_images['right'],
                           (self.gorilla_x[player_num], self.gorilla_y[player_num]))
            self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
            pygame.display.flip()
            pygame.time.wait(200)
    
    def play_game(self):
        # Main game loop
        current_player = 0
        
        while self.scores[0] < self.num_games and self.scores[1] < self.num_games:
            # Setup new round
            self.make_cityscape()
            self.place_gorillas()
            self.gorilla_alive = [True, True]
            self.sun_hit = False
            
            hit = False
            while not hit:
                angle, velocity = self.get_shot_input(current_player)
                if angle is None:
                    return False
                PLAY("MBo0L32A-L64CL16BL64A+")
                hit_player = self.plot_shot(current_player, angle, velocity)
                
                if hit_player is not None:
                    hit = True
                    if hit_player == current_player:
                        # Hit self
                        self.scores[1 - current_player] += 1
                    else:
                        self.scores[current_player] += 1
                    
                    winner = current_player if hit_player != current_player else 1 - current_player
                    self.victory_dance(winner)
                    current_player = 1 - current_player
                else:
                    # Miss - switch players
                    current_player = 1 - current_player
                    self.sun_hit = False
            
            pygame.time.wait(1000)
        return True
    
    def game_over(self):
        # Display game over screen
        self.screen.fill(EGA_PALETTE[0])
        
        self.center_text("GAME OVER!", 100, 15)
        self.center_text("Score:", 140, 7)
        
        p1_text = f"{self.player1_name}: {self.scores[0]}"
        p2_text = f"{self.player2_name}: {self.scores[1]}"
        
        self.center_text(p1_text, 170, 7)
        self.center_text(p2_text, 195, 7)
        self.center_text("Press any key to exit", SCREEN_HEIGHT - 40, 7)
        
        self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False
            pygame.time.wait(100)

    def run(self):
        # Main program flow
        # Intro screen
        if not self.intro_screen():
            return
        
        # Get inputs
        if not self.get_inputs():
            return
        
        # Gorilla intro choice
        cont, view = self.gorilla_intro()
        if not cont:
            return
        
        if view:
            self.view_intro()
        
        # Play game
        if self.play_game():
            self.game_over()
        
        pygame.quit()

if __name__ == "__main__":
    game = QBasicGorillas()
    game.run()

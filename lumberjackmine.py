import pygame
import random
import sys
import time
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1280, 720
FLOOR_HEIGHT = 10
PLAYER_WIDTH, PLAYER_HEIGHT = 20, 40
TREE_WIDTH = 10
TRUNK_HEIGHT = 100
LEAF_WIDTH = 30
LEAF_HEIGHT = 20
BRANCH_STEPS = 10
GRAVITY = 1
JUMP_STRENGTH = 15
PLAYER_SPEED = 5
TREE_COUNT_PER_LAYOUT = 40

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
PLAYER_COLOR = (255, 100, 100)
WOOD_COLOR = (139, 69, 19)
SKIN_COLOR       = (255, 220, 170)
AXE_HANDLE_COLOR = (160, 100,  40)
AXE_HEAD_COLOR   = (190, 195, 210)

# Killer Clown colors
CLOWN_SPEED      = 3            # slightly slower than player so human can win
CLOWN_BODY_COLOR = (220,  50, 150)   # hot-pink body
CLOWN_NOSE_COLOR = (255,  20,  20)
CLOWN_HAT_COLOR  = ( 80,   0, 180)
CLOWN_EYE_COLOR  = (255, 255,   0)   # yellow crazy eyes

# Hit / lives constants
HIT_COOLDOWN      = 2.0   # seconds of invincibility after being hit
CLOWN_HIT_REBOUND = 90    # pixels clown is pushed back after landing a hit
PLAYER_LIVES      = 3

# Day/Night cycle
DAY_DURATION = 600.0      # seconds for a full day+night cycle (5 min day + 5 min night)
SUN_RADIUS = 40
SUN_COLOR = (255, 230, 50)
SUN_GLOW_COLOR = (255, 200, 80)
NIGHT_SKY   = (10,  10,  35)
DAWN_SKY    = (255, 120,  40)
DAY_SKY     = (90, 170, 255)
DUSK_SKY    = (220,  70,  20)
game_start_time = time.time()

# Moon
MOON_RADIUS = 30
MOON_COLOR       = (230, 230, 200)
MOON_EDGE_COLOR  = (200, 200, 180)
# Phase 0=Cuarto Creciente, 1=Luna Llena, 2=Cuarto Menguante, 3=Luna Nueva

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LumberjackMine2D")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)
logo_font = pygame.font.SysFont("arialblack", 96)

# Game state
inventory = {"wood": 0, "coins": 0}
player_score = 0   # total wood ever collected by the player
game_state = "splash"  # "splash" -> "menu" -> "play" / "shop" / "gameover"
splash_start_time = time.time()
current_layout = 0
menu_selected = 0
# Menu items: two play modes + shop + quit
MENU_ITEMS = ["Play - Lumberjack", "Play - Killer", "Shop", "Quit"]

# Active game mode — set when a Play option is selected from the menu
# "lumberjack": clown competes for wood  |  "killer": clown hunts the player
GAME_MODE = "killer"

# Player
player_x = WIDTH // 2
player_y = HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT
player_vel_y = 0
is_jumping = False
walk_frame  = 0.0   # drives leg/arm animation
player_facing = 1   # 1 = right, -1 = left

# Player lives (used in killer mode)
player_lives = PLAYER_LIVES
player_invincible_until = 0.0   # time.time() value until which player cannot be hit


# ── Classes ──────────────────────────────────────────────────────────────────

class Tree:
    def __init__(self, x):
        self.x = x
        self.cut = False
        self.wood_dropped = False
        self.wood_rect = None

    def draw(self):
        if self.cut:
            if self.wood_dropped:
                pygame.draw.rect(screen, WOOD_COLOR, self.wood_rect)
            return
        base_y = HEIGHT - FLOOR_HEIGHT
        trunk_top_y = base_y - TRUNK_HEIGHT
        pygame.draw.rect(screen, WHITE, (self.x, trunk_top_y, TREE_WIDTH, TRUNK_HEIGHT))
        leaf_x = self.x - (LEAF_WIDTH - TREE_WIDTH) // 2
        leaf_y = trunk_top_y - LEAF_HEIGHT
        pygame.draw.rect(screen, GREEN, (leaf_x, leaf_y, LEAF_WIDTH, LEAF_HEIGHT))
        for _ in range(random.randint(2, 4)):
            x = self.x + TREE_WIDTH // 2
            y = trunk_top_y + random.randint(10, 50)
            for _ in range(BRANCH_STEPS):
                dx = random.randint(-5, 5)
                dy = -random.randint(2, 6)
                new_x = x + dx
                new_y = y + dy
                pygame.draw.line(screen, WHITE, (x, y), (new_x, new_y), 1)
                x, y = new_x, new_y

    def try_cut(self, px):
        if self.cut:
            return
        if abs(px - self.x) < 30:
            self.cut = True
            self.drop_wood()

    def drop_wood(self):
        self.wood_dropped = True
        self.wood_rect = pygame.Rect(self.x, HEIGHT - FLOOR_HEIGHT - 10, 15, 10)

    def check_pickup(self, entity_rect):
        if self.wood_dropped and self.wood_rect.colliderect(entity_rect):
            return True
        return False


class KillerClown:
    """
    Two-mode AI character.
    Mode "lumberjack": competes with player — chops trees and grabs wood.
    Mode "killer":     hunts the player and tries to kill them.
    """

    def __init__(self, start_x=120):
        self.x = float(start_x)
        self.y = float(HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT)
        self.vel_y = 0.0
        self.is_jumping = False
        self.walk_frame = 0.0
        self.facing = 1
        self.inventory = {"wood": 0, "coins": 0}
        self.score = 0          # total wood ever collected (lumberjack mode)
        self.state = "idle"     # displayed label above head
        self.target = None      # lumberjack mode target (Tree)
        self.target_pos = None  # killer mode target (player x, y)

    # ── Lumberjack AI brain ───────────────────────────────────────────────
    def _pick_target_lumberjack(self, trees):
        """Choose what to do: grab nearest wood, or chop nearest tree."""
        best_wood_tree = None
        best_wood_dist = float('inf')
        for tree in trees:
            if tree.wood_dropped and tree.wood_rect:
                d = abs(self.x - tree.wood_rect.centerx)
                if d < best_wood_dist:
                    best_wood_dist = d
                    best_wood_tree = tree
        if best_wood_tree:
            self.state = "chase_wood"
            self.target = best_wood_tree
            return
        best_tree = None
        best_tree_dist = float('inf')
        for tree in trees:
            if not tree.cut:
                d = abs(self.x - tree.x)
                if d < best_tree_dist:
                    best_tree_dist = d
                    best_tree = tree
        if best_tree:
            self.state = "chop_tree"
            self.target = best_tree
        else:
            self.state = "idle"
            self.target = None

    # ── Killer AI brain ───────────────────────────────────────────────────
    def _pick_target_killer(self, px, py):
        """Always hunt the player."""
        self.state = "HUNT!"
        self.target_pos = (px, py)

    # ── Update (both modes) ───────────────────────────────────────────────
    def update(self, trees, player_x=None, player_y=None):
        if GAME_MODE == "killer":
            self._pick_target_killer(player_x, player_y)
            if self.target_pos:
                tx, _ = self.target_pos
                dx = tx - self.x
                if abs(dx) > 4:
                    self.facing = 1 if dx > 0 else -1
                    self.x += self.facing * CLOWN_SPEED
                    self.walk_frame += 0.20
        else:
            # Lumberjack mode — original AI logic
            self._pick_target_lumberjack(trees)
            if self.target:
                if self.state == "chase_wood":
                    target_x = self.target.wood_rect.centerx
                else:
                    target_x = self.target.x
                dx = target_x - self.x
                if abs(dx) > 5:
                    self.facing = 1 if dx > 0 else -1
                    self.x += self.facing * CLOWN_SPEED
                    self.walk_frame += 0.18
                if self.state == "chop_tree" and abs(self.x - self.target.x) < 30:
                    self.target.try_cut(self.x)
            # Pick up wood
            clown_rect = pygame.Rect(int(self.x), int(self.y), PLAYER_WIDTH, PLAYER_HEIGHT)
            for tree in trees:
                if tree.check_pickup(clown_rect):
                    tree.wood_dropped = False
                    self.inventory["wood"] += 1
                    self.score += 1
                    if self.inventory["wood"] >= 100:
                        self.inventory["wood"] -= 100
                        self.inventory["coins"] += 50

        # Gravity (both modes)
        if self.is_jumping:
            self.vel_y += GRAVITY
            self.y += self.vel_y
            if self.y >= HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT:
                self.y = HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT
                self.vel_y = 0
                self.is_jumping = False

    # ── Drawing ───────────────────────────────────────────────────────────
    def draw(self):
        x, y = int(self.x), int(self.y)
        cx = x + PLAYER_WIDTH // 2
        sw     = math.sin(self.walk_frame)
        sw_arm = math.sin(self.walk_frame + math.pi)

        hip_y  = y + 27
        knee_y = y + 34
        foot_y = y + 42
        fk_x = cx + int(sw * 8)
        ff_x = cx + int(sw * 14)
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (cx - 1, hip_y), (fk_x, knee_y), 2)
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (fk_x, knee_y),  (ff_x, foot_y), 2)
        bk_x = cx - int(sw * 8)
        bf_x = cx - int(sw * 14)
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (cx + 1, hip_y), (bk_x, knee_y), 2)
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (bk_x, knee_y),  (bf_x, foot_y), 2)

        shoulder_y = y + 15
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (cx, y + 12), (cx, hip_y), 2)

        arm_sw = int(sw_arm * 7)
        ae_x = cx + self.facing * 8 + arm_sw
        ae_y = shoulder_y + 7
        ah_x = cx + self.facing * 10 + arm_sw * 2
        ah_y = shoulder_y + 13
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (cx, shoulder_y), (ae_x, ae_y), 2)
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (ae_x, ae_y),     (ah_x, ah_y), 2)
        draw_axe(ah_x, ah_y, self.facing)
        fe_x = cx - self.facing * 8 - arm_sw
        fe_y = shoulder_y + 7
        fh_x = cx - self.facing * 10 - arm_sw * 2
        fh_y = shoulder_y + 13
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (cx, shoulder_y), (fe_x, fe_y), 2)
        pygame.draw.line(screen, CLOWN_BODY_COLOR, (fe_x, fe_y),     (fh_x, fh_y), 2)

        head_cx, head_cy = cx, y + 5
        pygame.draw.circle(screen, CLOWN_BODY_COLOR, (head_cx, head_cy), 7)
        pygame.draw.circle(screen, CLOWN_EYE_COLOR,
                           (head_cx + self.facing * 3, head_cy - 1), 2)
        pygame.draw.circle(screen, BLACK,
                           (head_cx + self.facing * 3, head_cy - 1), 1)
        pygame.draw.circle(screen, CLOWN_NOSE_COLOR, (head_cx, head_cy + 2), 3)
        pygame.draw.polygon(screen, CLOWN_HAT_COLOR, [
            (head_cx,     head_cy - 16),
            (head_cx - 8, head_cy - 7),
            (head_cx + 8, head_cy - 7),
        ])
        pygame.draw.line(screen, CLOWN_HAT_COLOR,
                         (head_cx - 9, head_cy - 7),
                         (head_cx + 9, head_cy - 7), 2)

        label = small_font.render(self.state, True, CLOWN_EYE_COLOR)
        screen.blit(label, (head_cx - label.get_width() // 2, head_cy - 32))

    def draw_stats(self):
        if GAME_MODE == "killer":
            title = font.render("KILLER CLOWN!", True, CLOWN_NOSE_COLOR)
            screen.blit(title, (WIDTH - title.get_width() - 10, 10))
            warn = small_font.render("Run for your life!", True, CLOWN_EYE_COLOR)
            screen.blit(warn, (WIDTH - warn.get_width() - 10,
                                10 + title.get_height() + 4))
        else:
            wood_text  = font.render(f"Clown Wood:  {self.inventory['wood']}/100", True, CLOWN_BODY_COLOR)
            coin_text  = font.render(f"Clown Coins: {self.inventory['coins']}", True, (255, 150,  50))
            score_text = font.render(f"Clown Score: {self.score}", True, CLOWN_EYE_COLOR)
            rx = WIDTH - wood_text.get_width() - 10
            screen.blit(wood_text,  (rx, 10))
            screen.blit(coin_text,  (WIDTH - coin_text.get_width() - 10,
                                      10 + wood_text.get_height() + 4))
            screen.blit(score_text, (WIDTH - score_text.get_width() - 10,
                                      10 + (wood_text.get_height() + 4) * 2))


# ── Day/Night helpers ─────────────────────────────────────────────────────────

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

def get_day_t():
    """Returns 0..1 where 0=dawn, 0.5=dusk end, 1=next dawn."""
    elapsed = (time.time() - game_start_time) % DAY_DURATION
    return elapsed / DAY_DURATION

def get_sky_color(t):
    if t < 0.08:
        return lerp_color(NIGHT_SKY, DAWN_SKY, t / 0.08)
    elif t < 0.22:
        return lerp_color(DAWN_SKY, DAY_SKY, (t - 0.08) / 0.14)
    elif t < 0.38:
        return lerp_color(DAY_SKY, DUSK_SKY, (t - 0.22) / 0.16)
    elif t < 0.50:
        return lerp_color(DUSK_SKY, NIGHT_SKY, (t - 0.38) / 0.12)
    else:
        return NIGHT_SKY

def get_sun_pos(t):
    if t >= 0.5:
        return None
    day_progress = t / 0.5
    sun_x = int(-SUN_RADIUS + day_progress * (WIDTH + 2 * SUN_RADIUS))
    arc = 1.0 - (2.0 * day_progress - 1.0) ** 2
    sun_y = int((HEIGHT * 0.65) - arc * (HEIGHT * 0.55))
    return (sun_x, sun_y)

def draw_sun(t):
    pos = get_sun_pos(t)
    if pos is None:
        return
    sx, sy = pos
    pygame.draw.circle(screen, SUN_GLOW_COLOR, (sx, sy), SUN_RADIUS + 14)
    pygame.draw.circle(screen, SUN_COLOR,      (sx, sy), SUN_RADIUS)

def get_moon_pos(t):
    if t < 0.5:
        return None
    night_progress = (t - 0.5) / 0.5
    moon_x = int(-MOON_RADIUS + night_progress * (WIDTH + 2 * MOON_RADIUS))
    arc = 1.0 - (2.0 * night_progress - 1.0) ** 2
    moon_y = int((HEIGHT * 0.65) - arc * (HEIGHT * 0.55))
    return (moon_x, moon_y)

def get_moon_phase():
    day_number = int((time.time() - game_start_time) / DAY_DURATION)
    return day_number % 4

def _half_circle_points(cx, cy, radius, side):
    pts = [(cx, cy)]
    if side == 'right':
        angle_range = range(-90, 92)
    else:
        angle_range = range(90, 272)
    for deg in angle_range:
        rad = math.radians(deg)
        pts.append((cx + radius * math.sin(rad),
                    cy - radius * math.cos(rad)))
    return pts

def draw_moon(t):
    pos = get_moon_pos(t)
    if pos is None:
        return
    mx, my = pos
    phase = get_moon_phase()
    if phase == 1:
        pygame.draw.circle(screen, MOON_COLOR, (mx, my), MOON_RADIUS)
    elif phase == 3:
        pygame.draw.circle(screen, MOON_EDGE_COLOR, (mx, my), MOON_RADIUS, 2)
    else:
        size = (MOON_RADIUS * 2 + 6, MOON_RADIUS * 2 + 6)
        surf = pygame.Surface(size, pygame.SRCALPHA)
        cx, cy = MOON_RADIUS + 3, MOON_RADIUS + 3
        side = 'right' if phase == 0 else 'left'
        pts = _half_circle_points(cx, cy, MOON_RADIUS, side)
        pygame.draw.polygon(surf, (*MOON_COLOR, 255), pts)
        screen.blit(surf, (mx - MOON_RADIUS - 3, my - MOON_RADIUS - 3))


# ── Layout / world ────────────────────────────────────────────────────────────

def generate_trees():
    positions = sorted(random.sample(range(50, WIDTH - 50), TREE_COUNT_PER_LAYOUT))
    return [Tree(x) for x in positions]

tree_layouts = [generate_trees()]
trees = tree_layouts[0]

killer_clown = KillerClown(start_x=120)


# ── Draw helpers ──────────────────────────────────────────────────────────────

def draw_floor():
    pygame.draw.rect(screen, WHITE, (0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT))

def draw_axe(hx, hy, facing):
    tip_x = hx + facing * 12
    tip_y = hy - 11
    pygame.draw.line(screen, AXE_HANDLE_COLOR, (hx, hy), (tip_x, tip_y), 3)
    b_top  = (tip_x + facing * 5, tip_y - 8)
    b_bot  = (tip_x + facing * 5, tip_y + 5)
    b_back = (tip_x - facing * 3, tip_y - 2)
    pygame.draw.polygon(screen, AXE_HEAD_COLOR, [b_top, b_bot, b_back])
    pygame.draw.polygon(screen, (140, 145, 160), [b_top, b_bot, b_back], 1)

def draw_player(x, y):
    # Blink during invincibility in killer mode
    if GAME_MODE == "killer" and time.time() < player_invincible_until:
        if int(time.time() * 8) % 2 == 0:
            return

    cx = x + PLAYER_WIDTH // 2
    sw = math.sin(walk_frame)
    sw_arm = math.sin(walk_frame + math.pi)

    hip_y  = y + 27
    knee_y = y + 34
    foot_y = y + 42
    fk_x = cx + int(sw * 8)
    ff_x = cx + int(sw * 14)
    pygame.draw.line(screen, SKIN_COLOR, (cx - 1, hip_y), (fk_x, knee_y), 2)
    pygame.draw.line(screen, SKIN_COLOR, (fk_x,   knee_y), (ff_x, foot_y), 2)
    bk_x = cx - int(sw * 8)
    bf_x = cx - int(sw * 14)
    pygame.draw.line(screen, SKIN_COLOR, (cx + 1, hip_y), (bk_x, knee_y), 2)
    pygame.draw.line(screen, SKIN_COLOR, (bk_x,   knee_y), (bf_x, foot_y), 2)

    shoulder_y = y + 15
    pygame.draw.line(screen, SKIN_COLOR, (cx, y + 12), (cx, hip_y), 2)

    arm_sw = int(sw_arm * 7)
    ae_x = cx + player_facing * 8 + arm_sw
    ae_y = shoulder_y + 7
    ah_x = cx + player_facing * 10 + arm_sw * 2
    ah_y = shoulder_y + 13
    pygame.draw.line(screen, SKIN_COLOR, (cx, shoulder_y), (ae_x, ae_y), 2)
    pygame.draw.line(screen, SKIN_COLOR, (ae_x, ae_y),     (ah_x, ah_y), 2)
    draw_axe(ah_x, ah_y, player_facing)
    fe_x = cx - player_facing * 8 - arm_sw
    fe_y = shoulder_y + 7
    fh_x = cx - player_facing * 10 - arm_sw * 2
    fh_y = shoulder_y + 13
    pygame.draw.line(screen, SKIN_COLOR, (cx, shoulder_y), (fe_x, fe_y), 2)
    pygame.draw.line(screen, SKIN_COLOR, (fe_x, fe_y),     (fh_x, fh_y), 2)

    head_cx, head_cy = cx, y + 5
    pygame.draw.circle(screen, SKIN_COLOR, (head_cx, head_cy), 7)
    pygame.draw.circle(screen, BLACK, (head_cx + player_facing * 3, head_cy - 1), 1)

def draw_lives():
    """Draw life circles in the HUD (killer mode only)."""
    if GAME_MODE != "killer":
        return
    label = font.render("Lives:", True, WHITE)
    screen.blit(label, (10, 96))
    lx = 10 + label.get_width() + 10
    for i in range(PLAYER_LIVES):
        color = (220, 50, 50) if i < player_lives else (55, 55, 55)
        pygame.draw.circle(screen, color, (lx + i * 28, 108), 10)
        pygame.draw.circle(screen, WHITE,  (lx + i * 28, 108), 10, 1)

def draw_hit_flash():
    """Red screen tint while player is invincible after a hit."""
    if GAME_MODE != "killer":
        return
    if time.time() < player_invincible_until:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((180, 0, 0, 55))
        screen.blit(flash, (0, 0))

def draw_inventory():
    wood_text  = font.render(f"Wood:  {inventory['wood']}/100", True, WHITE)
    coin_text  = font.render(f"Coins: {inventory['coins']}", True, (255, 215, 0))
    score_text = font.render(f"Score: {player_score}", True, (150, 255, 150))
    screen.blit(wood_text,  (10, 10))
    screen.blit(coin_text,  (10, 10 + wood_text.get_height() + 4))
    screen.blit(score_text, (10, 10 + (wood_text.get_height() + 4) * 2))
    draw_lives()

    if GAME_MODE == "lumberjack":
        if player_score > killer_clown.score:
            who, col = "YOU LEAD!", (100, 255, 100)
        elif killer_clown.score > player_score:
            who, col = "CLOWN LEADS!", CLOWN_BODY_COLOR
        else:
            who, col = "TIED", WHITE
        vs_text = font.render(who, True, col)
        screen.blit(vs_text, vs_text.get_rect(center=(WIDTH // 2, 20)))
    else:
        warn = font.render("SURVIVE!", True, (255, 80, 80))
        screen.blit(warn, warn.get_rect(center=(WIDTH // 2, 20)))

    killer_clown.draw_stats()

def draw_splash():
    screen.fill(BLACK)
    text = logo_font.render("LumberjackMine2D", True, WHITE)
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, rect)
    pygame.display.flip()

def draw_menu():
    screen.fill(BLACK)
    title = logo_font.render("LumberjackMine2D", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 20)))
    item_font = pygame.font.SysFont("arialblack", 48)
    left_x = 80
    for i, label in enumerate(MENU_ITEMS):
        selected = (i == menu_selected)
        color = (255, 215, 0) if selected else (180, 180, 180)
        text  = item_font.render(("▶  " if selected else "    ") + label, True, color)
        screen.blit(text, (left_x, HEIGHT // 2 + i * 72))
    pygame.display.flip()

def draw_shop():
    screen.fill((20, 20, 50))
    title = logo_font.render("Shop", True, (255, 215, 0))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
    msg = font.render("Coming soon!  Press ESC to go back.", True, WHITE)
    screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    pygame.display.flip()

def draw_gameover():
    screen.fill(BLACK)
    go_font = pygame.font.SysFont("arialblack", 96)
    text = go_font.render("GAME OVER", True, (220, 50, 50))
    screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))
    score_text = font.render(f"Wood collected: {player_score}", True, WHITE)
    screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
    hint = font.render("ENTER — play again    ESC — menu", True, (180, 180, 180))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
    pygame.display.flip()

def draw_scene():
    t = get_day_t()
    sky_color = get_sky_color(t)
    screen.fill(sky_color)
    draw_sun(t)
    draw_moon(t)
    draw_floor()
    for tree in trees:
        tree.draw()
    killer_clown.draw()
    draw_player(player_x, player_y)
    draw_inventory()
    draw_hit_flash()
    pygame.display.flip()


# ── Game logic ────────────────────────────────────────────────────────────────

def handle_input():
    global player_x, is_jumping, player_vel_y, walk_frame, player_facing
    keys = pygame.key.get_pressed()
    moving = False
    if keys[pygame.K_LEFT]:
        player_x   -= PLAYER_SPEED
        player_facing = -1
        moving = True
    if keys[pygame.K_RIGHT]:
        player_x   += PLAYER_SPEED
        player_facing = 1
        moving = True
    if moving:
        walk_frame += 0.18
    if keys[pygame.K_SPACE] and not is_jumping:
        is_jumping = True
        player_vel_y = -JUMP_STRENGTH

def apply_gravity():
    global player_y, player_vel_y, is_jumping
    if is_jumping:
        player_vel_y += GRAVITY
        player_y += player_vel_y
        if player_y >= HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT:
            player_y = HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT
            player_vel_y = 0
            is_jumping = False

def check_tree_cut(pos):
    for tree in trees:
        if not tree.cut and abs(player_x - tree.x) < 30:
            tree.try_cut(player_x)

def check_pickups():
    global player_score
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    for tree in trees:
        if tree.check_pickup(player_rect):
            tree.wood_dropped = False
            inventory["wood"] += 1
            player_score += 1
            if inventory["wood"] >= 100:
                inventory["wood"] -= 100
                inventory["coins"] += 50

def check_player_hit():
    """Killer mode: if clown collides with player, lose a life and push clown back."""
    global player_lives, player_invincible_until
    if GAME_MODE != "killer":
        return
    now = time.time()
    if now < player_invincible_until:
        return
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    clown_rect  = pygame.Rect(int(killer_clown.x), int(killer_clown.y),
                               PLAYER_WIDTH, PLAYER_HEIGHT)
    if player_rect.colliderect(clown_rect):
        player_lives -= 1
        player_invincible_until = now + HIT_COOLDOWN
        # Push clown away so it can't chain-kill
        killer_clown.x -= killer_clown.facing * CLOWN_HIT_REBOUND

def check_world_wrap():
    global player_x, current_layout, trees
    if player_x > WIDTH:
        current_layout += 1
        if current_layout >= len(tree_layouts):
            tree_layouts.append(generate_trees())
        trees = tree_layouts[current_layout]
        player_x = 0
        killer_clown.x = 60.0
        killer_clown.target = None

def reset_game():
    """Reset all mutable player/world state for a fresh run."""
    global player_x, player_y, player_vel_y, is_jumping, walk_frame, player_facing
    global inventory, player_score, player_lives, player_invincible_until
    global current_layout, trees, tree_layouts
    player_x = WIDTH // 2
    player_y = HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT
    player_vel_y = 0
    is_jumping = False
    walk_frame = 0.0
    player_facing = 1
    inventory = {"wood": 0, "coins": 0}
    player_score = 0
    player_lives = PLAYER_LIVES
    player_invincible_until = 0.0
    current_layout = 0
    tree_layouts = [generate_trees()]
    trees = tree_layouts[0]
    killer_clown.x = 120.0
    killer_clown.y = float(HEIGHT - FLOOR_HEIGHT - PLAYER_HEIGHT)
    killer_clown.inventory = {"wood": 0, "coins": 0}
    killer_clown.score = 0
    killer_clown.state = "idle"
    killer_clown.target = None
    killer_clown.target_pos = None


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    global game_state, menu_selected, GAME_MODE

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif game_state == "menu" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    menu_selected = (menu_selected - 1) % len(MENU_ITEMS)
                elif event.key == pygame.K_DOWN:
                    menu_selected = (menu_selected + 1) % len(MENU_ITEMS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if menu_selected == 0:          # Play - Lumberjack
                        GAME_MODE = "lumberjack"
                        reset_game()
                        game_state = "play"
                    elif menu_selected == 1:         # Play - Killer
                        GAME_MODE = "killer"
                        reset_game()
                        game_state = "play"
                    elif menu_selected == 2:         # Shop
                        game_state = "shop"
                    elif menu_selected == 3:         # Quit
                        pygame.quit()
                        sys.exit()

            elif game_state == "shop" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"

            elif game_state == "play" and event.type == pygame.MOUSEBUTTONDOWN:
                check_tree_cut(event.pos)

            elif game_state == "play" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"

            elif game_state == "gameover" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    reset_game()
                    game_state = "play"
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"

        if game_state == "splash":
            draw_splash()
            if time.time() - splash_start_time > 4:
                game_state = "menu"
        elif game_state == "menu":
            draw_menu()
        elif game_state == "shop":
            draw_shop()
        elif game_state == "play":
            handle_input()
            apply_gravity()
            killer_clown.update(trees, player_x, player_y)
            check_pickups()
            check_player_hit()
            check_world_wrap()
            if GAME_MODE == "killer" and player_lives <= 0:
                game_state = "gameover"
            draw_scene()
        elif game_state == "gameover":
            draw_gameover()

        clock.tick(60)


if __name__ == "__main__":
    main()

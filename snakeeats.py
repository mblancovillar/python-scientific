import pygame
import random
import sys
import math
import numpy as np
import urllib.request
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()

WIDTH, HEIGHT = 800, 600
CELL = 20
MARGIN = 20

GRID_COLS = (WIDTH  - 2 * MARGIN) // CELL
GRID_ROWS = (HEIGHT - 2 * MARGIN) // CELL

BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
BG_COLOR     = (15,  25,  15)
WALL_COLOR   = (60,  45,  25)
WALL_EDGE    = (110, 80,  40)
SNAKE_HEAD   = (60,  230, 60)
SNAKE_BODY   = (35,  160, 35)
SNAKE_DARK   = (20,  100, 20)
SNAKE_EYE    = (255, 240, 0)
APPLE_COL    = (220, 35,  35)      # good apple
APPLE_HILITE = (255, 110, 110)
APPLE_LEAF   = (0,   170, 0)
BAD_COL      = (155, 18,  18)      # bad apple — slightly darker, same shape
BAD_HILITE   = (200, 70,  70)
SCORE_COL    = (190, 230, 190)
WARN_COL     = (255, 200, 0)

MOVE_DELAY      = 8     # frames between moves (60 fps → ~7.5 moves/s)
SNAKE_START_LEN = 5
BAD_LIFETIME    = 300   # frames before bad apple vanishes
SCARE_DURATION  = 200
PAIR_MIN_DIST   = 2     # cells — closest the bad apple can spawn to the good
PAIR_MAX_DIST   = 4     # cells — farthest

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake'Eats  — by Toto")
clock  = pygame.time.Clock()

font       = pygame.font.SysFont(None, 32)
small_font = pygame.font.SysFont(None, 24)
big_font   = pygame.font.SysFont("arialblack", 66)
title_font = pygame.font.SysFont("arialblack", 88)


# ── Scary apple image (OpenMoji public-domain PNG, transparent background) ────

_APPLE_IMG_PATH = os.path.join(SCRIPT_DIR, "images/scary_apple.png")
_APPLE_IMG_URL  = (
    "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master"
    "/color/618x618/1F34E.png"
)

def _load_apple_img():
    if not os.path.exists(_APPLE_IMG_PATH):
        try:
            urllib.request.urlretrieve(_APPLE_IMG_URL, _APPLE_IMG_PATH)
        except Exception:
            return None
    try:
        return pygame.image.load(_APPLE_IMG_PATH).convert_alpha()
    except Exception:
        return None

scary_apple_img = _load_apple_img()


# ── Sound generation (numpy) ──────────────────────────────────────────────────

SR = 44100

def _make_wave(freq_list, dur_ms, vol, decay, noise=0.0):
    n   = int(SR * dur_ms / 1000)
    t   = np.linspace(0, dur_ms / 1000, n, endpoint=False)
    w   = sum(np.sin(2 * np.pi * f * t) for f in freq_list) / max(len(freq_list), 1)
    if noise:
        w += np.random.uniform(-noise, noise, n)
    env = np.exp(-decay * t / (dur_ms / 1000))
    w   = np.clip(w * env * vol, -1.0, 1.0)
    s   = (w * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([s, s]))

def _make_sweep(f_start, f_end, dur_ms, vol, decay):
    n   = int(SR * dur_ms / 1000)
    t   = np.linspace(0, dur_ms / 1000, n, endpoint=False)
    f   = np.linspace(f_start, f_end, n)
    phase = np.cumsum(2 * np.pi * f / SR)
    w   = np.sin(phase)
    env = np.exp(-decay * t / (dur_ms / 1000))
    w   = np.clip(w * env * vol, -1.0, 1.0)
    s   = (w * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([s, s]))

# Pleasant "chomp" rising arpeggio
snd_eat      = _make_wave([523, 659, 784], 180, vol=0.45, decay=6)
# Subtle low warning ping when a pair of apples spawns
snd_pair     = _make_wave([220, 330],      280, vol=0.30, decay=4)
# Jarring scare blast: low rumble + high shriek + noise
snd_scare    = _make_wave([80, 100, 800, 1100], 700, vol=0.55, decay=1.5, noise=0.25)
# Descending game-over tune
snd_gameover = _make_sweep(440, 200,       900, vol=0.45, decay=1.2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def grid_to_px(gx, gy):
    return (MARGIN + gx * CELL, MARGIN + gy * CELL)

def random_pos(exclude):
    while True:
        pos = (random.randint(0, GRID_COLS - 1), random.randint(0, GRID_ROWS - 1))
        if pos not in exclude:
            return pos

def nearby_pos(center, min_d, max_d, exclude):
    """Random grid position within [min_d, max_d] cells of center."""
    cx, cy = center
    for _ in range(200):
        angle = random.uniform(0, 2 * math.pi)
        dist  = random.randint(min_d, max_d)
        nx    = cx + int(round(math.cos(angle) * dist))
        ny    = cy + int(round(math.sin(angle) * dist))
        pos   = (nx, ny)
        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS and pos not in exclude:
            return pos
    return random_pos(exclude)

def _turn_right(d):
    return {RIGHT: DOWN, DOWN: LEFT, LEFT: UP, UP: RIGHT}[d]

def _turn_left(d):
    return {RIGHT: UP, UP: LEFT, LEFT: DOWN, DOWN: RIGHT}[d]


# ── Snake ─────────────────────────────────────────────────────────────────────

class Snake:
    def __init__(self):
        cx, cy    = GRID_COLS // 2, GRID_ROWS // 2
        self.body = [(cx - i, cy) for i in range(SNAKE_START_LEN)]
        self.dir  = RIGHT
        self.next = RIGHT
        self.queue = 0
        self.last_horizontal = RIGHT   # tracks most recent horizontal direction
        self.pending_uturn   = []      # queued direction steps for a U-turn

    def try_dir(self, d):
        """Set direction; if d is the exact opposite of current dir, U-turn instead."""
        if d[0] + self.dir[0] == 0 and d[1] + self.dir[1] == 0:
            self.uturn()
        else:
            self.next = d
            self.pending_uturn = []

    def uturn(self):
        """Queue a two-step U-turn (rotate twice in the last horizontal direction)."""
        cur = self.dir
        if self.last_horizontal == RIGHT:
            step1 = _turn_right(cur)
            step2 = _turn_right(step1)
        else:
            step1 = _turn_left(cur)
            step2 = _turn_left(step1)
        self.pending_uturn = [step1, step2]

    def head(self):
        return self.body[0]

    def move(self):
        if self.pending_uturn:
            self.dir  = self.pending_uturn.pop(0)
            self.next = self.dir       # keep going this way once queue drains
        else:
            self.dir = self.next
        if self.dir in (LEFT, RIGHT):
            self.last_horizontal = self.dir
        hx, hy   = self.body[0]
        dx, dy   = self.dir
        self.body.insert(0, (hx + dx, hy + dy))
        if self.queue > 0:
            self.queue -= 1
        else:
            self.body.pop()

    def grow(self, n=1):
        self.queue += n

    def wall_hit(self):
        hx, hy = self.head()
        return hx < 0 or hx >= GRID_COLS or hy < 0 or hy >= GRID_ROWS

    def self_hit(self):
        return self.head() in self.body[1:]

    def draw(self):
        for i, (gx, gy) in enumerate(self.body):
            px, py = grid_to_px(gx, gy)
            col = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(screen, col,
                             (px + 1, py + 1, CELL - 2, CELL - 2), border_radius=4)
            if i > 0 and i % 2 == 0:
                pygame.draw.rect(screen, SNAKE_DARK,
                                 (px + 5, py + 5, CELL - 10, CELL - 10), border_radius=2)
        hx, hy   = self.body[0]
        px, py   = grid_to_px(hx, hy)
        cx, cy   = px + CELL // 2, py + CELL // 2
        dx, dy   = self.dir
        perp_x, perp_y = -dy, dx
        for sign in (1, -1):
            ex = cx + dx * 4 + sign * perp_x * 4
            ey = cy + dy * 4 + sign * perp_y * 4
            pygame.draw.circle(screen, SNAKE_EYE,  (int(ex), int(ey)), 3)
            pygame.draw.circle(screen, BLACK,       (int(ex + dx), int(ey + dy)), 1)


# ── Apple ─────────────────────────────────────────────────────────────────────

class Apple:
    def __init__(self, pos, bad=False):
        self.pos  = pos
        self.bad  = bad
        self.age  = 0

    def tick(self):
        self.age += 1
        if self.bad:
            return self.age < BAD_LIFETIME
        return True

    def draw(self):
        gx, gy = self.pos
        px, py = grid_to_px(gx, gy)
        cx, cy = px + CELL // 2, py + CELL // 2
        pulse  = math.sin(self.age * 0.14) * 1.5
        r      = int(CELL // 2 - 1 + pulse)

        col    = BAD_COL    if self.bad else APPLE_COL
        hilite = BAD_HILITE if self.bad else APPLE_HILITE

        pygame.draw.circle(screen, col,    (cx, cy),       r)
        pygame.draw.circle(screen, hilite, (cx - 3, cy - 3), max(r // 3, 2))
        # stem + leaf (leaf points right for bad, left for good — very subtle)
        leaf_dir = 1 if self.bad else -1
        pygame.draw.line(screen, APPLE_LEAF,
                         (cx, cy - r), (cx, cy - r - 4), 2)
        pygame.draw.line(screen, APPLE_LEAF,
                         (cx, cy - r - 2),
                         (cx + leaf_dir * 5, cy - r - 5), 2)

        # faint countdown ring on bad apple so player notices it will vanish
        if self.bad:
            frac = 1.0 - self.age / BAD_LIFETIME
            arc_rect = pygame.Rect(px, py, CELL, CELL)
            if frac > 0:
                pygame.draw.arc(screen, (200, 60, 60), arc_rect,
                                0, frac * 2 * math.pi, 2)


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_walls():
    for rect in [
        (0, 0, WIDTH, MARGIN),
        (0, HEIGHT - MARGIN, WIDTH, MARGIN),
        (0, 0, MARGIN, HEIGHT),
        (WIDTH - MARGIN, 0, MARGIN, HEIGHT),
    ]:
        pygame.draw.rect(screen, WALL_COLOR, rect)
        pygame.draw.rect(screen, WALL_EDGE,  rect, 3)
    for cx, cy in [(MARGIN // 2, MARGIN // 2),
                   (WIDTH - MARGIN // 2, MARGIN // 2),
                   (MARGIN // 2, HEIGHT - MARGIN // 2),
                   (WIDTH - MARGIN // 2, HEIGHT - MARGIN // 2)]:
        pygame.draw.circle(screen, WALL_EDGE, (cx, cy), 5)
        pygame.draw.circle(screen, BLACK,     (cx, cy), 2)


def draw_hud(score, length, pair_active):
    sc = font.render(f"Score: {score}   Length: {length}", True, SCORE_COL)
    screen.blit(sc, (MARGIN + 4, 3))
    if pair_active:
        tick = pygame.time.get_ticks() // 400 % 2
        if tick:
            w = font.render("Two apples close together — eat only one!", True, WARN_COL)
            screen.blit(w, w.get_rect(midtop=(WIDTH // 2, 3)))


def draw_scary_apple(frame):
    """Jumpscare: real apple image with evil eyes and angry eyebrows."""
    strobe = int(abs(math.sin(frame * 0.25)) * 90)
    screen.fill((strobe, 0, 0))

    cx, cy     = WIDTH // 2, HEIGHT // 2 - 30
    apple_size = 360 + int(math.sin(frame * 0.1) * 14)   # subtle pulsing
    # slight random shake for extra horror
    shake_x = random.randint(-3, 3) if frame % 3 == 0 else 0
    shake_y = random.randint(-3, 3) if frame % 3 == 0 else 0
    acx, acy = cx + shake_x, cy + shake_y

    if scary_apple_img is not None:
        scaled = pygame.transform.smoothscale(scary_apple_img, (apple_size, apple_size))
        screen.blit(scaled, scaled.get_rect(center=(acx, acy)))
    else:
        # Fallback drawn apple
        pygame.draw.circle(screen, (160, 20, 20), (acx, acy), apple_size // 2)
        pygame.draw.circle(screen, (220, 80, 80), (acx - 55, acy - 55), apple_size // 6)
        pygame.draw.line(screen, (60, 120, 30),
                         (acx, acy - apple_size // 2),
                         (acx, acy - apple_size // 2 - 24), 5)

    # Glowing evil eyes
    ep  = int(abs(math.sin(frame * 0.2)) * 10)
    eye_y = acy + 20
    for ex in (acx - 78, acx + 78):
        pygame.draw.circle(screen, (255, 210,  0), (ex, eye_y), 32 + ep)
        pygame.draw.circle(screen, (180, 150,  0), (ex, eye_y), 32 + ep, 3)
        pygame.draw.circle(screen, BLACK,           (ex, eye_y), 15)
        pygame.draw.circle(screen, (230,  0,   0),  (ex, eye_y),  8)
        pygame.draw.circle(screen, WHITE,           (ex - 8, eye_y - 8), 5)  # glare

    # Angry furrowed eyebrows
    boff  = int(abs(math.sin(frame * 0.13)) * 5)
    brow_y = acy - 22 - boff
    for side, ex in ((-1, acx - 78), (1, acx + 78)):
        x_outer = ex - side * 34
        x_inner = ex + side * 14
        pygame.draw.line(screen, (10,  5,  0),
                         (x_outer, brow_y + 12), (x_inner, brow_y - 10), 11)
        pygame.draw.line(screen, (50, 25,  0),
                         (x_outer, brow_y + 12), (x_inner, brow_y - 10),  4)

    # Rotating scary messages
    msgs = ["H I S S S S S S !", "GOTCHA,  T O T O !", "ATE THE WRONG APPLE !",
            "BWAHAHAHAHAHA !", "NO  SECOND  APPLES !"]
    idx  = (frame // 18) % len(msgs)
    r2   = int(abs(math.sin(frame * 0.2))  * 255)
    g2   = int(abs(math.sin(frame * 0.15)) * 200)
    txt  = big_font.render(msgs[idx], True, (255, r2, g2))
    screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT - 70)))


def draw_splash(frame):
    screen.fill(BLACK)
    r = int(abs(math.sin(frame * 0.03)) * 80) + 60
    g = int(abs(math.sin(frame * 0.03 + 1)) * 130) + 80
    title = title_font.render("Snake'Eats", True, (r, min(g + 80, 255), 40))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
    by = font.render("by  T O T O", True, (120, 210, 120))
    screen.blit(by, by.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))
    hint = small_font.render(
        "WASD to steer  —  opposite key = quick U-turn  —  ENTER to start",
        True, (160, 160, 160))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 105)))
    tip = small_font.render("Tip: two apples close together — only one is safe!", True, (140, 140, 140))
    screen.blit(tip, tip.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140)))


def draw_gameover(score, length):
    screen.fill(BLACK)
    go = big_font.render("GAME  OVER", True, (220, 50, 50))
    screen.blit(go, go.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))
    sc = font.render(f"Score: {score}   Snake length: {length}", True, WHITE)
    screen.blit(sc, sc.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 5)))
    hint = font.render("ENTER — play again     ESC — title", True, (160, 160, 160))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))


# ── Game factory ──────────────────────────────────────────────────────────────

def new_game():
    snake    = Snake()
    occupied = set(snake.body)
    apple    = Apple(random_pos(occupied))
    return dict(snake=snake, apple=apple, bad_apple=None,
                score=0, frame=0, move_timer=0)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    state    = "splash"
    splash_f = 0
    scare_f  = 0
    g        = new_game()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type != pygame.KEYDOWN:
                continue

            if state == "splash":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = "play"
                    g = new_game()

            elif state == "play":
                if   event.key == pygame.K_w:      g["snake"].try_dir(UP)
                elif event.key == pygame.K_a:      g["snake"].try_dir(LEFT)
                elif event.key == pygame.K_s:      g["snake"].try_dir(DOWN)
                elif event.key == pygame.K_d:      g["snake"].try_dir(RIGHT)
                elif event.key == pygame.K_ESCAPE: state = "splash"

            elif state == "gameover":
                if   event.key == pygame.K_RETURN:
                    g = new_game()
                    state = "play"
                elif event.key == pygame.K_ESCAPE:
                    state = "splash"

        # ── State rendering ───────────────────────────────────────────────────

        if state == "splash":
            draw_splash(splash_f)
            splash_f += 1

        elif state == "scare":
            draw_scary_apple(scare_f)
            scare_f += 1
            if scare_f >= SCARE_DURATION:
                state = "gameover"

        elif state == "gameover":
            draw_gameover(g["score"], len(g["snake"].body))

        elif state == "play":
            g["frame"]      += 1
            g["move_timer"] += 1

            g["apple"].age += 1
            if g["bad_apple"]:
                if not g["bad_apple"].tick():
                    g["bad_apple"] = None   # bad apple timed out — safe!

            if g["move_timer"] >= MOVE_DELAY:
                g["move_timer"] = 0
                g["snake"].move()

                if g["snake"].wall_hit() or g["snake"].self_hit():
                    snd_gameover.play()
                    state = "gameover"
                else:
                    head = g["snake"].head()

                    # ate the good apple
                    if head == g["apple"].pos:
                        g["snake"].grow()
                        g["score"] += 10
                        snd_eat.play()

                        occupied = set(g["snake"].body)
                        if g["bad_apple"]:
                            occupied.add(g["bad_apple"].pos)
                        new_apple = Apple(random_pos(occupied))

                        # 55% chance: spawn a bad apple near the new good apple
                        new_bad = None
                        if random.random() < 0.55:
                            occ2    = set(g["snake"].body) | {new_apple.pos}
                            bad_pos = nearby_pos(new_apple.pos,
                                                 PAIR_MIN_DIST, PAIR_MAX_DIST, occ2)
                            new_bad = Apple(bad_pos, bad=True)
                            snd_pair.play()

                        g["apple"]     = new_apple
                        g["bad_apple"] = new_bad

                    # ate the bad apple → SCARE!
                    elif g["bad_apple"] and head == g["bad_apple"].pos:
                        snd_scare.play()
                        scare_f = 0
                        state   = "scare"

            if state == "play":
                screen.fill(BG_COLOR)
                draw_walls()
                g["apple"].draw()
                if g["bad_apple"]:
                    g["bad_apple"].draw()
                g["snake"].draw()
                draw_hud(g["score"], len(g["snake"].body), g["bad_apple"] is not None)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()

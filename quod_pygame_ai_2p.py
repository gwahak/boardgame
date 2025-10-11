import pygame
import sys
import random

# -------------------- Config --------------------
GRID_N = 11
CELL = 48
MARGIN = 48
PANEL_W = 300
WIDTH = MARGIN*2 + GRID_N*CELL + PANEL_W
HEIGHT = MARGIN*2 + GRID_N*CELL
FPS = 60

# Player IDs
RED   = 2  # Red
BLUE  = 3  # Blue
QUASAR = 7
EMPTY  = 0

PLAYER_FILL = {
    RED:  (220, 40, 40),
    BLUE: (40, 100, 220),
    QUASAR: (180, 180, 180),
}
PLAYER_TEXT = {
    RED: (250, 250, 250),
    BLUE: (250, 250, 250),
    QUASAR: (20, 20, 20),
}
PLAYER_NAME = {
    RED: "Red",
    BLUE: "Blue",
    QUASAR: "Quasar",
}

BG = (250, 252, 255)
GRID = (40, 40, 40)
LBL = (60, 60, 60)
PANEL_BG = (245, 247, 250)
WIN_CLR = (10, 120, 40)
ERR_CLR = (160, 30, 30)

# Quads / Quasars
QUODS_PER_PLAYER = 20          # <- use this for quads left
QUASARS_PER_PLAYER = 6
USE_QUASAR_TIEBREAK = True     # On(True)/Off(False): tie-break by remaining quasars

# -------------------- UI helpers --------------------
def grid_rect(i, j):
    x = MARGIN + i*CELL
    y = MARGIN + j*CELL
    return pygame.Rect(x, y, CELL, CELL)

def cell_center(i, j):
    r = grid_rect(i, j)
    return (r.centerx, r.centery)

def colrow_from_pos(pos):
    x, y = pos
    gx0, gy0 = MARGIN, MARGIN
    gx1, gy1 = MARGIN + GRID_N*CELL, MARGIN + GRID_N*CELL
    if not (gx0 <= x < gx1 and gy0 <= y < gy1):
        return None
    i = (x - MARGIN) // CELL
    j = (y - MARGIN) // CELL
    return int(i), int(j)

def draw_grid(surface, font_lbl):
    for k in range(GRID_N + 1):
        x = MARGIN + k*CELL
        pygame.draw.line(surface, GRID, (x, MARGIN), (x, MARGIN + GRID_N*CELL), 1)
        y = MARGIN + k*CELL
        pygame.draw.line(surface, GRID, (MARGIN, y), (MARGIN + GRID_N*CELL, y), 1)
    for i in range(GRID_N):
        ch = chr(ord('A') + i)
        text = font_lbl.render(ch, True, LBL)
        tx = MARGIN + i*CELL + CELL//2 - text.get_width()//2
        ty = MARGIN - 28
        surface.blit(text, (tx, ty))
    for j in range(GRID_N):
        text = font_lbl.render(str(j+1), True, LBL)
        tx = MARGIN - 36
        ty = MARGIN + j*CELL + CELL//2 - text.get_height()//2
        surface.blit(text, (tx, ty))

def draw_stone(surface, i, j, label, owner_id, font_num):
    cx, cy = cell_center(i, j)
    pygame.draw.circle(surface, PLAYER_FILL[owner_id], (cx, cy), CELL//2 - 6)
    pygame.draw.circle(surface, (20,20,20), (cx, cy), CELL//2 - 6, 1)
    text = font_num.render(label, True, PLAYER_TEXT[owner_id])
    surface.blit(text, (cx - text.get_width()//2, cy - text.get_height()//2))

def wrap_text(text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# -------------------- Game core --------------------
def init_board():
    pan = [[EMPTY for _ in range(GRID_N)] for _ in range(GRID_N)]
    pan[0][0] = QUASAR
    pan[GRID_N-1][0] = QUASAR
    pan[0][GRID_N-1] = QUASAR
    pan[GRID_N-1][GRID_N-1] = QUASAR
    return pan

def count4gon(pan, n):
    cnt = 0
    for gg in range(1, 11):
        for hh in range(gg):
            for ii in range(11-gg):
                for jj in range(11-gg):
                    try:
                        if (pan[ii][jj+hh]    == n and
                            pan[ii+hh][jj+gg] == n and
                            pan[ii+gg-hh][jj] == n and
                            pan[ii+gg][jj+gg-hh] == n):
                            cnt += 1
                    except IndexError:
                        pass
    return cnt

# -------------------- Ported AI (from JS) --------------------
BIG = 1000

def add_list(dct, x, y, s):
    if 0 <= x < GRID_N and 0 <= y < GRID_N:
        dct[(x, y)] = dct.get((x, y), 0) + s

def pair_cells(pan, cx, cy, dx, dy, p, accum):
    def val(x, y):
        if 0 <= x < GRID_N and 0 <= y < GRID_N:
            return pan[x][y]
        return None
    u = val(cx, cy); v = val(dx, dy)
    if u is None or v is None: return

    if u == EMPTY and v == EMPTY:
        add_list(accum, cx, cy, 1)
        add_list(accum, dx, dy, 1)
        return
    if u == p:
        if v != EMPTY: return
        add_list(accum, dx, dy, BIG)
        return
    if v == p:
        if u != EMPTY: return
        add_list(accum, cx, cy, BIG)

def important(pan, p):
    stones = [(x, y) for x in range(GRID_N) for y in range(GRID_N) if pan[x][y] == p]
    l = {}
    n = len(stones)
    for i in range(n):
        ax, ay = stones[i]
        for j in range(i+1, n):
            bx, by = stones[j]
            vx, vy = (by - ay), (ax - bx)
            pair_cells(pan, ax + vx, ay + vy, bx + vx, by + vy, p, l)
            pair_cells(pan, ax - vx, ay - vy, bx - vx, by - vy, p, l)
            if ((vx + vy) % 2) == 0:
                gx, gy = (ax + bx + vx) // 2, (ay + by + vy) // 2
                pair_cells(pan, gx, gy, gx - vx, gy - vy, p, l)
    return l

def has_critical(accum):
    return any(score >= BIG for score in accum.values())

def chk_attack(pan, my, his, me, usedquasar):
    criticals = [pos for pos, sc in his.items() if sc >= BIG and pan[pos[0]][pos[1]] == EMPTY]
    if not criticals: return (None, [])
    best = max(criticals, key=lambda pos: my.get(pos, 0))
    quasar_targets = []
    for pos in criticals:
        if pos == best: continue
        if usedquasar[me] < QUASARS_PER_PLAYER:
            quasar_targets.append(pos)
            usedquasar[me] += 1  # reserve
    return (best, quasar_targets)

def chk_important(my, his):
    best, best_score = None, -1
    for pos, sc in my.items():
        s = sc + his.get(pos, 0)
        if s > best_score: best, best_score = pos, s
    for pos, sc in his.items():
        s = sc + my.get(pos, 0)
        if s > best_score: best, best_score = pos, s
    return best

def ai_take_turn(pan, state, move_labels):
    me = state['pid']
    opp = RED if me == BLUE else BLUE

    # 1) immediate win
    my = important(pan, me)
    if has_critical(my):
        cands = [pos for pos, sc in my.items() if sc >= BIG and pan[pos[0]][pos[1]] == EMPTY]
        if cands:
            x, y = cands[0]
            pan[x][y] = me
            state['move_no'] += 1
            move_labels[(x, y)] = (str(state['move_no']), me)
            state['quads_left'][me] -= 1            # consume quad
            return

    # 2) block opponent + place stone
    his = important(pan, opp)
    b, q_list = chk_attack(pan, my, his, me, state['usedquasar'])
    for (qx, qy) in q_list:
        if pan[qx][qy] == EMPTY:
            pan[qx][qy] = QUASAR
            move_labels[(qx, qy)] = ("Q", QUASAR)

    if b is not None and pan[b[0]][b[1]] == EMPTY:
        x, y = b
        pan[x][y] = me
        state['move_no'] += 1
        move_labels[(x, y)] = (str(state['move_no']), me)
        state['quads_left'][me] -= 1                # consume quad
        return

    # 3) best important
    a = chk_important(my, his)
    if a and pan[a[0]][a[1]] == EMPTY:
        x, y = a
        pan[x][y] = me
        state['move_no'] += 1
        move_labels[(x, y)] = (str(state['move_no']), me)
        state['quads_left'][me] -= 1                # consume quad
        return

    # 4) random
    empties = [(i, j) for i in range(GRID_N) for j in range(GRID_N) if pan[i][j] == EMPTY]
    if empties:
        x, y = random.choice(empties)
        pan[x][y] = me
        state['move_no'] += 1
        move_labels[(x, y)] = (str(state['move_no']), me)
        state['quads_left'][me] -= 1                # consume quad

# -------------------- Menu --------------------
class Toggle:
    def __init__(self, rect, label, value=False, group=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.value = value
        self.group = group  # exclusive group key

    def draw(self, surf, font, on_color=(30,30,40), off_color=(120,120,130)):
        pygame.draw.rect(surf, (230,234,240), self.rect, border_radius=8)
        dot = pygame.Rect(0,0,16,16)
        dot.center = (self.rect.x+16, self.rect.centery)
        pygame.draw.circle(surf, (200,200,205), dot.center, 9)
        if self.value:
            pygame.draw.circle(surf, (60,60,80), dot.center, 6)
        txt = font.render(self.label, True, on_color if self.value else off_color)
        surf.blit(txt, (self.rect.x+32, self.rect.y + self.rect.height//2 - txt.get_height()//2))

    def handle(self, pos, toggles):
        if self.rect.collidepoint(pos):
            if self.group:
                for t in toggles:
                    if t.group == self.group:
                        t.value = False
            self.value = True
            return True
        return False

def make_menu(font_small, x0, y0):
    toggles = []
    modes = [
        ("Human vs Human", "HvsH"),
        ("Human vs AI",    "HvsC"),
        ("AI vs Human",    "CvsH"),
        ("AI vs AI",       "CvsC"),
    ]
    y = y0
    for idx,(label, key) in enumerate(modes):
        toggles.append(Toggle((x0, y, 200, 30), label, value=(idx==1), group="mode"))  # default HvsC
        y += 38

    y += 12
    firsts = [("Red first", "Rfirst"), ("Blue first", "Bfirst")]
    for idx,(label,key) in enumerate(firsts):
        toggles.append(Toggle((x0, y, 200, 30), label, value=(idx==0), group="first"))  # default Red first
        y += 38

    start_btn = pygame.Rect(x0, y+10, 120, 36)
    return toggles, start_btn

def read_menu(toggles):
    mode = "HvsC"
    first = RED
    for t in toggles:
        if t.group == "mode" and t.value:
            mode = t.label
        if t.group == "first" and t.value:
            first = RED if "Red" in t.label else BLUE

    if mode == "Human vs Human":
        is_human = {RED: True, BLUE: True}
    elif mode == "Human vs AI":
        is_human = {RED: True, BLUE: False}
    elif mode == "AI vs Human":
        is_human = {RED: False, BLUE: True}
    else:  # AI vs AI
        is_human = {RED: False, BLUE: False}
    return is_human, first

# -------------------- Panel --------------------
def draw_panel(surface, font_small, font_big, state):
    panel_rect = pygame.Rect(MARGIN + GRID_N*CELL, 0, PANEL_W, HEIGHT)
    pygame.draw.rect(surface, PANEL_BG, panel_rect)
    x0 = panel_rect.x + 16
    y = MARGIN

    if state['mode'] == 'menu':
        title = font_big.render("QUOD — Options", True, (30,30,30))
        surface.blit(title, (x0, y)); y += 44
        tip = [
            "Choose who is Human/AI and who goes first.",
            "Left-click toggles, then press Start."
        ]
        for line in tip:
            t = font_small.render(line, True, (50,50,60))
            surface.blit(t, (x0, y)); y += 24
        return

    title = font_big.render("QUOD (2 Players)", True, (30,30,30))
    surface.blit(title, (x0, y)); y += 36

    lines = [
        f"Turn: {PLAYER_NAME[state['pid']]} {'(Human)' if state['is_human'][state['pid']] else '(AI)'}",
        f"Red Quads Left:  {state['quads_left'][RED]} / {QUODS_PER_PLAYER}",
        f"Blue Quads Left: {state['quads_left'][BLUE]} / {QUODS_PER_PLAYER}",
        f"Red Quasars:  {state['usedquasar'][RED]}/{QUASARS_PER_PLAYER}",
        f"Blue Quasars: {state['usedquasar'][BLUE]}/{QUASARS_PER_PLAYER}",
        "",
        "Controls:",
        "- Left click: place a stone",
        "- Right click: place a Quasar (no turn cost)",
    ]
    for line in lines:
        if line == "":
            y += 6
            continue
        t = font_small.render(line, True, (50,50,60))
        surface.blit(t, (x0, y)); y += 24

    if state['message']:
        y += 8
        color = ERR_CLR if state['msg_is_error'] else (40,40,40)
        for line in wrap_text(state['message'], font_small, PANEL_W-32):
            t = font_small.render(line, True, color)
            surface.blit(t, (x0, y)); y += 22

    if state['mode'] == 'gameover':
        y += 16
        win = font_big.render("Game Over", True, WIN_CLR)
        surface.blit(win, (x0, y)); y += 40
        if state['winner'] is not None:
            wtxt = font_small.render(f"Winner: {PLAYER_NAME[state['winner']]}", True, (20,100,30))
            surface.blit(wtxt, (x0, y)); y += 24
        else:
            draw = font_small.render("Result: Draw", True, (40,40,40))
            surface.blit(draw, (x0, y)); y += 24

# -------------------- Tie-break helper --------------------
def maybe_end_by_quads(state):
    """If both sides have 0 quads left and game not ended by QUOD, end by tiebreak rule."""
    if state['mode'] != 'playing':
        return
    if state['quads_left'][RED] == 0 and state['quads_left'][BLUE] == 0:
        if USE_QUASAR_TIEBREAK:
            red_rem  = QUASARS_PER_PLAYER - state['usedquasar'][RED]
            blue_rem = QUASARS_PER_PLAYER - state['usedquasar'][BLUE]
            state['mode'] = 'gameover'
            if red_rem > blue_rem:
                state['winner'] = RED
                state['message'] = "Both ran out of quads. Red has more quasars left. Red wins!"
            elif blue_rem > red_rem:
                state['winner'] = BLUE
                state['message'] = "Both ran out of quads. Blue has more quasars left. Blue wins!"
            else:
                state['winner'] = None
                state['message'] = "Both ran out of quads. Quasars left are equal. Draw."
        else:
            state['mode'] = 'gameover'
            state['winner'] = None
            state['message'] = "Both ran out of quads. Tie-break is OFF. Draw."

# -------------------- Main --------------------
def main():
    pygame.init()
    pygame.display.set_caption("QUOD (2P: Human/AI selector)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    font_lbl = pygame.font.SysFont(None, 22)
    font_num = pygame.font.SysFont(None, 22)
    font_small = pygame.font.SysFont(None, 22)
    font_big = pygame.font.SysFont(None, 28)

    pan = init_board()
    move_labels = {}
    for (i, j) in [(0,0),(GRID_N-1,0),(0,GRID_N-1),(GRID_N-1,GRID_N-1)]:
        move_labels[(i,j)] = ("Q", QUASAR)

    state = {
        'mode': 'menu',                 # 'menu' | 'playing' | 'gameover'
        'pid': RED,
        'is_human': {RED: True, BLUE: False},
        'usedquasar': {RED: 0, BLUE: 0},
        'quads_left': {RED: QUODS_PER_PLAYER, BLUE: QUODS_PER_PLAYER},  # NEW
        'message': "",
        'msg_is_error': False,
        'winner': None,
        'move_no': 0,
        'ai_cooldown': 0,
    }

    # ---- Menu widgets (lowered) ----
    menu_x = MARGIN + GRID_N*CELL + 16
    menu_y = HEIGHT // 2 - 40
    toggles, start_btn = make_menu(font_small, menu_x, menu_y)

    running = True
    hover = None

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # MENU
            if state['mode'] == 'menu':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    for t in toggles:
                        t.handle(pos, toggles)
                    if start_btn.collidepoint(pos):
                        state['is_human'], first = read_menu(toggles)
                        state['pid'] = first
                        state['mode'] = 'playing'
                        state['message'] = "Game started."
                        pan[:] = init_board()
                        move_labels.clear()
                        for (i, j) in [(0,0),(GRID_N-1,0),(0,GRID_N-1),(GRID_N-1,GRID_N-1)]:
                            move_labels[(i,j)] = ("Q", QUASAR)
                        state['usedquasar'] = {RED: 0, BLUE: 0}
                        state['quads_left']  = {RED: QUODS_PER_PLAYER, BLUE: QUODS_PER_PLAYER}  # reset
                        state['winner'] = None
                        state['move_no'] = 0
                        state['ai_cooldown'] = 0
                continue

            # PLAYING
            if state['mode'] == 'playing':
                if event.type == pygame.MOUSEMOTION:
                    hover = colrow_from_pos(event.pos)

                if state['is_human'][state['pid']]:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                        cell = colrow_from_pos(event.pos)
                        if cell is None: continue
                        i, j = cell
                        if pan[i][j] != EMPTY:
                            state['message'] = "That cell is already occupied."
                            state['msg_is_error'] = True
                            continue
                        if event.button == 3:
                            # Quasar
                            if state['usedquasar'][state['pid']] >= QUASARS_PER_PLAYER:
                                state['message'] = "No quasars left."
                                state['msg_is_error'] = True
                                continue
                            pan[i][j] = QUASAR
                            move_labels[(i, j)] = ("Q", QUASAR)
                            state['usedquasar'][state['pid']] += 1
                            state['message'] = "Quasar placed. Your turn continues."
                            state['msg_is_error'] = False
                        else:
                            # Place quad (stone)
                            pan[i][j] = state['pid']
                            state['move_no'] += 1
                            move_labels[(i, j)] = (str(state['move_no']), state['pid'])
                            state['quads_left'][state['pid']] -= 1  # consume quad

                            # Win by QUOD?
                            if count4gon(pan, state['pid']) >= 1:
                                state['mode'] = 'gameover'
                                state['winner'] = state['pid']
                                state['message'] = f"{PLAYER_NAME[state['pid']]} wins!"
                                state['msg_is_error'] = False
                            else:
                                # Maybe end by quads?
                                maybe_end_by_quads(state)
                                if state['mode'] == 'playing':
                                    state['pid'] = BLUE if state['pid'] == RED else RED
                                    state['message'] = ""
                                    state['ai_cooldown'] = 0

        # AI TURN
        if state['mode'] == 'playing' and not state['is_human'][state['pid']]:
            state['ai_cooldown'] += 1
            if state['ai_cooldown'] >= 8:
                ai_take_turn(pan, state, move_labels)
                # Win by QUOD?
                if count4gon(pan, state['pid']) >= 1:
                    state['mode'] = 'gameover'
                    state['winner'] = state['pid']
                    state['message'] = f"{PLAYER_NAME[state['pid']]} (AI) wins!"
                    state['msg_is_error'] = False
                else:
                    # Maybe end by quads?
                    maybe_end_by_quads(state)
                    if state['mode'] == 'playing':
                        state['pid'] = BLUE if state['pid'] == RED else RED
                        state['message'] = ""
                        state['ai_cooldown'] = 0

        # RENDER
        screen.fill(BG)
        draw_grid(screen, font_lbl)

        if state['mode'] == 'playing' and hover is not None and state['is_human'][state['pid']]:
            i, j = hover
            if 0 <= i < GRID_N and 0 <= j < GRID_N and pan[i][j] == EMPTY:
                r = grid_rect(i, j)
                pygame.draw.rect(screen, (210, 225, 250), r, 3, border_radius=6)

        for i in range(GRID_N):
            for j in range(GRID_N):
                v = pan[i][j]
                if v != EMPTY:
                    lab, owner = move_labels.get((i, j), ("", v))
                    if v == QUASAR: lab, owner = "Q", QUASAR
                    draw_stone(screen, i, j, lab, owner, font_num)

        for (i, j) in [(0,0),(GRID_N-1,0),(0,GRID_N-1),(GRID_N-1,GRID_N-1)]:
            pygame.draw.rect(screen, (80,80,80), grid_rect(i, j), 2, border_radius=6)

        draw_panel(screen, font_small, font_big, state)

        if state['mode'] == 'menu':
            for t in toggles:
                t.draw(screen, font_small)
            pygame.draw.rect(screen, (230,234,240), start_btn, border_radius=8)
            txt = font_small.render("Start", True, (30,30,40))
            screen.blit(txt, (start_btn.centerx - txt.get_width()//2,
                              start_btn.centery - txt.get_height()//2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

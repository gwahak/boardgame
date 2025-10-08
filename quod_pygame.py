import pygame
import sys

# -------------------- Config --------------------
GRID_N = 11
CELL = 48         # cell size (px)
MARGIN = 48       # left/top margin around grid
PANEL_W = 260     # right status panel width
WIDTH = MARGIN*2 + GRID_N*CELL + PANEL_W
HEIGHT = MARGIN*2 + GRID_N*CELL
FPS = 60

# Player IDs: 1..6, Quasar: 7, Empty: 0
PLAYER_FILL = {
    1: (245, 245, 245),   # White
    2: (220, 40, 40),     # Red
    3: (40, 100, 220),    # Blue
    4: (245, 140, 20),    # Orange
    5: (240, 200, 0),     # Yellow/Gold
    6: (30, 160, 80),     # Green
    7: (180, 180, 180),   # Quasar
}
PLAYER_TEXT = {
    1: (20, 20, 20),
    2: (250, 250, 250),
    3: (250, 250, 250),
    4: (20, 20, 20),
    5: (20, 20, 20),
    6: (250, 250, 250),
    7: (20, 20, 20),
}
PLAYER_NAME = {
    1: "White",
    2: "Red",
    3: "Blue",
    4: "Orange",
    5: "Yellow",
    6: "Green",
    7: "Quasar",
}

# Matches original: [0,6,6,4,3,2,2] for 0..6 players (we use 2..6)
QUASARS_BY_PLAYERS = [0, 6, 6, 4, 3, 2, 2]

BG = (250, 252, 255)
GRID = (40, 40, 40)
LBL = (60, 60, 60)
PANEL_BG = (245, 247, 250)
HL = (0, 0, 0)
WIN_CLR = (10, 120, 40)
ERR_CLR = (160, 30, 30)

# -------------------- Helpers --------------------
def grid_rect(i, j):
    """Return pixel rect for cell (i,j) where i,j in [0..10]."""
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
    # grid lines
    for k in range(GRID_N + 1):
        # vertical
        x = MARGIN + k*CELL
        pygame.draw.line(surface, GRID, (x, MARGIN), (x, MARGIN + GRID_N*CELL), 1)
        # horizontal
        y = MARGIN + k*CELL
        pygame.draw.line(surface, GRID, (MARGIN, y), (MARGIN + GRID_N*CELL, y), 1)
    # axis labels A..K and 1..11
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

def drawing(surface, i, j, move_label, owner_id, font_num):
    cx, cy = cell_center(i, j)
    # stone
    pygame.draw.circle(surface, PLAYER_FILL[owner_id], (cx, cy), CELL//2 - 6)
    # outline
    pygame.draw.circle(surface, (20,20,20), (cx, cy), CELL//2 - 6, 1)
    # number / "Q"
    label = str(move_label)
    if owner_id == 7 and isinstance(move_label, str):
        label = move_label
    text = font_num.render(label, True, PLAYER_TEXT[owner_id])
    surface.blit(text, (cx - text.get_width()//2, cy - text.get_height()//2))

def count4gon(pan, n):
    """Count axis-aligned (original logic) squares whose 4 vertices are 'n'."""
    count = 0
    # Keep original nested loops/logic
    for gg in range(1, 11):
        for hh in range(gg):
            for ii in range(11-gg):
                for jj in range(11-gg):
                    try:
                        if (pan[ii][jj+hh]    == n and
                            pan[ii+hh][jj+gg] == n and
                            pan[ii+gg-hh][jj] == n and
                            pan[ii+gg][jj+gg-hh] == n):
                            count += 1
                    except IndexError:
                        # safety (shouldn't happen with bounds)
                        pass
    return count

def init_board():
    # pan[x][y] as in original (x: column, y: row)
    pan = [[0 for _ in range(GRID_N)] for _ in range(GRID_N)]
    # Four corners are Quasar(7)
    pan[0][0] = 7
    pan[GRID_N-1][0] = 7
    pan[0][GRID_N-1] = 7
    pan[GRID_N-1][GRID_N-1] = 7
    return pan

def draw_panel(surface, font_small, font_big, state):
    # Side panel background
    panel_rect = pygame.Rect(MARGIN + GRID_N*CELL, 0, PANEL_W, HEIGHT)
    pygame.draw.rect(surface, PANEL_BG, panel_rect)
    x0 = panel_rect.x + 16
    y = MARGIN

    # Title
    title = font_big.render("QUOD (Pygame)", True, (30,30,30))
    surface.blit(title, (x0, y)); y += 40

    # Status
    if state['mode'] == 'menu':
        tip = [
            "Select number of players:",
            "2 to 6 players are supported."
        ]
        for line in tip:
            t = font_small.render(line, True, (50,50,60))
            surface.blit(t, (x0, y)); y += 24
        y += 6
        # Buttons
        state['menu_buttons'] = []
        for p in range(2, 7):
            btn = pygame.Rect(x0, y, 120, 36)
            pygame.draw.rect(surface, (230,234,240), btn, border_radius=8)
            lbl = font_small.render(f"{p} Players", True, (30,30,40))
            surface.blit(lbl, (btn.centerx - lbl.get_width()//2, btn.centery - lbl.get_height()//2))
            state['menu_buttons'].append((btn, p))
            y += 48
        return

    # Playing / Game over panel
    players = state['players']
    pid = state['pid']
    qm = QUASARS_BY_PLAYERS[players]
    used = state['usedquasars'][pid]

    lines = [
        f"Players: {players}",
        f"Turn: {PLAYER_NAME[pid]}",
        f"Quasars: {used}/{qm} used",
        "",
        "Controls:",
        "- Left click: place stone",
        "- Right click: place Quasar",
        "",
        "Quasar does NOT consume the turn.",
    ]
    for line in lines:
        t = font_small.render(line, True, (50,50,60))
        surface.blit(t, (x0, y)); y += 24

    y += 8
    if state['message']:
        color = ERR_CLR if state['msg_is_error'] else (40,40,40)
        for line in wrap_text(state['message'], font_small, PANEL_W-32):
            t = font_small.render(line, True, color)
            surface.blit(t, (x0, y)); y += 22

    if state['mode'] == 'gameover':
        y += 16
        win = font_big.render("Game Over", True, WIN_CLR)
        surface.blit(win, (x0, y)); y += 40
        if state['winner']:
            wtxt = font_small.render(f"Winner: {PLAYER_NAME[state['winner']]}", True, (20,100,30))
            surface.blit(wtxt, (x0, y)); y += 24

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

# -------------------- Main --------------------
def main():
    pygame.init()
    pygame.display.set_caption("QUOD (Pygame)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    font_lbl = pygame.font.SysFont(None, 22)
    font_num = pygame.font.SysFont(None, 22)
    font_small = pygame.font.SysFont(None, 22)
    font_big = pygame.font.SysFont(None, 28)

    # State
    pan = init_board()
    usedquasars = [0]*8  # 1..6
    move_no = 0
    placed_moves = 4  # four corners already
    players = None
    pid = 1

    state = {
        'mode': 'menu',     # 'menu' | 'playing' | 'gameover'
        'players': players,
        'pid': pid,
        'usedquasars': usedquasars,
        'message': "",
        'msg_is_error': False,
        'winner': None,
        'menu_buttons': [],
    }

    # Pre-draw static background
    def redraw_all():
        screen.fill(BG)
        # Grid and labels
        draw_grid(screen, font_lbl)
        # Stones
        for i in range(GRID_N):
            for j in range(GRID_N):
                v = pan[i][j]
                if v != 0:
                    label = "Q" if v == 7 else ""  # move numbers drawn from history below
                    # For numbered stones we need stored move numbers; simplest: draw number = move index per cell
                    # We'll keep a separate move_labels dict.
        # We'll render stones using move_labels dict (populated during placements)

    # Track move labels (number or 'Q') per cell
    move_labels = {}  # (i,j) -> (label, owner_id)

    # Seed corner labels
    for (i, j) in [(0,0),(GRID_N-1,0),(0,GRID_N-1),(GRID_N-1,GRID_N-1)]:
        move_labels[(i,j)] = ("Q", 7)

    running = True
    hover = None

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Menu clicks
            if state['mode'] == 'menu' and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for btn, p in state['menu_buttons']:
                    if btn.collidepoint(pos):
                        state['players'] = p
                        players = p
                        state['pid'] = 1
                        pid = 1
                        state['mode'] = 'playing'
                        state['message'] = f"Starting QUOD for {players} players."
                        state['msg_is_error'] = False
                        break

            if state['mode'] == 'playing':
                # Hover
                if event.type == pygame.MOUSEMOTION:
                    cell = colrow_from_pos(event.pos)
                    hover = cell

                # Left click: stone, Right click: quasar
                if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                    cell = colrow_from_pos(event.pos)
                    if cell is None:
                        continue
                    i, j = cell

                    # Occupied?
                    if pan[i][j] != 0:
                        state['message'] = "That cell is already occupied."
                        state['msg_is_error'] = True
                        continue

                    if event.button == 3:
                        # Quasar placement (does not consume turn)
                        limit = QUASARS_BY_PLAYERS[players]
                        if state['usedquasars'][pid] >= limit:
                            state['message'] = "You have already used all your quasars."
                            state['msg_is_error'] = True
                            continue
                        pan[i][j] = 7
                        state['usedquasars'][pid] += 1
                        move_labels[(i, j)] = ("Q", 7)
                        placed_moves += 1
                        state['message'] = "Quasar placed. Your turn continues."
                        state['msg_is_error'] = False
                        # turn stays same
                    else:
                        # Normal stone placement
                        pan[i][j] = pid
                        move_no += 1
                        move_labels[(i, j)] = (str(move_no), pid)
                        placed_moves += 1

                        # Win check
                        if count4gon(pan, pid) >= 1:
                            state['mode'] = 'gameover'
                            state['winner'] = pid
                            state['message'] = f"{PLAYER_NAME[pid]} has formed a square and wins!"
                            state['msg_is_error'] = False
                        else:
                            # Advance turn
                            pid = (pid % players) + 1
                            state['pid'] = pid
                            state['message'] = ""
                            state['msg_is_error'] = False

                        # Board full or move cap (similar to original max players*20)
                        if placed_moves >= GRID_N*GRID_N:
                            if state['mode'] != 'gameover':
                                state['mode'] = 'gameover'
                                state['winner'] = None
                                state['message'] = "Board is full. Game over."
                                state['msg_is_error'] = False

        # ----- Render -----
        screen.fill(BG)
        # Grid and labels
        draw_grid(screen, font_lbl)

        # Draw hover highlight
        if state['mode'] == 'playing' and hover is not None:
            i, j = hover
            if 0 <= i < GRID_N and 0 <= j < GRID_N:
                r = grid_rect(i, j)
                pygame.draw.rect(screen, (210, 225, 250), r, 3, border_radius=6)

        # Draw stones (with labels)
        for i in range(GRID_N):
            for j in range(GRID_N):
                v = pan[i][j]
                if v != 0:
                    label, owner = move_labels.get((i, j), ("", v))
                    drawing(screen, i, j, label if label else str(""), owner, font_num)

        # Side panel
        draw_panel(screen, font_small, font_big, state)
        # Draw left-bottom quasar summary
        draw_quasar_status(screen, font_small, state)

        # Draw corner frames
        for (i, j) in [(0,0),(GRID_N-1,0),(0,GRID_N-1),(GRID_N-1,GRID_N-1)]:
            r = grid_rect(i, j)
            pygame.draw.rect(screen, (80,80,80), r, 2, border_radius=6)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

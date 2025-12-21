import sys
import pygame

# -----------------------------
# Game config
# -----------------------------
COLS = 19
ROWS = 19
WIN_N = 4
PLAYERS = 3  # 3-player

# Player IDs: 1..3
P_NAMES = {1: "Black", 2: "White", 3: "Red"}
P_COLORS = {1: (25, 25, 25), 2: (245, 245, 245), 3: (220, 45, 45)}
P_TEXT = {1: (245, 245, 245), 2: (25, 25, 25), 3: (245, 245, 245)}

# -----------------------------
# UI config
# -----------------------------
CELL = 32
MARGIN = 30
TOPBAR = 90
PANEL_W = 260

BOARD_W = (COLS - 1) * CELL
BOARD_H = (ROWS - 1) * CELL

W = MARGIN * 2 + BOARD_W + PANEL_W
H = MARGIN * 2 + TOPBAR + BOARD_H

FPS = 60

BG = (245, 245, 245)
BOARD_BG = (235, 210, 160)   # wood-ish
GRID = (60, 60, 60)
TEXT = (20, 20, 20)
MUTED = (90, 90, 90)

BTN_BG = (235, 235, 235)
BTN_BG_H = (220, 235, 255)
BTN_BORDER = (80, 80, 80)

HOVER_RING = (20, 20, 20)

# -----------------------------
# Helpers
# -----------------------------
def inside(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def new_board():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]

def cell_center(r, c):
    """Return screen coords (x,y) center for intersection (r,c)."""
    x0 = MARGIN
    y0 = MARGIN + TOPBAR
    x = x0 + c * CELL
    y = y0 + r * CELL
    return x, y

def rc_from_mouse(mx, my):
    """Map mouse to nearest intersection; return (r,c) or None if outside board."""
    x0 = MARGIN
    y0 = MARGIN + TOPBAR
    if mx < x0 - CELL * 0.5 or mx > x0 + BOARD_W + CELL * 0.5:
        return None
    if my < y0 - CELL * 0.5 or my > y0 + BOARD_H + CELL * 0.5:
        return None

    c = int(round((mx - x0) / CELL))
    r = int(round((my - y0) / CELL))
    if inside(r, c):
        return r, c
    return None

def coord_label(r, c):
    """Convert (r,c) -> 'A1' style, matching your original A.. and 1.."""
    # Columns: A..S (19)
    letter = chr(ord('A') + c)
    number = str(r + 1)
    return f"{letter}{number}"

def check_winner(board):
    """Return winner player id (1..3) or 0."""
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p == 0:
                continue
            for dr, dc in dirs:
                ok = True
                for k in range(1, WIN_N):
                    rr = r + dr * k
                    cc = c + dc * k
                    if not inside(rr, cc) or board[rr][cc] != p:
                        ok = False
                        break
                if ok:
                    return p
    return 0

def is_draw(board):
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 0:
                return False
    return True

# -----------------------------
# UI widgets
# -----------------------------
class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.hover = False

    def draw(self, screen):
        bg = BTN_BG_H if self.hover else BTN_BG
        pygame.draw.rect(screen, bg, self.rect, border_radius=12)
        pygame.draw.rect(screen, BTN_BORDER, self.rect, 2, border_radius=12)
        surf = self.font.render(self.label, True, TEXT)
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def handle_motion(self, pos):
        self.hover = self.rect.collidepoint(pos)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

# -----------------------------
# Drawing
# -----------------------------
def draw_board(screen):
    x0 = MARGIN
    y0 = MARGIN + TOPBAR

    # board background
    pygame.draw.rect(screen, BOARD_BG, (x0 - 18, y0 - 18, BOARD_W + 36, BOARD_H + 36), border_radius=18)

    # grid lines
    for r in range(ROWS):
        x1, y1 = cell_center(r, 0)
        x2, y2 = cell_center(r, COLS - 1)
        pygame.draw.line(screen, GRID, (x1, y1), (x2, y2), 2)

    for c in range(COLS):
        x1, y1 = cell_center(0, c)
        x2, y2 = cell_center(ROWS - 1, c)
        pygame.draw.line(screen, GRID, (x1, y1), (x2, y2), 2)

def draw_stones(screen, board, move_no_font):
    radius = int(CELL * 0.38)
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p == 0:
                continue
            cx, cy = cell_center(r, c)
            pygame.draw.circle(screen, P_COLORS[p], (cx, cy), radius)
            pygame.draw.circle(screen, (0,0,0), (cx, cy), radius, 2)

            # Move number: optional; mimic your turtle "write(i)"
            # We'll write a small number in contrasting color.
            # (Comment this out if you want it cleaner.)
            # Determine move index isn't stored; we'll skip numbering by default.

def draw_hover_hint(screen, board, hover_rc, current_player):
    if hover_rc is None:
        return
    r, c = hover_rc
    if board[r][c] != 0:
        return

    radius = int(CELL * 0.38)
    cx, cy = cell_center(r, c)

    # faint piece preview + ring
    s = pygame.Surface((radius*2+6, radius*2+6), pygame.SRCALPHA)
    pygame.draw.circle(s, (*P_COLORS[current_player], 90), (radius+3, radius+3), radius)
    screen.blit(s, (cx - radius - 3, cy - radius - 3))
    pygame.draw.circle(screen, HOVER_RING, (cx, cy), radius+2, 2)

def draw_topbar(screen, font, small, turn_player, winner, draw_flag, last_move_label):
    # top bar
    pygame.draw.rect(screen, (255,255,255), (MARGIN, MARGIN, BOARD_W, TOPBAR - 12), border_radius=16)
    pygame.draw.rect(screen, (220,220,220), (MARGIN, MARGIN, BOARD_W, TOPBAR - 12), 2, border_radius=16)

    if winner:
        msg = f"{P_NAMES[winner]} wins (4-in-a-row)!"
    elif draw_flag:
        msg = "Draw!"
    else:
        msg = f"Turn: {P_NAMES[turn_player]}"

    screen.blit(font.render(msg, True, TEXT), (MARGIN + 18, MARGIN + 16))

    if last_move_label:
        screen.blit(small.render(f"Last move: {last_move_label}", True, MUTED), (MARGIN + 18, MARGIN + 52))

    if not winner and not draw_flag:
        pygame.draw.circle(screen, P_COLORS[turn_player], (MARGIN + 52, MARGIN + 52), 14)
        pygame.draw.circle(screen, (0,0,0), (MARGIN + 52, MARGIN + 52), 14, 2)

def draw_side_panel(screen, font, small, turn_player, winner, draw_flag, moves_played):
    px = MARGIN * 2 + BOARD_W
    py = MARGIN

    pygame.draw.rect(screen, (255,255,255), (px, py, PANEL_W, H - 2*MARGIN), border_radius=16)
    pygame.draw.rect(screen, (210,210,210), (px, py, PANEL_W, H - 2*MARGIN), 2, border_radius=16)
    
    y = py + 18
    screen.blit(font.render("Saminsamok", True, TEXT), (px + 18, y))
    y += 30
    screen.blit(font.render("(3-Player Gomoku)", True, TEXT), (px + 18, y))
    y += 42

    screen.blit(small.render(f"Board: {COLS} x {ROWS}", True, MUTED), (px + 18, y)); y += 26
    screen.blit(small.render(f"Win: {WIN_N}-in-a-row", True, MUTED), (px + 18, y)); y += 26
    screen.blit(small.render(f"Moves: {moves_played}", True, MUTED), (px + 18, y)); y += 30

    if winner:
        screen.blit(font.render(f"Winner: {P_NAMES[winner]}", True, TEXT), (px + 18, y))
        y += 44
    elif draw_flag:
        screen.blit(font.render("Draw!", True, TEXT), (px + 18, y))
        y += 44
    else:
        screen.blit(font.render(f"Turn: {P_NAMES[turn_player]}", True, TEXT), (px + 18, y))
        y += 60

# -----------------------------
# Main
# -----------------------------
def main():
    pygame.init()
    pygame.display.set_caption("3-Player Gomoku (4) - Pygame Port")
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Segoe UI", 26, bold=True)
    small = pygame.font.SysFont("Segoe UI", 18)
    big = pygame.font.SysFont("Segoe UI", 42, bold=True)

    # Menu buttons
    btn_start = Button((W//2 - 160, H//2 - 20, 320, 64), "Start Game", font)

    # In-game buttons
    restart_btn = Button((MARGIN*2 + BOARD_W + 30, H - MARGIN - 120, PANEL_W - 60, 48), "Restart", font)
    newgame_btn = Button((MARGIN*2 + BOARD_W + 30, H - MARGIN - 60,  PANEL_W - 60, 48), "New Game", font)

    state = "menu"  # menu | game
    board = new_board()
    turn_player = 1
    winner = 0
    draw_flag = False
    hover_rc = None
    moves_played = 0
    last_move_label = ""

    def reset_game(to_menu=False):
        nonlocal board, turn_player, winner, draw_flag, hover_rc, moves_played, last_move_label, state
        board = new_board()
        turn_player = 1
        winner = 0
        draw_flag = False
        hover_rc = None
        moves_played = 0
        last_move_label = ""
        if to_menu:
            state = "menu"

    running = True
    while running:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()

        if state == "menu":
            btn_start.handle_motion((mx, my))
        else:
            restart_btn.handle_motion((mx, my))
            newgame_btn.handle_motion((mx, my))
            hover_rc = rc_from_mouse(mx, my)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                break

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if state == "menu":
                    if btn_start.clicked((mx, my)):
                        state = "game"
                        reset_game(to_menu=False)

                else:
                    # Buttons
                    if restart_btn.clicked((mx, my)):
                        reset_game(to_menu=False)
                        continue
                    if newgame_btn.clicked((mx, my)):
                        reset_game(to_menu=True)
                        continue

                    if winner or draw_flag:
                        continue

                    rc = rc_from_mouse(mx, my)
                    if rc is None:
                        continue
                    r, c = rc
                    if board[r][c] != 0:
                        continue

                    board[r][c] = turn_player
                    moves_played += 1
                    last_move_label = coord_label(r, c)

                    w = check_winner(board)
                    if w:
                        winner = w
                    elif is_draw(board):
                        draw_flag = True
                    else:
                        turn_player += 1
                        if turn_player > PLAYERS:
                            turn_player = 1

        # Draw
        screen.fill(BG)

        if state == "menu":
            title = big.render("3-Player Gomoku (4)", True, TEXT)
            screen.blit(title, title.get_rect(center=(W//2, H//2 - 110)))

            subtitle = small.render("Click Start, then click an intersection to place a stone.", True, MUTED)
            screen.blit(subtitle, subtitle.get_rect(center=(W//2, H//2 - 70)))

            btn_start.draw(screen)

            note = small.render("Players: Black → White → Red. First to make 4-in-a-row wins.", True, MUTED)
            screen.blit(note, note.get_rect(center=(W//2, H//2 + 90)))

        else:
            draw_topbar(screen, font, small, turn_player, winner, draw_flag, last_move_label)
            draw_board(screen)
            draw_stones(screen, board, small)
            draw_hover_hint(screen, board, hover_rc, turn_player)
            draw_side_panel(screen, font, small, turn_player, winner, draw_flag, moves_played)

            restart_btn.draw(screen)
            newgame_btn.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

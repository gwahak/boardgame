import sys
import pygame

# -----------------------------
# Config
# -----------------------------
BOARD_N = 8
CELL = 80
MARGIN = 40
WIDTH = HEIGHT = BOARD_N * CELL + MARGIN * 2
FPS = 60

EMPTY = 0
RED   = 1
YELLOW= 2
GREEN = 3
BLUE  = 4

ALL_COLORS = {RED, YELLOW, GREEN, BLUE}
COLOR_ORDER = [RED, YELLOW, GREEN, BLUE]
COLOR_NAME  = {RED:"Red", YELLOW:"Yellow", GREEN:"Green", BLUE:"Blue"}
STONE_RGB   = {
    RED:   (220, 20, 60),
    YELLOW:(255, 215, 0),
    GREEN: (34, 139, 34),
    BLUE:  (30, 144, 255),
}

BG_COLOR = (240, 240, 240)
GRID_COLOR = (90, 90, 90)
HINT_COLOR = (148, 0, 211)      # violet for legal move with flips (요청 반영)
HINT_ANY_COLOR = (160, 160, 160) # anywhere/no-flip hint (회색)
LASTMOVE_COLOR = (255, 215, 0)

# 8 directions
DIRS = [(-1,-1), (-1,0), (-1,1),
        ( 0,-1),         ( 0,1),
        ( 1,-1), ( 1,0), ( 1,1)]

# -----------------------------
# Helpers
# -----------------------------
def to_screen(rc):
    r, c = rc
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return x, y

def from_mouse(pos):
    mx, my = pos
    if mx < MARGIN or my < MARGIN:
        return None
    c = (mx - MARGIN) // CELL
    r = (my - MARGIN) // CELL
    if 0 <= r < BOARD_N and 0 <= c < BOARD_N:
        return int(r), int(c)
    return None

def inside(r, c):
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N

def init_board():
    """Standard 2x2 center occupied by R/Y/G/B (all flippable)."""
    board = [[EMPTY for _ in range(BOARD_N)] for _ in range(BOARD_N)]
    mid = BOARD_N // 2
    board[mid-1][mid-1] = RED
    board[mid-1][mid]   = YELLOW
    board[mid][mid-1]   = BLUE
    board[mid][mid]     = GREEN
    return board

def anywhere_moves(board):
    """Return dict of all empty cells as no-flip moves."""
    return {(r, c): [] for r in range(BOARD_N) for c in range(BOARD_N) if board[r][c] == EMPTY}

# -----------------------------
# Simple UI Button
# -----------------------------
class Button:
    def __init__(self, rect, label, base_color, text_color=(0,0,0), toggle=False, on_color=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.base_color = base_color
        self.on_color = on_color if on_color else base_color
        self.text_color = text_color
        self.toggle = toggle
        self.is_on = False
        self.enabled = True

    def draw(self, surface, font):
        color = self.on_color if (self.toggle and self.is_on) else self.base_color
        if not self.enabled:
            color = tuple(int(c*0.6) for c in color)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (30,30,30), self.rect, 2, border_radius=8)
        text = font.render(self.label, True, self.text_color)
        tr = text.get_rect(center=self.rect.center)
        surface.blit(text, tr)

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.is_on = not self.is_on
                return True
        return False

# -----------------------------
# Start menu with buttons
# -----------------------------
def choose_players(screen, clock):
    font = pygame.font.SysFont(None, 26)
    big  = pygame.font.SysFont(None, 40)

    # Player count buttons (left)
    btn2 = Button((60, 80, 70, 40), "2", (220,220,220), toggle=True)
    btn3 = Button((140, 80, 70, 40), "3", (220,220,220), toggle=True)
    btn4 = Button((220, 80, 70, 40), "4", (220,220,220), toggle=True)
    count_buttons = [btn2, btn3, btn4]

    # Color toggle buttons (center)
    btnR = Button((120, 180, 90, 60), "R", STONE_RGB[RED], (255,255,255), toggle=True, on_color=STONE_RGB[RED])
    btnY = Button((230, 180, 90, 60), "Y", STONE_RGB[YELLOW], (0,0,0), toggle=True, on_color=STONE_RGB[YELLOW])
    btnG = Button((340, 180, 90, 60), "G", STONE_RGB[GREEN], (255,255,255), toggle=True, on_color=STONE_RGB[GREEN])
    btnB = Button((450, 180, 90, 60), "B", STONE_RGB[BLUE], (255,255,255), toggle=True, on_color=STONE_RGB[BLUE])
    color_buttons = [(RED, btnR), (YELLOW, btnY), (GREEN, btnG), (BLUE, btnB)]

    # Anywhere-drop toggle (bottom)
    btnAny = Button((120, 270, 300, 44), "Anywhere drop: OFF", (210,210,210), (0,0,0), toggle=True)

    # Start button (right)
    btnStart = Button((480, 80, 140, 50), "Start", (0, 170, 90), (255,255,255))

    # Defaults: 2 players (R,Y)
    btn2.is_on = True
    btnR.is_on = True
    btnY.is_on = True

    def current_selected_colors():
        return {col for col, b in color_buttons if b.is_on}

    def current_players_count():
        if btn2.is_on: return 2
        if btn3.is_on: return 3
        if btn4.is_on: return 4
        return None

    def sync_count_exclusive(clicked):
        for b in count_buttons:
            b.is_on = (b is clicked)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit(0)

            # handle buttons
            if btn2.handle_event(e):
                sync_count_exclusive(btn2)
                # 자동 색 변경 없음 (원하시면 여기서 2개만 남기도록 조정 가능)

            if btn3.handle_event(e):
                sync_count_exclusive(btn3)
                # 자동 색 변경 없음

            if btn4.handle_event(e):
                sync_count_exclusive(btn4)
                # ★ 4명 선택 시 R/Y/G/B 자동 ON (요청 반영)
                if btn4.is_on:
                    for _, b in color_buttons:
                        b.is_on = True

            for _, b in color_buttons:
                b.handle_event(e)

            if btnAny.handle_event(e):
                btnAny.label = "Anywhere drop: ON" if btnAny.is_on else "Anywhere drop: OFF"

            if btnStart.handle_event(e):
                players_count = current_players_count()
                selected = current_selected_colors()
                if players_count is not None and len(selected) == players_count:
                    return selected, btnAny.is_on

        # compute Start enabled
        players_count = current_players_count()
        selected = current_selected_colors()
        btnStart.enabled = (players_count is not None and len(selected) == players_count)

        # draw
        screen.fill((245, 248, 255))
        screen.blit(big.render("Rolit Setup", True, (20,20,40)), (60, 25))
        # Left
        screen.blit(font.render("Players:", True, (30,30,30)), (60, 56))
        for b in count_buttons: b.draw(screen, font)
        # Center colors
        screen.blit(font.render("Select colors (toggle):", True, (30,30,30)), (120, 156))
        for _, b in color_buttons: b.draw(screen, big)
        # Anywhere toggle
        btnAny.draw(screen, font)
        screen.blit(font.render("ESC: Quit", True, (100,100,120)), (60, 330))
        # Right start
        screen.blit(font.render("Start when count = selected", True, (40,120,40)), (430, 56))
        btnStart.draw(screen, font)
        # status
        sel_names = ", ".join(COLOR_NAME[c] for c in COLOR_ORDER if c in selected) or "(none)"
        screen.blit(font.render(f"Selected: {sel_names}", True, (30,30,30)), (120, 235))
        screen.blit(font.render(f"Count: {players_count if players_count else '-'} | Selected: {len(selected)}", True, (30,30,30)), (120, 255))

        pygame.display.flip()
        clock.tick(FPS)

# -----------------------------
# Rolit rules
# -----------------------------
def find_flips(board, r, c, player):
    """Return list of stones to flip for a placement by 'player'.
       Opponents = EVERY other color (active or not).
    """
    if not inside(r, c) or board[r][c] != EMPTY:
        return []

    opponents = ALL_COLORS - {player}
    flips_total = []

    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        if not inside(rr, cc) or board[rr][cc] not in opponents:
            continue
        while inside(rr, cc) and board[rr][cc] in opponents:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if inside(rr, cc) and board[rr][cc] == player and line:
            flips_total.extend(line)

    return flips_total

def legal_moves(board, player, anywhere_drop):
    """Return dict {(r,c): flips}. If anywhere_drop=True, add all empties as no-flip moves."""
    moves = {}
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            flips = find_flips(board, r, c, player)
            if flips:
                moves[(r, c)] = flips
    if anywhere_drop:
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                if board[r][c] == EMPTY:
                    moves.setdefault((r, c), [])
    return moves

def apply_move(board, r, c, player, flips):
    board[r][c] = player
    for rr, cc in flips:
        board[rr][cc] = player

def board_full(board):
    return all(board[r][c] != EMPTY for r in range(BOARD_N) for c in range(BOARD_N))

def scores_by_color(board):
    counts = {col:0 for col in COLOR_ORDER}
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            v = board[r][c]
            if v in counts:
                counts[v] += 1
    return counts

def next_active_player(cur, active_players):
    idx = COLOR_ORDER.index(cur)
    for k in range(1, 5):
        nxt = COLOR_ORDER[(idx + k) % 4]
        if nxt in active_players:
            return nxt
    return cur

# -----------------------------
# Drawing
# -----------------------------
def draw_board(screen, font, small_font, board, current, hints, last_move, msg,
               active_players, anywhere_drop):
    screen.fill(BG_COLOR)

    # grid & stones
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            x, y = to_screen((r, c))
            rect = pygame.Rect(x, y, CELL, CELL)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)

            v = board[r][c]
            if v != EMPTY:
                cx, cy = x + CELL // 2, y + CELL // 2
                radius = CELL // 2 - 8
                col = STONE_RGB.get(v, (0,0,0))
                pygame.draw.circle(screen, col, (cx, cy), radius)
                pygame.draw.circle(screen, (0,0,0), (cx, cy), radius, 1)

    # last move highlight
    if last_move is not None:
        r, c = last_move
        x, y = to_screen((r, c))
        pygame.draw.rect(screen, LASTMOVE_COLOR, (x+3, y+3, CELL-6, CELL-6), 3)

    # hints: violet for flips, gray for no-flip
    for (r, c), flips in hints.items():
        x, y = to_screen((r, c))
        cx, cy = x + CELL // 2, y + CELL // 2
        if flips:
            pygame.draw.circle(screen, HINT_COLOR, (cx, cy), 6)     # violet
        else:
            pygame.draw.circle(screen, HINT_ANY_COLOR, (cx, cy), 4) # gray

    # HUD
    counts = scores_by_color(board)
    score_text = " | ".join(f"{COLOR_NAME[col]} {counts[col]}" for col in COLOR_ORDER if col in active_players)
    hud1 = font.render(f"Turn: {COLOR_NAME[current]}   Scores: {score_text}", True, (10,10,10))
    hud2 = small_font.render("Click to place.  R: Restart   ESC: Quit", True, (40,40,40))
    hud3 = small_font.render(f"Anywhere-drop option: {'ON' if anywhere_drop else 'OFF'}", True, (80,80,80))
    screen.blit(hud1, (MARGIN, 8))
    screen.blit(hud2, (MARGIN, 34))
    screen.blit(hud3, (MARGIN, 56))

    if msg:
        hud4 = font.render(msg, True, (180, 30, 30))
        screen.blit(hud4, (MARGIN, HEIGHT - 40))

# -----------------------------
# Main
# -----------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Rolit (4-player Reversi variant)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    small_font = pygame.font.SysFont(None, 22)

    # Setup
    board = init_board()
    active_players, anywhere_drop = choose_players(screen, clock)

    # current = first active in fixed order
    current = next(p for p in COLOR_ORDER if p in active_players)

    # initial hints (기본 규칙: flips 우선, 없으면 anywhere 허용)
    hints = legal_moves(board, current, anywhere_drop)
    msg = ""
    if not hints:
        hints = anywhere_moves(board)
        msg = "No legal flips: you may place anywhere."

    last_move = None
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
                if event.key == pygame.K_r:
                    # restart & re-config
                    board = init_board()
                    active_players, anywhere_drop = choose_players(screen, clock)
                    current = next(p for p in COLOR_ORDER if p in active_players)
                    hints = legal_moves(board, current, anywhere_drop)
                    msg = ""
                    if not hints:
                        hints = anywhere_moves(board)
                        msg = "No legal flips: you may place anywhere."
                    last_move = None
                    game_over = False

            if game_over:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sel = from_mouse(event.pos)
                if sel is None:
                    continue
                r, c = sel
                if (r, c) in hints:
                    flips = hints[(r, c)]
                    apply_move(board, r, c, current, flips)
                    last_move = (r, c)

                    # next player
                    current = next_active_player(current, active_players)

                    # recompute hints
                    hints = legal_moves(board, current, anywhere_drop)
                    msg = ""
                    if not hints:
                        hints = anywhere_moves(board)
                        if hints:
                            msg = "No legal flips: you may place anywhere."

                    # end when board is full
                    if board_full(board):
                        counts = scores_by_color(board)
                        active_counts = {col: counts[col] for col in active_players}
                        best = max(active_counts.values())
                        winners = [COLOR_NAME[c] for c, v in active_counts.items() if v == best]
                        msg = "Game Over! " + (f"Winner: {winners[0]} (score {best})" if len(winners)==1
                                               else "Joint winners: " + ", ".join(winners))
                        game_over = True
                else:
                    msg = "Illegal move."

        draw_board(screen, font, small_font, board, current, hints, last_move, msg,
                   active_players, anywhere_drop)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()

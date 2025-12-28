import pygame
from dataclasses import dataclass

# =========================
# Config
# =========================
W, H = 1000, 700
FPS = 60

GRID = 7
CELL = 70
MARGIN = 40
BOARD_X = MARGIN
BOARD_Y = MARGIN

PANEL_X = BOARD_X + GRID * CELL + 40
PANEL_Y = BOARD_Y
PANEL_W = W - PANEL_X - 20
PANEL_H = H - PANEL_Y - 20

N = 99          # Totem
BLOCKED = -N    # Unusable cell

# Value-symbol mapping (UI only)
SYMBOLS = {1: "=", 2: "O", 3: "Y", 4: "X"}

DIRS8 = [(-1, -1), (-1, 0), (-1, 1),
         (0, -1),           (0, 1),
         (1, -1),  (1, 0),  (1, 1)]

# =========================
# Mask (your 7x7)
# xxoooxx
# xooooox
# ooooooo
# ooooooo
# ooooooo
# xooooox
# xxoooxx
# =========================
MASK = [
    "xxoooxx",
    "xooooox",
    "ooooooo",
    "ooooooo",
    "ooooooo",
    "xooooox",
    "xxoooxx",
]

def in_bounds(r, c):
    return 0 <= r < GRID and 0 <= c < GRID

def is_blocked(v): return v == BLOCKED
def is_empty(v): return v == 0
def is_totem(v): return v == N
def is_piece(v): return 1 <= abs(v) <= 4
def piece_owner(v):
    # returns +1 for White, -1 for Red (only valid if is_piece)
    return 1 if v > 0 else -1

# =========================
# UI helpers
# =========================
@dataclass
class Button:
    rect: pygame.Rect
    label: str
    value: int  # piece value 1..4
    def draw(self, surf, font, enabled=True, selected=False):
        pygame.draw.rect(surf, (230,230,230) if enabled else (180,180,180), self.rect, border_radius=10)
        if selected:
            pygame.draw.rect(surf, (40,120,255), self.rect, width=3, border_radius=10)
        else:
            pygame.draw.rect(surf, (90,90,90), self.rect, width=2, border_radius=10)
        txt = font.render(self.label, True, (0,0,0))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

# =========================
# Game
# =========================
class YoxiiGame:
    def __init__(self):
        self.board = [[0]*GRID for _ in range(GRID)]
        for r in range(GRID):
            for c in range(GRID):
                if MASK[r][c] == 'x':
                    self.board[r][c] = BLOCKED

        # Totem starts at center square (3,3) which is usable in your mask
        self.totem = (3, 3)
        tr, tc = self.totem
        self.board[tr][tc] = N

        # Turn: +1 = White, -1 = Red (White first)
        self.turn = +1

        # Stocks: per player sign -> dict value -> count
        self.stock = {
            +1: {1: 5, 2: 5, 3: 5, 4: 3},
            -1: {1: 5, 2: 5, 3: 5, 4: 3},
        }

        # Selected piece value (1..4) or None
        self.selected_value = None

        # Phase: "MOVE_TOTEM", "PLACE_PIECE", "GAME_OVER"
        self.phase = "MOVE_TOTEM"

        # Cached legal moves
        self.legal_t_moves = set()
        self.legal_p_cells = set()

        # End / score
        self.game_over = False
        self.final_score = None  # (white_sum, red_sum, white_adj_count, red_adj_count)

        self.recompute_legals()

    def recompute_legals(self):
        if self.phase == "MOVE_TOTEM":
            self.legal_t_moves = self.legal_totem_moves(self.turn)
            self.legal_p_cells = set()
            if not self.legal_t_moves:
                self.end_game()
        elif self.phase == "PLACE_PIECE":
            self.legal_t_moves = set()
            self.legal_p_cells = self.legal_place_cells()
        else:
            self.legal_t_moves = set()
            self.legal_p_cells = set()

    def end_game(self):
        self.phase = "GAME_OVER"
        self.game_over = True
        self.final_score = self.compute_final_score()

    def compute_final_score(self):
        tr, tc = self.totem
        white_sum = red_sum = 0
        white_n = red_n = 0
        for dr, dc in DIRS8:
            rr, cc = tr + dr, tc + dc
            if not in_bounds(rr, cc): 
                continue
            v = self.board[rr][cc]
            if is_blocked(v) or is_totem(v) or is_empty(v):
                continue
            if is_piece(v):
                if v > 0:
                    white_sum += abs(v); white_n += 1
                else:
                    red_sum += abs(v); red_n += 1
        return (white_sum, red_sum, white_n, red_n)

    def legal_totem_moves(self, player_sign):
        """Return set of (r,c) where Totem can move this turn."""
        tr, tc = self.totem
        moves = set()

        for dr, dc in DIRS8:
            r, c = tr + dr, tc + dc
            if not in_bounds(r, c): 
                continue
            v = self.board[r][c]
            if is_blocked(v):
                continue

            # Adjacent empty
            if is_empty(v):
                moves.add((r, c))
                continue

            # Adjacent is opponent piece -> cannot jump over opponent
            if is_piece(v) and piece_owner(v) != player_sign:
                continue

            # Adjacent is totem shouldn't happen; blocked already handled

            # Jump line over own pieces to an empty cell
            # Condition: there is a continuous line of own pieces (>=1) then an empty cell.
            if is_piece(v) and piece_owner(v) == player_sign:
                rr, cc = r, c
                # consume continuous own pieces
                while True:
                    rr2, cc2 = rr + dr, cc + dc
                    if not in_bounds(rr2, cc2):
                        break
                    vv = self.board[rr2][cc2]
                    if is_blocked(vv):
                        break
                    if is_piece(vv) and piece_owner(vv) == player_sign:
                        rr, cc = rr2, cc2
                        continue
                    # cannot jump over opponent piece
                    if is_piece(vv) and piece_owner(vv) != player_sign:
                        break
                    # empty => landing square
                    if is_empty(vv):
                        moves.add((rr2, cc2))
                    break

        return moves

    def legal_place_cells(self):
        """After Totem moved, return placeable cells for current player."""
        tr, tc = self.totem
        around = []
        for dr, dc in DIRS8:
            r, c = tr + dr, tc + dc
            if not in_bounds(r, c): 
                continue
            v = self.board[r][c]
            if is_blocked(v) or is_totem(v):
                continue
            around.append((r, c, v))

        empties = {(r, c) for (r, c, v) in around if is_empty(v)}
        if empties:
            return empties

        # SPECIAL CASE: no empty squares around Totem (among usable adjacent squares)
        all_empty = set()
        for r in range(GRID):
            for c in range(GRID):
                v = self.board[r][c]
                if is_empty(v):  # only real empty playable squares; blocked excluded already
                    all_empty.add((r, c))
        return all_empty

    def move_totem_to(self, r, c):
        # assume legal
        tr, tc = self.totem
        self.board[tr][tc] = 0
        self.totem = (r, c)
        self.board[r][c] = N
        self.phase = "PLACE_PIECE"
        self.recompute_legals()

    def place_piece_at(self, r, c):
        if self.selected_value is None:
            return  # require explicit selection
        if self.stock[self.turn][self.selected_value] <= 0:
            self.selected_value = None
            return
        # place
        self.board[r][c] = self.turn * self.selected_value
        self.stock[self.turn][self.selected_value] -= 1
        if self.stock[self.turn][self.selected_value] == 0:
            self.selected_value = None

        # next turn
        self.turn *= -1
        self.phase = "MOVE_TOTEM"
        self.recompute_legals()

    def click_cell(self, r, c):
        if self.phase == "GAME_OVER":
            return
        if not in_bounds(r, c):
            return
        v = self.board[r][c]
        if is_blocked(v):
            return

        if self.phase == "MOVE_TOTEM":
            if (r, c) in self.legal_t_moves:
                self.move_totem_to(r, c)
        elif self.phase == "PLACE_PIECE":
            if (r, c) in self.legal_p_cells and is_empty(v):
                self.place_piece_at(r, c)

# =========================
# Rendering
# =========================
def cell_rect(r, c):
    return pygame.Rect(BOARD_X + c*CELL, BOARD_Y + r*CELL, CELL, CELL)

def draw_board(screen, font, game: YoxiiGame):
    # Board background
    pygame.draw.rect(screen, (245,245,245), (BOARD_X-8, BOARD_Y-8, GRID*CELL+16, GRID*CELL+16), border_radius=12)
    pygame.draw.rect(screen, (120,120,120), (BOARD_X-8, BOARD_Y-8, GRID*CELL+16, GRID*CELL+16), width=2, border_radius=12)

    for r in range(GRID):
        for c in range(GRID):
            rect = cell_rect(r, c)
            v = game.board[r][c]

            if is_blocked(v):
                pygame.draw.rect(screen, (60,60,60), rect)
                pygame.draw.rect(screen, (30,30,30), rect, width=1)
                continue

            # highlight legal squares
            if game.phase == "MOVE_TOTEM" and (r,c) in game.legal_t_moves:
                pygame.draw.rect(screen, (220,250,220), rect)
            elif game.phase == "PLACE_PIECE" and (r,c) in game.legal_p_cells:
                pygame.draw.rect(screen, (250,230,210), rect)
            else:
                pygame.draw.rect(screen, (235,235,235), rect)

            pygame.draw.rect(screen, (180,180,180), rect, width=1)

            # draw contents
            if is_totem(v):
                # Totem as circle
                draw_totem(screen, rect.center, CELL)
            elif is_piece(v):
                owner = piece_owner(v)
                val = abs(v)
                color = (245,245,245) if owner == +1 else (210,60,60)
                edge = (0,0,0)
                pygame.draw.circle(screen, color, rect.center, CELL//3)
                pygame.draw.circle(screen, edge, rect.center, CELL//3, width=2)
                label = SYMBOLS[val]
                t = font.render(label, True, (0,0,0) if owner == +1 else (255,255,255))
                screen.blit(t, t.get_rect(center=rect.center))
def draw_totem(surface, center, cell_size):
    """
    Draw Yoxii-style neutral Totem:
    yellow ring + green inner disc
    """
    R = cell_size // 3

    # outer yellow ring
    pygame.draw.circle(
        surface,
        (230, 200, 40),   # yellow / gold
        center,
        R,
        width=4
    )

    # inner green disc
    pygame.draw.circle(
        surface,
        (60, 170, 80),    # green
        center,
        R - 8
    )

    # thin dark outline (optional, for contrast)
    pygame.draw.circle(
        surface,
        (40, 40, 40),
        center,
        R,
        width=1
    )

def draw_panel(screen, font, small_font, game: YoxiiGame, buttons):
    # panel frame
    pygame.draw.rect(screen, (248,248,248), (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), border_radius=12)
    pygame.draw.rect(screen, (140,140,140), (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), width=2, border_radius=12)

    # Turn info
    turn_name = "WHITE(+)" if game.turn == +1 else "RED(-)"
    phase = game.phase
    title = font.render(f"Turn: {turn_name}", True, (0,0,0))
    screen.blit(title, (PANEL_X + 16, PANEL_Y + 14))

    phase_txt = small_font.render(f"Phase: {phase}", True, (0,0,0))
    screen.blit(phase_txt, (PANEL_X + 16, PANEL_Y + 52))

    hint = ""
    if game.phase == "MOVE_TOTEM":
        hint = "Click a highlighted cell to move Totem."
    elif game.phase == "PLACE_PIECE":
        hint = "Select a piece, then click a highlighted empty cell."
        if game.selected_value is None:
            hint += " (No piece selected)"
    elif game.phase == "GAME_OVER":
        hint = "Game Over."
    hint_txt = small_font.render(hint, True, (20,20,20))
    screen.blit(hint_txt, (PANEL_X + 16, PANEL_Y + 78))

    # Buttons + stock
    y0 = PANEL_Y + 120
    lab = small_font.render("Select piece (value):", True, (0,0,0))
    screen.blit(lab, (PANEL_X + 16, y0 - 28))

    for b in buttons:
        v = b.value
        cnt = game.stock[game.turn][v]
        enabled = cnt > 0 and game.phase in ("MOVE_TOTEM", "PLACE_PIECE")
        selected = (game.selected_value == v)
        b.draw(screen, font, enabled=enabled, selected=selected)
        cnt_txt = small_font.render(f"x{cnt}", True, (0,0,0))
        screen.blit(cnt_txt, (b.rect.right + 10, b.rect.centery - 10))

    # Final score
    if game.game_over and game.final_score:
        ws, rs, wn, rn = game.final_score
        y = PANEL_Y + 420
        screen.blit(font.render("Final:", True, (0,0,0)), (PANEL_X + 16, y))
        y += 40
        screen.blit(small_font.render(f"White sum={ws}, adjacent={wn}", True, (0,0,0)), (PANEL_X + 16, y))
        y += 24
        screen.blit(small_font.render(f"Red   sum={rs}, adjacent={rn}", True, (0,0,0)), (PANEL_X + 16, y))
        y += 32

        winner = "Tie"
        if ws != rs:
            winner = "White wins" if ws > rs else "Red wins"
        else:
            if wn != rn:
                winner = "White wins" if wn > rn else "Red wins"
        screen.blit(font.render(winner, True, (10,10,10)), (PANEL_X + 16, y))

def build_buttons(font):
    # Four buttons for values 1..4
    bx = PANEL_X + 16
    by = PANEL_Y + 120
    bw = 70
    bh = 60
    gap = 14

    buttons = []
    for i, v in enumerate([1,2,3,4]):
        rect = pygame.Rect(bx, by + i*(bh+gap), bw, bh)
        label = SYMBOLS[v]
        buttons.append(Button(rect=rect, label=label, value=v))
    return buttons

def pos_to_cell(mx, my):
    if mx < BOARD_X or my < BOARD_Y:
        return None
    c = (mx - BOARD_X) // CELL
    r = (my - BOARD_Y) // CELL
    if 0 <= r < GRID and 0 <= c < GRID:
        return int(r), int(c)
    return None

# =========================
# Main
# =========================
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("YOXII (prototype)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 40)
    small_font = pygame.font.SysFont(None, 24)

    game = YoxiiGame()
    buttons = build_buttons(font)

    running = True
    while running:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos

                # buttons
                for b in buttons:
                    if b.rect.collidepoint(mx, my):
                        cnt = game.stock[game.turn][b.value]
                        if cnt > 0 and game.phase in ("MOVE_TOTEM", "PLACE_PIECE"):
                            # toggle
                            if game.selected_value == b.value:
                                game.selected_value = None
                            else:
                                game.selected_value = b.value
                        break
                else:
                    # board click
                    rc = pos_to_cell(mx, my)
                    if rc:
                        r, c = rc
                        game.click_cell(r, c)

        # draw
        screen.fill((225, 225, 225))
        draw_board(screen, font, game)
        draw_panel(screen, font, small_font, game, buttons)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

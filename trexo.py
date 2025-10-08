import pygame
import sys
from typing import List, Tuple, Optional, Dict

# --- Game constants ---
GRID_SIZE = 10
CELL_SIZE = 56
MARGIN = 40
PANEL_W = 260
SCREEN_W = MARGIN * 2 + GRID_SIZE * CELL_SIZE + PANEL_W
SCREEN_H = MARGIN * 2 + GRID_SIZE * CELL_SIZE
FPS = 60

# Colors
WHITE = (245, 245, 245)
BLACK = (24, 24, 24)
GRAY = (200, 200, 200)
LIGHT_GRAY = (225, 225, 225)
DARK = (40, 40, 40)
RED = (230, 70, 70)
BLUE = (60, 120, 230)
GREEN = (60, 180, 120)
ORANGE = (255, 150, 60)
YELLOW = (255, 210, 70)
SEAM_GOOD = (60, 180, 120)
SEAM_BAD = (220, 80, 80)

# Players: O is Red, X is Blue (fixed for clarity)
PLAYER_O = 'O'
PLAYER_X = 'X'

# Orientation (4-way)
# 0:E (→), 1:S (↓), 2:W (←), 3:N (↑)
EAST, SOUTH, WEST, NORTH = 0, 1, 2, 3

pygame.init()

FONT = pygame.font.SysFont('consolas', 18)
FONT_L = pygame.font.SysFont('consolas', 24, bold=True)
FONT_S = pygame.font.SysFont('consolas', 14)

# --- Data structures ---
class Placement:
    """Represents a single domino placement at a specific level.
    Stores id for seam-checking, and the symbol order on the two cells.
    """
    __slots__ = ("pid", "cells", "symbols")
    def __init__(self, pid: int, cells: List[Tuple[int, int]], symbols: List[str]):
        self.pid = pid              # unique placement id
        self.cells = cells          # [(r1,c1), (r2,c2)] (adjacent)
        self.symbols = symbols      # [sym at cell0, sym at cell1] e.g., ['O','X']

class Board:
    def __init__(self, n: int):
        self.n = n
        # For each cell, maintain a stack of symbols (top at end)
        self.symbol_stacks: List[List[List[str]]] = [[[] for _ in range(n)] for _ in range(n)]
        # For each level per cell, track placement id that contributed that tile layer
        self.pid_stacks: List[List[List[int]]] = [[[] for _ in range(n)] for _ in range(n)]
        self.placements: Dict[int, Placement] = {}
        self.next_pid = 1

    def height(self, r: int, c: int) -> int:
        return len(self.symbol_stacks[r][c])

    def top_symbol(self, r: int, c: int) -> Optional[str]:
        if self.symbol_stacks[r][c]:
            return self.symbol_stacks[r][c][-1]
        return None

    def can_place_ground(self, cells: List[Tuple[int, int]]) -> bool:
        # ground placement allowed only if both empty (level 0)
        return all(self.height(r, c) == 0 for (r, c) in cells)

    def can_place_stack(self, cells: List[Tuple[int, int]]) -> bool:
        # All heights must match and be > 0 (no floating over emptiness)
        h0 = self.height(cells[0][0], cells[0][1])
        if h0 == 0:
            return False
        for (r, c) in cells:
            if self.height(r, c) != h0:
                return False
        # Seam rule: the layer beneath (h0-1) must come from different placements
        (r1, c1), (r2, c2) = cells
        pid_a = self.pid_stacks[r1][c1][h0 - 1]
        pid_b = self.pid_stacks[r2][c2][h0 - 1]
        return pid_a != pid_b

    def can_place(self, cells: List[Tuple[int, int]]) -> bool:
        # Either ground (both empty) or valid stack bridging a seam
        return self.can_place_ground(cells) or self.can_place_stack(cells)

    def place(self, cells: List[Tuple[int, int]], symbols: List[str]) -> int:
        """Place a domino with given two symbols onto given two cells.
        Precondition: can_place(cells) is True and cells are adjacent.
        Returns pid of this placement.
        """
        pid = self.next_pid
        self.next_pid += 1
        plc = Placement(pid, cells, symbols)
        self.placements[pid] = plc
        for (r, c), sym in zip(cells, symbols):
            self.symbol_stacks[r][c].append(sym)
            self.pid_stacks[r][c].append(pid)
        return pid

    def place_with_pid(self, pid: int, cells: List[Tuple[int, int]], symbols: List[str]) -> None:
        """Re-apply a previously created placement id (for Redo). Does not bump next_pid."""
        plc = self.placements.get(pid)
        if plc is None:
            plc = Placement(pid, cells, symbols)
            self.placements[pid] = plc
        else:
            plc.cells = cells
            plc.symbols = symbols
        for (r, c), sym in zip(cells, symbols):
            self.symbol_stacks[r][c].append(sym)
            self.pid_stacks[r][c].append(pid)
        # keep next_pid at least pid+1 to avoid future collisions
        if self.next_pid <= pid:
            self.next_pid = pid + 1

    def inside(self, r: int, c: int) -> bool:
        return 0 <= r < self.n and 0 <= c < self.n

    # --- Win detection: exact-five (overlines do not count) ---
    def has_exact_five(self, sym: str) -> bool:
        # Check only the top layer (visible board)
        top = [[self.top_symbol(r, c) for c in range(self.n)] for r in range(self.n)]

        def count_dir(r, c, dr, dc):
            cnt = 0
            i, j = r, c
            while self.inside(i, j) and top[i][j] == sym:
                cnt += 1
                i += dr
                j += dc
            return cnt

        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(self.n):
            for c in range(self.n):
                if top[r][c] != sym:
                    continue
                for dr, dc in dirs:
                    # Only count from the start of a segment
                    pr, pc = r - dr, c - dc
                    if self.inside(pr, pc) and top[pr][pc] == sym:
                        continue
                    length = count_dir(r, c, dr, dc)
                    if length == 5:
                        # ensure not an overline (no 6+)
                        ar, ac = r + dr * 5, c + dc * 5
                        if not (self.inside(ar, ac) and top[ar][ac] == sym):
                            return True
        return False

class TilePool:
    def __init__(self, total_tiles: int):
        self.total = total_tiles
        self.used = 0

    def remaining(self) -> int:
        return max(0, self.total - self.used)

    def take(self) -> bool:
        if self.remaining() > 0:
            self.used += 1
            return True
        return False

    def give_back(self, n: int = 1) -> None:
        # Safely restore tiles to the pool
        self.used = max(0, self.used - n)

class GameState:
    def __init__(self, total_tiles: int):
        self.board = Board(GRID_SIZE)
        self.pool = TilePool(total_tiles)
        self.current = PLAYER_O  # O (red) starts by default
        self.orientation = EAST  # default facing right
        # symbol order on the two cells (index 0 then 1 along orientation)
        # by default current player's symbol first then opponent's
        self.order_flip = False  # whether to flip ends (swap symbols)
        self.winner: Optional[str] = None
        self.ended_by_simul_loss = False
        # history/redo stacks store placement ids (pid)
        self.history: List[int] = []
        self.redo_stack: List[int] = []

    def current_pair(self) -> Tuple[str, str]:
        me = self.current
        opp = PLAYER_X if me == PLAYER_O else PLAYER_O
        pair = (me, opp)
        if self.order_flip:
            pair = (pair[1], pair[0])
        return pair

    def next_player(self):
        # Switch turn and reset end-order flip; do not return anything
        self.current = PLAYER_X if self.current == PLAYER_O else PLAYER_O
        self.order_flip = False


def cell_rect(r: int, c: int) -> pygame.Rect:
    return pygame.Rect(MARGIN + c * CELL_SIZE + 1, MARGIN + r * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)


def draw_grid(screen):
    # Board background
    pygame.draw.rect(screen, LIGHT_GRAY, (MARGIN, MARGIN, GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE))
    # Grid lines
    for i in range(GRID_SIZE + 1):
        x = MARGIN + i * CELL_SIZE
        y0 = MARGIN
        y1 = MARGIN + GRID_SIZE * CELL_SIZE
        pygame.draw.line(screen, GRAY, (x, y0), (x, y1), 1)
        y = MARGIN + i * CELL_SIZE
        x0 = MARGIN
        x1 = MARGIN + GRID_SIZE * CELL_SIZE
        pygame.draw.line(screen, GRAY, (x0, y), (x1, y), 1)
    # Axis labels
    for r in range(GRID_SIZE):
        txt = FONT_S.render(str(r), True, DARK)
        screen.blit(txt, (MARGIN - 20, MARGIN + r * CELL_SIZE + CELL_SIZE // 2 - 8))
    for c in range(GRID_SIZE):
        txt = FONT_S.render(str(c), True, DARK)
        screen.blit(txt, (MARGIN + c * CELL_SIZE + CELL_SIZE // 2 - 6, MARGIN - 22))


def draw_stacks(screen, board: Board):
    # Draw top symbol as a large mark; optionally draw small height and pid indicators
    for r in range(board.n):
        for c in range(board.n):
            rect = cell_rect(r, c)
            top = board.top_symbol(r, c)
            h = board.height(r, c)
            if top == PLAYER_O:
                pygame.draw.circle(screen, RED, rect.center, CELL_SIZE // 3, 3)
            elif top == PLAYER_X:
                # Draw X
                pygame.draw.line(screen, BLUE, (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 3)
                pygame.draw.line(screen, BLUE, (rect.left + 8, rect.bottom - 8), (rect.right - 8, rect.top + 8), 3)
            # Height label (top-right)
            if h > 0:
                ht = FONT_S.render(str(h), True, DARK)
                screen.blit(ht, (rect.right - 16, rect.top + 2))
                # Placement-id label (bottom-left): show which domino occupies the top layer of this cell
                pid = board.pid_stacks[r][c][-1]
                pid_txt = FONT_S.render(str(pid), True, DARK)
                screen.blit(pid_txt, (rect.left + 2, rect.bottom - pid_txt.get_height() - 2))


def draw_preview(screen, gs: GameState, hover: Optional[Tuple[int, int]]):
    if hover is None:
        return
    r, c = hover
    cells = get_cells_along(r, c, gs.orientation)
    if cells is None:
        return
    colors = {PLAYER_O: RED, PLAYER_X: BLUE}
    pair = gs.current_pair()

    # Placement legality
    in_bounds = all(gs.board.inside(rr, cc) for rr, cc in cells)
    can = in_bounds and gs.board.can_place(cells)

    # Shade cells preview (allow drawing even if offboard; purely visual)
    for idx, (rr, cc) in enumerate(cells):
        if not gs.board.inside(rr, cc):
            continue
        rect = cell_rect(rr, cc)
        col = colors[pair[idx]]
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        s.fill((col[0], col[1], col[2], 70 if can else 25))
        screen.blit(s, rect.topleft)
        # Faint symbol
        if pair[idx] == PLAYER_O:
            pygame.draw.circle(screen, col, rect.center, CELL_SIZE // 3, 1)
        else:
            pygame.draw.line(screen, col, (rect.left + 10, rect.top + 10), (rect.right - 10, rect.bottom - 10), 1)
            pygame.draw.line(screen, col, (rect.left + 10, rect.bottom - 10), (rect.right - 10, rect.top + 10), 1)

    # Seam badge only if fully in-bounds
    if in_bounds:
        (r1, c1), (r2, c2) = cells
        h1 = gs.board.height(r1, c1)
        h2 = gs.board.height(r2, c2)
        if h1 == h2 and h1 > 0:
            pid_a = gs.board.pid_stacks[r1][c1][h1 - 1]
            pid_b = gs.board.pid_stacks[r2][c2][h2 - 1]
            good = pid_a != pid_b
            rect1 = cell_rect(r1, c1)
            rect2 = cell_rect(r2, c2)
            midx = (rect1.centerx + rect2.centerx) // 2
            midy = (rect1.centery + rect2.centery) // 2
            clr = SEAM_GOOD if good else SEAM_BAD
            pygame.draw.circle(screen, clr, (midx, midy), 8)
            if good:
                pygame.draw.line(screen, WHITE, (midx - 3, midy), (midx - 1, midy + 3), 2)
                pygame.draw.line(screen, WHITE, (midx - 1, midy + 3), (midx + 4, midy - 3), 2)
            else:
                pygame.draw.line(screen, WHITE, (midx - 4, midy - 4), (midx + 4, midy + 4), 2)
                pygame.draw.line(screen, WHITE, (midx - 4, midy + 4), (midx + 4, midy - 4), 2)


def get_mouse_cell(pos) -> Optional[Tuple[int, int]]:
    x, y = pos
    bx0, by0 = MARGIN, MARGIN
    bx1, by1 = MARGIN + GRID_SIZE * CELL_SIZE, MARGIN + GRID_SIZE * CELL_SIZE
    if not (bx0 <= x < bx1 and by0 <= y < by1):
        return None
    c = (x - MARGIN) // CELL_SIZE
    r = (y - MARGIN) // CELL_SIZE
    return (r, c)


def get_cells_along(r: int, c: int, orientation: int) -> Optional[List[Tuple[int, int]]]:
    # 4-way orientation support
    if orientation == EAST:
        cells = [(r, c), (r, c + 1)]
    elif orientation == SOUTH:
        cells = [(r, c), (r + 1, c)]
    elif orientation == WEST:
        cells = [(r, c), (r, c - 1)]
    else:  # NORTH
        cells = [(r, c), (r - 1, c)]
    return cells


def try_place(gs: GameState, r: int, c: int) -> bool:
    cells = get_cells_along(r, c, gs.orientation)
    if cells is None:
        return False
    # Bounds check
    for (rr, cc) in cells:
        if not gs.board.inside(rr, cc):
            return False
    # Check valid placement
    if not gs.board.can_place(cells):
        return False
    # Check tile availability
    if gs.pool.remaining() <= 0:
        return False

    pair = list(gs.current_pair())

    if gs.redo_stack:
        # --- Branch case: reuse the most recent pid + discard the rest of redo ---
        reuse_pid = gs.redo_stack.pop()     # Reuse the pid of the most recently undone move
        gs.board.place_with_pid(reuse_pid, cells, pair)

        # Remaining redo moves are from a "discarded timeline"; remove them from placements
        stale_pids = gs.redo_stack[:]       # after pop, the remaining ones
        gs.redo_stack.clear()
        for sp in stale_pids:
            if sp in gs.board.placements:
                del gs.board.placements[sp]

        # Consume one tile + add to history
        if not gs.pool.take():
            return False
        gs.history.append(reuse_pid)

        # Reset pid counter to (max existing pid + 1)
        gs.board.next_pid = (max(gs.history) + 1) if gs.history else 1

    else:
        # --- Normal case: before creating a new pid, ensure next_pid = (max existing +1) ---
        desired_next = (max(gs.history) + 1) if gs.history else 1
        gs.board.next_pid = desired_next

        pid = gs.board.place(cells, pair)
        gs.redo_stack.clear()

        if not gs.pool.take():
            return False
        gs.history.append(pid)

        # After placement, update next_pid again for consistency
        gs.board.next_pid = (max(gs.history) + 1)

    # Win check
    o5 = gs.board.has_exact_five(PLAYER_O)
    x5 = gs.board.has_exact_five(PLAYER_X)
    if o5 and x5:
        gs.winner = PLAYER_X if gs.current == PLAYER_O else PLAYER_O
        gs.ended_by_simul_loss = True
    elif o5:
        gs.winner = PLAYER_O
    elif x5:
        gs.winner = PLAYER_X

    # Draw if no tiles remain
    if gs.winner is None and gs.pool.remaining() == 0:
        gs.winner = 'DRAW'

    # If no result, pass the turn
    if gs.winner is None:
        gs.next_player()
    return True



def undo_last(gs: GameState) -> bool:
    """Undo the last placement. Returns True if something was undone."""
    if not gs.history:
        return False
    last_pid = gs.history.pop()
    plc = gs.board.placements.get(last_pid)
    if plc is None:
        return False
    # Pop from the two cells if the top layer belongs to last_pid
    popped_cells = 0
    for (r, c) in plc.cells:
        if gs.board.pid_stacks[r][c] and gs.board.pid_stacks[r][c][-1] == last_pid:
            gs.board.pid_stacks[r][c].pop()
            gs.board.symbol_stacks[r][c].pop()
            popped_cells += 1
    # Only give a tile back if both cells were popped (a valid domino undo)
    if popped_cells == 2:
        gs.pool.give_back(1)
        # Push to redo stack to enable reapplying with same pid
        gs.redo_stack.append(last_pid)
    else:
        # If mismatch (shouldn't happen), push pid back to history to avoid desync
        gs.history.append(last_pid)
        return False
    # Reset winner state
    gs.winner = None
    gs.ended_by_simul_loss = False
    # Give turn back to the player who made that move
    gs.current = PLAYER_X if gs.current == PLAYER_O else PLAYER_O
    gs.order_flip = False
    return True


def redo_last(gs: GameState) -> bool:
    """Redo the last undone placement. Returns True if something was redone."""
    if not gs.redo_stack:
        return False
    pid = gs.redo_stack.pop()
    plc = gs.board.placements.get(pid)
    if plc is None:
        return False
    cells = plc.cells
    symbols = plc.symbols
    # Re-apply exactly the same placement id and symbols without rule re-check
    gs.board.place_with_pid(pid, cells, symbols)
    if not gs.pool.take():
        # If pool is empty (shouldn't be due to prior undo), revert re-application
        for (r, c) in reversed(cells):
            if gs.board.pid_stacks[r][c] and gs.board.pid_stacks[r][c][-1] == pid:
                gs.board.pid_stacks[r][c].pop()
                gs.board.symbol_stacks[r][c].pop()
        # Put pid back to redo stack
        gs.redo_stack.append(pid)
        return False
    gs.history.append(pid)
    # Advance turn
    gs.next_player()
    # Reset winner state and recompute in case redo creates a win
    gs.winner = None
    gs.ended_by_simul_loss = False
    o5 = gs.board.has_exact_five(PLAYER_O)
    x5 = gs.board.has_exact_five(PLAYER_X)
    if o5 and x5:
        gs.winner = PLAYER_X if gs.current == PLAYER_O else PLAYER_O
        gs.ended_by_simul_loss = True
    elif o5:
        gs.winner = PLAYER_O
    elif x5:
        gs.winner = PLAYER_X
    if gs.winner is None and gs.pool.remaining() == 0:
        gs.winner = 'DRAW'
    return True

# --- Start menu to set tile count ---
class StartMenu:
    def __init__(self):
        self.tiles_total = 50  # sensible default for 10x10
        self.done = False

    def draw(self, screen):
        screen.fill(WHITE)
        title = FONT_L.render("Domino Gomoku — Start", True, BLACK)
        screen.blit(title, (MARGIN, MARGIN))

        y = MARGIN + 60
        label = FONT.render("Total domino tiles (shared pool):", True, DARK)
        screen.blit(label, (MARGIN, y))
        y += 36
        minus_rect = pygame.Rect(MARGIN, y, 34, 34)
        plus_rect = pygame.Rect(MARGIN + 160, y, 34, 34)
        val_rect = pygame.Rect(MARGIN + 50, y, 100, 34)

        pygame.draw.rect(screen, LIGHT_GRAY, minus_rect)
        pygame.draw.rect(screen, LIGHT_GRAY, plus_rect)
        pygame.draw.rect(screen, WHITE, val_rect)
        pygame.draw.rect(screen, GRAY, minus_rect, 2)
        pygame.draw.rect(screen, GRAY, plus_rect, 2)
        pygame.draw.rect(screen, GRAY, val_rect, 2)

        mtxt = FONT_L.render("-", True, DARK)
        ptxt = FONT_L.render("+", True, DARK)
        screen.blit(mtxt, (minus_rect.centerx - 6, minus_rect.centery - 12))
        screen.blit(ptxt, (plus_rect.centerx - 6, plus_rect.centery - 12))

        vtxt = FONT_L.render(str(self.tiles_total), True, BLACK)
        screen.blit(vtxt, (val_rect.centerx - vtxt.get_width() // 2, val_rect.centery - vtxt.get_height() // 2))

        y += 70
        hint = FONT_S.render("Tip: Use 40–60 for a tense game on 10x10.", True, DARK)
        screen.blit(hint, (MARGIN, y))

        y += 40
        start_rect = pygame.Rect(MARGIN, y, 140, 42)
        pygame.draw.rect(screen, GREEN, start_rect, border_radius=8)
        stxt = FONT.render("Start (Enter)", True, (255, 255, 255))
        screen.blit(stxt, (start_rect.centerx - stxt.get_width() // 2, start_rect.centery - stxt.get_height() // 2))

        # Controls info
        ci = [
            "Controls:",
            "Left click = place",
            "E / Q = rotate CW/CCW (4-way)",
            "F = swap ends (O|X ↔ X|O)",
            "Z / Ctrl+Z = Undo",
            "Y / R / Ctrl+Y = Redo",
            "Esc = quit",
        ]
        y = start_rect.bottom + 20
        for line in ci:
            t = FONT.render(line, True, DARK)
            screen.blit(t, (MARGIN, y))
            y += 24

        return minus_rect, plus_rect, start_rect

# --- Main loop ---
def run():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Domino Gomoku (10x10)")
    clock = pygame.time.Clock()

    # Start menu
    menu = StartMenu()
    while not menu.done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_RETURN:
                    menu.done = True
                if event.key in (pygame.K_LEFT, pygame.K_MINUS):
                    menu.tiles_total = max(1, menu.tiles_total - 1)
                if event.key in (pygame.K_RIGHT, pygame.K_EQUALS, pygame.K_PLUS):
                    menu.tiles_total = min(200, menu.tiles_total + 1)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                minus_rect, plus_rect, start_rect = menu.draw(screen)
                if minus_rect.collidepoint(mx, my):
                    menu.tiles_total = max(1, menu.tiles_total - 1)
                elif plus_rect.collidepoint(mx, my):
                    menu.tiles_total = min(200, menu.tiles_total + 1)
                elif start_rect.collidepoint(mx, my):
                    menu.done = True
        # draw menu UI
        minus_rect, plus_rect, start_rect = menu.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    gs = GameState(menu.tiles_total)

    hover_cell = None
    message = "O (Red) to move"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                # 4-way rotation
                if event.key == pygame.K_e:
                    gs.orientation = (gs.orientation + 1) % 4  # CW
                elif event.key == pygame.K_q:
                    gs.orientation = (gs.orientation - 1) % 4  # CCW
                elif event.key == pygame.K_f:
                    gs.order_flip = not gs.order_flip
                # Undo / Redo
                elif event.key == pygame.K_z or (event.key == pygame.K_z and (mods & pygame.KMOD_CTRL)):
                    if undo_last(gs):
                        message = "Undid last move."
                elif event.key in (pygame.K_y, pygame.K_r) or (event.key == pygame.K_y and (mods & pygame.KMOD_CTRL)):
                    if redo_last(gs):
                        message = "Redid move."
            if event.type == pygame.MOUSEMOTION:
                hover_cell = get_mouse_cell(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hc = get_mouse_cell(event.pos)
                if hc and gs.winner is None:
                    placed = try_place(gs, hc[0], hc[1])
                    if placed:
                        if gs.winner == PLAYER_O:
                            message = "O (Red) wins!"
                        elif gs.winner == PLAYER_X:
                            if gs.ended_by_simul_loss:
                                message = f"X (Blue) wins — opponent completed both!"
                            else:
                                message = "X (Blue) wins!"
                        elif gs.winner == 'DRAW':
                            message = "Draw — tile pool exhausted."
                        else:
                            cur = 'O (Red)' if gs.current == PLAYER_O else 'X (Blue)'
                            message = f"{cur} to move"

        # Draw
        screen.fill(WHITE)
        draw_grid(screen)
        draw_stacks(screen, gs.board)
        draw_preview(screen, gs, hover_cell)

        # Side panel
        px = MARGIN + GRID_SIZE * CELL_SIZE + 20
        py = MARGIN
        pygame.draw.rect(screen, WHITE, (MARGIN + GRID_SIZE * CELL_SIZE, 0, PANEL_W, SCREEN_H))
        # Panel border
        pygame.draw.line(screen, GRAY, (MARGIN + GRID_SIZE * CELL_SIZE, 0), (MARGIN + GRID_SIZE * CELL_SIZE, SCREEN_H), 2)

        title = FONT_L.render("Status", True, BLACK)
        screen.blit(title, (px, py))
        py += 36
        screen.blit(FONT.render(message, True, DARK), (px, py))
        py += 28
        rem = gs.pool.remaining()
        screen.blit(FONT.render(f"Tiles remaining: {rem}", True, DARK), (px, py))
        py += 28
        turn = 'O (Red)' if gs.current == PLAYER_O else 'X (Blue)'
        screen.blit(FONT.render(f"Turn: {turn}", True, RED if gs.current == PLAYER_O else BLUE), (px, py))
        py += 28
        ori_names = {EAST: '→ East', SOUTH: '↓ South', WEST: '← West', NORTH: '↑ North'}
        screen.blit(FONT.render(f"Orientation: {ori_names[gs.orientation]}", True, DARK), (px, py))
        py += 24
        order = "O|X" if not gs.order_flip else "X|O"
        screen.blit(FONT.render(f"Ends: {order}", True, DARK), (px, py))
        py += 36

        # Rules summary & controls
        rules = [
            "Rules:",
            "• Place O|X dominoes.",
            "• Stack only if both cells",
            "  same height (>0) and",
            "  you bridge a seam",
            "  (two different tiles).",
            "• Exact five wins.",
            "  Overlines do not count.",
            "• If both complete at",
            "  once, mover loses.",
            "• Pool exhaustion = draw.",
            "",
            "Controls:",
            "• Q / E : rotate CCW / CW",
            "• F     : flip ends (O|X↔X|O)",
            "• Z / Ctrl+Z : Undo",
            "• Y / R / Ctrl+Y : Redo",
        ]
        for line in rules:
            screen.blit(FONT_S.render(line, True, DARK), (px, py))
            py += 18

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    run()

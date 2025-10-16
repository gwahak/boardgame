import pygame
import sys
from copy import deepcopy
import time

# -------------------- Config --------------------
GRID = 8
CELL = 72
MARGIN = 40
PANEL_W = 300
WIDTH = MARGIN*2 + GRID*CELL + PANEL_W
HEIGHT = MARGIN*2 + GRID*CELL
FPS = 60

EMPTY = 0
RED = 1
BLUE = 2

BG = (245, 245, 245)
BOARD_COLOR = (230, 230, 230)
GRID_COLOR = (190, 190, 190)
RED_COLOR = (220, 40, 40)
BLUE_COLOR = (40, 100, 220)
SEL_COLOR = (30, 30, 30)
CLONE_HINT = (20, 180, 60)
JUMP_HINT = (150, 60, 200)
TEXT = (20, 20, 20)

# -------------------- Helpers --------------------
def inside(r, c):
    return 0 <= r < GRID and 0 <= c < GRID

def chebyshev_dist(a, b):
    (r1, c1), (r2, c2) = a, b
    return max(abs(r1 - r2), abs(c1 - c2))

def neighbors8(r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if inside(rr, cc):
                yield rr, cc

def ring16_dist2(r, c):
    for rr in range(r-2, r+3):
        for cc in range(c-2, c+3):
            if not inside(rr, cc):
                continue
            if (rr, cc) == (r, c):
                continue
            if max(abs(rr - r), abs(cc - c)) == 2:
                yield rr, cc

def count_pieces(board):
    r = sum(cell == RED for row in board for cell in row)
    b = sum(cell == BLUE for row in board for cell in row)
    e = GRID*GRID - (r + b)
    return r, b, e

def generate_moves(board, player):
    moves = []
    for r in range(GRID):
        for c in range(GRID):
            if board[r][c] != player:
                continue
            for rr, cc in neighbors8(r, c):
                if board[rr][cc] == EMPTY:
                    moves.append((r, c, rr, cc, True))   # clone
            for rr, cc in ring16_dist2(r, c):
                if board[rr][cc] == EMPTY:
                    moves.append((r, c, rr, cc, False))  # jump
    return moves

def play_move_on(board, player, move):
    sr, sc, dr, dc, is_clone = move
    nb = deepcopy(board)
    if nb[dr][dc] != EMPTY:
        return None, player
    if is_clone:
        nb[dr][dc] = player
    else:
        nb[dr][dc] = player
        nb[sr][sc] = EMPTY
    # 감염
    opp = RED if player == BLUE else BLUE
    for rr, cc in neighbors8(dr, dc):
        if nb[rr][cc] == opp:
            nb[rr][cc] = player
    np = RED if player == BLUE else BLUE
    return nb, np

# -------------------- Game State --------------------
class Game:
    def __init__(self):
        self.board = [[EMPTY]*GRID for _ in range(GRID)]
        self.turn = RED
        self.history = []
        self.redo_stack = []
        self.message = ""
        # AI
        self.ai_on = {RED: False, BLUE: True}
        self.ai_depth = 2
        self.ai_mode_greedy = False
        # Only No-Progress
        self.no_progress_limit = 20  # plies
        self.no_progress_plies = 0
        self._last_rb = (0, 0)
        self._force_game_over = False
        self.reset()

    def reset(self):
        self.board = [[EMPTY]*GRID for _ in range(GRID)]
        for r in (0,1):
            for c in (0,1):
                self.board[r][c] = RED
        for r in (GRID-2, GRID-1):
            for c in (GRID-2, GRID-1):
                self.board[r][c] = RED
        for r in (GRID-2, GRID-1):
            for c in (0,1):
                self.board[r][c] = BLUE
        for r in (0,1):
            for c in (GRID-2, GRID-1):
                self.board[r][c] = BLUE

        self.turn = RED
        self.history.clear()
        self.redo_stack.clear()
        self.message = ""
        r, b, _ = self.count()
        self._last_rb = (r, b)
        self.no_progress_plies = 0
        self._force_game_over = False

    def copy_state(self):
        return (deepcopy(self.board), self.turn, self.no_progress_plies, self._last_rb, self._force_game_over)

    def restore_state(self, state):
        b, t, plies, last_rb, fgo = state
        self.board = deepcopy(b)
        self.turn = t
        self.no_progress_plies = plies
        self._last_rb = last_rb
        self._force_game_over = fgo

    def count(self):
        return count_pieces(self.board)

    def legal_moves(self, player):
        return generate_moves(self.board, player)

    def infect(self, player, r, c):
        opp = RED if player == BLUE else BLUE
        for rr, cc in neighbors8(r, c):
            if self.board[rr][cc] == opp:
                self.board[rr][cc] = player

    def apply_move(self, src, dst):
        sr, sc = src
        dr, dc = dst
        if self.board[dr][dc] != EMPTY:
            return False
        dist = chebyshev_dist(src, dst)
        if dist not in (1, 2):
            return False

        # 허용 수 여부(둘 곳이 아예 없을 때만 패스가 발생하므로 별도 필터 없음)
        if (sr, sc, dr, dc, dist == 1) not in self.legal_moves(self.turn):
            return False

        self.history.append(self.copy_state())
        self.redo_stack.clear()

        if dist == 1:
            self.board[dr][dc] = self.turn
        else:
            self.board[dr][dc] = self.turn
            self.board[sr][sc] = EMPTY

        self.infect(self.turn, dr, dc)
        self._update_no_progress()
        self._advance_turn()
        return True

    def _update_no_progress(self):
        r, b, _ = self.count()
        if (r, b) == self._last_rb:
            self.no_progress_plies += 1
            if self.no_progress_plies >= self.no_progress_limit:
                self._force_game_over = True
        else:
            self.no_progress_plies = 0
            self._last_rb = (r, b)

    def _advance_turn(self):
        self.turn = RED if self.turn == BLUE else BLUE
        if not self.legal_moves(self.turn):
            self.message = ("Red" if self.turn == RED else "Blue") + " has no moves: Pass"
            self.turn = RED if self.turn == BLUE else BLUE
        else:
            self.message = ""

    def game_over(self):
        if self._force_game_over:
            return True
        r, b, e = self.count()
        if e == 0:
            return True
        if not self.legal_moves(RED) and not self.legal_moves(BLUE):
            return True
        return False

    def winner(self):
        r, b, _ = self.count()
        if r > b: return "Red"
        if b > r: return "Blue"
        return "Draw"

    def undo(self):
        if not self.history: return
        self.redo_stack.append(self.copy_state())
        prev = self.history.pop()
        self.restore_state(prev)
        self.message = "Undo"

    def redo(self):
        if not self.redo_stack: return
        self.history.append(self.copy_state())
        nxt = self.redo_stack.pop()
        self.restore_state(nxt)
        self.message = "Redo"

# -------------------- AI --------------------
def mobility(board, player):
    return len(generate_moves(board, player))

def evaluate(board, player_perspective):
    r, b, _ = count_pieces(board)
    me, opp = player_perspective, (RED if player_perspective == BLUE else BLUE)
    my = r if me == RED else b
    op = b if me == RED else r

    center_bonus = 0.0
    for rr in range(GRID):
        for cc in range(GRID):
            d = max(abs(rr - 3.5), abs(cc - 3.5))
            if board[rr][cc] == me:
                center_bonus += (3 - d) * 0.2
            elif board[rr][cc] == opp:
                center_bonus -= (3 - d) * 0.2

    w_count, w_mob = 1.0, 0.2
    my_m = mobility(board, me)
    op_m = mobility(board, opp)
    return w_count*(my - op) + w_mob*(my_m - op_m) + center_bonus

def greedy_best_move(board, player):
    best, best_score = None, -1e18
    for mv in generate_moves(board, player):
        nb, np = play_move_on(board, player, mv)
        if nb is None: continue
        r1, b1, _ = count_pieces(board)
        r2, b2, _ = count_pieces(nb)
        gain = (r2 - r1) if player == RED else (b2 - b1)
        d = max(abs(mv[2] - 3.5), abs(mv[3] - 3.5))
        central = (3 - d) * 0.1
        sc = gain + central
        if sc > best_score:
            best_score, best = sc, mv
    return best

def minimax(board, player, depth, alpha, beta, root_player):
    if depth == 0:
        return evaluate(board, root_player), None

    moves = generate_moves(board, player)
    opp = RED if player == BLUE else BLUE

    if not moves:
        opp_moves = generate_moves(board, opp)
        if not opp_moves:
            return evaluate(board, root_player), None
        val, _ = minimax(board, opp, depth, alpha, beta, root_player)
        return val, None

    maximizing = (player == root_player)
    best_move = None

    if maximizing:
        value = -1e18
        for mv in moves:
            nb, np = play_move_on(board, player, mv)
            if nb is None: continue
            child, _ = minimax(nb, np, depth-1, alpha, beta, root_player)
            if child > value:
                value, best_move = child, mv
            alpha = max(alpha, value)
            if beta <= alpha: break
        return value, best_move
    else:
        value = 1e18
        for mv in moves:
            nb, np = play_move_on(board, player, mv)
            if nb is None: continue
            child, _ = minimax(nb, np, depth-1, alpha, beta, root_player)
            if child < value:
                value, best_move = child, mv
            beta = min(beta, value)
            if beta <= alpha: break
        return value, best_move

def ai_choose_move(game):
    player = game.turn
    board = game.board
    moves = generate_moves(board, player)
    if not moves:
        return None
    if game.ai_mode_greedy or game.ai_depth <= 1:
        return greedy_best_move(board, player)
    _, mv = minimax(board, player, game.ai_depth, -1e18, 1e18, player)
    return mv or greedy_best_move(board, player)

# -------------------- UI --------------------
def draw_board(screen, game, font, small_font, selected, clone_targets, jump_targets, last_ai_ms):
    screen.fill(BG)
    board_rect = pygame.Rect(MARGIN, MARGIN, GRID*CELL, GRID*CELL)
    pygame.draw.rect(screen, BOARD_COLOR, board_rect, border_radius=10)

    for i in range(GRID+1):
        x = MARGIN + i*CELL
        y = MARGIN + i*CELL
        pygame.draw.line(screen, GRID_COLOR, (MARGIN, y), (MARGIN+GRID*CELL, y), 1)
        pygame.draw.line(screen, GRID_COLOR, (x, MARGIN), (x, MARGIN+GRID*CELL), 1)

    for (rr, cc) in clone_targets:
        cx = MARGIN + cc*CELL + CELL//2
        cy = MARGIN + rr*CELL + CELL//2
        pygame.draw.circle(screen, CLONE_HINT, (cx, cy), CELL//6)
    for (rr, cc) in jump_targets:
        cx = MARGIN + cc*CELL + CELL//2
        cy = MARGIN + rr*CELL + CELL//2
        pygame.draw.circle(screen, JUMP_HINT, (cx, cy), CELL//6)

    for r in range(GRID):
        for c in range(GRID):
            v = game.board[r][c]
            if v == EMPTY: continue
            cx = MARGIN + c*CELL + CELL//2
            cy = MARGIN + r*CELL + CELL//2
            color = RED_COLOR if v == RED else BLUE_COLOR
            pygame.draw.circle(screen, color, (cx, cy), CELL//2 - 6)
            if selected == (r, c):
                pygame.draw.circle(screen, SEL_COLOR, (cx, cy), CELL//2 - 6, 3)

    panel_x = MARGIN + GRID*CELL + 20
    panel_y = MARGIN
    draw_panel(screen, game, font, small_font, panel_x, panel_y, last_ai_ms)

def draw_panel(screen, game, font, small_font, x, y, last_ai_ms):
    r, b, e = game.count()
    t = f"Turn: {'Red' if game.turn == RED else 'Blue'}"
    s = f"Red {r} : {b} Blue"
    emp = f"Empty: {e}"

    screen.blit(font.render(t, True, TEXT), (x, y))
    screen.blit(font.render(s, True, TEXT), (x, y+36))
    screen.blit(small_font.render(emp, True, TEXT), (x, y+72))

    if game.message:
        screen.blit(small_font.render(game.message, True, TEXT), (x, y+100))

    mode = "Greedy" if game.ai_mode_greedy else f"Minimax d={game.ai_depth}"
    info = [
        "", "AI:",
        f"  Red {'ON' if game.ai_on[RED] else 'OFF'} (S)",
        f"  Blue {'ON' if game.ai_on[BLUE] else 'OFF'} (A)",
        f"  Mode: {mode}   (G, 1-4 depth)",
        f"  Last AI: {last_ai_ms:.0f} ms",
        "", "Keys:",
        "  N: New   Z/Y: Undo/Redo",
        "  A/S: Toggle Blue/Red AI",
        "  G: Greedy <-> Minimax",
        "  1-4: Depth",
        "  [: -2  ]: +2  (No-Progress limit)",
        f"  No-Progress: {game.no_progress_plies}/{game.no_progress_limit}",
    ]
    yy = y + 130
    for line in info:
        screen.blit(small_font.render(line, True, TEXT), (x, yy))
        yy += 22

    if game.game_over():
        res = game.winner()
        screen.blit(font.render(f"Result: {res}", True, TEXT), (x, yy+10))

def cell_from_pos(pos):
    x, y = pos
    bx, by = x - MARGIN, y - MARGIN
    if bx < 0 or by < 0: return None
    c, r = bx // CELL, by // CELL
    if not inside(r, c): return None
    return (r, c)

def main():
    pygame.init()
    pygame.display.set_caption("세균전 (Ataxx Variant) + AI (No-Progress only)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    try:
        font = pygame.font.SysFont("malgungothic", 28)
        small_font = pygame.font.SysFont("malgungothic", 20)
    except:
        font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)

    game = Game()
    selected = None
    clone_targets, jump_targets = [], []
    last_ai_ms = 0.0

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    game.reset(); selected=None; clone_targets.clear(); jump_targets.clear()
                elif event.key == pygame.K_z:
                    game.undo(); selected=None; clone_targets.clear(); jump_targets.clear()
                elif event.key == pygame.K_y:
                    game.redo(); selected=None; clone_targets.clear(); jump_targets.clear()
                elif event.key == pygame.K_a:
                    game.ai_on[BLUE] = not game.ai_on[BLUE]
                elif event.key == pygame.K_s:
                    game.ai_on[RED] = not game.ai_on[RED]
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    game.ai_depth = int(event.unicode)
                elif event.key == pygame.K_g:
                    game.ai_mode_greedy = not game.ai_mode_greedy
                elif event.key == pygame.K_LEFTBRACKET:
                    game.no_progress_limit = max(2, game.no_progress_limit - 2)
                elif event.key == pygame.K_RIGHTBRACKET:
                    game.no_progress_limit += 2

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    selected=None; clone_targets.clear(); jump_targets.clear()
                elif event.button == 1:
                    if game.game_over() or game.ai_on[game.turn]:
                        pass
                    else:
                        cell = cell_from_pos(event.pos)
                        if not cell: continue
                        r, c = cell; v = game.board[r][c]
                        if selected is None:
                            if v == game.turn:
                                selected = (r, c)
                                moves = game.legal_moves(game.turn)
                                clone_targets = [(dr,dc) for (sr,sc,dr,dc,is_clone) in moves if (sr,sc)==(r,c) and is_clone]
                                jump_targets  = [(dr,dc) for (sr,sc,dr,dc,is_clone) in moves if (sr,sc)==(r,c) and not is_clone]
                        else:
                            dist = chebyshev_dist(selected, (r, c))
                            tentative = (selected[0], selected[1], r, c, dist==1)
                            if tentative in game.legal_moves(game.turn):
                                game.apply_move(selected, (r, c))
                            selected=None; clone_targets.clear(); jump_targets.clear()

        if (not game.game_over()) and game.ai_on[game.turn]:
            start = time.time()
            mv = ai_choose_move(game)
            if mv is None:
                game.message = ("Red" if game.turn == RED else "Blue") + " (AI) has no moves: Pass"
                game._advance_turn()
            else:
                sr, sc, dr, dc, is_clone = mv
                game.apply_move((sr, sc), (dr, dc))
            last_ai_ms = (time.time() - start) * 1000.0
            selected=None; clone_targets.clear(); jump_targets.clear()

        # 끝 조건: 노-프로그레스 한도만으로도 끝날 수 있음
        if game.game_over():
            pass

        draw_board(screen, game, font, small_font, selected, clone_targets, jump_targets, last_ai_ms)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

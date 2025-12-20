import sys
import pygame

# -------------------- Game Config --------------------
FILES = "abcdefghijk"   # 11 columns
RANKS = "7654321"       # 7 rows (top=7, bottom=1)
W, H = 11, 7

CELL = 72
MARGIN = 40
PANEL_W = 260
WIDTH = MARGIN * 2 + W * CELL + PANEL_W
HEIGHT = MARGIN * 2 + H * CELL
FPS = 60

# pieces
EMPTY = 0
WP = 1
BQ = 2
BK = 3

WHITE_TURN = 0
BLACK_TURN = 1

# zones
RIVER_ROWS = {0, 6}          # rank7(row0) and rank1(row6)
PLAY_ROWS = set(range(1, 6)) # 11x5 playable interior

# -------------------- Colors --------------------
BG = (248, 248, 248)
PANEL_BG = (240, 240, 240)
TEXT = (25, 25, 25)

# checkboard
CHK_LIGHT = (255, 255, 255)
CHK_DARK  = (250, 200, 150)

# rivers (dark/light alternating)
RIV_DARK  = (12, 45, 120)
RIV_LIGHT = (70, 140, 220)

# outlines / highlights
GRID_LINE = (165, 165, 165)
SELECT = (20, 20, 20)
MOVE_HINT = (30, 180, 60)

# piece colors
WHITE_PIECE = (245, 245, 245)
BLACK_PIECE = (30, 30, 30)

# -------------------- Helpers --------------------
def inside(r, c):
    return 0 <= r < H and 0 <= c < W

def sq_to_rc(sq: str):
    # "a1" -> (row, col) where row0 = rank7, row6 = rank1
    file_ch = sq[0]
    rank_ch = sq[1]
    c = FILES.index(file_ch)
    r = RANKS.index(rank_ch)  # because RANKS = "7654321"
    return r, c

def rc_to_sq(r, c):
    return f"{FILES[c]}{RANKS[r]}"

def river_forbidden(r):
    return r in RIVER_ROWS

def draw_button(screen, rect, label, font, enabled=True):
    col = (220, 220, 220) if enabled else (235, 235, 235)
    border = (120, 120, 120)
    pygame.draw.rect(screen, col, rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, 2, border_radius=10)
    surf = font.render(label, True, (30, 30, 30) if enabled else (140, 140, 140))
    screen.blit(surf, surf.get_rect(center=rect.center))

# -------------------- Rules: move generation --------------------
DIRS_8 = [(-1, 0), (0, 1), (1, 0), (0, -1),
          (-1, 1), (-1, -1), (1, 1), (1, -1)]

def gen_moves(board, turn):
    """Return list of moves: (r0,c0,r1,c1)."""
    moves = []
    if turn == WHITE_TURN:
        # White pawns: move 1 step north (r-1) if empty
        for r in range(H):
            for c in range(W):
                if board[r][c] == WP:
                    nr, nc = r - 1, c
                    if inside(nr, nc) and board[nr][nc] == EMPTY:
                        moves.append((r, c, nr, nc))
    else:
        # Black pieces:
        for r in range(H):
            for c in range(W):
                p = board[r][c]
                if p == BQ:
                    # Queen slides any distance, cannot enter rivers, cannot capture
                    for dr, dc in DIRS_8:
                        nr, nc = r + dr, c + dc
                        while inside(nr, nc):
                            if river_forbidden(nr):
                                break
                            if board[nr][nc] != EMPTY:
                                break  # blocked; capturing NOT allowed
                            moves.append((r, c, nr, nc))
                            nr += dr
                            nc += dc
                elif p == BK:
                    # King steps 1, cannot enter rivers, can capture WP
                    for dr, dc in DIRS_8:
                        nr, nc = r + dr, c + dc
                        if not inside(nr, nc):
                            continue
                        if river_forbidden(nr):
                            continue
                        dst = board[nr][nc]
                        if dst == EMPTY or dst == WP:
                            moves.append((r, c, nr, nc))
    return moves

def apply_move(board, move):
    r0, c0, r1, c1 = move
    p = board[r0][c0]
    board[r0][c0] = EMPTY
    board[r1][c1] = p

# -------------------- Initial position --------------------
def make_initial_board():
    b = [[EMPTY for _ in range(W)] for _ in range(H)]
    # White pawns on a1..k1 => row rank1 -> r=6
    for c in range(W):
        b[6][c] = WP

    # Black queens: d6 e6 g6 h6 (rank6 => r=1)
    for sq in ["d6", "e6", "g6", "h6"]:
        r, c = sq_to_rc(sq)
        b[r][c] = BQ

    # Black king: f6
    r, c = sq_to_rc("f6")
    b[r][c] = BK
    return b

# -------------------- Win/Lose conditions --------------------
def check_outcome(board, turn):
    # White wins if any pawn reaches top river (rank7 => row0)
    for c in range(W):
        if board[0][c] == WP:
            return "WHITE_WIN"

    # Black wins if no pawns remain (optional but sensible with "catch all Buffalo")
    any_pawn = any(board[r][c] == WP for r in range(H) for c in range(W))
    if not any_pawn:
        return "BLACK_WIN"

    # White loses if stalemated on its turn
    if turn == WHITE_TURN:
        if len(gen_moves(board, WHITE_TURN)) == 0:
            return "WHITE_LOSE_STALEMATE"

    return None

# -------------------- Drawing --------------------
def draw_board(screen, board, selected, legal_dests, font_piece):
    # background
    screen.fill(BG)

    # board
    bx = MARGIN
    by = MARGIN
    board_rect = pygame.Rect(bx, by, W * CELL, H * CELL)

    # squares
    for r in range(H):
        for c in range(W):
            x = bx + c * CELL
            y = by + r * CELL
            rect = pygame.Rect(x, y, CELL, CELL)

            # river rows: alternating dark/light blue
            if r in RIVER_ROWS:
                col = RIV_DARK if (c % 2 == 0) else RIV_LIGHT
            else:
                col = CHK_DARK if ((r + c) % 2 == 0) else CHK_LIGHT

            pygame.draw.rect(screen, col, rect)

            # move hints
            if (r, c) in legal_dests:
                pygame.draw.rect(screen, MOVE_HINT, rect, 4)

            # selection outline
            if selected == (r, c):
                pygame.draw.rect(screen, SELECT, rect, 4)

            # grid line
            pygame.draw.rect(screen, GRID_LINE, rect, 1)

    # pieces
    for r in range(H):
        for c in range(W):
            p = board[r][c]
            if p == EMPTY:
                continue
            cx = bx + c * CELL + CELL // 2
            cy = by + r * CELL + CELL // 2
            rad = int(CELL * 0.34)

            if p == WP:
                pygame.draw.circle(screen, WHITE_PIECE, (cx, cy), rad)
                pygame.draw.circle(screen, (90, 90, 90), (cx, cy), rad, 2)
                t = font_piece.render("P", True, (20, 20, 20))
                screen.blit(t, t.get_rect(center=(cx, cy)))
            elif p == BQ:
                pygame.draw.circle(screen, BLACK_PIECE, (cx, cy), rad)
                pygame.draw.circle(screen, (200, 200, 200), (cx, cy), rad, 2)
                t = font_piece.render("Q", True, (240, 240, 240))
                screen.blit(t, t.get_rect(center=(cx, cy)))
            elif p == BK:
                pygame.draw.circle(screen, BLACK_PIECE, (cx, cy), rad)
                pygame.draw.circle(screen, (200, 200, 200), (cx, cy), rad, 2)
                t = font_piece.render("K", True, (240, 240, 240))
                screen.blit(t, t.get_rect(center=(cx, cy)))

    return board_rect

def draw_panel(screen, turn, outcome, font_ui, font_small):
    px = MARGIN + W * CELL
    py = MARGIN
    rect = pygame.Rect(px, py, PANEL_W, H * CELL)
    pygame.draw.rect(screen, PANEL_BG, rect)
    pygame.draw.rect(screen, (180, 180, 180), rect, 1)

    y = py + 16
    title = font_ui.render("BuffaloChess", True, TEXT)
    screen.blit(title, (px + 16, y))
    y += 44

    turn_text = "Turn: WHITE (Pawns)" if turn == WHITE_TURN else "Turn: BLACK (K/Q)"
    t = font_small.render(turn_text, True, TEXT)
    screen.blit(t, (px + 16, y))
    y += 28

    # rules summary
    lines = [
        "WHITE: Pawns move 1 step up.",
        "  Win if any pawn reaches top river.",
        "  Lose if stalemated on White's turn.",
        "BLACK: Moves only in middle 11x5.",
        "  King captures; Queen cannot capture."
    ]
    y += 10
    for ln in lines:
        surf = font_small.render(ln, True, (50, 50, 50))
        screen.blit(surf, (px + 16, y))
        y += 22

    y += 14
    if outcome:
        if outcome == "WHITE_WIN":
            msg = "WHITE WINS (reached river)!"
        elif outcome == "BLACK_WIN":
            msg = "BLACK WINS (all pawns captured)!"
        else:
            msg = "WHITE LOSES (stalemated)!"
        surf = font_small.render(msg, True, (160, 20, 20))
        screen.blit(surf, (px + 16, y))
        y += 30

    return rect

# -------------------- Main --------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("BuffaloChess (pygame)")
    clock = pygame.time.Clock()

    font_ui = pygame.font.SysFont(None, 32)
    font_small = pygame.font.SysFont(None, 22)
    font_piece = pygame.font.SysFont(None, 34)

    board = make_initial_board()
    turn = WHITE_TURN
    outcome = None

    selected = None
    legal_dests = set()  # destinations for selected piece
    cached_moves = []    # all moves for current turn

    # buttons
    px = MARGIN + W * CELL + 16
    py = MARGIN + H * CELL - 70
    btn_restart = pygame.Rect(px, py, PANEL_W - 32, 46)

    def recache():
        nonlocal cached_moves
        cached_moves = gen_moves(board, turn)

    recache()

    running = True
    while running:
        clock.tick(FPS)

        # outcome check
        if outcome is None:
            outcome = check_outcome(board, turn)

        # draw
        board_rect = draw_board(screen, board, selected, legal_dests, font_piece)
        draw_panel(screen, turn, outcome, font_ui, font_small)
        draw_button(screen, btn_restart, "Restart (R)", font_small, enabled=True)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if event.key == pygame.K_r:
                    board = make_initial_board()
                    turn = WHITE_TURN
                    outcome = None
                    selected = None
                    legal_dests = set()
                    recache()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # restart
                if btn_restart.collidepoint(mx, my):
                    board = make_initial_board()
                    turn = WHITE_TURN
                    outcome = None
                    selected = None
                    legal_dests = set()
                    recache()
                    continue

                # ignore moves after game end (still allow restart)
                if outcome is not None:
                    continue

                # click on board?
                if board_rect.collidepoint(mx, my):
                    c = (mx - MARGIN) // CELL
                    r = (my - MARGIN) // CELL
                    if not inside(r, c):
                        continue

                    # if selecting destination
                    if selected and (r, c) in legal_dests:
                        # find the move that matches
                        r0, c0 = selected
                        chosen = None
                        for mv in cached_moves:
                            if mv == (r0, c0, r, c):
                                chosen = mv
                                break
                        if chosen is not None:
                            apply_move(board, chosen)

                            # switch turn
                            turn = BLACK_TURN if turn == WHITE_TURN else WHITE_TURN
                            selected = None
                            legal_dests = set()
                            recache()

                            # (optional) if black has no moves, still fine (no explicit stalemate for black)
                        continue

                    # else: selecting a piece
                    p = board[r][c]
                    if turn == WHITE_TURN and p == WP:
                        selected = (r, c)
                    elif turn == BLACK_TURN and p in (BQ, BK):
                        selected = (r, c)
                    else:
                        selected = None
                        legal_dests = set()
                        continue

                    # compute legal destinations for this selected piece
                    legal_dests = set()
                    if selected:
                        r0, c0 = selected
                        for mv in cached_moves:
                            if mv[0] == r0 and mv[1] == c0:
                                legal_dests.add((mv[2], mv[3]))

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

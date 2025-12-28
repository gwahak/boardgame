# minishogi_pygame.py
# 5x5 Minishogi in Pygame
# Pieces: K R B G S P (promotions supported, drops supported)
# UI layout (display coords in "cell units"):
#   Top hand:    y in [0,2)
#   Gap:         y in [2,2.5)
#   Board 5x5:   y in [2.5,7.5)
#   Gap:         y in [7.5,8)
#   Bottom hand: y in [8,10)
#
# Data storage:
#   board: 5x5 only (game rules)
#   hands: piece-count dict per side
#
# Controls:
#   - Click your piece on board to select; click a highlighted square to move.
#   - Click a piece in your hand (top/bottom 5x2 slots; you use bottom) to select for drop; click a highlighted square to drop.
#   - If promotion is optional after a move, you'll be prompted: press Y to promote, N to decline.
#   - ESC cancels selection.
#
# Rules implemented:
#   - Standard minishogi initial setup (per Wikipedia).
#   - Promotion zone = opponent's back rank (last rank).
#   - Promotes: P,S -> move as Gold; R,B -> gain king-step (R adds diagonals 1; B adds orthogonals 1)
#   - K,G do not promote.
#   - Capture sends piece to capturer's hand (always unpromoted).
#   - Drops:
#       * can drop to empty squares
#       * pawn: cannot drop on last rank; no "nifu" (two unpromoted pawns in same file)
#       * pawn-drop mate is forbidden (implemented by checking if drop gives checkmate)
#   - You may not make a move/drop leaving your own king in check.
#   - Win condition: checkmate (opponent in check and has no legal moves).
#
# Requires: pygame

import pygame
import sys
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Iterable

# ----------------------------
# Game model
# ----------------------------

SIDES = ("B", "W")  # Black at bottom, moves up (towards decreasing row); White at top, moves down.
PIECES = ["R", "B", "G", "S", "P"]  # For hand UI columns (K never in hand)
ALL_PIECES = ["K", "R", "B", "G", "S", "P"]

@dataclass(frozen=True)
class Piece:
    side: str          # "B" or "W"
    kind: str          # "K","R","B","G","S","P"
    promoted: bool = False

Move = Tuple[Tuple[int, int], Tuple[int, int], bool]  # (from_rc, to_rc, promote_flag)
Drop = Tuple[str, Tuple[int, int]]                    # (piece_kind, to_rc)

def opponent(side: str) -> str:
    return "W" if side == "B" else "B"

def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 5 and 0 <= c < 5

def promo_zone_row(side: str) -> int:
    # Opponent's back rank
    return 0 if side == "B" else 4

def forward_dir(side: str) -> int:
    # Black goes up (row - 1), White goes down (row + 1)
    return -1 if side == "B" else 1

def king_steps() -> List[Tuple[int, int]]:
    return [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def gold_steps(side: str) -> List[Tuple[int, int]]:
    # Gold: forward 3, sideways 2, back straight 1 (no back diagonals)
    f = forward_dir(side)
    return [(f,-1),(f,0),(f,1),(0,-1),(0,1),(-f,0)]

def silver_steps(side: str) -> List[Tuple[int, int]]:
    # Silver: forward 3 diagonals+straight, back diagonals (no sideways, no back straight)
    f = forward_dir(side)
    return [(f,-1),(f,0),(f,1),(-f,-1),(-f,1)]

def pawn_steps(side: str) -> List[Tuple[int, int]]:
    f = forward_dir(side)
    return [(f,0)]

def slide_dirs_rook() -> List[Tuple[int, int]]:
    return [(-1,0),(1,0),(0,-1),(0,1)]

def slide_dirs_bishop() -> List[Tuple[int, int]]:
    return [(-1,-1),(-1,1),(1,-1),(1,1)]

class Minishogi:
    def __init__(self):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(5)] for _ in range(5)]
        self.hands: Dict[str, Dict[str, int]] = {
            "B": {k: 0 for k in PIECES},
            "W": {k: 0 for k in PIECES},
        }
        self.side_to_move: str = "B"
        self._setup_initial()

    def _setup_initial(self):
        # Per Wikipedia minishogi:
        # White top row (r=0): K G S B R
        # White pawn at (r=1,c=0)?? Actually minishogi places P in front of king (same file as king).
        # Using the Wikipedia diagram: top row: K G S B R, second row: . P . . .
        # bottom row: R B S G K, row above bottom: . . . P .
        #
        # Convention: columns 0..4 left to right.
        # We'll set:
        # White: row0 = [K,G,S,B,R], row1 col1 = P
        # Black: row4 = [R,B,S,G,K], row3 col3 = P
        self.board[0][0] = Piece("W","K")
        self.board[0][1] = Piece("W","G")
        self.board[0][2] = Piece("W","S")
        self.board[0][3] = Piece("W","B")
        self.board[0][4] = Piece("W","R")
        self.board[1][0] = Piece("W","P")

        self.board[4][0] = Piece("B","R")
        self.board[4][1] = Piece("B","B")
        self.board[4][2] = Piece("B","S")
        self.board[4][3] = Piece("B","G")
        self.board[4][4] = Piece("B","K")
        self.board[3][4] = Piece("B","P")

    def clone(self) -> "Minishogi":
        g = Minishogi.__new__(Minishogi)
        g.board = [[self.board[r][c] for c in range(5)] for r in range(5)]
        g.hands = {
            "B": dict(self.hands["B"]),
            "W": dict(self.hands["W"]),
        }
        g.side_to_move = self.side_to_move
        return g

    # --- Core helpers ---
    def find_king(self, side: str) -> Optional[Tuple[int,int]]:
        for r in range(5):
            for c in range(5):
                p = self.board[r][c]
                if p and p.side == side and p.kind == "K":
                    return (r,c)
        return None

    def is_attacked_by(self, target_rc: Tuple[int,int], attacker_side: str) -> bool:
        tr, tc = target_rc
        # Generate all pseudo attacks by attacker and see if any hits target.
        for r in range(5):
            for c in range(5):
                p = self.board[r][c]
                if not p or p.side != attacker_side:
                    continue
                for rr, cc in self.pseudo_moves_from((r,c), attacks_only=True):
                    if (rr,cc) == (tr,tc):
                        return True
        return False

    def in_check(self, side: str) -> bool:
        kpos = self.find_king(side)
        if kpos is None:
            return False
        return self.is_attacked_by(kpos, opponent(side))

    # --- Move generation (pseudo & legal) ---
    def pseudo_moves_from(self, from_rc: Tuple[int,int], attacks_only: bool=False) -> List[Tuple[int,int]]:
        r, c = from_rc
        p = self.board[r][c]
        if not p:
            return []
        side = p.side
        kind = p.kind
        prom = p.promoted

        dests: List[Tuple[int,int]] = []

        def add_step(dr: int, dc: int):
            rr, cc = r+dr, c+dc
            if not in_bounds(rr,cc):
                return
            q = self.board[rr][cc]
            if q is None or q.side != side:
                dests.append((rr,cc))

        def add_slide(dr: int, dc: int):
            rr, cc = r+dr, c+dc
            while in_bounds(rr,cc):
                q = self.board[rr][cc]
                if q is None:
                    dests.append((rr,cc))
                else:
                    if q.side != side:
                        dests.append((rr,cc))
                    break
                rr += dr
                cc += dc

        # King
        if kind == "K":
            for dr,dc in king_steps():
                add_step(dr,dc)
            return dests

        # Gold (and promoted P/S behave like Gold)
        if kind == "G" or (prom and kind in ("P","S")):
            for dr,dc in gold_steps(side):
                add_step(dr,dc)
            return dests

        # Silver
        if kind == "S":
            for dr,dc in silver_steps(side):
                add_step(dr,dc)
            return dests

        # Pawn
        if kind == "P":
            for dr,dc in pawn_steps(side):
                add_step(dr,dc)
            return dests

        # Rook
        if kind == "R":
            for dr,dc in slide_dirs_rook():
                add_slide(dr,dc)
            if prom:
                # dragon king: king diagonals 1
                for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    add_step(dr,dc)
            return dests

        # Bishop
        if kind == "B":
            for dr,dc in slide_dirs_bishop():
                add_slide(dr,dc)
            if prom:
                # dragon horse: king orthogonals 1
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    add_step(dr,dc)
            return dests

        return dests

    def can_promote(self, p: Piece) -> bool:
        return p.kind in ("R","B","S","P")

    def promotion_optional_for_move(self, p: Piece, from_rc: Tuple[int,int], to_rc: Tuple[int,int]) -> bool:
        # Promotion can happen if:
        # - piece is promotable and not already promoted
        # - either from or to square is in promotion zone (opponent back rank)
        # For minishogi: zone is last rank only.
        if not self.can_promote(p) or p.promoted:
            return False
        z = promo_zone_row(p.side)
        fr, _ = from_rc
        tr, _ = to_rc
        return (fr == z) or (tr == z)

    def promotion_mandatory_for_move(self, p: Piece, to_rc: Tuple[int,int]) -> bool:
        # Pawn must promote if it reaches last rank (otherwise it would have no legal moves).
        if p.kind == "P" and (not p.promoted) and to_rc[0] == promo_zone_row(p.side):
            return True
        return False

    def apply_move(self, mv: Move):
        (fr,fc),(tr,tc),promote_flag = mv
        p = self.board[fr][fc]
        assert p is not None
        captured = self.board[tr][tc]
        if captured:
            # Send to mover's hand (unpromoted, K never captured in legal play)
            if captured.kind != "K":
                self.hands[p.side][captured.kind] += 1
        # move
        self.board[fr][fc] = None
        if promote_flag:
            p = Piece(p.side, p.kind, True)
        self.board[tr][tc] = p
        self.side_to_move = opponent(self.side_to_move)

    def apply_drop(self, dp: Drop):
        kind, (tr,tc) = dp
        side = self.side_to_move
        assert self.board[tr][tc] is None
        assert self.hands[side][kind] > 0
        self.hands[side][kind] -= 1
        self.board[tr][tc] = Piece(side, kind, False)
        self.side_to_move = opponent(self.side_to_move)

    def legal_moves_for_side(self, side: str) -> Tuple[List[Move], List[Drop]]:
        moves: List[Move] = []
        drops: List[Drop] = []

        # piece moves
        for r in range(5):
            for c in range(5):
                p = self.board[r][c]
                if not p or p.side != side:
                    continue
                from_rc = (r,c)
                for to_rc in self.pseudo_moves_from(from_rc):
                    # generate with/without promotion as applicable
                    # First determine if move is legal wrt self-check
                    opt = self.promotion_optional_for_move(p, from_rc, to_rc)
                    must = self.promotion_mandatory_for_move(p, to_rc)

                    promo_choices = [False, True] if opt else [False]
                    if must:
                        promo_choices = [True]

                    for promote_flag in promo_choices:
                        g2 = self.clone()
                        g2.side_to_move = side  # ensure consistent
                        g2.apply_move((from_rc, to_rc, promote_flag))
                        if not g2.in_check(side):
                            moves.append((from_rc, to_rc, promote_flag))

        # drops
        for kind in PIECES:
            if self.hands[side][kind] <= 0:
                continue
            for r in range(5):
                for c in range(5):
                    if self.board[r][c] is not None:
                        continue
                    if not self.drop_is_legal(kind, (r,c), side):
                        continue
                    g2 = self.clone()
                    g2.side_to_move = side
                    g2.apply_drop((kind,(r,c)))
                    if not g2.in_check(side):
                        drops.append((kind,(r,c)))

        return moves, drops

    def drop_is_legal(self, kind: str, to_rc: Tuple[int,int], side: str) -> bool:
        r,c = to_rc
        # Pawn restrictions
        if kind == "P":
            # cannot drop pawn on last rank (would have no moves)
            if r == promo_zone_row(side):
                return False
            # nifu: cannot have another unpromoted pawn in same file
            for rr in range(5):
                p = self.board[rr][c]
                if p and p.side == side and p.kind == "P" and (not p.promoted):
                    return False
            # pawn-drop mate forbidden: if this drop gives immediate checkmate, illegal
            # We'll test by simulating the drop and checking mate.
            g2 = self.clone()
            g2.side_to_move = side
            if g2.board[r][c] is not None:
                return False
            if g2.hands[side][kind] <= 0:
                return False
            g2.apply_drop((kind,(r,c)))
            opp = opponent(side)
            if g2.in_check(opp):
                mvs, dps = g2.legal_moves_for_side(opp)
                if len(mvs) == 0 and len(dps) == 0:
                    return False
        return True

    def is_checkmate(self, side: str) -> bool:
        # side is the side to test: if side is in check and has no legal moves/drops => mate
        if not self.in_check(side):
            return False
        mvs, dps = self.legal_moves_for_side(side)
        return (len(mvs) == 0 and len(dps) == 0)
    def apply_move_no_turn(self, from_rc: Tuple[int,int], to_rc: Tuple[int,int]):
        """Move piece WITHOUT promotion and WITHOUT switching turn (promotion decision comes after)."""
        fr, fc = from_rc
        tr, tc = to_rc
        p = self.board[fr][fc]
        assert p is not None

        captured = self.board[tr][tc]
        if captured:
            if captured.kind != "K":
                self.hands[p.side][captured.kind] += 1

        self.board[fr][fc] = None
        # move as-is (unpromoted for now; promoted piece cannot re-promote anyway)
        self.board[tr][tc] = Piece(p.side, p.kind, False if (p.kind in ("R","B","S","P")) else p.promoted)

    def promote_piece_at(self, rc: Tuple[int,int]):
        """Promote the piece currently at rc (if it can promote and is not already promoted)."""
        r, c = rc
        p = self.board[r][c]
        if not p:
            return
        if p.promoted:
            return
        if p.kind in ("K","G"):
            return
        if not self.can_promote(p):
            return
        self.board[r][c] = Piece(p.side, p.kind, True)

# ----------------------------
# UI / Pygame
# ----------------------------

CELL = 86
MARGIN = 24

# Half-cell spacing is represented by using "display y" coordinates that can be .5
TOP_HAND_Y0 = 0.0
BOARD_Y0 = 2.5
BOT_HAND_Y0 = 8.0

WINDOW_W = MARGIN*2 + 5*CELL
WINDOW_H = MARGIN*2 + int(10*CELL)

BG = (245, 245, 245)
GRID = (40, 40, 40)
HILITE = (60, 160, 255)
MOVE_HILITE = (100, 210, 120)
CAP_HILITE = (240, 140, 140)
TEXT = (15, 15, 15)
RED = (200, 40, 40)

def disp_to_pixel(x: float, y: float) -> Tuple[int,int]:
    px = MARGIN + int(x * CELL)
    py = MARGIN + int(y * CELL)
    return px, py

def pixel_to_disp(mx: int, my: int) -> Tuple[float,float]:
    x = (mx - MARGIN) / CELL
    y = (my - MARGIN) / CELL
    return x, y

def which_region(x: float, y: float) -> str:
    if 0 <= x < 5:
        if 0.0 <= y < 2.0:
            return "TOP_HAND"
        if 2.5 <= y < 7.5:
            return "BOARD"
        if 8.0 <= y < 10.0:
            return "BOT_HAND"
    return "NONE"

def hand_slot_from_disp(y: float, y0: float) -> int:
    # y in [y0, y0+2), rows 0/1
    return int(y - y0)

def board_rc_from_disp(x: float, y: float) -> Tuple[int,int]:
    # board y in [2.5, 7.5)
    c = int(x)
    r = int(y - BOARD_Y0)
    return r, c

def disp_rect(x: float, y: float) -> pygame.Rect:
    px, py = disp_to_pixel(x,y)
    return pygame.Rect(px, py, CELL, CELL)


def disp_rect_any(x: float, y: float, w_cells: float, h_cells: float) -> pygame.Rect:
    px, py = disp_to_pixel(x, y)
    return pygame.Rect(px, py, int(w_cells * CELL), int(h_cells * CELL))

TOP_GAP_Y0 = 2.0     # [2.0, 2.5)
BOT_GAP_Y0 = 7.5     # [7.5, 8.0)
def promo_bar_y0_opposite_gap(mover_side: str) -> float:
    """
    Promotion decision UI should appear on the opposite gap so it doesn't cover the board.
    - Black promotes on top rank => UI on bottom gap
    - White promotes on bottom rank => UI on top gap
    """
    return BOT_GAP_Y0 if mover_side == "B" else TOP_GAP_Y0

def promo_choice_rects(mover_side: str) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    y0 = promo_bar_y0_opposite_gap(mover_side)
    bar = disp_rect_any(0.0, y0, 5.0, 0.5)  # exactly one gap height
    left_w = bar.width // 2
    left = pygame.Rect(bar.x, bar.y, left_w, bar.height)                 # O
    right = pygame.Rect(bar.x + left_w, bar.y, bar.width - left_w, bar.height)  # X
    return bar, left, right

def draw_promo_choice_bar(surface: pygame.Surface, font_small: pygame.font.Font, mover_side: str):
    bar, left, right = promo_choice_rects(mover_side)
    bar2, _, _ = promo_choice_rects(opponent(mover_side))
    pygame.draw.rect(surface, (235,235,235), bar)
    pygame.draw.rect(surface, (40,40,40), bar, 1)
    pygame.draw.line(surface, (40,40,40), (right.x, bar.y), (right.x, bar.y + bar.height), 2)

    tO = font_small.render("O", True, (20,20,20))
    tX = font_small.render("X", True, (20,20,20))
    surface.blit(tO, tO.get_rect(center=left.center))
    surface.blit(tX, tX.get_rect(center=right.center))
    msg = font_small.render("O=promote, X=not yet", True, (20,20,20))
    # 핵심: 메시지는 '보드 반대편'으로 빼기
    # - mover_side == "B" 이면 바는 아래 갭에 있으니, 메시지는 그 아래쪽(화면 아래)으로
    # - mover_side == "W" 이면 바는 위 갭에 있으니, 메시지는 그 위쪽(화면 위)으로

    bar2, _, _ = promo_choice_rects(opponent(mover_side))
    surface.blit(msg, (bar2.x + 6, bar2.y + 2))
def piece_display_text(p: Piece) -> Tuple[str, Optional[str], bool]:
    """
    Returns: (main_text, sub_text, has_plus_badge)
    - Promoted P/S: main 'G', sub 'p'/'s'
    - Promoted R/B: main 'R'/'B', plus badge
    - Others: main kind
    """
    if p.promoted and p.kind in ("P","S"):
        return ("G", p.kind.lower(), False)
    if p.promoted and p.kind in ("R","B"):
        return (p.kind, None, True)
    return (p.kind, None, False)

def piece_color(p: Piece) -> Tuple[int,int,int]:
    # Your earlier plan: promoted R/B -> red; everything else black
    if p.promoted and p.kind in ("R","B"):
        return RED
    return TEXT

def render_piece_surface(font_main, font_sub, p: Piece) -> pygame.Surface:
    main, sub, plus = piece_display_text(p)
    col = piece_color(p)

    main_surf = font_main.render(main, True, col)
    # Create a combined surface
    w = max(main_surf.get_width(), 1)
    h = max(main_surf.get_height(), 1)
    pad = 8
    comb_w = w + pad*2
    comb_h = h + pad*2

    sub_surf = None
    if sub is not None:
        sub_surf = font_sub.render(sub, True, col)
        comb_w = max(comb_w, main_surf.get_width() + sub_surf.get_width() + pad*2)

    comb = pygame.Surface((comb_w, comb_h), pygame.SRCALPHA)
    comb.fill((0,0,0,0))
    # Center main
    mx = (comb_w - main_surf.get_width()) // 2
    my = (comb_h - main_surf.get_height()) // 2
    comb.blit(main_surf, (mx, my))

    # Subscript bottom-right-ish
    if sub_surf is not None:
        sx = mx + main_surf.get_width() - int(sub_surf.get_width()*0.2)
        sy = my + main_surf.get_height() - int(sub_surf.get_height()*0.2)
        comb.blit(sub_surf, (sx, sy))

    # Plus badge top-right
    if plus:
        plus_surf = font_sub.render("+", True, col)
        px = mx + main_surf.get_width() - int(plus_surf.get_width()*0.2)
        py = my - int(plus_surf.get_height()*0.2)
        comb.blit(plus_surf, (px, py))

    # Rotate for White (pointing down)
    if p.side == "W":
        comb = pygame.transform.rotate(comb, 180)
    return comb

def draw_grid(surface: pygame.Surface):
    # Draw 5x2 top hand
    for yy in range(2):
        for x in range(5):
            r = disp_rect(x, TOP_HAND_Y0 + yy)
            pygame.draw.rect(surface, GRID, r, 1)

    # Draw 5x5 board
    for y in range(5):
        for x in range(5):
            r = disp_rect(x, BOARD_Y0 + y)
            pygame.draw.rect(surface, GRID, r, 1)

    # Draw 5x2 bottom hand
    for yy in range(2):
        for x in range(5):
            r = disp_rect(x, BOT_HAND_Y0 + yy)
            pygame.draw.rect(surface, GRID, r, 1)

def draw_labels(surface: pygame.Surface, font_small: pygame.font.Font):
    # Simple labels
    top = font_small.render("WHITE HAND", True, (90,90,90))
    bot = font_small.render("BLACK HAND", True, (90,90,90))
    surface.blit(top, (MARGIN, MARGIN - 18))
    surface.blit(bot, (MARGIN, MARGIN + int(10*CELL) + 2))

def draw_hands(surface: pygame.Surface, game: Minishogi, font_main, font_sub):
    # Each column is a piece type in PIECES; two rows are "slot 1" and "slot 2"
    # Top shows White hand (captured by White), bottom shows Black hand.
    for side, y0 in [("W", TOP_HAND_Y0), ("B", BOT_HAND_Y0)]:
        for col, kind in enumerate(PIECES):
            cnt = game.hands[side][kind]
            for row in range(2):
                slot = disp_rect(col, y0 + row)
                if cnt >= row + 1:
                    # Render unpromoted piece in hand (always unpromoted by rule)
                    p = Piece(side, kind, False)
                    ps = render_piece_surface(font_main, font_sub, p)
                    surface.blit(ps, ps.get_rect(center=slot.center))
                else:
                    # optional faint dot or nothing
                    pass

def draw_board(surface: pygame.Surface, game: Minishogi, font_main, font_sub):
    for r in range(5):
        for c in range(5):
            p = game.board[r][c]
            if not p:
                continue
            cell = disp_rect(c, BOARD_Y0 + r)
            ps = render_piece_surface(font_main, font_sub, p)
            surface.blit(ps, ps.get_rect(center=cell.center))

def draw_highlights(surface: pygame.Surface,
                    region: str,
                    selected_from: Optional[Tuple[int,int]],
                    selected_drop_kind: Optional[str],
                    legal_targets: List[Tuple[int,int]],
                    game: Minishogi):
    # Board targets only
    if region in ("MOVE", "DROP"):
        for (r,c) in legal_targets:
            cell = disp_rect(c, BOARD_Y0 + r)
            target_piece = game.board[r][c]
            color = MOVE_HILITE if target_piece is None else CAP_HILITE
            pygame.draw.rect(surface, color, cell, 4)

    if selected_from is not None:
        r,c = selected_from
        cell = disp_rect(c, BOARD_Y0 + r)
        pygame.draw.rect(surface, HILITE, cell, 4)

def draw_status(surface: pygame.Surface, game: Minishogi, font_small: pygame.font.Font,
                message: str = ""):
    s = f"Turn: {game.side_to_move}    "
    if game.in_check(game.side_to_move):
        s += "CHECK!  "
    if message:
        s += message
    txt = font_small.render(s, True, (20,20,20))
    surface.blit(txt, (MARGIN, MARGIN + int(10*CELL) - 18))

# ----------------------------
# Main loop
# ----------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H + 30))
    pygame.display.set_caption("Minishogi (5x5) - Pygame")

    font_main = pygame.font.SysFont("Arial", 42, bold=True)
    font_sub  = pygame.font.SysFont("Arial", 20, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)

    game = Minishogi()

    # UI state
    mode = "IDLE"  # IDLE, MOVE_SELECTED, DROP_SELECTED, PROMOTE_QUERY
    selected_from: Optional[Tuple[int,int]] = None
    selected_drop_kind: Optional[str] = None
    legal_targets: List[Tuple[int,int]] = []

    # Promotion query state
    pending_move: Optional[Move] = None  # (from,to,False) 형태로만 쓸 것
    pending_promo_rc: Optional[Tuple[int,int]] = None  # 이동한 목적지(승급 적용 위치)
    pending_mover_side: Optional[str] = None          # 승급 선택 기다리는 쪽
    promo_message = ""


    def clear_selection():
        nonlocal mode, selected_from, selected_drop_kind, legal_targets, pending_move, pending_promo_rc, pending_mover_side, promo_message
        mode = "IDLE"
        selected_from = None
        selected_drop_kind = None
        legal_targets = []
        pending_move = None
        pending_promo_rc = None
        pending_mover_side = None
        promo_message = ""


    def recompute_legal_targets_for_move(fr: Tuple[int,int]) -> List[Tuple[int,int]]:
        r,c = fr
        p = game.board[r][c]
        if not p or p.side != game.side_to_move:
            return []
        # Gather legal moves from this square (ignoring promotion choice for highlighting)
        moves, _ = game.legal_moves_for_side(game.side_to_move)
        ts = []
        for (a,b,_prom) in moves:
            if a == fr and b not in ts:
                ts.append(b)
        return ts

    def recompute_legal_targets_for_drop(kind: str) -> List[Tuple[int,int]]:
        _, drops = game.legal_moves_for_side(game.side_to_move)
        ts = []
        for k,(r,c) in drops:
            if k == kind:
                ts.append((r,c))
        return ts

    def handle_move_click(to_rc: Tuple[int,int]):
        nonlocal mode, pending_move, pending_promo_rc, pending_mover_side, promo_message
        assert selected_from is not None
        fr = selected_from
        p = game.board[fr[0]][fr[1]]
        if not p:
            return

        must = game.promotion_mandatory_for_move(p, to_rc)
        opt = game.promotion_optional_for_move(p, fr, to_rc)

        if must:
            # 강제 승급(보병 마지막 줄 등) -> 즉시 확정 + 턴 넘김
            game.apply_move((fr, to_rc, True))
            clear_selection()
            return

        if opt:
            # 1) 일단 이동 (승급은 아직)
            mover = p.side  # side_to_move와 같아야 함
            game.apply_move_no_turn(fr, to_rc)

            # 2) 승급 선택 대기 상태로
            pending_move = (fr, to_rc, False)
            pending_promo_rc = to_rc
            pending_mover_side = mover
            mode = "PROMOTE_QUERY"
            return

        # 승급 불가/불필요
        game.apply_move((fr, to_rc, False))
        clear_selection()


    def finalize_promotion_choice(promote_yes: bool):
        nonlocal pending_move, pending_promo_rc, pending_mover_side

        if pending_promo_rc is None or pending_mover_side is None:
            return

        # promote in place if chosen
        if promote_yes:
            game.promote_piece_at(pending_promo_rc)

        # 이제서야 턴 넘김(중요!)
        game.side_to_move = opponent(pending_mover_side)

        clear_selection()


    def check_end_conditions() -> Optional[str]:
        # After a move/drop, side_to_move already switched.
        # Check if side_to_move is checkmated.
        stm = game.side_to_move
        if game.is_checkmate(stm):
            winner = opponent(stm)
            return f"CHECKMATE! Winner: {winner}"
        return None

    end_message = ""

    clock = pygame.time.Clock()
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if mode == "PROMOTE_QUERY":
                        finalize_promotion_choice(False)  # ESC = 승급 안함
                        msg = check_end_conditions()
                        if msg: end_message = msg
                    else:
                        clear_selection()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if end_message:
                    # Click to restart
                    game = Minishogi()
                    end_message = ""
                    clear_selection()
                    continue

                mx, my = event.pos
                x, y = pixel_to_disp(mx, my)
                reg = which_region(x, y)

                if mode == "PROMOTE_QUERY":
                    # O/X bar click handling (mobile-friendly)
                    if pending_mover_side is not None:
                        bar, left, right = promo_choice_rects(pending_mover_side)
                        if left.collidepoint(event.pos):
                            finalize_promotion_choice(True)
                            msg = check_end_conditions()
                            if msg: end_message = msg
                        elif right.collidepoint(event.pos):
                            finalize_promotion_choice(False)
                            msg = check_end_conditions()
                            if msg: end_message = msg
                        # else: ignore outside clicks
                    continue


                # Board click
                if reg == "BOARD":
                    r,c = board_rc_from_disp(x, y)
                    if not in_bounds(r,c):
                        continue

                    if mode == "IDLE":
                        p = game.board[r][c]
                        if p and p.side == game.side_to_move:
                            selected_from = (r,c)
                            legal_targets = recompute_legal_targets_for_move(selected_from)
                            if legal_targets:
                                mode = "MOVE_SELECTED"
                            else:
                                clear_selection()

                    elif mode == "MOVE_SELECTED":
                        if (r,c) in legal_targets:
                            handle_move_click((r,c))
                            msg = check_end_conditions()
                            if msg: end_message = msg
                        else:
                            # allow reselection
                            p = game.board[r][c]
                            if p and p.side == game.side_to_move:
                                selected_from = (r,c)
                                legal_targets = recompute_legal_targets_for_move(selected_from)
                                mode = "MOVE_SELECTED" if legal_targets else "IDLE"
                            else:
                                clear_selection()

                    elif mode == "DROP_SELECTED":
                        if (r,c) in legal_targets and selected_drop_kind is not None:
                            game.apply_drop((selected_drop_kind, (r,c)))
                            clear_selection()
                            msg = check_end_conditions()
                            if msg: end_message = msg
                        else:
                            clear_selection()

                # Hand click (only allow current player to pick from their hand area)
                elif reg in ("TOP_HAND", "BOT_HAND"):
                    side = "W" if reg == "TOP_HAND" else "B"
                    if side != game.side_to_move:
                        continue
                    # Determine which column and row
                    col = int(x)
                    if not (0 <= col < 5):
                        continue
                    kind = PIECES[col]
                    y0 = TOP_HAND_Y0 if reg == "TOP_HAND" else BOT_HAND_Y0
                    row = hand_slot_from_disp(y, y0)
                    if row not in (0,1):
                        continue
                    cnt = game.hands[side][kind]
                    if cnt <= row:
                        # clicked an empty slot -> cancel
                        clear_selection()
                        continue
                    # select this piece to drop
                    selected_drop_kind = kind
                    legal_targets = recompute_legal_targets_for_drop(kind)
                    if legal_targets:
                        mode = "DROP_SELECTED"
                    else:
                        clear_selection()

                else:
                    clear_selection()

        # Draw
        screen.fill(BG)
        draw_grid(screen)
        draw_labels(screen, font_small)
        draw_hands(screen, game, font_main, font_sub)
        draw_board(screen, game, font_main, font_sub)

        draw_highlights(
            screen,
            "MOVE" if mode == "MOVE_SELECTED" else ("DROP" if mode == "DROP_SELECTED" else "NONE"),
            selected_from,
            selected_drop_kind,
            legal_targets,
            game
        )

        status_msg = ""
        if mode == "DROP_SELECTED" and selected_drop_kind:
            status_msg = f"Dropping: {selected_drop_kind}"
        if mode == "PROMOTE_QUERY":
            status_msg = promo_message

        if end_message:
            # overlay
            overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            screen.blit(overlay, (0,0))
            big = pygame.font.SysFont("Arial", 34, bold=True).render(end_message, True, (255,255,255))
            sub = pygame.font.SysFont("Arial", 20).render("Click to restart", True, (255,255,255))
            screen.blit(big, big.get_rect(center=(WINDOW_W//2, WINDOW_H//2 - 10)))
            screen.blit(sub, sub.get_rect(center=(WINDOW_W//2, WINDOW_H//2 + 25)))
        else:
            if mode == "PROMOTE_QUERY" and pending_move is not None:
                fr, to, _ = pending_move
                p0 = game.board[fr[0]][fr[1]]
                if not end_message and mode == "PROMOTE_QUERY" and pending_mover_side is not None:
                    draw_promo_choice_bar(screen, font_small, pending_mover_side)

            draw_status(screen, game, font_small, status_msg)

        pygame.display.flip()

if __name__ == "__main__":
    main()

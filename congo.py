import pygame, sys, math, random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set

# =========================
# Fancy Graphics Edition
# - Procedural piece icons (no image files needed)
# - River ripple animation
# - Capture splash effect
# - Last-move arrow
# - Legal move dots (green) & monkey jumps (violet)
# - Subtle drop shadows / rounded tiles
# =========================

# ---- Board/Rules Config ----
GRID = 7
CELL = 96
MARGIN = 40
W, H = MARGIN*2 + GRID*CELL, MARGIN*2 + GRID*CELL + 60
FPS = 60
RIVER_ROW = 3

WHITE_SIDE = 'W'
BLACK_SIDE = 'B'

LION='L'; ZEBRA='Z'; ELEPHANT='E'; GIRAFFE='G'; MONKEY='M'; CROC='C'; PAWN='P'; SUPERP='S'
PIECE_ORDER = [GIRAFFE, MONKEY, ELEPHANT, LION, ELEPHANT, CROC, ZEBRA]

WHITE_CASTLE = {(r,c) for r in range(4,7) for c in range(2,5)}
BLACK_CASTLE = {(r,c) for r in range(0,3) for c in range(2,5)}

# ---- Colors ----
BG = (19,19,24)
GRID_C = (58,58,66)
RIVER_FILL = (67,141,198)
CASTLE_FILL = (215,200,150)
PANEL_TEXT = (230,230,235)
SEL = (255,220,120)
LEGAL = (58, 214, 146)
CAPTURE = (220,40,40)
JUMP = (184,120,250)
LAST = (250, 190, 60)

WHITE_FILL = (240,240,246)
WHITE_EDGE = (35,35,45)
BLACK_FILL = (36,37,42)
BLACK_EDGE = (225,225,235)
SHADOW = (0,0,0,90)

@dataclass
class Piece:
    side: str
    kind: str
    river_deadline_turn: Optional[int] = None
    has_moved: bool = False

# ---- Helpers ----
def in_bounds(r,c): return 0 <= r < GRID and 0 <= c < GRID

def is_river(r,c): return r == RIVER_ROW

def forward_dir(side):
    return -1 if side==WHITE_SIDE else 1

# ---- Game Core ----
class Game:
    def __init__(self):
        self.board: List[List[Optional[Piece]]] = [[None]*GRID for _ in range(GRID)]
        self.turn = 0
        self.sel: Optional[Tuple[int,int]] = None
        self.multi_jump_piece: Optional[Tuple[int,int]] = None
        self.multi_jump_path: List[Tuple[int,int]] = []  # stores jumped coords (for monkey)
        self.game_over = False
        self.winner: Optional[str] = None
        self.last_move: Optional[Tuple[Tuple[int,int], Tuple[int,int]]] = None
        self.splashes: List[dict] = []  # capture splash animations
        self.place_initial()

    def side_to_move(self): return WHITE_SIDE if self.turn % 2 == 0 else BLACK_SIDE

    def place_initial(self):
        for c, kind in enumerate(PIECE_ORDER):
            self.board[6][c] = Piece(WHITE_SIDE, kind)
            self.board[0][c] = Piece(BLACK_SIDE, kind)
        for c in range(GRID):
            self.board[5][c] = Piece(WHITE_SIDE, PAWN)
            self.board[1][c] = Piece(BLACK_SIDE, PAWN)

    def occupied_by_side(self, r,c, side):
        p = self.board[r][c]
        return p is not None and p.side == side

    def enemy_at(self, r,c, side):
        p = self.board[r][c]
        return p is not None and p.side != side

    def empty(self, r,c):
        return self.board[r][c] is None

    def path_between(self, a,b):
        (r1,c1),(r2,c2) = a,b
        dr = (r2-r1); dc=(c2-c1)
        sr = 0 if dr==0 else (1 if dr>0 else -1)
        sc = 0 if dc==0 else (1 if dc>0 else -1)
        path=[]; r,c = r1+sr, c1+sc
        while (r,c)!=(r2,c2):
            path.append((r,c)); r+=sr; c+=sc
        return path

    def unobstructed(self, path):
        for (r,c) in path:
            if self.board[r][c] is not None:
                return False
        return True

    def find_lion(self, side):
        for r in range(GRID):
            for c in range(GRID):
                p=self.board[r][c]
                if p and p.side==side and p.kind==LION:
                    return (r,c)
        return None

    # ------------- Move generation per piece -------------
    def legal_moves(self, r,c):
        p = self.board[r][c]
        if not p: return []
        side = p.side
        moves: Set[Tuple[int,int]] = set()

        if p.kind == LION:
            # king-like inside castle
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    rr,cc=r+dr,c+dc
                    if in_bounds(rr,cc) and ((rr,cc) in (WHITE_CASTLE if side==WHITE_SIDE else BLACK_CASTLE)):
                        if not self.occupied_by_side(rr,cc, side):
                            moves.add((rr,cc))
            # flying lion capture if unobstructed path crossing river
            enemy_lion = self.find_lion(BLACK_SIDE if side==WHITE_SIDE else WHITE_SIDE)
            if enemy_lion:
                er,ec = enemy_lion
                same_file = (c==ec)
                diag = (abs(r-er)==abs(c-ec))
                if same_file or diag:
                    path = self.path_between((r,c),(er,ec))
                    crosses = any(rr==RIVER_ROW for rr,cc in path+[(er,ec)])
                    if crosses and self.unobstructed(path):
                        moves.add((er,ec))
            return list(moves)

        if p.kind == ZEBRA:
            for dr,dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
                rr,cc=r+dr,c+dc
                if in_bounds(rr,cc) and not self.occupied_by_side(rr,cc, side):
                    moves.add((rr,cc))
            return list(moves)

        if p.kind == ELEPHANT:
            for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                rr,cc=r+dr,c+dc
                if in_bounds(rr,cc) and not self.occupied_by_side(rr,cc, side):
                    moves.add((rr,cc))
            for dr,dc in [(2,0),(-2,0),(0,2),(0,-2)]:
                rr,cc=r+dr,c+dc
                if in_bounds(rr,cc) and not self.occupied_by_side(rr,cc, side):
                    moves.add((rr,cc))
            return list(moves)

        if p.kind == GIRAFFE:
            # move-only 1 any dir
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    rr,cc=r+dr,c+dc
                    if in_bounds(rr,cc) and self.empty(rr,cc):
                        moves.add((rr,cc))
            # move&capture 2 any dir
            for dr in (-2,0,2):
                for dc in (-2,0,2):
                    if dr==0 and dc==0: continue
                    rr,cc=r+dr,c+dc
                    if in_bounds(rr,cc) and not self.occupied_by_side(rr,cc, side):
                        moves.add((rr,cc))
            return list(moves)

        if p.kind == MONKEY:
            # step 1 any dir (no cap)
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    rr,cc=r+dr,c+dc
                    if in_bounds(rr,cc) and self.empty(rr,cc):
                        moves.add((rr,cc))
            # jump capture checkers-style
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    mr,mc=r+dr,c+dc
                    jr,jc=r+2*dr,c+2*dc
                    if in_bounds(jr,jc) and self.enemy_at(mr,mc, side) and self.empty(jr,jc):
                        moves.add((jr,jc))
            return list(moves)

        if p.kind in (PAWN, SUPERP):
            f = forward_dir(side)
            # forward move / diag capture
            for dr,dc in [(f,0),(f,-1),(f,1)]:
                rr,cc=r+dr,c+dc
                if not in_bounds(rr,cc):
                    continue
                if dc==0:
                    if self.empty(rr,cc):
                        moves.add((rr,cc))
                else:
                    if self.enemy_at(rr,cc, side):
                        moves.add((rr,cc))
            # past river: 1-2 backward straight (move only)
            past = (side==WHITE_SIDE and r < RIVER_ROW) or (side==BLACK_SIDE and r > RIVER_ROW)
            if past:
                for step in (1,2):
                    rr,cc = r - f*step, c
                    if in_bounds(rr,cc) and self.empty(rr,cc):
                        if step==2 and not self.empty(r - f*1, c):
                            break
                        moves.add((rr,cc))
                    else:
                        break
            if p.kind == SUPERP:
                # sideways 1 (move/capture)
                for dc in (-1,1):
                    rr,cc=r, c+dc
                    if in_bounds(rr,cc) and not self.occupied_by_side(rr,cc, side):
                        moves.add((rr,cc))
                # backward diagonals move-only 1 or 2
                for ddr in (1,2):
                    for dc in (-1,1):
                        rr,cc = r - f*ddr, c+dc
                        if in_bounds(rr,cc) and self.empty(rr,cc):
                            moves.add((rr,cc))
            return list(moves)

        if p.kind == CROC:
            # king-like 1
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    rr,cc=r+dr,c+dc
                    if in_bounds(rr,cc) and not self.occupied_by_side(rr,cc, side):
                        moves.add((rr,cc))
            # rook toward river along file
            if not is_river(r,c):
                dir_r = 1 if r < RIVER_ROW else -1
                rr = r + dir_r
                while in_bounds(rr,c):
                    if self.occupied_by_side(rr,c, side): break
                    moves.add((rr,c))
                    if self.board[rr][c] is not None: break
                    rr += dir_r
            # in river: along rank like rook
            if is_river(r,c):
                for dc in (-1,1):
                    cc = c+dc
                    while in_bounds(r,cc):
                        if self.occupied_by_side(r,cc, side): break
                        moves.add((r,cc))
                        if self.board[r][cc] is not None: break
                        cc += dc
            return list(moves)

        return []

    # ------------- Apply & finalize -------------
    def apply_move(self, src, dst):
        sr,sc = src; dr,dc = dst
        p = self.board[sr][sc]
        assert p

        target = self.board[dr][dc]
        jumped = None
        is_monkey_jump = False
        if p.kind == MONKEY and (abs(dr-sr)==2 or abs(dc-sc)==2):
            mr,mc = (sr+dr)//2, (sc+dc)//2
            if self.enemy_at(mr,mc, p.side) and self.empty(dr,dc):
                jumped = (mr,mc)
                is_monkey_jump = True

        # normal capture (incl. lion)
        if target and p.kind != MONKEY:
            if target.kind == LION:
                self.board[dr][dc] = p; self.board[sr][sc] = None
                p.has_moved=True
                self.last_move = (src, dst)
                self.spawn_splash(dr,dc)
                self.finish_game(captured_lion=target.side)
                return
            self.board[dr][dc] = p; self.board[sr][sc] = None
            self.spawn_splash(dr,dc)
        else:
            self.board[dr][dc] = p; self.board[sr][sc] = None

        p.has_moved=True
        self.last_move = (src, dst)

        if is_monkey_jump and jumped:
            self.multi_jump_piece = (dr,dc)
            self.multi_jump_path.append(jumped)
        else:
            self.finalize_move((dr,dc))

    def finalize_move(self, pos):
        r,c = pos
        p = self.board[r][c]
        if not p: return

        # remove all jumped by monkey
        if p.kind == MONKEY and self.multi_jump_path:
            for (jr,jc) in self.multi_jump_path:
                q = self.board[jr][jc]
                if q and q.kind == LION:
                    self.board[jr][jc] = None
                    self.spawn_splash(jr,jc)
                    self.finish_game(captured_lion=q.side)
                    return
                if q:
                    self.board[jr][jc] = None
                    self.spawn_splash(jr,jc)

        # promotion
        if p.kind in (PAWN, SUPERP):
            if (p.side==WHITE_SIDE and r==0) or (p.side==BLACK_SIDE and r==6):
                p.kind = SUPERP

        # drowning bookkeeping
        if is_river(r,c) and p.kind != CROC:
            p.river_deadline_turn = self.turn + 1
        else:
            p.river_deadline_turn = None

        # cleanup chain
        self.multi_jump_piece = None
        self.multi_jump_path.clear()

        # drown any mover's piece whose deadline == current turn
        self.check_drown(self.side_to_move())

        # advance
        self.turn += 1

        # check lions exist
        if self.find_lion(WHITE_SIDE) is None:
            self.finish_game(captured_lion=WHITE_SIDE)
        elif self.find_lion(BLACK_SIDE) is None:
            self.finish_game(captured_lion=BLACK_SIDE)

    def check_drown(self, side):
        # remove any piece of 'side' still in river when deadline reached
        for r in range(GRID):
            for c in range(GRID):
                p=self.board[r][c]
                if p and p.side==side and p.kind!=CROC and is_river(r,c):
                    if p.river_deadline_turn is not None and p.river_deadline_turn <= self.turn:
                        self.board[r][c] = None
                        self.spawn_splash(r,c, water=True)

    def finish_game(self, captured_lion:str):
        self.game_over = True
        self.winner = WHITE_SIDE if captured_lion==BLACK_SIDE else BLACK_SIDE

    # ------------- FX -------------
    def spawn_splash(self, r,c, water=False):
        # simple radial particles
        x = MARGIN + c*CELL + CELL//2
        y = MARGIN + r*CELL + CELL//2
        col = (235,240,245) if not water else (180, 220, 255)
        self.splashes.append({
            'x':x,'y':y,'t':0,'life':18,'color':col,
            'parts':[{
                'ang': random.random()*math.tau,
                'spd': 2+random.random()*3,
                'r': 4+int(random.random()*6)
            } for _ in range(10)]
        })

# ---- Drawing ----
def draw_board(screen, game:Game, frame):
    screen.fill(BG)
    # river with animated waves
    ry = MARGIN + RIVER_ROW*CELL
    wave_h = 10
    wave = pygame.Surface((CELL*GRID, CELL), pygame.SRCALPHA)
    wave.fill((*RIVER_FILL, 200))
    screen.blit(wave, (MARGIN, ry))
    # ripple lines
    for i in range(6):
        t = (frame*0.06 + i*0.8)
        y = ry + CELL//2 + int(math.sin(t)*CELL*0.25*(0.6 - i*0.08))
        pygame.draw.line(screen, (235,245,255,120), (MARGIN, y), (MARGIN+GRID*CELL, y), 2)

    # castles
    for (r,c) in WHITE_CASTLE|BLACK_CASTLE:
        x = MARGIN + c*CELL; y = MARGIN + r*CELL
        rect = pygame.Rect(x,y,CELL,CELL)
        pygame.draw.rect(screen, CASTLE_FILL, rect)

    # grid
    for r in range(GRID+1):
        y = MARGIN + r*CELL
        pygame.draw.line(screen, GRID_C, (MARGIN, y), (MARGIN+GRID*CELL, y), 2)
    for c in range(GRID+1):
        x = MARGIN + c*CELL
        pygame.draw.line(screen, GRID_C, (x, MARGIN), (x, MARGIN+GRID*CELL), 2)

    # last move arrow
    if game.last_move and not game.game_over:
        (sr,sc),(dr,dc) = game.last_move
        sx = MARGIN + sc*CELL + CELL//2
        sy = MARGIN + sr*CELL + CELL//2
        dx = MARGIN + dc*CELL + CELL//2
        dy = MARGIN + dr*CELL + CELL//2
        pygame.draw.line(screen, LAST, (sx,sy), (dx,dy), 4)
        draw_arrowhead(screen, (sx,sy), (dx,dy), LAST)

    # pieces with subtle shadows
    for r in range(GRID):
        for c in range(GRID):
            p=game.board[r][c]
            if not p: continue
            x = MARGIN + c*CELL; y = MARGIN + r*CELL
            draw_piece(screen, p, x, y, CELL)
            
    # selection + legal
    if game.sel and not game.game_over:
        r,c = game.sel
        x = MARGIN + c*CELL; y = MARGIN + r*CELL
        pygame.draw.rect(screen, SEL, (x+4,y+4,CELL-8,CELL-8), 3, border_radius=10)
        moves = game.legal_moves(r,c)
        p = game.board[r][c]
        for (rr,cc) in moves:
            cx = MARGIN + cc*CELL + CELL//2
            cy = MARGIN + rr*CELL + CELL//2
            color = LEGAL
            if p and p.kind==MONKEY and (abs(rr-r)==2 or abs(cc-c)==2):
                color = JUMP
            if game.enemy_at(rr,cc,p.side):
                color = CAPTURE
            pygame.draw.circle(screen, color, (cx,cy), 10)


    # splashes
    draw_splashes(screen, game.splashes)

    # status
    font = pygame.font.SysFont(None, 28)
    if game.game_over:
        msg = f"Game over: {'White' if game.winner==WHITE_SIDE else 'Black'} wins"
    else:
        msg = f"{'White' if game.side_to_move()==WHITE_SIDE else 'Black'} to move  —  R-click/Enter to end monkey chain, R to reset"
    text = font.render(msg, True, PANEL_TEXT)
    screen.blit(text, (MARGIN, MARGIN + GRID*CELL + 12))


def draw_piece(surf, piece:Piece, x, y, size):
    # tile
    tile = pygame.Surface((size, size), pygame.SRCALPHA)
    # shadow
    sh = pygame.Surface((size-6, size-6), pygame.SRCALPHA)
    pygame.draw.rect(sh, SHADOW, (0,4,size-6,size-6), border_radius=14)
    surf.blit(sh, (x+3,y+3))
    # body
    body = pygame.Surface((size-10, size-10), pygame.SRCALPHA)
    fill = WHITE_FILL if piece.side==WHITE_SIDE else BLACK_FILL
    edge = WHITE_EDGE if piece.side==BLACK_SIDE else BLACK_EDGE
    pygame.draw.rect(body, fill, (0,0,size-10,size-10), border_radius=16)
    pygame.draw.rect(body, edge, (0,0,size-10,size-10), 2, border_radius=16)
    surf.blit(body, (x+5,y+5))

    # icon drawing area
    cx, cy = x + size//2, y + size//2
    r = size//2 - 14

    if piece.kind == LION:
        # mane
        pygame.draw.circle(surf, (212,164,86), (cx,cy), r)
        pygame.draw.circle(surf, fill, (cx,cy), r-10)
        # face
        pygame.draw.circle(surf, (196,150,90), (cx,cy+2), r-14)
        # eyes & nose
        pygame.draw.circle(surf, (30,30,30), (cx-8,cy-2), 3)
        pygame.draw.circle(surf, (30,30,30), (cx+8,cy-2), 3)
        pygame.draw.polygon(surf, (40,25,15), [(cx,cy+2),(cx-4,cy+10),(cx+4,cy+10)])

    elif piece.kind == ZEBRA:
        # body with stripes
        bw = r*2-4
        rect = pygame.Rect(cx-bw//2, cy-r//2, bw, r)
        pygame.draw.rect(surf, (235,235,240), rect)
        for i in range(6):
            t = i/6
            x1 = rect.left + int(rect.width*t)
            pygame.draw.line(surf, (40,40,50), (x1, rect.top), (x1+8, rect.bottom), 3)
        # head
        pygame.draw.circle(surf, (235,235,240), (cx+bw//2-6, cy-r//2), 10)
        pygame.draw.circle(surf, (40,40,50), (cx+bw//2-2, cy-r//2), 2)

    elif piece.kind == ELEPHANT:
        # body
        pygame.draw.ellipse(surf, (140,160,178), (cx-r, cy-r//2, 2*r, r))
        # ear
        pygame.draw.circle(surf, (160,180,198), (cx-r//2, cy), r//2)
        # trunk
        pygame.draw.rect(surf, (120,140,160), (cx+r//3, cy-6, 14, r//2+8), border_radius=7)

    elif piece.kind == GIRAFFE:
        # neck
        pygame.draw.rect(surf, (215, 180, 100), (cx-6, cy-r, 12, r+14), border_radius=6)
        # head
        pygame.draw.circle(surf, (220, 190, 120), (cx, cy-r), 10)
        # spots
        for i in range(6):
            ang = i * math.tau/6
            sx = cx + int(math.cos(ang)* (r-18))
            sy = cy + int(math.sin(ang)* (r-18))
            pygame.draw.circle(surf, (175,140,70), (sx,sy), 4)

    elif piece.kind == MONKEY:
        # head
        pygame.draw.circle(surf, (166,120,80), (cx,cy-4), r-6)
        pygame.draw.circle(surf, (210,176,140), (cx,cy), r-12)
        # eyes & smile
        pygame.draw.circle(surf, (20,20,20), (cx-8,cy-6), 3)
        pygame.draw.circle(surf, (20,20,20), (cx+8,cy-6), 3)
        pygame.draw.arc(surf, (40,30,30), (cx-12,cy-2,24,16), math.pi*0.1, math.pi*0.9, 3)

    elif piece.kind == CROC:
        # body
        pygame.draw.rect(surf, (60,140,92), (cx-r+6, cy-10, 2*r-12, 20), border_radius=10)
        # back ridges
        for i in range(-r+10, r-10, 10):
            pygame.draw.polygon(surf, (50,120,80), [(cx+i,cy-10),(cx+i+5,cy-18),(cx+i+10,cy-10)])
        # mouth
        pygame.draw.polygon(surf, (220,240,220), [(cx+r-12,cy-6),(cx+r-2,cy),(cx+r-12,cy+6)])

    elif piece.kind == PAWN or piece.kind == SUPERP:
        # pawn body
        pygame.draw.circle(surf, (170,170,180), (cx,cy-10), r-18)
        pygame.draw.rect(surf, (190,190,200), (cx-(r-18), cy-10, 2*(r-18), r-4), border_radius=8)
        if piece.kind == SUPERP:
            # star badge
            draw_star(surf, (cx, cy-22), 6, 8, 4, (250,215,90))


def draw_star(surf, center, spikes, outer_r, inner_r, color):
    cx,cy=center
    pts=[]
    for i in range(spikes*2):
        ang = i*math.pi/spikes
        r = outer_r if i%2==0 else inner_r
        pts.append((cx + math.cos(ang)*r, cy + math.sin(ang)*r))
    pygame.draw.polygon(surf, color, pts)


def draw_arrowhead(surf, start, end, color):
    sx,sy=start; ex,ey=end
    ang = math.atan2(ey-sy, ex-sx)
    size = 10
    p1 = (ex,ey)
    p2 = (ex - size*math.cos(ang - 0.4), ey - size*math.sin(ang - 0.4))
    p3 = (ex - size*math.cos(ang + 0.4), ey - size*math.sin(ang + 0.4))
    pygame.draw.polygon(surf, color, [p1,p2,p3])


def draw_splashes(surf, splashes:List[dict]):
    rm=[]
    for s in splashes:
        s['t'] += 1
        t = s['t']; life=s['life']
        alpha = max(0, 200 - int(200*(t/life)))
        for prt in s['parts']:
            ang=prt['ang']; spd=prt['spd']; rr=prt['r']
            dx = math.cos(ang)*spd*t
            dy = math.sin(ang)*spd*t*0.8
            col = (*s['color'], alpha)
            circle = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
            pygame.draw.circle(circle, col, (rr,rr), rr)
            surf.blit(circle, (s['x']+dx-rr, s['y']+dy-rr))
        if t>=life: rm.append(s)
    for s in rm:
        splashes.remove(s)

# ---- Main Loop ----
class CongoApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W,H))
        pygame.display.set_caption("Congo (Fancy Graphics Edition)")
        self.clock = pygame.time.Clock()
        self.game = Game()
        self.frame = 0

    def run(self):
        running=True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running=False
                elif e.type == pygame.KEYDOWN and not self.game.game_over:
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.game.multi_jump_piece:
                        self.game.finalize_move(self.game.multi_jump_piece)
                    if e.key == pygame.K_r:
                        self.game = Game()
                elif e.type == pygame.MOUSEBUTTONDOWN and not self.game.game_over:
                    mx,my = e.pos
                    if not (MARGIN <= mx < MARGIN+GRID*CELL and MARGIN <= my < MARGIN+GRID*CELL):
                        continue
                    c = (mx - MARGIN)//CELL
                    r = (my - MARGIN)//CELL

                    if e.button == 3 and self.game.multi_jump_piece:
                        self.game.finalize_move(self.game.multi_jump_piece)
                        continue

                    if self.game.sel is None:
                        if self.game.board[r][c] and self.game.board[r][c].side == self.game.side_to_move():
                            self.game.sel = (r,c)
                    else:
                        sr,sc = self.game.sel
                        p = self.game.board[sr][sc]
                        if p and (r,c) in self.game.legal_moves(sr,sc):
                            # lion castle constraint already baked into generator
                            self.game.apply_move((sr,sc),(r,c))
                            # chaining handled inside
                            if self.game.multi_jump_piece:
                                self.game.sel = self.game.multi_jump_piece
                            else:
                                self.game.sel = None
                        else:
                            # reselect if clicking own piece
                            if self.game.board[r][c] and self.game.board[r][c].side == self.game.side_to_move():
                                self.game.sel = (r,c)
                            else:
                                self.game.sel = None

            draw_board(self.screen, self.game, self.frame)
            pygame.display.flip()
            self.clock.tick(FPS)
            self.frame += 1

        pygame.quit(); sys.exit()

if __name__ == "__main__":
    CongoApp().run()

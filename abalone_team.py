import math
import pygame
from typing import Dict, Tuple, Set, List, Optional

# -------------------- Types / constants --------------------
Pos = Tuple[int, int]  # axial (q, r)

MAX_PLAYERS = 7
EMPTY = 0
P1 = 1
P2 = 2
P3 = 3
P4 = 4
P5 = 5
P6 = 6
P7 = 7
def next_player(cur: int, players: int) -> int:
    # players: 2..6, player ids: 1..players
    return 1 if cur >= players else cur + 1

BOARD_R = 4                       # hex radius 4 => 61 cells
ROW_LENS = [5, 6, 7, 8, 9, 8, 7, 6, 5]
DEFAULT_WIN_PUSHED = 6

# Axial directions (6)
DIRS: List[Pos] = [
    (1, 0),    # down-right
    (1, -1),   # right
    (0, -1),   # up-right
    (-1, 0),   # up-left
    (-1, 1),   # left
    (0, 1),    # down-left
]

# Optional keyboard mapping (you can disable by setting ENABLE_KEY_MOVES=False)
ENABLE_KEY_MOVES = True
KEY_TO_DIR: Dict[int, Pos] = {
    pygame.K_d: (1, 0),     # ↘
    pygame.K_e: (1, -1),    # →
    pygame.K_w: (0, -1),    # ↗
    pygame.K_q: (-1, 0),    # ↖
    pygame.K_a: (-1, 1),    # ←
    pygame.K_s: (0, 1),     # ↙
}

# -------------------- Board / geometry --------------------
def make_cells(R: int = BOARD_R) -> Set[Pos]:
    cells = {
        (q, r)
        for q in range(-R, R + 1)
        for r in range(-R, R + 1)
        if max(abs(q), abs(r), abs(q + r)) <= R
    }
    assert len(cells) == 61
    return cells

def make_empty_board(cells: Set[Pos]) -> Dict[Pos, int]:
    return {pos: EMPTY for pos in cells}

def q_range_for_r(r: int, R: int = BOARD_R):
    q_min = max(-R, -r - R)
    q_max = min(R, -r + R)
    return q_min, q_max  # length = q_max-q_min+1

def layout_to_preset(layout_rows) -> Dict[Pos, int]:
    """
    layout_rows: 9줄 리스트, 길이 [5,6,7,8,9,8,7,6,5]
    각 원소는 0/None/'.'/' ' => 빈칸, 1..6 => 플레이어
    """
    preset: Dict[Pos, int] = {}
    assert len(layout_rows) == 9
    for i, row in enumerate(layout_rows):
        r = i - 4
        q_min, q_max = q_range_for_r(r, BOARD_R)
        assert len(row) == (q_max - q_min + 1), f"Row {i} length mismatch."
        for j, v in enumerate(row):
            if v in (0, None, '.', ' '):
                continue
            pid = int(v)
            q = q_min + j
            preset[(q, r)] = pid
    return preset

def make_empty_layout():
    return [['.' for _ in range(L)] for L in ROW_LENS]

def preset_to_layout(preset: Dict[Pos, int]):
    lay = make_empty_layout()
    for (q, r), pid in preset.items():
        i = r + 4
        q_min, q_max = q_range_for_r(r, BOARD_R)
        j = q - q_min
        if 0 <= i < 9 and 0 <= j < ROW_LENS[i]:
            lay[i][j] = pid
    return lay

def flower(center: Pos, pid: int) -> Dict[Pos, int]:
    q, r = center
    pts = {(q, r)}
    for dq, dr in DIRS:
        pts.add((q + dq, r + dr))
    return {p: pid for p in pts}

def mirror(p: Pos) -> Pos:
    return (-p[0], -p[1])

# -------------------- Presets (as 9-row layouts) --------------------
def build_2p_classic_layout():
    # 표준 14/14 배치: axial 기준
    preset: Dict[Pos, int] = {}
    # P1 (top)
    for q in range(0, 5):      # r=-4, q=0..4
        preset[(q, -4)] = P1
    for q in range(-1, 5):     # r=-3, q=-1..4
        preset[(q, -3)] = P1
    for q in (0, 1, 2):        # r=-2, q=0,1,2
        preset[(q, -2)] = P1
    # P2 (bottom)
    for q in range(-4, 1):     # r=4, q=-4..0
        preset[(q, 4)] = P2
    for q in range(-4, 2):     # r=3, q=-4..1
        preset[(q, 3)] = P2
    for q in (-2, -1, 0):      # r=2, q=-2,-1,0
        preset[(q, 2)] = P2
    return preset_to_layout(preset)

def build_belgian_daisy_layout():
    # 꽃 7개*2 덩어리 (총 14)씩 대칭 배치
    preset: Dict[Pos, int] = {}
    preset |= flower((0, -3), P1)
    preset |= flower(( 0,  3), P1)
    preset |= flower(( 3, -3), P2)
    preset |= flower((-3,  3), P2)
    return preset_to_layout(preset)

def build_face2face_layout():
    # 좌우 마주보는 덩어리(좌측 14개 찌그러진 육각형 + 원점대칭)
    left = [
        (-4, 0), (-4, 1), (-4, 2),    # 3
        (-3, -1),(-3,0), (-3, 1), (-3, 2),             # 4
        (-2, -2), (-2, -1),  (-2, 0), (-2, 1),                      # 4
        (-1, -2), (-1, -1), (-1, -0),                               # 3  => 14
    ]
    preset: Dict[Pos, int] = {p: P1 for p in left}
    preset.update({mirror(p): P2 for p in left})
    return preset_to_layout(preset)

ALIEN_ATTACK_LAYOUT = [
    # r = -4  (5)
    [2,'.',  2, '.', 2],

    # r = -3  (6)
    ['.', 2, 1, 1, 2, '.'],

    # r = -2  (7)
    ['.', 2, 1, 2, 1, 2, '.'],

    # r = -1  (8)
    ['.', '.', '.', 2, 2, '.', '.', '.'],

    # r =  0  (9)
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],

    # r =  1  (8)
    ['.', '.', '.', 1, 1, '.', '.', '.'],

    # r =  2  (7)
    ['.', 1, 2, 1, 2, 1, '.'],

    # r =  3  (6)
    ['.', 1, 2, 2, 1, '.'],

    # r =  4  (5)
    [1,'.',  1, '.', 1]]

PRESETS = {
    "2P-Classic": {
        "players": 2,
        "win_push": DEFAULT_WIN_PUSHED,
        "layout": build_2p_classic_layout(),
    },
    "Belgian Daisy": {
        "players": 2,
        "win_push": DEFAULT_WIN_PUSHED,
        "layout": build_belgian_daisy_layout(),
    },
    "Alien Attack": {
        "players": 2,
        "win_push": DEFAULT_WIN_PUSHED,
        "layout": ALIEN_ATTACK_LAYOUT,
    },
    "Face 2 Face": {
        "players": 2,
        "win_push": DEFAULT_WIN_PUSHED,
        "layout": build_face2face_layout(),
    },
}



def add_preset(name: str, players: int, layout_rows, win_push=DEFAULT_WIN_PUSHED):
    PRESETS[name] = {"players": players, "win_push": win_push, "layout": layout_rows}


THREEP_CLASSIC_LAYOUT = [
    [1, 1, '.', 3, 3],                          # 5
    [1, 1, '.', '.', 3, 3],                     # 6
    [1, 1, '.', '.', '.', 3, 3],                # 7
    [1, 1, '.', '.', '.', '.', 3, 3],           # 8
    [1, 1, '.', '.', '.', '.', '.', 3, 3],      # 9
    [1, '.', '.', '.', '.', '.', '.', 3],       # 8  (원본 7칸 -> '.' 1개 추가)
    ['.', '.', '.', '.', '.', '.', '.'],        # 7  (원본 5칸 -> '.' 2개 추가)
    [2, 2, 2, 2, 2, 2],                         # 6
    [2, 2, 2, 2, 2],                            # 5
]

add_preset("3P-Classic", 3, THREEP_CLASSIC_LAYOUT)

FOURP_CLASSIC_LAYOUT = [
    [1, '.', '.', '.', 4],                          # 5
    [1, 1, '.', '.', 4, 4],                     # 6
    [1, 1, 1, '.', 4, 4, 4],                # 7
    [1, 1, 1, '.', '.', 4, 4, 4],           # 8
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],      # 9
    [2, 2, 2, '.', '.', 3, 3, 3],       # 8  (원본 7칸 -> '.' 1개 추가)
    [2, 2, 2, '.', 3, 3, 3],       # 7  (원본 5칸 -> '.' 2개 추가)
    [2, 2, '.', '.', 3, 3],                         # 6
    [2, '.', '.', '.', 3],                           # 5
]

add_preset("4P-Classic", 4, FOURP_CLASSIC_LAYOUT)


FIVEP_CLASSIC_LAYOUT = [
    [1, 1, '.', 4, 4],                          # 5
    [1, 1, '.', '.', 4, 4],                     # 6
    [1, 1, '.', '.', '.', 4, 4],                # 7
    [1, 1, '.', 5, 5, '.', 4, 4],           # 8
    ['.', '.', '.', 5, 5, 5, '.', '.', '.'],      # 9
    [2, 2, '.', 5, 5, '.', 3, 3],       # 8  (원본 7칸 -> '.' 1개 추가)
    [2, 2, '.', '.', '.', 3, 3],       # 7  (원본 5칸 -> '.' 2개 추가)
    [2, 2, '.', '.', 3, 3],                         # 6
    [2, 2, '.', 3, 3],                           # 5
]

add_preset("5P-Classic", 5, FIVEP_CLASSIC_LAYOUT)


SIXP_CLASSIC_LAYOUT = [
    ['.', 1, 1, 1, '.'],                          # 5
    [2, '.', 1, 1, '.', 6],                     # 6
    [2, 2, '.', 1, '.', 6, 6],                # 7
    [2, 2, 2, '.', '.', 6, 6, 6],           # 8
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],      # 9
    [3, 3, 3, '.', '.', 5, 5, 5],       # 8  (원본 7칸 -> '.' 1개 추가)
    [3, 3, '.', 4, '.', 5, 5],       # 7  (원본 5칸 -> '.' 2개 추가)
    [3, '.', 4, 4, '.', 5],                         # 6
    ['.', 4, 4, 4, '.'],                           # 5
]

add_preset("6P-Classic", 6, SIXP_CLASSIC_LAYOUT)

SIXP_CORNER_LAYOUT = [
    [1, 1, '.', 6, 6],                          # 5
    [1, 1, 1, 6, 6, 6],                     # 6
    ['.', 1, '.', '.', '.', 6, '.'],                # 7
    [2, 2, '.', '.', '.', '.', 5, 5],           # 8
    [2, 2, '.', '.', '.', '.', '.', 5, 5],      # 9
    [2, 2, '.', '.', '.', '.', 5, 5],       # 8  (원본 7칸 -> '.' 1개 추가)
    ['.', 3, '.', '.', '.', 4, '.'],       # 7  (원본 5칸 -> '.' 2개 추가)
    [3, 3, 3, 4, 4, 4],                         # 6
    [3, 3, '.', 4, 4],                           # 5
]

add_preset("6P-Corner", 6, SIXP_CORNER_LAYOUT)

# -------------------- Rendering helpers (pointy-top) --------------------
def axial_to_pixel(q: int, r: int, size: float, origin: Tuple[float, float]) -> Tuple[float, float]:
    ox, oy = origin
    x = size * math.sqrt(3) * (q + r / 2) + ox
    y = size * 1.5 * r + oy
    return x, y

def hex_corners(cx: float, cy: float, size: float):
    pts = []
    for k in range(6):
        ang = math.radians(30 + 60 * k)
        pts.append((cx + size * math.cos(ang), cy + size * math.sin(ang)))
    return pts

# -------------------- Axial ops --------------------
def add(a: Pos, b: Pos) -> Pos:
    return (a[0] + b[0], a[1] + b[1])

def sub(a: Pos, b: Pos) -> Pos:
    return (a[0] - b[0], a[1] - b[1])

def neg(d: Pos) -> Pos:
    return (-d[0], -d[1])

def in_board(pos: Pos, cells: Set[Pos]) -> bool:
    return pos in cells

def opponent(pid: int) -> int:
    return P2 if pid == P1 else P1

# -------------------- Line detection --------------------
def detect_line_axis(sel: List[Pos]) -> Optional[str]:
    if len(sel) <= 1:
        return "q"
    qs = {p[0] for p in sel}
    rs = {p[1] for p in sel}
    ss = {p[0] + p[1] for p in sel}
    if len(qs) == 1: return "q"
    if len(rs) == 1: return "r"
    if len(ss) == 1: return "s"
    return None

def step_for_axis(axis: str) -> Pos:
    if axis == "q": return (0, 1)
    if axis == "r": return (1, 0)
    return (1, -1)  # "s"

def sort_along_axis(sel: List[Pos], axis: str) -> List[Pos]:
    if axis == "q": return sorted(sel, key=lambda p: p[1])
    if axis == "r": return sorted(sel, key=lambda p: p[0])
    return sorted(sel, key=lambda p: p[0])  # "s"

def is_contiguous_in_line(sel: List[Pos], axis: str) -> bool:
    if len(sel) <= 1:
        return True
    ordered = sort_along_axis(sel, axis)
    step = step_for_axis(axis)
    diffs = [sub(ordered[i + 1], ordered[i]) for i in range(len(ordered) - 1)]
    # must be monotone with exact step
    return all(d == diffs[0] for d in diffs) and (diffs[0] == step or diffs[0] == neg(step))

def dir_is_along_axis(d: Pos, axis: str) -> bool:
    if axis == "q": return d in [(0, 1), (0, -1)]
    if axis == "r": return d in [(1, 0), (-1, 0)]
    return d in [(1, -1), (-1, 1)]  # "s"

def projection(pos: Pos, d: Pos) -> int:
    return pos[0] * d[0] + pos[1] * d[1]

# -------------------- Move rules (1~3 inline + broadside; push 1~2) --------------------
def try_move(board, cells, current, selected, d, pushed_out, team_of, team_control):
    
    if len(selected) == 0:
        return False, "Select 1-3 marbles first."
    if len(selected) > 3:
        return False, "You can move at most 3 marbles."
    if not selection_allowed(selected, current, board, team_of, team_control):
        return False, "Invalid team selection."

    axis = detect_line_axis(selected)
    if axis is None:
        return False, "Selection must be in a straight line."
    if not is_contiguous_in_line(selected, axis):
        return False, "Selected marbles must be contiguous."

    # single marble
    if len(selected) == 1:
        src = selected[0]
        dst = add(src, d)
        if not in_board(dst, cells):
            return False, "Can't move off the board."
        if board[dst] != EMPTY:
            return False, "Destination occupied."
        pid0 = board[src]
        board[dst] = pid0
        board[src] = EMPTY
        return True, "Moved."

    inline = dir_is_along_axis(d, axis)

    if not inline:
        # broadside: all dests must be empty and in-board
        dests = [add(p, d) for p in selected]
        if any((not in_board(x, cells)) for x in dests):
            return False, "Can't broadside off the board."
        if any(board[x] != EMPTY for x in dests):
            return False, "Broadside blocked."
        owners = {p: board[p] for p in selected}

        for p in selected:
            board[p] = EMPTY
        for p in selected:
            board[add(p, d)] = owners[p]
        return True, "Broadside moved."

    # inline: determine front-most along d
    ordered = sorted(selected, key=lambda p: projection(p, d))
    front = ordered[-1]
    next_pos = add(front, d)

    # simple slide if empty
    if in_board(next_pos, cells) and board[next_pos] == EMPTY:
        owners = {p: board[p] for p in ordered}

        for p in reversed(ordered):
            board[add(p, d)] = owners[p]
            board[p] = EMPTY
        return True, "Inline moved."

    if not in_board(next_pos, cells):
        return False, "Can't move off the board."

    if team_of is None:
        if board[next_pos] == current:
            return False, "Inline blocked by your own marble."
    else:
        if team_of.get(board[next_pos]) == team_of[current]:
            return False, "Inline blocked by your team marble."


    # --- multi-player push: the chain must be same-owner (first encountered pid) ---
    chain_pid = board[next_pos]        # someone else's pid
    if chain_pid == EMPTY:
        return False, "Unexpected."

    opp_chain = []          # [(pos, pid), ...]
    cur = next_pos

    while in_board(cur, cells):
        pid = board[cur]
        if pid == EMPTY:
            break

        # 팀전: 아군이면 push 불가
        if team_of is not None and team_of.get(pid) == team_of[current]:
            return False, "Cannot push your team marble."

        # 개인전: 첫 pid와 달라지면 중단
        if team_of is None:
            if pid != board[next_pos]:
                break

        opp_chain.append((cur, pid))
        cur = add(cur, d)

    opp_n = len(opp_chain)
    my_n = len(selected)

    if opp_n >= my_n:
        return False, "Not enough force to push."
    if opp_n > 2:
        return False, "Can push at most 2 marbles."

    after = cur

    # 마지막 돌이 탈락
    if not in_board(after, cells):
        last_pos, last_pid = opp_chain[-1]
        pushed_out[last_pid] += 1

        for i in range(len(opp_chain) - 1, 0, -1):
            pos, pid = opp_chain[i - 1]
            board[add(pos, d)] = pid
        board[opp_chain[0][0]] = EMPTY
    else:
        # 빈 칸으로 밀림
        board[after] = opp_chain[-1][1]
        for i in range(len(opp_chain) - 1, 0, -1):
            pos, pid = opp_chain[i]
            board[add(pos, d)] = pid
        board[opp_chain[0][0]] = EMPTY


    # shift our marbles
    owners = {p: board[p] for p in ordered}
    for p in reversed(ordered):
        board[add(p, d)] = owners[p]
        board[p] = EMPTY

    return True, "Pushed."


# -------------------- Picking / click-to-direction --------------------
def pick_cell(mouse_xy: Tuple[int, int], cells: Set[Pos], size: float, origin: Tuple[float, float]) -> Optional[Pos]:
    mx, my = mouse_xy
    best = None
    best_d2 = 1e18
    thresh2 = (size * 0.85) ** 2
    for (q, r) in cells:
        cx, cy = axial_to_pixel(q, r, size, origin)
        d2 = (cx - mx) ** 2 + (cy - my) ** 2
        if d2 < best_d2:
            best_d2 = d2
            best = (q, r)
    if best is None or best_d2 > thresh2:
        return None
    return best

def infer_move_dir_from_click(selected: List[Pos], clicked: Pos) -> Optional[Pos]:
    if not selected:
        return None

    cand_ds = set()
    for p in selected:
        dq, dr = clicked[0] - p[0], clicked[1] - p[1]
        if (dq, dr) in DIRS:
            cand_ds.add((dq, dr))

    if len(selected) == 1:
        if len(cand_ds) == 1:
            return next(iter(cand_ds))
        return None

    axis = detect_line_axis(selected)
    if axis is None or not is_contiguous_in_line(selected, axis):
        return None

    # inline: click must be exactly one step in front/back of the chain
    for d in DIRS:
        if not dir_is_along_axis(d, axis):
            continue
        ordered = sorted(selected, key=lambda p: projection(p, d))
        front = ordered[-1]
        back = ordered[0]
        if clicked == add(front, d):
            return d
        if clicked == add(back, neg(d)):
            return neg(d)

    # broadside: click must be one-step destination of any selected marble with same d
    for d in cand_ds:
        if dir_is_along_axis(d, axis):
            continue
        dests = {add(p, d) for p in selected}
        if clicked in dests:
            return d

    return None

# -------------------- UI Buttons --------------------
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, surf, font, bg=(230, 230, 230), fg=(20, 20, 20), border=(60, 60, 60)):
        pygame.draw.rect(surf, bg, self.rect, border_radius=10)
        pygame.draw.rect(surf, border, self.rect, width=2, border_radius=10)
        label = font.render(self.text, True, fg)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

def start_menu(screen, presets, default_key="2P-Classic") -> Optional[tuple]:
    font_big = pygame.font.SysFont("consolas", 36, bold=True)
    font = pygame.font.SysFont("consolas", 22)
    font_small = pygame.font.SysFont("consolas", 16)
    W, H = screen.get_size()

    keys = list(presets.keys())
    selected = default_key if default_key in presets else keys[0]

    # team choice UI only (not applied to gameplay yet)
    # values: "ffa", "opposite", "alternate"
    team_choice = "ffa"

    btns = []
    x, y = 60, 150
    for k in keys:
        btns.append((k, Button((x, y, 420, 48), k)))
        y += 60

    # Left-bottom buttons
    play_btn = Button((60, y + 20, 200, 52), "Play")
    quit_btn = Button((280, y + 20, 200, 52), "Quit")

    # ---- Right panel: Team Settings ----
    panel_x = 520
    panel_y = 150
    panel_w = W - panel_x - 60
    panel_h = 260

    team_ffa_btn = Button((panel_x, panel_y + 60, panel_w, 44), "Free-for-all")
    team_opp_btn = Button((panel_x, panel_y + 120, panel_w, 44), "Opposite Pairs")
    team_alt_btn = Button((panel_x, panel_y + 180, panel_w, 44), "Alternate Teams")

    msg = ""

    clock = pygame.time.Clock()
    while True:
        # compute eligibility (block only for odd players, but allow 2P)
        players = int(presets[selected].get("players", 2))
        team_requested = (team_choice != "ffa")
        team_blocked = team_requested and (players % 2 == 1) and (players != 2)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # left preset selection
                for k, b in btns:
                    if b.hit(e.pos):
                        selected = k
                        msg = ""
                # right team selection
                if team_ffa_btn.hit(e.pos):
                    team_choice = "ffa"
                    msg = ""
                elif team_opp_btn.hit(e.pos):
                    team_choice = "opposite"
                    msg = ""
                elif team_alt_btn.hit(e.pos):
                    team_choice = "alternate"
                    msg = ""

                # play/quit
                if quit_btn.hit(e.pos):
                    return None
                if play_btn.hit(e.pos):
                    if team_blocked:
                        msg = "Team mode requires 4 or 6 players."
                    else:
                        # return selection + team_choice (even if not used yet)
                        return (selected, team_choice)

        # ---- draw ----
        screen.fill((245, 246, 248))
        screen.blit(font_big.render("Abalone (pygame)", True, (20, 20, 20)), (60, 60))

        # top status
        team_label = {"ffa": "Free-for-all", "opposite": "Opposite Pairs", "alternate": "Alternate Teams"}[team_choice]
        screen.blit(font.render(f"Mode: {selected}", True, (40, 40, 40)), (60, 110))
        screen.blit(font.render(f"Team: {team_label}", True, (40, 40, 40)), (520, 110))

        # left buttons
        for k, b in btns:
            bg = (210, 235, 210) if k == selected else (230, 230, 230)
            b.draw(screen, font, bg=bg)

        # right panel box
        pygame.draw.rect(screen, (235, 238, 244), pygame.Rect(panel_x, panel_y, panel_w, panel_h), border_radius=14)
        pygame.draw.rect(screen, (170, 176, 188), pygame.Rect(panel_x, panel_y, panel_w, panel_h), width=2, border_radius=14)
        screen.blit(font.render("Team Settings", True, (20, 20, 20)), (panel_x + 12, panel_y + 14))

        # team buttons with highlight
        def draw_team_btn(btn, active: bool):
            bg = (210, 235, 210) if active else (230, 230, 230)
            btn.draw(screen, font, bg=bg)

        draw_team_btn(team_ffa_btn, team_choice == "ffa")
        draw_team_btn(team_opp_btn, team_choice == "opposite")
        draw_team_btn(team_alt_btn, team_choice == "alternate")

        # detail text (always shown; not yet applied in game)
        detail_y = panel_y + 230
        screen.blit(font_small.render("Opposite Pairs:", True, (60, 60, 60)), (panel_x + 12, detail_y))
        screen.blit(font_small.render("4P: (1,3) vs (2,4)", True, (60, 60, 60)), (panel_x + 12, detail_y + 18))
        screen.blit(font_small.render("6P: (1,4) / (2,5) / (3,6)", True, (60, 60, 60)), (panel_x + 12, detail_y + 36))

        # play button disabled if blocked
        if team_blocked:
            play_btn.draw(screen, font, bg=(210, 210, 210), fg=(120, 120, 120), border=(140, 140, 140))
        else:
            play_btn.draw(screen, font, bg=(220, 240, 255))
        quit_btn.draw(screen, font, bg=(255, 230, 230))

        # bottom message
        if msg:
            screen.blit(font.render(msg, True, (120, 40, 40)), (60, H - 52))

        pygame.display.flip()
        clock.tick(60)

                

# -------------------- Game loader --------------------
def load_mode(mode_key: str, board: Dict[Pos, int], cells: Set[Pos]) -> Tuple[int, int]:
    info = PRESETS[mode_key]
    preset = layout_to_preset(info["layout"])

    for p in cells:
        board[p] = EMPTY
    for pos, pid in preset.items():
        if pos in cells:
            board[pos] = pid

    players = int(info.get("players", 2))
    win_push = int(info.get("win_push", DEFAULT_WIN_PUSHED))
    return players, win_push

def build_team_map(players: int, team_choice: str) -> Optional[Dict[int, int]]:
    """
    return: pid -> team_id (0,1,2,...)
    None이면 개인전
    """
    if team_choice == "ffa":
        return None

    # 2P는 팀 의미 없음 → 개인전 처리
    if players == 2:
        return None

    # 홀수 인원은 메뉴에서 이미 차단됨
    if players % 2 == 1:
        return None

    team_of: Dict[int, int] = {}

    if team_choice == "opposite":
        if players == 4:
            # (1,3) vs (2,4)
            team_of = {1:0, 3:0, 2:1, 4:1}
        elif players == 6:
            # (1,4), (2,5), (3,6)
            team_of = {1:0, 4:0, 2:1, 5:1, 3:2, 6:2}

    elif team_choice == "alternate":
        if players == 4:
            # same as opposite
            team_of = {1:0, 3:0, 2:1, 4:1}
        elif players == 6:
            # 3 vs 3
            team_of = {1:0, 3:0, 5:0, 2:1, 4:1, 6:1}

    return team_of

def get_mode_text(players: int, team_choice: str) -> str:
    if team_choice == "ffa" or players == 2:
        return "Free-for-all"

    if players == 4:
        return "2 vs 2"

    if players == 6:
        if team_choice == "opposite":
            return "2 vs 2 vs 2"
        elif team_choice == "alternate":
            return "3 vs 3"

    return "Free-for-all"

def selection_allowed(selected, current, board, team_of, team_control):
    if team_of is None:
        return all(board[p] == current for p in selected)

    cur_team = team_of[current]

    owners = [board[p] for p in selected]

    # 모두 같은 팀이어야 함
    if not all(team_of.get(o) == cur_team for o in owners):
        return False

    if team_control == "anchor":
        return current in owners   # 내 말이 최소 1개
    else:
        return True                # full team control

def can_select_cell(p, current, board, team_of):
    pid = board[p]
    if pid == EMPTY:
        return False

    if team_of is None:
        return pid == current

    # 팀전: 팀만 같으면 선택 가능
    return team_of.get(pid) == team_of[current]


# -------------------- Pygame main --------------------
def main():
    pygame.init()
    pygame.display.set_caption("Abalone (move + push + menu)")

    W, H = 980, 820
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 18)
    font_big = pygame.font.SysFont("consolas", 26, bold=True)
    font_btn = pygame.font.SysFont("consolas", 18, bold=True)

    # visuals
    BG = (245, 246, 248)
    HEX_FILL = (232, 236, 242)
    HEX_EDGE = (170, 176, 188)

    # In main(), replace P1_FILL/P2_FILL with:
    PLAYER_FILL = {
        1: (210, 70, 70),    # red
        2: (70, 110, 210),   # blue
        3: (210, 170, 60),   # yellow
        4: (70, 170, 90),    # green-ish
        5: (170, 90, 200),   # purple-ish
        6: (60, 190, 190),   # cyan-ish
        7: (255, 255, 255),   # white
    }    
    STONE_EDGE = (25, 25, 25)

    SEL_RING = (20, 180, 60)
    MSG_COLOR = (30, 30, 30)

    size = 34.0
    origin = (W * 0.50, H * 0.56)

    cells = make_cells(BOARD_R)
    board = make_empty_board(cells)

    # ---- Start menu loop ----
    menu_ret = start_menu(screen, PRESETS, default_key="2P-Classic")
    if menu_ret is None:
        pygame.quit()
        return

    mode_key, team_choice = menu_ret

    players, win_push = load_mode(mode_key, board, cells)
    team_of = build_team_map(players, team_choice)
    team_control = "anchor"

    # game state

    players, win_push = load_mode(mode_key, board, cells)
    selected: List[Pos] = []
    pushed_out = {pid: 0 for pid in range(1, players + 1)}
    team_pushed = {}  # team_id -> count

    if team_of is not None:
        for t in set(team_of.values()):
            team_pushed[t] = 0
            
    alive: Set[int] = set(range(1, players + 1))
    current = 1
    winner: Optional[int] = None
    msg = f"Mode: {mode_key} (click-to-move)."
    def recompute_alive():
        nonlocal winner, msg

        if team_of is None:
            # 개인전 (기존 그대로)
            for pid in list(alive):
                if pushed_out.get(pid, 0) >= win_push:
                    alive.remove(pid)
            return

        # ---- 팀전 ----
        # 팀별 합산
        team_pushed.clear()
        for pid, cnt in pushed_out.items():
            t = team_of.get(pid)
            if t is not None:
                team_pushed[t] = team_pushed.get(t, 0) + cnt

        # 패배한 팀 찾기
        defeated_teams = {t for t, c in team_pushed.items() if c >= win_push}

        if not defeated_teams:
            return

        # 살아있는 팀
        alive_teams = set(team_pushed.keys()) - defeated_teams

        if len(alive_teams) == 1:
            winner_team = alive_teams.pop()
            members = [pid for pid, t in team_of.items() if t == winner_team]
            msg = f"TEAM {winner_team + 1} wins!  Members: {members}"
            winner = members[0]  # 표시용


    def advance_turn():
        nonlocal current, winner, msg
        recompute_alive()

        # ---- 팀전 승리 판정은 여기서 끝 ----
        if team_of is not None and winner is not None:
            return

        # ---- 개인전 ----
        if team_of is None:
            if len(alive) <= 1:
                if len(alive) == 1:
                    winner = next(iter(alive))
                    msg = f"P{winner} wins! (last remaining)"
                return

        # next alive player (팀전/개인전 공통)
        cur = current
        while True:
            cur = next_player(cur, players)
            if team_of is None:
                if cur in alive:
                    current = cur
                    return
            else:
                current = cur
                return

    selected: List[Pos] = []
    pushed_out = {pid: 0 for pid in range(1, players + 1)}
    winner: Optional[int] = None
    msg = f"Mode: {mode_key} (click-to-move)."

    # buttons in game
    restart_btn = Button((W - 280, 18, 120, 40), "Restart")
    newgame_btn = Button((W - 150, 18, 120, 40), "New Game")

    def restart_same_mode():
        nonlocal current, selected, winner, msg, players, win_push, pushed_out, alive
        players, win_push = load_mode(mode_key, board, cells)
        selected = []
        pushed_out = {pid: 0 for pid in range(1, players + 1)}
        alive = set(range(1, players + 1))
        current = 1
        winner = None
        msg = f"Restarted: {mode_key}. P1 to move."


    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_BACKSPACE:
                    selected = []
                    msg = "Selection cleared."
                else:
                    # ✅ 여기: 키보드로 뭔가 하려는 순간, 현재 플레이어가 얼음이면 턴을 넘김
                    if winner is None and current not in alive:
                        advance_turn()
                    if ENABLE_KEY_MOVES and (winner is None) and (e.key in KEY_TO_DIR):
                        d = KEY_TO_DIR[e.key]
                        ok, m = try_move(board, cells, current, selected, d, pushed_out, team_of, team_control)
                        msg = m
                        if ok:
                            current = next_player(current, players)
                            selected = []
                            advance_turn()

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # top buttons
                if restart_btn.hit(e.pos):
                    restart_same_mode()
                    continue
                if newgame_btn.hit(e.pos):
                    menu_ret = start_menu(screen, PRESETS, default_key=mode_key)
                    if menu_ret is None:
                        running = False
                        break
                    mode_key2, team_choice = menu_ret  # team_choice 아직 미사용
                    mode_key = mode_key2
                    players, win_push = load_mode(mode_key, board, cells)
                    selected = []
                    pushed_out = {pid: 0 for pid in range(1, players + 1)}
                    alive = set(range(1, players + 1))
                    current = 1
                    winner = None
                    msg = f"Mode: {mode_key} (click-to-move)."
                    continue

                if winner is not None:
                    continue

                p = pick_cell(e.pos, cells, size, origin)
                if p is None:
                    continue

                # 1️⃣ 선택 가능한 말이고, 아직 3개 미만이면 → 선택
                if can_select_cell(p, current, board, team_of) and len(selected) < 3:
                    if p in selected:
                        selected.remove(p)
                    else:
                        selected.append(p)
                    continue

                # 2️⃣ 그 외의 경우 → 실행 시도
                if selected:
                    d = infer_move_dir_from_click(selected, p)
                    if d is None:
                        msg = "Invalid target click."
                        selected.clear()
                    else:
                        ok, m = try_move(board, cells, current, selected, d, pushed_out, team_of, team_control)
                        msg = m
                        if ok:
                            advance_turn()
                            selected.clear()
                        else:
                            selected.clear()
        # ---- draw ----
        screen.fill(BG)

        # draw board hexes
        for (q, r) in sorted(cells, key=lambda t: (t[1], t[0])):
            cx, cy = axial_to_pixel(q, r, size, origin)
            pts = hex_corners(cx, cy, size)
            pygame.draw.polygon(screen, HEX_FILL, pts)
            pygame.draw.polygon(screen, HEX_EDGE, pts, width=2)

        # draw stones
        stone_rad = int(size * 0.62)
        for (q, r), pid in board.items():
            if pid == EMPTY:
                continue
            cx, cy = axial_to_pixel(q, r, size, origin)
            color = PLAYER_FILL.get(pid, (120,120,120))
            pygame.draw.circle(screen, color, (int(cx), int(cy)), stone_rad)
            pygame.draw.circle(screen, STONE_EDGE, (int(cx), int(cy)), stone_rad, width=2)

        # selection ring
        for p in selected:
            cx, cy = axial_to_pixel(p[0], p[1], size, origin)
            pygame.draw.circle(screen, SEL_RING, (int(cx), int(cy)), stone_rad + 4, width=3)

        # top info
        top_y = 18
        push_txt = "  ".join([f"P{pid}:{pushed_out.get(pid,0)}" for pid in range(1, players+1)])
        alive_txt = "".join([str(pid) if pid in alive else "x" for pid in range(1, players+1)])
        if team_of is None:
            mode_txt = "Free-for-all"
        else:
            team_sizes = {}
            for pid, t in team_of.items():
                team_sizes[t] = team_sizes.get(t, 0) + 1
            sizes = sorted(team_sizes.values())
            mode_txt = " vs ".join(str(s) for s in sizes)
        mode_txt = get_mode_text(players, team_choice)
        header = f"Preset: {mode_key}   Mode: {mode_txt}   Turn: P{current}   Alive:{alive_txt}"
        header2 = f"Pushed: {push_txt}   Lose@{win_push}"
        screen.blit(font_big.render(header, True, (20, 20, 20)), (20, top_y))
        screen.blit(font_big.render(header2, True, (20, 20, 20)), (20, top_y+50))
        if winner is not None:
            if team_of is None:
                win_txt = f"WINNER: P{winner}"
            else:
                win_txt = f"WINNER: Team {winner}"
            screen.blit(font_big.render(win_txt, True, (10, 10, 10)), (20, top_y + 100))

        # buttons
        restart_btn.draw(screen, font_btn, bg=(235, 235, 235))
        newgame_btn.draw(screen, font_btn, bg=(235, 235, 235))

        # bottom message
        screen.blit(font.render("Msg: " + msg, True, MSG_COLOR), (20, H - 30))

        # controls hint
        hint = "Click 1-3 (in-line & contiguous) marbles, then click a 1-step target cell. Backspace clears selection."
        screen.blit(font.render(hint, True, (70, 70, 70)), (20, H - 52))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

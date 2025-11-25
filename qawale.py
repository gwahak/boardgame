import pygame
import sys
import os
from copy import deepcopy

# --- Game constants ---
GRID_SIZE = 4
CELL_SIZE = 128
MARGIN = 32
BOARD_SIZE = GRID_SIZE * CELL_SIZE
PANEL_H = 140
WIDTH = BOARD_SIZE + MARGIN * 2
HEIGHT = BOARD_SIZE + PANEL_H + MARGIN
FPS = 60

# Colors
BG = (244, 241, 235)
BOARD_BG = (225, 214, 200)
LINE = (120, 100, 85)
YELLOW = (235, 195,  40)   # neutral
RED    = (200,  60,  60)
WHITE  = (235, 235, 235)
BLACK  = ( 30,  30,  30)
BLUE   = ( 60, 120, 220)
GREEN  = ( 60, 160, 120)
GRAY   = (160, 150, 140)

COLOR_MAP = {
    'Y': YELLOW,
    'R': RED,
    'W': WHITE,
}

# Player order and stock
PLAYERS = ['R', 'W']  # Red goes first by default
START_STONES_PER_PLAYER = 8

# Rule option: allow placing on empty cell (default False)
ALLOW_PLACE_ON_EMPTY = False

# Debug
DEBUG_SHOW_TOPS = False  # T 키로 토글

# -------------------- Font helpers (cross-platform Korean) --------------------
_font_cache = {}

def get_korean_font(size=24, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]

    # 1) Try known file paths / names (Windows / macOS / Linux common)
    candidates_files = [
        'malgun.ttf',  # Windows (Malgun Gothic)
        'Malgun.ttf',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # macOS
        '/Library/Fonts/AppleGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # Ubuntu Nanum
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # fallback (often OK)
    ]

    for path in candidates_files:
        try:
            if os.path.exists(path) or os.path.sep not in path:
                font = pygame.font.Font(path, size)
                _font_cache[key] = font
                return font
        except Exception:
            pass

    # 2) Try system font names
    candidates_names = [
        'Malgun Gothic', 'AppleGothic', 'Apple SD Gothic Neo',
        'NanumGothic', 'Noto Sans CJK KR', 'Noto Sans CJK', 'UnDotum', 'Baekmuk Gulim',
        'DejaVu Sans', 'Arial Unicode MS', 'Arial'
    ]
    for name in candidates_names:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            _font_cache[key] = font
            return font
        except Exception:
            continue

    # 3) Absolute fallback
    _font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
    return _font_cache[key]

# -------------------- Game state containers --------------------
class GameState:
    def __init__(self):
        self.board = [[[] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        corners = [(0,0), (0,GRID_SIZE-1), (GRID_SIZE-1,0), (GRID_SIZE-1,GRID_SIZE-1)]
        for (r,c) in corners:
            self.board[r][c] = ['Y','Y']

        self.current_player_idx = 0
        self.stocks = { 'R': START_STONES_PER_PLAYER, 'W': START_STONES_PER_PLAYER }

        self.mode = 'idle'
        self.selected = None
        self.carry_stack = []
        self.cur_pos = None
        self.prev_pos = None

        self.winner = None
        self.message = "Red의 차례 — 스택을 클릭해서 내 자갈을 올리고 이동을 시작하세요"

        self.history = []

    def clone(self):
        g = GameState()
        g.board = deepcopy(self.board)
        g.current_player_idx = self.current_player_idx
        g.stocks = deepcopy(self.stocks)
        g.mode = self.mode
        g.selected = self.selected
        g.carry_stack = self.carry_stack[:]
        g.cur_pos = self.cur_pos
        g.prev_pos = self.prev_pos
        g.winner = self.winner
        g.message = self.message
        g.history = deepcopy(self.history)
        return g

    @property
    def current_player(self):
        return PLAYERS[self.current_player_idx]

    def next_player(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(PLAYERS)

    def push_history(self):
        snap = (deepcopy(self.board), deepcopy(self.stocks), self.current_player_idx, self.mode, self.selected, self.carry_stack[:], self.cur_pos, self.prev_pos, self.winner, self.message)
        self.history.append(snap)
        if len(self.history) > 3:
            self.history.pop(0)

    def undo(self):
        if not self.history:
            return
        (self.board, self.stocks, self.current_player_idx, self.mode, self.selected, self.carry_stack, self.cur_pos, self.prev_pos, self.winner, self.message) = self.history.pop()

# -------------------- Geometry helpers --------------------

def cell_rect(r, c):
    x = MARGIN + c * CELL_SIZE
    y = MARGIN + r * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

def pos_to_cell(mx, my):
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rect = cell_rect(r, c)
            if rect.collidepoint(mx, my):
                return (r, c)
    return None

def is_orth_adj(a, b):
    if a is None or b is None:
        return False
    ar, ac = a
    br, bc = b
    return abs(ar - br) + abs(ac - bc) == 1

# -------------------- Win / draw checks & debug helpers --------------------

def compute_tops(board):
    """각 칸의 소유자: 위에서부터(RTL) 내려오며 처음 만나는 R/W.
    노랑(Y)은 스택 어디에 있든 무시한다."""
    res = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            stack = board[r][c]
            # 위에서부터 확인: reversed = top -> bottom
            for s in reversed(stack):
                if s in ('R', 'W'):
                    res[r][c] = s
                    break
            # 전부 Y이거나 빈칸이면 None 유지
    return res


def check_winner(board):
    """가로, 세로, 두 대각선 중 한 줄이 전부 R 또는 전부 W면 승리"""
    tops = compute_tops(board)

    # 가로
    for r in range(GRID_SIZE):
        row = [tops[r][c] for c in range(GRID_SIZE)]
        if None not in row and len(set(row)) == 1:
            return row[0]

    # 세로
    for c in range(GRID_SIZE):
        col = [tops[r][c] for r in range(GRID_SIZE)]
        if None not in col and len(set(col)) == 1:
            return col[0]

    # 대각선 ↘
    diag1 = [tops[i][i] for i in range(GRID_SIZE)]
    if None not in diag1 and len(set(diag1)) == 1:
        return diag1[0]

    # 대각선 ↙
    diag2 = [tops[i][GRID_SIZE - 1 - i] for i in range(GRID_SIZE)]
    if None not in diag2 and len(set(diag2)) == 1:
        return diag2[0]
def find_winning_lines(board):
    """가로/세로/두 대각선 중, 한 줄이 전부 R 또는 전부 W인 라인들을 색별로 반환."""
    tops = compute_tops(board)
    wins = {'R': [], 'W': []}

    # 가로
    for r in range(GRID_SIZE):
        row = [tops[r][c] for c in range(GRID_SIZE)]
        if None not in row and len(set(row)) == 1:
            color = row[0]  # 'R' or 'W'
            wins[color].append([(r, c) for c in range(GRID_SIZE)])

    # 세로
    for c in range(GRID_SIZE):
        col = [tops[r][c] for r in range(GRID_SIZE)]
        if None not in col and len(set(col)) == 1:
            color = col[0]
            wins[color].append([(r, c) for r in range(GRID_SIZE)])

    # 대각선 ↘
    diag1 = [tops[i][i] for i in range(GRID_SIZE)]
    if None not in diag1 and len(set(diag1)) == 1:
        color = diag1[0]
        wins[color].append([(i, i) for i in range(GRID_SIZE)])

    # 대각선 ↙
    diag2 = [tops[i][GRID_SIZE - 1 - i] for i in range(GRID_SIZE)]
    if None not in diag2 and len(set(diag2)) == 1:
        color = diag2[0]
        wins[color].append([(i, GRID_SIZE - 1 - i) for i in range(GRID_SIZE)])

    return wins

def both_stocks_depleted(stocks):
    return stocks['R'] == 0 and stocks['W'] == 0

# -------------------- Rendering --------------------

def draw_text(surface, text, x, y, size=24, color=BLACK, center=False, bold=False):
    font = get_korean_font(size=size, bold=bold)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)

def draw_board(screen, gs: 'GameState'):
    board_rect = pygame.Rect(MARGIN, MARGIN, BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(screen, BOARD_BG, board_rect, border_radius=16)

    # Grid
    for i in range(GRID_SIZE + 1):
        x = MARGIN + i * CELL_SIZE
        y = MARGIN + i * CELL_SIZE
        pygame.draw.line(screen, LINE, (x, MARGIN), (x, MARGIN + BOARD_SIZE), 2)
        pygame.draw.line(screen, LINE, (MARGIN, y), (MARGIN + BOARD_SIZE, y), 2)

    # Moving hints
    if gs.mode == 'moving' and gs.cur_pos is not None:
        r, c = gs.cur_pos
        pygame.draw.rect(screen, GREEN, cell_rect(r, c), 4, border_radius=10)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                if gs.prev_pos is not None and (nr, nc) == gs.prev_pos:
                    continue
                pygame.draw.rect(screen, BLUE, cell_rect(nr, nc), 3, border_radius=10)

    # Stacks
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            stack = gs.board[r][c]
            rect = cell_rect(r, c)
            radius = int(min(CELL_SIZE * 0.28, 28))
            spacing = int(radius * 0.75)
            base_y = rect.bottom - radius - 8
            cx = rect.centerx
            max_draw = 5
            start_idx = max(0, len(stack) - max_draw)
            visible = stack[start_idx:]
            for i, stone in enumerate(visible):
                cy = base_y - spacing * (len(visible) - 1 - i)
                pygame.draw.circle(screen, BLACK, (cx, cy), radius + 2)
                pygame.draw.circle(screen, COLOR_MAP[stone], (cx, cy), radius)
                if i == len(visible) - 1:
                    pygame.draw.circle(screen, BLACK, (cx, cy), radius, 2)

            hidden = len(stack) - len(visible)
            if hidden > 0:
                badge = pygame.Rect(rect.right - 34, rect.top + 8, 26, 22)
                pygame.draw.rect(screen, BLACK, badge, border_radius=6)
                pygame.draw.rect(screen, (250,250,250), badge.inflate(-4,-4), border_radius=6)
                draw_text(screen, f"+{hidden}", badge.centerx, badge.centery-10, size=18, color=BLACK, center=True)

    # Info panel
    panel_top = MARGIN + BOARD_SIZE + 12
    pygame.draw.rect(screen, (250,248,244), (MARGIN, panel_top, BOARD_SIZE, PANEL_H-24), border_radius=12)

    if gs.mode != 'game_over':
        cp = gs.current_player
        cp_name = 'Red' if cp == 'R' else 'White'
        draw_text(screen, f"현재 차례: {cp_name}  |  보유 자갈 — Red:{gs.stocks['R']}  White:{gs.stocks['W']}",
                  MARGIN + 8, panel_top + 8, size=24, color=BLACK)
    else:
        draw_text(screen, "게임 종료", MARGIN + 8, panel_top + 8, size=24, color=BLACK)

    draw_text(screen, f"옵션 — 빈칸 시작: {'On' if ALLOW_PLACE_ON_EMPTY else 'Off'} (P로 토글)", MARGIN + 8, panel_top + 40 - 26, size=18, color=GRAY)
    draw_text(screen, gs.message, MARGIN + 8, panel_top + 40, size=22, color=BLACK)

    # Carry stack preview
    if gs.mode == 'moving' and gs.carry_stack:
        x0 = MARGIN + 12
        y0 = panel_top + 80
        radius = 18
        spacing = 40
        draw_text(screen, "들고 있는 순서 (왼쪽이 맨밑):", x0, y0 - 28, size=18, color=BLACK)
        for i, s in enumerate(gs.carry_stack):
            cx = x0 + i * spacing + 16
            cy = y0
            pygame.draw.circle(screen, BLACK, (cx, cy), radius + 2)
            pygame.draw.circle(screen, COLOR_MAP[s], (cx, cy), radius)
            if i == len(gs.carry_stack) - 1:
                pygame.draw.circle(screen, BLACK, (cx, cy), radius, 2)

    # Debug: 탑 오버레이
    if DEBUG_SHOW_TOPS:
        tops = compute_tops(gs.board)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                owner = tops[r][c]
                if owner:
                    rect = cell_rect(r, c)
                    draw_text(screen, owner, rect.left + 8, rect.top + 6, size=22, color=BLACK, bold=True)

    # Debug: 승리 라인 하이라이트
    wins = find_winning_lines(gs.board)
    for line in wins['R']:
        for (r, c) in line:
            pygame.draw.rect(screen, (255, 120, 120), cell_rect(r, c), 5, border_radius=12)
    for line in wins['W']:
        for (r, c) in line:
            pygame.draw.rect(screen, (180, 180, 255), cell_rect(r, c), 5, border_radius=12)

    # Controls hint
    draw_text(
        screen,
        "조작: 셀 클릭 선택/이동 · 스페이스/우클릭 정지 · Z 되돌리기 · R 재시작 · P 빈칸시작 토글 · T 탑표시 · ESC 종료",
        MARGIN + 8, HEIGHT - 36, size=18, color=GRAY
    )

# -------------------- Turn / move mechanics --------------------

def start_turn(gs: 'GameState'):
    if gs.stocks[gs.current_player] == 0:
        if both_stocks_depleted(gs.stocks):
            gs.mode = 'game_over'
            gs.winner = None
            gs.message = "무승부 — 두 플레이어의 자갈을 모두 사용했습니다"
            return
        gs.message = "자갈이 없습니다. 자동 패스합니다."
        gs.next_player()
        cp_name = 'Red' if gs.current_player == 'R' else 'White'
        gs.message = f"{cp_name}의 차례 — 스택을 클릭해서 내 자갈을 올리고 이동을 시작하세요"
    else:
        cp_name = 'Red' if gs.current_player == 'R' else 'White'
        gs.message = f"{cp_name}의 차례 — 스택을 클릭해서 내 자갈을 올리고 이동을 시작하세요"

def select_stack_and_pickup(gs: 'GameState', cell):
    if gs.mode != 'idle':
        return
    r, c = cell
    cur = gs.current_player
    if gs.stocks[cur] <= 0:
        return

    # NEW: rule enforcement — disallow starting from empty unless option enabled
    if not ALLOW_PLACE_ON_EMPTY and len(gs.board[r][c]) == 0:
        gs.message = "빈칸에서는 시작할 수 없습니다. (P 키로 옵션 토글)"
        return

    gs.push_history()

    gs.board[r][c].append(cur)
    gs.stocks[cur] -= 1

    gs.carry_stack = gs.board[r][c]
    gs.board[r][c] = []

    gs.selected = (r, c)
    gs.cur_pos = (r, c)
    gs.prev_pos = None
    gs.mode = 'moving'
    gs.message = "이동: 인접 칸을 클릭할 때마다 맨밑 자갈을 하나씩 놓습니다. 스페이스/우클릭으로 정지하여 나머지를 내려놓으세요."

def step_move(gs: 'GameState', dest_cell):
    if gs.mode != 'moving' or gs.cur_pos is None:
        return
    if not is_orth_adj(gs.cur_pos, dest_cell):
        return
    if gs.prev_pos is not None and dest_cell == gs.prev_pos:
        return

    bottom = gs.carry_stack.pop(0)
    dr, dc = dest_cell
    gs.board[dr][dc].append(bottom)

    gs.prev_pos = gs.cur_pos
    gs.cur_pos = dest_cell

    if not gs.carry_stack:
        finish_move(gs)

def finish_move(gs: 'GameState'):
    if gs.mode != 'moving':
        return

    # 이동을 멈추면 남은 자갈을 현재 칸에 모두 내려놓는다.
    if gs.carry_stack and gs.cur_pos is not None:
        r, c = gs.cur_pos
        gs.board[r][c].extend(gs.carry_stack)
        gs.carry_stack = []

    # ★ 여기서만 승리 판정(돌을 전부 내려놓은 뒤)
    result = check_winner(gs.board)
    if result is not None:
        if result in ('R', 'W'):
            gs.winner = result
            name = 'Red' if result == 'R' else 'White'
            gs.mode = 'game_over'
            gs.message = f"{name} 승리! (한 줄 완성)"
            return
        elif result == 'BOTH':
            gs.winner = None
            gs.mode = 'game_over'
            gs.message = "동시 완성 — 무승부"
            return

    # 재고 모두 소진 시 무승부
    if both_stocks_depleted(gs.stocks):
        gs.mode = 'game_over'
        gs.winner = None
        gs.message = "무승부 — 두 플레이어의 자갈을 모두 사용했습니다"
        return

    # 다음 턴으로
    gs.mode = 'idle'
    gs.selected = None
    gs.cur_pos = None
    gs.prev_pos = None
    gs.next_player()
    start_turn(gs)

# -------------------- Main loop --------------------

def main():
    pygame.init()
    pygame.display.set_caption("Qawale (콰왈레) — Pygame")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    gs = GameState()

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    gs = GameState()
                elif event.key == pygame.K_SPACE:
                    if gs.mode == 'moving':
                        finish_move(gs)
                elif event.key == pygame.K_z:
                    gs.undo()
                elif event.key == pygame.K_p:
                    # Toggle rule option
                    global ALLOW_PLACE_ON_EMPTY
                    ALLOW_PLACE_ON_EMPTY = not ALLOW_PLACE_ON_EMPTY
                    state = '허용' if ALLOW_PLACE_ON_EMPTY else '금지'
                    gs.message = f"옵션 변경 — 빈칸 시작 {state}"
                elif event.key == pygame.K_t:
                    global DEBUG_SHOW_TOPS
                    DEBUG_SHOW_TOPS = not DEBUG_SHOW_TOPS
                    gs.message = f"탑 오버레이: {'On' if DEBUG_SHOW_TOPS else 'Off'} (T)"
                elif event.key == pygame.K_l:
                    tops = compute_tops(gs.board)
                    print("TOPS:")
                    for row in tops:
                        print(row)
                    from pprint import pprint
                    wins = find_winning_lines(gs.board)
                    print("WINS R:", wins['R'])
                    print("WINS W:", wins['W'])
                    print("check_winner:", check_winner(gs.board))
                    gs.message = "콘솔에 TOPS/라인 출력 (L)"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                cell = pos_to_cell(mx, my)

                if event.button == 3:
                    if gs.mode == 'moving':
                        finish_move(gs)
                    continue

                if cell is None:
                    continue

                if gs.mode == 'idle':
                    select_stack_and_pickup(gs, cell)
                elif gs.mode == 'moving':
                    step_move(gs, cell)

        if gs.mode == 'idle':
            start_turn(gs)

        screen.fill(BG)
        draw_board(screen, gs)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

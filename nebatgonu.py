import pygame
import sys
from collections import deque

# -------------------- Config --------------------
GRID = 4               # 4x4
CELL = 120             # 한 칸 픽셀
MARGIN = 40
PANEL_W = 300
WIDTH = MARGIN*2 + GRID*CELL + PANEL_W
HEIGHT = MARGIN*2 + GRID*CELL
FPS = 60

# 색상
BG = (245, 245, 245)
GRID_COLOR = (30, 30, 30)
SEL_COLOR = (80, 140, 255)
MOVE_COLOR = (40, 180, 120)
CAP_COLOR = (150, 70, 200)
TEXT = (20, 20, 20)
P1_COLOR = (30, 30, 30)      # ● (위쪽 시작)
P2_COLOR = (230, 230, 230)   # ○ (아래쪽 시작)
OUTLINE = (0, 0, 0)
CAP_COLOR = (220, 40, 40)  # 빨강 (캡처 가능 위치 표시용)


# 플레이어 표기
P1 = 1   # Black ●
P2 = -1  # White ○
EMPTY = 0

# -------------------- 보드 / 규칙 --------------------
DIRS = [(1,0),(-1,0),(0,1),(0,-1)]  # 상하좌우

def in_bounds(r, c):
    return 0 <= r < GRID and 0 <= c < GRID

def init_board():
    # 위 2줄 ●, 아래 2줄 ○
    b = [[EMPTY for _ in range(GRID)] for _ in range(GRID)]
    for r in range(2):
        for c in range(GRID):
            b[r][c] = P1
    for r in range(2, GRID):
        for c in range(GRID):
            b[r][c] = P2
    return b

def clone(board):
    return [row[:] for row in board]

def count_pieces(board, who):
    return sum(1 for r in range(GRID) for c in range(GRID) if board[r][c] == who)

def legal_steps(board, r, c):
    """빈칸으로 1칸 이동(상하좌우)"""
    res = []
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc) and board[nr][nc] == EMPTY:
            res.append((nr, nc))
    return res

def legal_captures_over_ally_to_enemy(board, r, c):
    """
    요청 규칙 구현:
    [나][아군][적] 형태로 일직선 3칸이 있는 경우,
    가운데 '아군'을 넘어 끝의 '적' 칸으로 착지하며 적 돌을 제거.
    착지칸은 '적'이 있는 칸(빈칸 아님).
    """
    me = board[r][c]
    if me == EMPTY:
        return []
    res = []
    for dr, dc in DIRS:
        mid_r, mid_c = r+dr, c+dc
        end_r, end_c = r+2*dr, c+2*dc
        if in_bounds(mid_r, mid_c) and in_bounds(end_r, end_c):
            if board[mid_r][mid_c] == me and board[end_r][end_c] == -me:
                # 캡처: (end_r, end_c)에 착지
                res.append((end_r, end_c))
    return res

def all_legal_moves(board, player):
    """플레이어가 할 수 있는 모든 수 (한 번의 이동/점프만 허용)"""
    moves = []
    caps_exist = False
    for r in range(GRID):
        for c in range(GRID):
            if board[r][c] == player:
                caps = legal_captures_over_ally_to_enemy(board, r, c)
                if caps:
                    caps_exist = True
                steps = legal_steps(board, r, c)
                if caps or steps:
                    moves.append(((r,c), steps, caps))
    # 캡처가 가능한 경우, 보통은 캡처 우선 규칙을 둘 수 있으나
    # 문제 설명에 우선순위 명시 없음 → 둘 다 허용 (원문대로 "따는 대신 1칸 이동"이라 선택)
    return moves, caps_exist

def apply_move(board, src, dst):
    """일반 이동(빈칸 1칸)"""
    r, c = src
    nr, nc = dst
    nb = clone(board)
    nb[nr][nc] = nb[r][c]
    nb[r][c] = EMPTY
    return nb

def apply_capture(board, src, dst):
    """
    점프 캡처: src -> dst로 이동하며,
    중간칸은 아군, 착지칸의 적을 제거(그 칸을 내 말로 교체)
    """
    r, c = src
    nr, nc = dst
    dr = (nr - r) // 2
    dc = (nc - c) // 2
    mid_r, mid_c = r + dr, c + dc

    nb = clone(board)
    me = nb[r][c]
    # 착지칸에 있는 적 제거 + 내 말로 교체
    nb[nr][nc] = me
    nb[r][c] = EMPTY
    # 중간 아군은 건드리지 않음 (넘어만 감)
    return nb

def has_any_move(board, player):
    moves, _ = all_legal_moves(board, player)
    return any(steps or caps for (_, steps, caps) in moves)

# -------------------- 상태 --------------------
class Game:
    def __init__(self):
        self.board = init_board()
        self.turn = P1
        self.selected = None
        self.valid_steps = []
        self.valid_caps = []
        self.message = "네밭고누: ● 차례"
        self.history = deque()  # (board, turn, message)
        self.future = deque()

    def push_history(self):
        self.history.append((clone(self.board), self.turn, self.message))
        # 분기 발생 시 redo 스택 폐기
        self.future.clear()

    def undo(self):
        if not self.history:
            return
        self.future.appendleft((clone(self.board), self.turn, self.message))
        b, t, m = self.history.pop()
        self.board, self.turn, self.message = clone(b), t, m
        self.selected = None
        self.valid_steps = []
        self.valid_caps = []

    def redo(self):
        if not self.future:
            return
        self.history.append((clone(self.board), self.turn, self.message))
        b, t, m = self.future.popleft()
        self.board, self.turn, self.message = clone(b), t, m
        self.selected = None
        self.valid_steps = []
        self.valid_caps = []

    def restart(self):
        self.__init__()

    def select(self, cell):
        r, c = cell
        if not in_bounds(r,c):
            return
        if self.board[r][c] != self.turn:
            # 내 말만 선택
            self.selected = None
            self.valid_steps = []
            self.valid_caps = []
            return
        self.selected = (r, c)
        self.valid_steps = legal_steps(self.board, r, c)
        self.valid_caps = legal_captures_over_ally_to_enemy(self.board, r, c)

    def try_move(self, dst):
        if self.selected is None:
            return
        r, c = self.selected
        nr, nc = dst
        if (nr, nc) in self.valid_steps:
            self.push_history()
            self.board = apply_move(self.board, (r,c), (nr,nc))
            self.end_turn()
        elif (nr, nc) in self.valid_caps:
            self.push_history()
            self.board = apply_capture(self.board, (r,c), (nr,nc))
            self.end_turn()
        # 선택 해제
        self.selected = None
        self.valid_steps = []
        self.valid_caps = []

    def end_turn(self):
        # 승패 체크 (상대 돌 1 이하이거나 상대가 수가 없으면 승)
        opp = -self.turn
        if count_pieces(self.board, opp) <= 1:
            self.message = ("● 승리!" if self.turn == P1 else "○ 승리!")
            self.turn = 0
            return
        # 상대 수 가능성
        if not has_any_move(self.board, opp):
            self.message = ("● 승리!" if self.turn == P1 else "○ 승리!")
            self.turn = 0
            return

        # 턴 넘김
        self.turn = opp
        self.message = "● 차례" if self.turn == P1 else "○ 차례"

# -------------------- 렌더링 --------------------
def grid_to_px(r, c):
    x = MARGIN + c*CELL
    y = MARGIN + r*CELL
    return x, y

def draw_board(surface, g: Game, font, small_font):
    # 배경
    surface.fill(BG)

    # 보드 외곽
    board_rect = pygame.Rect(MARGIN, MARGIN, GRID*CELL, GRID*CELL)
    pygame.draw.rect(surface, (220,220,220), board_rect)
    pygame.draw.rect(surface, GRID_COLOR, board_rect, 3)

    # 격자
    for i in range(GRID+1):
        # 가로선
        y = MARGIN + i*CELL
        pygame.draw.line(surface, GRID_COLOR, (MARGIN, y), (MARGIN+GRID*CELL, y), 2)
        # 세로선
        x = MARGIN + i*CELL
        pygame.draw.line(surface, GRID_COLOR, (x, MARGIN), (x, MARGIN+GRID*CELL), 2)

    # 선택 표시
    if g.selected:
        r, c = g.selected
        x, y = grid_to_px(r, c)
        pygame.draw.rect(surface, SEL_COLOR, (x+4, y+4, CELL-8, CELL-8), 4)

    # 가능 수 표시
    for (rr, cc) in g.valid_steps:
        x, y = grid_to_px(rr, cc)
        pygame.draw.circle(surface, MOVE_COLOR, (x+CELL//2, y+CELL//2), CELL//8)


    # 말 그리기
    for r in range(GRID):
        for c in range(GRID):
            v = g.board[r][c]
            if v == EMPTY:
                continue
            x, y = grid_to_px(r, c)
            cx, cy = x + CELL//2, y + CELL//2
            rad = CELL//2 - 10
            if v == P1:
                fill = P1_COLOR
                outline = OUTLINE
            else:
                fill = P2_COLOR
                outline = OUTLINE
            pygame.draw.circle(surface, fill, (cx, cy), rad)
            pygame.draw.circle(surface, outline, (cx, cy), rad, 3)
    for (rr, cc) in g.valid_caps:
        x, y = grid_to_px(rr, cc)
        # 빨간색 꽉 찬 원으로 내부 표시
        pygame.draw.circle(surface, CAP_COLOR, (x+CELL//2, y+CELL//2), CELL//8)
    # 사이드 패널
    panel_x = MARGIN + GRID*CELL + 20
    # 제목
    title = font.render("네밭고누 (4×4)", True, TEXT)
    surface.blit(title, (panel_x, MARGIN))

    # 안내
    msg1 = small_font.render("조작: 마우스로 선택/이동", True, TEXT)
    msg2 = small_font.render("Z 실행취소 / Y 다시하기", True, TEXT)
    msg3 = small_font.render("R 재시작", True, TEXT)
    surface.blit(msg1, (panel_x, MARGIN+50))
    surface.blit(msg2, (panel_x, MARGIN+80))
    surface.blit(msg3, (panel_x, MARGIN+110))

    # 규칙 요약
    lines = [
        "규칙:",
        "• 상하좌우 1칸 이동",
        "• [나][아군][적] 직선이면",
        "   아군을 '넘어' 적 자리로 착지하여 따기",
        "• 상대가 수가 없거나",
        "  상대 돌이 1개 이하면 승리",
    ]
    y0 = MARGIN+150
    for i, t in enumerate(lines):
        surface.blit(small_font.render(t, True, TEXT), (panel_x, y0 + i*26))

    # 턴/결과
    surface.blit(font.render(g.message, True, TEXT), (panel_x, HEIGHT - MARGIN - 40))

def get_korean_font():
    pygame.font.init()
    # 가능한 폰트 후보들 중 존재하는 것 사용
    candidates = ["malgungothic", "AppleGothic", "NanumGothic", "Arial Unicode MS", "arial"]
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, 28)
            if f is not None:
                small = pygame.font.SysFont(name, 22)
                return f, small
        except:
            pass
    # 최후: 기본 폰트
    return pygame.font.Font(None, 28), pygame.font.Font(None, 22)

def cell_from_mouse(pos):
    mx, my = pos
    x0, y0 = MARGIN, MARGIN
    if not (x0 <= mx < x0 + GRID*CELL and y0 <= my < y0 + GRID*CELL):
        return None
    c = (mx - x0) // CELL
    r = (my - y0) // CELL
    return int(r), int(c)

# -------------------- 메인 루프 --------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("네밭고누 (Pygame)")
    clock = pygame.time.Clock()

    font, small_font = get_korean_font()
    game = Game()

    running = True
    while running:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    game.restart()
                elif e.key == pygame.K_z:
                    game.undo()
                elif e.key == pygame.K_y:
                    game.redo()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if game.turn == 0:
                    # 게임 종료 후 클릭은 무시
                    continue
                cell = cell_from_mouse(e.pos)
                if cell is None:
                    continue
                r, c = cell
                # 선택 중이고, 그 칸으로 시도
                if game.selected is not None:
                    if (r, c) == game.selected:
                        # 선택 토글 해제
                        game.selected = None
                        game.valid_steps = []
                        game.valid_caps = []
                    else:
                        game.try_move((r, c))
                else:
                    # 말 선택
                    if in_bounds(r,c) and game.board[r][c] == game.turn:
                        game.select((r,c))

        draw_board(screen, game, font, small_font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

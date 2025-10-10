import pygame
import sys
from collections import deque

# -------------------- Config --------------------
GRID = 5               # 5x5 (3인용 보드)
CELL = 96
MARGIN = 40
PANEL_W = 360
WIDTH = MARGIN*2 + GRID*CELL + PANEL_W
HEIGHT = MARGIN*2 + GRID*CELL
FPS = 60

# 옵션: 가운데 제3자를 넘어 적을 딸 수 있는가?
ALLY_CAPTURE = False  # False: [나][나][적]만 허용 / True: [나][제3자][적]도 허용(단 [나][적][적]은 금지)

# 색상
BG = (245, 245, 245)
GRID_COLOR = (30, 30, 30)
SEL_COLOR = (80, 140, 255)
MOVE_COLOR = (40, 180, 120)
TEXT = (20, 20, 20)
OUTLINE = (0, 0, 0)

# 플레이어 색
P1_COLOR = (30, 30, 30)       # ● (Black)
P2_COLOR = (230, 230, 230)    # ◯ (White)
P3_COLOR = (220, 40, 40)      # ⭙ (Red)
CAP_COLOR = (220, 220, 40)     # 캡처 가능 위치(내부 빨강)

# 플레이어 표기
P1 = 1    # ●
P2 = 2    # ◯
P3 = 3    # ⭙
EMPTY = 0

# 차례 순서: ◯ -> ⭙ -> ● (요청 순서)
TURN_ORDER = [P2, P3, P1]

# -------------------- 보드 / 규칙 --------------------
DIRS = [(1,0),(-1,0),(0,1),(0,-1)]  # 상하좌우

def in_bounds(r, c):
    return 0 <= r < GRID and 0 <= c < GRID

def init_board_3p():
    """
    5x5 초기 배치:
    ⬤ ⬤ ⬤ ⭙ ⭙
    ⬤ ⬤ ⬤ ⭙ ⭙
    ⬤ ⬤ ⬤ ⭙ ⭙
    ◯ ◯ ◯ ⭙ ◯
    ◯ ◯ ◯ ◯ ⭙
    """
    b = [[EMPTY for _ in range(GRID)] for _ in range(GRID)]
    # ● 블랙 영역
    for r in range(3):
        for c in range(3):
            b[r][c] = P1
    # ⭙ 레드 영역
    for r in range(3):
        for c in range(3, 5):
            b[r][c] = P3
    b[3][3] = P3
    b[4][4] = P3
    # ◯ 화이트 영역
    for c in range(3):
        b[3][c] = P2
        b[4][c] = P2
    b[4][3] = P2
    b[3][4] = P2
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

def is_enemy(cell, me):
    return cell != EMPTY and cell != me

def legal_captures_by_rule(board, r, c):
    """
    캡처 규칙:
    - 항상 허용: [me][me][enemy]
    - ALly_CAPTURE=True일 때만 허용: [me][third][enemy]  (third != me, third != enemy, third != EMPTY)
    - 절대 금지: [me][enemy][enemy]
    - 그 외: 불가
    착지는 '적'이 있는 end 칸.
    """
    me = board[r][c]
    if me == EMPTY:
        return []
    res = []
    for dr, dc in DIRS:
        mid_r, mid_c = r + dr, c + dc
        end_r, end_c = r + 2*dr, c + 2*dc
        if not (in_bounds(mid_r, mid_c) and in_bounds(end_r, end_c)):
            continue

        mid = board[mid_r][mid_c]
        end = board[end_r][end_c]

        # end 는 반드시 '적'이어야 함
        if end == EMPTY or end == me:
            continue

        # 금지 케이스: [me][enemy][enemy]
        if mid == end:
            continue

        # 항상 허용: [me][me][enemy]
        if mid == me:
            res.append((end_r, end_c))
            continue

        # 옵션 허용: [me][third][enemy] (third != me, != enemy, != EMPTY)
        if ALLY_CAPTURE and mid != EMPTY and mid != me and mid != end:
            res.append((end_r, end_c))
            continue

        # 그 외는 불가
    return res

def all_legal_moves(board, player):
    """플레이어가 할 수 있는 모든 수 (한 번의 이동/점프만 허용)"""
    moves = []
    caps_exist = False
    for r in range(GRID):
        for c in range(GRID):
            if board[r][c] == player:
                caps = legal_captures_by_rule(board, r, c)
                if caps:
                    caps_exist = True
                steps = legal_steps(board, r, c)
                if caps or steps:
                    moves.append(((r,c), steps, caps))
    return moves, caps_exist

def apply_move(board, src, dst):
    r, c = src
    nr, nc = dst
    nb = clone(board)
    nb[nr][nc] = nb[r][c]
    nb[r][c] = EMPTY
    return nb

def apply_capture(board, src, dst):
    """
    점프 캡처: src -> dst로 이동.
    가운데 칸은 '그냥 넘기'만 하고, dst의 적은 제거(그 칸을 내 말로 교체)
    """
    r, c = src
    nr, nc = dst
    nb = clone(board)
    me = nb[r][c]
    nb[nr][nc] = me      # 적 자리를 내 말로 교체 (적 제거)
    nb[r][c] = EMPTY
    return nb

def has_any_move(board, player):
    moves, _ = all_legal_moves(board, player)
    return any(steps or caps for (_, steps, caps) in moves)

# -------------------- 상태 --------------------
class Game:
    def __init__(self):
        self.board = init_board_3p()
        self.turn_order = TURN_ORDER[:]     # 활성 플레이어 순서
        self.turn_idx = 0                   # 현재 차례 인덱스
        self.turn = self.turn_order[self.turn_idx]
        self.selected = None
        self.valid_steps = []
        self.valid_caps = []
        self.message = self.turn_label() + " 차례"
        self.history = deque()  # 스냅샷 스택
        self.future = deque()

    # --------- 스냅샷/히스토리 ---------
    def snapshot(self):
        return (
            clone(self.board),
            self.turn_order[:],
            self.turn_idx,
            self.selected,
            self.valid_steps[:],
            self.valid_caps[:],
            self.message,
            ALLY_CAPTURE
        )

    def restore(self, snap):
        (b, order, idx, sel, steps, caps, msg, ally_cap) = snap
        global ALLY_CAPTURE
        self.board = clone(b)
        self.turn_order = order[:]
        self.turn_idx = idx
        self.turn = self.turn_order[self.turn_idx] if self.turn_order else 0
        self.selected = sel
        self.valid_steps = steps[:]
        self.valid_caps = caps[:]
        self.message = msg
        ALLY_CAPTURE = ally_cap

    def push_history(self):
        self.history.append(self.snapshot())
        self.future.clear()

    def undo(self):
        if not self.history:
            return
        self.future.appendleft(self.snapshot())
        snap = self.history.pop()
        self.restore(snap)

    def redo(self):
        if not self.future:
            return
        self.history.append(self.snapshot())
        snap = self.future.popleft()
        self.restore(snap)

    def restart(self):
        self.__init__()

    # --------- 유틸 ---------
    def player_color(self, p):
        return {P1:P1_COLOR, P2:P2_COLOR, P3:P3_COLOR}.get(p, (128,128,128))

    def player_symbol(self, p):
        return {P1:"흑", P2:"백", P3:"홍"}.get(p, "?")

    def turn_label(self):
        return self.player_symbol(self.turn)

    # --------- 입력/선택 ---------
    def select(self, cell):
        if self.turn == 0:
            return
        r, c = cell
        if not in_bounds(r,c):
            return
        if self.board[r][c] != self.turn:
            self.selected = None
            self.valid_steps = []
            self.valid_caps = []
            return
        self.selected = (r, c)
        self.valid_steps = legal_steps(self.board, r, c)
        self.valid_caps = legal_captures_by_rule(self.board, r, c)

    def try_move(self, dst):
        if self.turn == 0 or self.selected is None:
            return
        r, c = self.selected
        nr, nc = dst
        if (nr, nc) in self.valid_steps:
            self.push_history()
            self.board = apply_move(self.board, (r,c), (nr,nc))
            self.after_action()
        elif (nr, nc) in self.valid_caps:
            self.push_history()
            self.board = apply_capture(self.board, (r,c), (nr,nc))
            self.after_action()

        # 선택 해제
        self.selected = None
        self.valid_steps = []
        self.valid_caps = []

    # --------- 진행/판정 ---------
    def eliminate_if_needed_by_piece_count(self, player):
        """
        돌이 1개만 남으면 즉시 탈락.
        단, 돌은 판 위에 그대로 남는다(장애물).
        -> 턴순서에서만 제거.
        """
        if player not in self.turn_order:
            return False
        piece_cnt = count_pieces(self.board, player)
        if piece_cnt <= 1:
            idx = self.turn_order.index(player)
            self.turn_order.pop(idx)
            # turn_idx 보정
            if self.turn_order:
                if idx <= self.turn_idx:
                    self.turn_idx = (self.turn_idx - 1) % len(self.turn_order)
            else:
                self.turn_idx = 0
            return True
        return False

    def advance_to_next_player(self):
        if not self.turn_order:
            self.turn = 0
            return
        # 현재 turn이 순서에 있으면 그 다음으로, 없으면 turn_idx 사용
        if self.turn in self.turn_order:
            self.turn_idx = (self.turn_order.index(self.turn) + 1) % len(self.turn_order)
        else:
            self.turn_idx %= len(self.turn_order)
        self.turn = self.turn_order[self.turn_idx]
        self.message = self.player_symbol(self.turn) + " 차례"

    def auto_pass_if_no_moves(self):
        """
        현 턴 플레이어가 둘 수가 없으면 자동 패스.
        (패스는 패배가 아님)
        """
        if self.turn == 0 or not self.turn_order:
            return
        if not has_any_move(self.board, self.turn):
            self.push_history()
            sym = self.player_symbol(self.turn)
            self.advance_to_next_player()
            self.message = f"{sym} 패스 → {self.player_symbol(self.turn)} 차례"

    def after_action(self):
        # 행동 후, 모든 플레이어에 대해 '돌 1개 이하' 탈락 판정
        changed = True
        while changed:
            changed = False
            for p in TURN_ORDER:  # 고정 순회, 내부에서 제거될 수 있음
                if p in self.turn_order:
                    if self.eliminate_if_needed_by_piece_count(p):
                        changed = True

        # 남은 인원 확인
        if len(self.turn_order) <= 1:
            if self.turn_order:
                self.message = self.player_symbol(self.turn_order[0]) + " 최종 승리!"
            else:
                self.message = "종료"
            self.turn = 0
            return

        # 내 턴 종료 → 다음 활성 플레이어
        self.advance_to_next_player()

        # 새 턴 시작 시, 수가 없으면 자동 패스(연속 패스 허용)
        while self.turn != 0 and not has_any_move(self.board, self.turn):
            self.push_history()
            sym = self.player_symbol(self.turn)
            self.advance_to_next_player()
            self.message = f"{sym} 패스 → {self.player_symbol(self.turn)} 차례"

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
        y = MARGIN + i*CELL
        pygame.draw.line(surface, GRID_COLOR, (MARGIN, y), (MARGIN+GRID*CELL, y), 2)
        x = MARGIN + i*CELL
        pygame.draw.line(surface, GRID_COLOR, (x, MARGIN), (x, MARGIN+GRID*CELL), 2)

    # 선택 표시
    if g.selected:
        r, c = g.selected
        x, y = grid_to_px(r, c)
        pygame.draw.rect(surface, SEL_COLOR, (x+4, y+4, CELL-8, CELL-8), 4)

    # 이동 가능(빈칸) 표시
    for (rr, cc) in g.valid_steps:
        x, y = grid_to_px(rr, cc)
        pygame.draw.circle(surface, MOVE_COLOR, (x+CELL//2, y+CELL//2), CELL//10)

    # 말 그리기
    for r in range(GRID):
        for c in range(GRID):
            v = g.board[r][c]
            if v == EMPTY:
                continue
            x, y = grid_to_px(r, c)
            cx, cy = x + CELL//2, y + CELL//2
            rad = CELL//2 - 10
            color = g.player_color(v)
            pygame.draw.circle(surface, color, (cx, cy), rad)
            pygame.draw.circle(surface, OUTLINE, (cx, cy), rad, 3)

    # 캡처 가능 칸(적 자리) 표시 — 말 위에 찍어서 가시성↑
    for (rr, cc) in g.valid_caps:
        x, y = grid_to_px(rr, cc)
        cx, cy = x + CELL//2, y + CELL//2
        pygame.draw.circle(surface, CAP_COLOR, (cx, cy), CELL//6)

    # 사이드 패널
    panel_x = MARGIN + GRID*CELL + 20
    title = font.render("3인 고누 (5×5)", True, TEXT)
    surface.blit(title, (panel_x, MARGIN))

    # 안내
    y0 = MARGIN + 50
    infos = [
        "차례: 백 → 홍 → 흑",
        "조작: 마우스 선택/이동",
        "Z 실행취소 / Y 다시하기",
        "R 재시작 / A ALLY_CAPTURE 토글",
        "",
        f"ALLY_CAPTURE: {'ON' if ALLY_CAPTURE else 'OFF'}",
        "",
        "캡처 규칙:",
        "• 기본 [나][나][적]만 허용",
        "• ON이면 [나][제3자][적]도 허용",
        "• [나][적][적]은 항상 금지",
        "",
        "기타:",
        "• 상하좌우 1칸 이동",
        "• 둘 수 없으면 자동 패스",
        "• 마지막 1명이 남으면 승리",
    ]
    for i, t in enumerate(infos):
        surface.blit(small_font.render(t, True, TEXT), (panel_x, y0 + i*26))

    # 턴/결과
    surface.blit(font.render(g.message, True, TEXT), (panel_x, HEIGHT - MARGIN - 20))

def get_korean_font():
    pygame.font.init()
    candidates = ["malgungothic", "AppleGothic", "NanumGothic", "Arial Unicode MS", "arial"]
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, 28)
            if f is not None:
                small = pygame.font.SysFont(name, 22)
                return f, small
        except:
            pass
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
    global ALLY_CAPTURE
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3인 고누 (Pygame)")
    clock = pygame.time.Clock()

    font, small_font = get_korean_font()
    game = Game()

    running = True
    while running:
        clock.tick(FPS)

        # 턴 시작 시 수가 없으면 자동 패스(연속 패스 허용)
        if game.turn != 0:
            game.auto_pass_if_no_moves()

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
                elif e.key == pygame.K_a:
                    # ALLY_CAPTURE 토글 (히스토리에 반영)
                    game.push_history()
                    ALLY_CAPTURE = not ALLY_CAPTURE
                    game.message = f"ALLY_CAPTURE {'ON' if ALLY_CAPTURE else 'OFF'} / {game.player_symbol(game.turn)} 차례"
                    # 선택 갱신
                    if game.selected:
                        r, c = game.selected
                        game.valid_steps = legal_steps(game.board, r, c)
                        game.valid_caps = legal_captures_by_rule(game.board, r, c)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if game.turn == 0:
                    continue
                cell = cell_from_mouse(e.pos)
                if cell is None:
                    continue
                r, c = cell
                if game.selected is not None:
                    if (r, c) == game.selected:
                        game.selected = None
                        game.valid_steps = []
                        game.valid_caps = []
                    else:
                        game.try_move((r, c))
                else:
                    if in_bounds(r,c) and game.board[r][c] == game.turn:
                        game.select((r,c))

        draw_board(screen, game, font, small_font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

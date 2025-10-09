import pygame
import sys
from typing import List, Tuple, Optional, Set

# -------------------- 기본 설정 --------------------
GRID_N = 7
CELL = 80
MARGIN = 40
PANEL_W = 400
WIDTH = MARGIN*2 + GRID_N*CELL + PANEL_W
HEIGHT = MARGIN*2 + GRID_N*CELL
FPS = 60

BG = (25, 27, 34)
GRID = (60, 64, 72)
WHITE = (235, 235, 235)
RED = (220, 60, 60)
BLUE = (60, 120, 220)
GREEN = (60, 200, 120)
VIOLET = (170, 120, 220)
YELLOW = (240, 200, 60)
GREY = (180, 180, 180)

EMPTY = 0
P1 = 1  # Red
P2 = 2  # Blue

MAX_PIECES_PER_PLAYER = 24

DIR8 = [(-1,-1), (-1,0), (-1,1),
        ( 0,-1),         ( 0,1),
        ( 1,-1), ( 1,0), ( 1,1)]


# -------------------- 유틸 --------------------
def inside(r:int, c:int)->bool:
    return 0 <= r < GRID_N and 0 <= c < GRID_N

def neighbors8(r:int, c:int)->List[Tuple[int,int]]:
    out = []
    for dr,dc in DIR8:
        rr, cc = r+dr, c+dc
        if inside(rr,cc):
            out.append((rr,cc))
    return out

def find_korean_font():
    pygame.font.init()
    candidates = ['malgungothic', 'Malgun Gothic', 'nanumgothic', 'NanumGothic',
                  'D2Coding', 'AppleGothic', 'arialunicode', 'arialuni']
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            return path
    return None

def board_full(gs) -> bool:
    for r in range(GRID_N):
        for c in range(GRID_N):
            if gs.board[r][c] == EMPTY:
                return False
    return True

def check_and_set_draw(gs) -> bool:
    """무승부 조건이면 game_over 세팅하고 True 반환."""
    # 양측 말 모두 소진
    if gs.pieces_left[P1] == 0 and gs.pieces_left[P2] == 0:
        gs.game_over = True
        gs.winner = 0
        return True
    # 보드 만원인데 승자 없음
    if board_full(gs):
        gs.game_over = True
        gs.winner = 0
        return True
    return False


# -------------------- 승리/유효수 --------------------
def has_four_in_a_row(board, r, c, pid)->bool:
    # 4목 체크 (4방향쌍)
    dirs = [(1,0), (0,1), (1,1), (1,-1)]
    for dr,dc in dirs:
        cnt = 1
        # forward
        rr, cc = r+dr, c+dc
        while inside(rr,cc) and board[rr][cc] == pid:
            cnt += 1
            rr += dr
            cc += dc
        # backward
        rr, cc = r-dr, c-dc
        while inside(rr,cc) and board[rr][cc] == pid:
            cnt += 1
            rr -= dr
            cc -= dc
        if cnt >= 4:
            return True
    return False

def compute_valid_moves(gs, pid:int) -> Tuple[Set[Tuple[int,int]], str]:
    """
    현재 pid가 '규칙상' 둘 수 있는 합법 수 집합과 이유코드 반환.
    (남은 말 수는 여기서 체크하지 않음; 턴 로직/렌더에서 별도 고려)
    """
    opp = gs.opponent(pid)
    empties = [(r,c) for r in range(GRID_N) for c in range(GRID_N) if gs.board[r][c]==EMPTY]

    # 시작(첫수): 자유
    if gs.last_move is None:
        return set(empties), "free_opening"

    # 기본 앵커: 직전 수
    base_anchor = gs.last_move
    base_moves = set((rr,cc) for (rr,cc) in neighbors8(*base_anchor) if gs.board[rr][cc]==EMPTY)

    # 선택 앵커(상대 돌 클릭)
    selected_moves = set()
    if gs.selected_anchor is not None:
        ar, ac = gs.selected_anchor
        if inside(ar,ac) and gs.board[ar][ac] == opp:
            selected_moves = set((rr,cc) for (rr,cc) in neighbors8(ar,ac) if gs.board[rr][cc]==EMPTY)
        else:
            gs.selected_anchor = None  # 무효 선택 정리

    if base_moves or selected_moves:
        return (selected_moves or base_moves), "anchor_ok"

    # 임의 앵커 탐색
    any_anchor_moves = set()
    for r in range(GRID_N):
        for c in range(GRID_N):
            if gs.board[r][c] == opp:
                for (rr,cc) in neighbors8(r,c):
                    if gs.board[rr][cc]==EMPTY:
                        any_anchor_moves.add((rr,cc))

    if any_anchor_moves:
        return any_anchor_moves, "any_anchor"

    # 임의 앵커도 전부 막힘 → 비상
    if gs.emergency_anywhere:
        return set(empties), "emergency_anywhere"
    else:
        return set(), "no_moves_any_anchor_all_blocked"


# -------------------- DEBUG --------------------
DEBUG_SCENARIO = False # 테스트 모드: True면 시작 시 시나리오 로드
# 비상상황 예시 순서 (빈칸은 None) — 테스트/디버깅 전용
order_matrix = [
    [None, 26, 25, 24, 23, 20, 18],
    [30,   28, 27, 22, 21, 19, 17],
    [31,   29, 45, 46, 47, 16, 14],
    [33,   32, 42, 43, 12, 13, 15],
    [34,   41, 44, 10, 11,  3,  1],
    [35,   40, 39,  9,  5,  4,  2],
    [36,   37, 38,  8,  7,  6, None]
]
def load_from_order_matrix(gs, matrix):
    """order_matrix를 이용해 보드를 구성하고 현재 차례/남은 말/턴을 세팅한다."""
    # 초기화
    gs.board = [[EMPTY]*GRID_N for _ in range(GRID_N)]
    gs.game_over = False
    gs.winner = None
    gs.selected_anchor = None
    gs.pass_streak = 0
    gs.offer_emergency = False
    gs.offer_reason = ""

    moves = []
    for r in range(GRID_N):
        for c in range(GRID_N):
            v = matrix[r][c]
            if v is not None:
                moves.append((int(v), r, c))

    if not moves:
        gs.current = P1
        gs.turn = 0
        gs.pieces_left = {P1: MAX_PIECES_PER_PLAYER, P2: MAX_PIECES_PER_PLAYER}
        gs.last_move = None
        return

    # 턴 순서대로 정렬
    moves.sort(key=lambda x: x[0])
    last_num, last_r, last_c = moves[-1]

    # 보드 채우기
    for num, r, c in moves:
        pid = P1 if num % 2 == 1 else P2
        gs.board[r][c] = pid

    # 남은 말 계산(안전하게 카운트로 갱신)
    placed_p1 = sum(1 for num,_,_ in moves if num % 2 == 1)
    placed_p2 = sum(1 for num,_,_ in moves if num % 2 == 0)
    gs.pieces_left = {
        P1: max(0, MAX_PIECES_PER_PLAYER - placed_p1),
        P2: max(0, MAX_PIECES_PER_PLAYER - placed_p2),
    }

    # 턴/직전수 설정
    gs.turn = last_num
    gs.last_move = (last_r, last_c)
    last_player = P1 if last_num % 2 == 1 else P2
    gs.current = gs.opponent(last_player)

    # 현재 규칙 상태 반영 (패스/오퍼/무승부 등 자동 처리)
    gs.handle_pass_if_needed()

# -------------------- 게임 상태 --------------------
class GameState:
    def __init__(self):
        self.board = [[EMPTY]*GRID_N for _ in range(GRID_N)]
        self.current = P1
        self.turn = 0
        self.last_move: Optional[Tuple[int,int]] = None  # (r,c) 마지막 착수
        self.pieces_left = {P1: MAX_PIECES_PER_PLAYER, P2: MAX_PIECES_PER_PLAYER}
        self.game_over = False
        self.winner: Optional[int] = None  # 0=무승부, 1/2=승자, None=진행중
        self.emergency_anywhere = True     # 비상시 아무데나 두기 허용 스위치
        self.selected_anchor: Optional[Tuple[int,int]] = None
        self.pass_streak = 0               # 연속 패스 카운트(2가 되면 무승부)
        self.offer_emergency = False       # ★ 무승부 직전 비상 ON 선택 오퍼
        self.offer_reason = ""             # 디버그/표시용

    def reset(self):
        self.__init__()

    def opponent(self, pid:int)->int:
        return P1 if pid == P2 else P2

    def place(self, r:int, c:int)->bool:
        if self.game_over or self.offer_emergency:
            return False
        if not inside(r,c) or self.board[r][c] != EMPTY:
            return False
        if self.pieces_left[self.current] <= 0:
            return False

        # 규칙상 합법 수인지 확인
        valids, _ = compute_valid_moves(self, self.current)
        if (r,c) not in valids:
            return False

        # 착수
        self.board[r][c] = self.current
        self.pieces_left[self.current] -= 1
        self.last_move = (r,c)
        self.turn += 1

        # 승리 체크
        if has_four_in_a_row(self.board, r, c, self.current):
            self.game_over = True
            self.winner = self.current
            return True  # 즉시 종료

        # 착수 성공 → 패스 스트릭 리셋
        self.pass_streak = 0

        # 착수 직후 무승부 확정 (말 소진/보드 만원)
        if check_and_set_draw(self):
            return True

        # 턴 넘기기
        self.selected_anchor = None
        self.current = self.opponent(self.current)

        # 다음 플레이어 상태 처리 (말 0개/패스/비상 등) — 루프형으로 끝까지 해결
        self.handle_pass_if_needed()
        return True

    def handle_pass_if_needed(self):
        """턴 시작 시 호출: 말 0개/패스/연속 패스/무승부/오퍼 등을 '자동'으로 끝까지 처리."""
        if self.game_over:
            return

        guard = 0
        while not self.game_over and not self.offer_emergency and guard < 8:
            guard += 1

            # 전역 무승부(양측 0개/보드 만원)는 즉시 종료 — 오퍼 제공 X
            if check_and_set_draw(self):
                return

            # 현재 차례 말이 0 → 패스 후보
            if self.pieces_left[self.current] <= 0:
                # 두 번째 패스 직전이면 오퍼
                if self.pass_streak == 1 and not self.emergency_anywhere:
                    self.offer_emergency = True
                    self.offer_reason = "two_pass_draw_via_zero_piece"
                    return
                self.pass_streak += 1
                if self.pass_streak >= 2:
                    self.game_over = True
                    self.winner = 0
                    return
                self.current = self.opponent(self.current)
                continue

            # 남은 말은 있는데, 비상 OFF + 규칙상 둘 곳이 없음 → 패스 후보
            valids, reason = compute_valid_moves(self, self.current)
            if not valids and reason == "no_moves_any_anchor_all_blocked" and not self.emergency_anywhere:
                if self.pass_streak == 1:
                    # 두 번째 패스 직전 → 오퍼
                    self.offer_emergency = True
                    self.offer_reason = "two_pass_draw_via_blocked"
                    return
                self.pass_streak += 1
                if self.pass_streak >= 2:
                    self.game_over = True
                    self.winner = 0
                    return
                self.current = self.opponent(self.current)
                continue

            # 여기까지 왔으면 현재 차례가 실제로 둘 수 있음(혹은 비상 ON으로 가능)
            return

        # 안전망
        if not self.game_over and board_full(self):
            self.game_over = True
            self.winner = 0


# -------------------- 렌더링 --------------------
def draw_board(screen, gs: GameState, font, small):
    screen.fill(BG)
    left = MARGIN
    top = MARGIN

    # 격자
    for i in range(GRID_N+1):
        y = top + i*CELL
        pygame.draw.line(screen, GRID, (left, y), (left + GRID_N*CELL, y), 2)
        x = left + i*CELL
        pygame.draw.line(screen, GRID, (x, top), (x, top + GRID_N*CELL), 2)

    # 돌(정육면체 느낌 라운드 사각형)
    for r in range(GRID_N):
        for c in range(GRID_N):
            pid = gs.board[r][c]
            if pid != EMPTY:
                color = RED if pid==P1 else BLUE
                cx = left + c*CELL + CELL//2
                cy = top + r*CELL + CELL//2
                rect = pygame.Rect(0,0, CELL-16, CELL-16)
                rect.center = (cx, cy)
                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(screen, WHITE, rect, width=2, border_radius=10)

    # 유효 수 하이라이트 (오퍼/게임오버/말 0개면 표시 X)
    if not gs.game_over and not gs.offer_emergency and gs.pieces_left[gs.current] > 0:
        valids, reason = compute_valid_moves(gs, gs.current)

        # 선택 앵커 표시
        if gs.selected_anchor is not None:
            ar, ac = gs.selected_anchor
            if inside(ar,ac):
                ax = left + ac*CELL + CELL//2
                ay = top + ar*CELL + CELL//2
                pygame.draw.circle(screen, VIOLET, (ax, ay), 10)
                pygame.draw.circle(screen, WHITE, (ax, ay), 10, 2)

        # 유효수 점
        for (r,c) in valids:
            cx = left + c*CELL + CELL//2
            cy = top + r*CELL + CELL//2
            dot_color = GREEN if gs.selected_anchor is None else VIOLET
            pygame.draw.circle(screen, dot_color, (cx, cy), 8)
            pygame.draw.circle(screen, WHITE, (cx, cy), 8, 2)

    # 우측 패널
    panel_x = left + GRID_N*CELL + 20
    title = font.render("4Mation (7x7 · 4목)", True, WHITE)
    screen.blit(title, (panel_x, top))

    turn_txt = f"턴: {'빨강(R)' if gs.current==P1 else '파랑(B)'}"
    t_surf = font.render(turn_txt, True, RED if gs.current==P1 else BLUE)
    screen.blit(t_surf, (panel_x, top+40))

    p1txt = small.render(f"빨강 남은 조각: {gs.pieces_left[P1]}", True, WHITE)
    p2txt = small.render(f"파랑 남은 조각: {gs.pieces_left[P2]}", True, WHITE)
    screen.blit(p1txt, (panel_x, top+80))
    screen.blit(p2txt, (panel_x, top+105))

    etxt = small.render(f"[E] 비상 아무데나 두기: {'ON' if gs.emergency_anywhere else 'OFF'}",
                        True, YELLOW if gs.emergency_anywhere else GREY)
    screen.blit(etxt, (panel_x, top+145))

    info1 = small.render("막히면: 상대 돌 클릭해", True, WHITE)
    info2 = small.render("그 돌 주변에 둘 수 있어요", True, WHITE)
    screen.blit(info1, (panel_x, top+185))
    screen.blit(info2, (panel_x, top+210))

    key1 = small.render("[마우스] 착수 / 상대돌 클릭=앵커 선택", True, WHITE)
    key2 = small.render("[R] 재시작, [E] 토글, [Esc] 종료", True, WHITE)
    key3 = small.render("[Enter]=무승부 확정(오퍼 중)", True, WHITE)
    screen.blit(key1, (panel_x, top+250))
    screen.blit(key2, (panel_x, top+275))
    screen.blit(key3, (panel_x, top+300))

    # 상태 메시지
    ymsg = top+320
    if gs.game_over:
        if gs.winner == 0:
            msg = "무승부!"
            color = WHITE
        else:
            msg = "빨강 승리!" if gs.winner==P1 else "파랑 승리!"
            color = RED if gs.winner==P1 else BLUE
        over = font.render(msg, True, color)
        screen.blit(over, (panel_x, ymsg))
    else:
        # 안내 메시지
        if gs.pieces_left[P1] == 0 and gs.pieces_left[P2] == 0:
            note = small.render("양측 말 소진: 무승부 조건", True, WHITE)
            screen.blit(note, (panel_x, ymsg)); ymsg += 25
        if gs.pieces_left[gs.current] <= 0:
            note = small.render("현재 차례 말 소진: 자동 패스", True, WHITE)
            screen.blit(note, (panel_x, ymsg)); ymsg += 25
        if gs.pass_streak > 0 and not gs.emergency_anywhere:
            note = small.render(f"연속 패스 {gs.pass_streak}/2 → 2회시 무승부", True, WHITE)
            screen.blit(note, (panel_x, ymsg)); ymsg += 25
        else:
            candidate, reason = compute_valid_moves(gs, gs.current)
            if not candidate and reason == "no_moves_any_anchor_all_blocked" and not gs.emergency_anywhere:
                note = small.render("비상 OFF: 현재 차례 패스", True, WHITE)
                screen.blit(note, (panel_x, ymsg)); ymsg += 25
            elif reason == "emergency_anywhere":
                note = small.render("비상: 아무 빈칸 가능", True, YELLOW)
                screen.blit(note, (panel_x, ymsg))

    # ★ 오퍼 상태 오버레이
    if gs.offer_emergency and not gs.game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,140))  # 반투명 블랙
        screen.blit(overlay, (0,0))

        box_w, box_h = 700, 170
        box = pygame.Rect((WIDTH-box_w)//2, (HEIGHT-box_h)//2, box_w, box_h)
        pygame.draw.rect(screen, (40,44,52), box, border_radius=14)
        pygame.draw.rect(screen, (220,220,220), box, width=2, border_radius=14)

        title = font.render("연속 패스 2회로 무승부가 됩니다.", True, (255,255,255))
        tip1  = small.render("비상 아무데나 두기를 [E] 로 ON 하면 경기를 계속할 수 있습니다.", True, (255,255,255))
        tip2  = small.render("무승부로 끝내려면 [Enter] 를 누르세요.", True, (200,200,200))

        cx = box.centerx
        screen.blit(title, (cx - title.get_width()//2, box.y + 22))
        screen.blit(tip1,  (cx - tip1.get_width()//2,  box.y + 70))
        screen.blit(tip2,  (cx - tip2.get_width()//2,  box.y + 102))


# -------------------- 입출력 --------------------
def rc_from_mouse(pos)->Optional[Tuple[int,int]]:
    x,y = pos
    left = MARGIN
    top = MARGIN
    if not (left <= x < left+GRID_N*CELL and top <= y < top+GRID_N*CELL):
        return None
    c = (x - left) // CELL
    r = (y - top) // CELL
    return (r,c)


# -------------------- 메인 루프 --------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("4Mation (7x7 · 4목)")
    clock = pygame.time.Clock()

    # 폰트
    kfont = find_korean_font()
    if kfont:
        font = pygame.font.Font(kfont, 26)
        small = pygame.font.Font(kfont, 20)
    else:
        font = pygame.font.SysFont(None, 26)
        small = pygame.font.SysFont(None, 20)

    gs = GameState()
    
    # ★ 테스트 모드 자동 로드
    if DEBUG_SCENARIO:
        load_from_order_matrix(gs, order_matrix)
        
    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                elif event.key == pygame.K_r:
                    gs.reset()
                    # 테스트 모드에서 R 이후에도 동일 시나리오로 복원하려면:
                    if DEBUG_SCENARIO:
                        load_from_order_matrix(gs, order_matrix)
                    continue
                # ★ 테스트 시나리오 재로드 단축키
                elif event.key == pygame.K_t:
                    gs.reset()
                    load_from_order_matrix(gs, order_matrix)
                    continue

                # ★ 오퍼 상태일 때 전용 키만 허용
                if gs.offer_emergency:
                    if event.key == pygame.K_e:
                        gs.emergency_anywhere = True
                        gs.offer_emergency = False
                        gs.offer_reason = ""
                        # 비상 ON 즉시 재평가
                        gs.handle_pass_if_needed()
                    elif event.key == pygame.K_RETURN:
                        # 무승부 확정
                        gs.game_over = True
                        gs.winner = 0
                        gs.offer_emergency = False
                        gs.offer_reason = ""
                    # 오퍼 중 다른 키는 무시
                    continue

                # 오퍼 아닐 때 일반 키
                if event.key == pygame.K_e:
                    gs.emergency_anywhere = not gs.emergency_anywhere
                    gs.handle_pass_if_needed()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 오퍼/게임 종료 중엔 클릭 무시
                if gs.game_over or gs.offer_emergency:
                    continue
                rc = rc_from_mouse(event.pos)
                if rc is None:
                    continue
                r,c = rc
                # 상대 돌 클릭 → 앵커 선택
                if gs.board[r][c] == gs.opponent(gs.current):
                    gs.selected_anchor = (r,c)
                else:
                    # 빈칸 클릭 → 착수 시도
                    gs.place(r,c)

        draw_board(screen, gs, font, small)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

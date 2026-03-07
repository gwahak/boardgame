import sys
import random
from collections import deque

import pygame


# =========================
# Constants
# =========================
BOARD_SIZE = 9
CELL_SIZE = 64
MARGIN = 48
INFO_HEIGHT = 160

WINDOW_WIDTH = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)
WINDOW_HEIGHT = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1) + INFO_HEIGHT

EMPTY = 0
BLUE = 1
ORANGE = 2
NEUTRAL = 3

NO_TERRITORY = 0
BLUE_TERRITORY = -1
ORANGE_TERRITORY = -2

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

BG_COLOR = (245, 235, 200)
LINE_COLOR = (60, 40, 20)
TEXT_COLOR = (20, 20, 20)

BLUE_STONE = (50, 90, 210)
ORANGE_STONE = (235, 140, 40)
NEUTRAL_STONE = (120, 120, 120)

BLUE_TERR_COLOR = (195, 220, 255)
ORANGE_TERR_COLOR = (255, 220, 185)

LEGAL_GHOST_BLUE = (120, 160, 255)
LEGAL_GHOST_ORANGE = (255, 190, 120)
ILLEGAL_MARK = (220, 40, 40)

STAR_COLOR = (50, 50, 50)

BUTTON_FILL = (230, 220, 185)
BUTTON_HOVER = (245, 235, 205)
BUTTON_BORDER = (90, 70, 40)

AI_ON_FILL_BLUE = (180, 210, 255)
AI_ON_FILL_ORANGE = (255, 205, 160)
AI_OFF_FILL = (220, 215, 205)

AI_DELAY_MS = 250


# =========================
# Utility
# =========================
def other_player(player):
    return ORANGE if player == BLUE else BLUE


def board_to_screen(r, c):
    x = MARGIN + c * CELL_SIZE
    y = MARGIN + r * CELL_SIZE
    return x, y


def screen_to_board(pos):
    mx, my = pos
    best = None
    best_dist2 = (CELL_SIZE * 0.45) ** 2

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = board_to_screen(r, c)
            dx = mx - x
            dy = my - y
            dist2 = dx * dx + dy * dy
            if dist2 <= best_dist2:
                best = (r, c)
                best_dist2 = dist2

    return best


def do_pass(state):
    if state["game_over"]:
        return

    state["pass_count"] += 1
    if state["pass_count"] >= 2:
        finish_by_score(state)
    else:
        state["current_player"] = other_player(state["current_player"])

    state["last_ai_move_time"] = pygame.time.get_ticks()


# =========================
# Go-like group / capture
# =========================
def get_group_and_liberties(board, sr, sc):
    color = board[sr][sc]
    if color not in (BLUE, ORANGE):
        return set(), set()

    stack = [(sr, sc)]
    visited = set()
    group = set()
    liberties = set()

    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        group.add((r, c))

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                cell = board[nr][nc]
                if cell == EMPTY:
                    liberties.add((nr, nc))
                elif cell == color and (nr, nc) not in visited:
                    stack.append((nr, nc))

    return group, liberties


def collect_captured_groups(board, placed_r, placed_c, current_player):
    opponent = other_player(current_player)
    captured = set()

    for dr, dc in DIRS:
        nr, nc = placed_r + dr, placed_c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr][nc] == opponent:
                group, liberties = get_group_and_liberties(board, nr, nc)
                if len(liberties) == 0:
                    captured |= group

    return captured


def is_suicide(board, r, c, current_player):
    test_board = [row[:] for row in board]
    test_board[r][c] = current_player

    captured = collect_captured_groups(test_board, r, c, current_player)
    for gr, gc in captured:
        test_board[gr][gc] = EMPTY

    group, liberties = get_group_and_liberties(test_board, r, c)
    return len(liberties) == 0


# =========================
# Territory
# =========================
def compute_territory_map(board):
    territory_map = [[NO_TERRITORY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    for sr in range(BOARD_SIZE):
        for sc in range(BOARD_SIZE):
            if board[sr][sc] != EMPTY or visited[sr][sc]:
                continue

            q = deque([(sr, sc)])
            visited[sr][sc] = True

            region = []
            bordering_colors = set()
            touches_neutral = False
            touched_sides = set()

            while q:
                r, c = q.popleft()
                region.append((r, c))

                if r == 0:
                    touched_sides.add("top")
                if r == BOARD_SIZE - 1:
                    touched_sides.add("bottom")
                if c == 0:
                    touched_sides.add("left")
                if c == BOARD_SIZE - 1:
                    touched_sides.add("right")

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                        continue

                    cell = board[nr][nc]
                    if cell == EMPTY:
                        if not visited[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr, nc))
                    elif cell == BLUE:
                        bordering_colors.add(BLUE)
                    elif cell == ORANGE:
                        bordering_colors.add(ORANGE)
                    elif cell == NEUTRAL:
                        touches_neutral = True

            owner = NO_TERRITORY
            if len(touched_sides) < 4 and not touches_neutral:
                if bordering_colors == {BLUE}:
                    owner = BLUE_TERRITORY
                elif bordering_colors == {ORANGE}:
                    owner = ORANGE_TERRITORY

            for r, c in region:
                territory_map[r][c] = owner

    return territory_map


def count_territory(territory_map):
    blue_count = 0
    orange_count = 0

    for row in territory_map:
        for cell in row:
            if cell == BLUE_TERRITORY:
                blue_count += 1
            elif cell == ORANGE_TERRITORY:
                orange_count += 1

    return blue_count, orange_count


# =========================
# Move legality
# =========================
def can_place(board, territory_map, r, c, player):
    if board[r][c] != EMPTY:
        return False

    if player == BLUE and territory_map[r][c] == ORANGE_TERRITORY:
        return False
    if player == ORANGE and territory_map[r][c] == BLUE_TERRITORY:
        return False

    if is_suicide(board, r, c, player):
        return False

    return True


def get_legal_moves(board, territory_map, player):
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if can_place(board, territory_map, r, c, player):
                moves.append((r, c))
    return moves


# =========================
# AI
# NOTE:
# The current AI is intentionally simple and should be regarded as a placeholder.
# It is very weak and exists only to automate basic play/testing.
# A stronger AI (e.g., minimax, alpha-beta pruning, or MCTS) may be added later.
# =========================
def choose_ai_move(board, territory_map, player):
    legal_moves = get_legal_moves(board, territory_map, player)
    if not legal_moves:
        return None

    # 1순위: 즉시 포획 승리 수
    winning_moves = []
    for r, c in legal_moves:
        test_board = [row[:] for row in board]
        test_board[r][c] = player
        captured = collect_captured_groups(test_board, r, c, player)
        if captured:
            winning_moves.append((r, c))

    if winning_moves:
        return random.choice(winning_moves)

    # 2순위: 자기 집을 늘리는 수 대충 선호
    scored_moves = []
    for r, c in legal_moves:
        test_board = [row[:] for row in board]
        test_board[r][c] = player
        test_territory = compute_territory_map(test_board)
        blue_score, orange_score = count_territory(test_territory)
        score = blue_score if player == BLUE else orange_score
        scored_moves.append((score, (r, c)))

    best_score = max(score for score, _ in scored_moves)
    best_moves = [move for score, move in scored_moves if score == best_score]
    return random.choice(best_moves)


def perform_move(state, r, c):
    board = state["board"]
    player = state["current_player"]

    board[r][c] = player
    captured = collect_captured_groups(board, r, c, player)

    if captured:
        for gr, gc in captured:
            board[gr][gc] = EMPTY

        state["territory_map"] = compute_territory_map(board)
        state["game_over"] = True
        state["winner_text"] = "Blue wins by capture!" if player == BLUE else "Orange wins by capture!"
        state["last_ai_move_time"] = pygame.time.get_ticks()
        return

    state["territory_map"] = compute_territory_map(board)
    state["pass_count"] = 0
    state["current_player"] = other_player(player)
    state["last_ai_move_time"] = pygame.time.get_ticks()


def maybe_do_ai_turn(state):
    if state["game_over"]:
        return

    player = state["current_player"]
    if not state["blue_ai"] and player == BLUE:
        return
    if not state["orange_ai"] and player == ORANGE:
        return

    now = pygame.time.get_ticks()
    if now - state["last_ai_move_time"] < AI_DELAY_MS:
        return

    move = choose_ai_move(state["board"], state["territory_map"], player)
    if move is None:
        do_pass(state)
    else:
        perform_move(state, move[0], move[1])


# =========================
# Buttons
# =========================
def get_button_rects():
    panel_top = WINDOW_HEIGHT - INFO_HEIGHT
    pass_rect = pygame.Rect(20, panel_top + 100, 110, 34)
    restart_rect = pygame.Rect(145, panel_top + 100, 120, 34)
    blue_ai_rect = pygame.Rect(280, panel_top + 100, 130, 34)
    orange_ai_rect = pygame.Rect(425, panel_top + 100, 145, 34)
    return pass_rect, restart_rect, blue_ai_rect, orange_ai_rect


def draw_button(screen, font, rect, text, hovered, fill=None):
    if fill is None:
        fill = BUTTON_HOVER if hovered else BUTTON_FILL
    elif hovered:
        fill = tuple(min(255, x + 10) for x in fill)

    pygame.draw.rect(screen, fill, rect, border_radius=8)
    pygame.draw.rect(screen, BUTTON_BORDER, rect, 2, border_radius=8)

    txt = font.render(text, True, TEXT_COLOR)
    tx = rect.x + (rect.width - txt.get_width()) // 2
    ty = rect.y + (rect.height - txt.get_height()) // 2
    screen.blit(txt, (tx, ty))


# =========================
# Drawing
# =========================
def draw_board_background(screen):
    screen.fill(BG_COLOR)

    for i in range(BOARD_SIZE):
        x1, y1 = board_to_screen(0, i)
        x2, y2 = board_to_screen(BOARD_SIZE - 1, i)
        pygame.draw.line(screen, LINE_COLOR, (x1, y1), (x2, y2), 2)

        x1, y1 = board_to_screen(i, 0)
        x2, y2 = board_to_screen(i, BOARD_SIZE - 1)
        pygame.draw.line(screen, LINE_COLOR, (x1, y1), (x2, y2), 2)

    for r, c in [(2, 2), (2, 6), (4, 4), (6, 2), (6, 6)]:
        x, y = board_to_screen(r, c)
        pygame.draw.circle(screen, STAR_COLOR, (x, y), 4)


def draw_territory(screen, territory_map):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            terr = territory_map[r][c]
            if terr == NO_TERRITORY:
                continue

            x, y = board_to_screen(r, c)

            s = pygame.Surface((CELL_SIZE - 8, CELL_SIZE - 8), pygame.SRCALPHA)
            color = BLUE_TERR_COLOR if terr == BLUE_TERRITORY else ORANGE_TERR_COLOR
            s.fill((*color, 120))
            screen.blit(s, (x - (CELL_SIZE - 8) // 2, y - (CELL_SIZE - 8) // 2))


def draw_stones(screen, board):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = board[r][c]
            if cell == EMPTY:
                continue

            x, y = board_to_screen(r, c)

            if cell == BLUE:
                pygame.draw.circle(screen, BLUE_STONE, (x, y), 22)
                pygame.draw.circle(screen, (20, 30, 90), (x, y), 22, 2)
            elif cell == ORANGE:
                pygame.draw.circle(screen, ORANGE_STONE, (x, y), 22)
                pygame.draw.circle(screen, (140, 80, 20), (x, y), 22, 2)
            elif cell == NEUTRAL:
                pygame.draw.circle(screen, NEUTRAL_STONE, (x, y), 18)
                pygame.draw.circle(screen, (40, 40, 40), (x, y), 18, 2)
                pygame.draw.circle(screen, (200, 200, 200), (x, y), 5)


def draw_hover(screen, board, territory_map, hover_cell, player, game_over, blue_ai, orange_ai):
    if game_over or hover_cell is None:
        return

    if (player == BLUE and blue_ai) or (player == ORANGE and orange_ai):
        return

    r, c = hover_cell
    x, y = board_to_screen(r, c)

    legal = can_place(board, territory_map, r, c, player)

    if legal:
        color = LEGAL_GHOST_BLUE if player == BLUE else LEGAL_GHOST_ORANGE
        pygame.draw.circle(screen, color, (x, y), 18, 3)
    else:
        pygame.draw.line(screen, ILLEGAL_MARK, (x - 16, y - 16), (x + 16, y + 16), 4)
        pygame.draw.line(screen, ILLEGAL_MARK, (x + 16, y - 16), (x - 16, y + 16), 4)


def draw_info(screen, font, small_font, state):
    blue_score, orange_score = count_territory(state["territory_map"])

    panel_top = WINDOW_HEIGHT - INFO_HEIGHT
    pygame.draw.rect(screen, (235, 225, 190), (0, panel_top, WINDOW_WIDTH, INFO_HEIGHT))
    pygame.draw.line(screen, LINE_COLOR, (0, panel_top), (WINDOW_WIDTH, panel_top), 2)

    if not state["game_over"]:
        turn_text = "Turn: Blue" if state["current_player"] == BLUE else "Turn: Orange"
    else:
        turn_text = "Game Over"

    t1 = font.render(turn_text, True, TEXT_COLOR)
    t2 = small_font.render(f"Blue territory: {blue_score}", True, TEXT_COLOR)
    t3 = small_font.render(f"Orange territory: {orange_score}", True, TEXT_COLOR)
    t4 = small_font.render(f"Consecutive passes: {state['pass_count']}", True, TEXT_COLOR)
    t5 = small_font.render("Left click: place   P: pass   R: restart   ESC: quit", True, TEXT_COLOR)
    t6 = small_font.render("If AI has no legal move, it automatically passes.", True, TEXT_COLOR)

    screen.blit(t1, (20, panel_top + 12))
    screen.blit(t2, (20, panel_top + 48))
    screen.blit(t3, (200, panel_top + 48))
    screen.blit(t4, (390, panel_top + 48))
    screen.blit(t5, (20, panel_top + 72))
    screen.blit(t6, (20, panel_top + 132))

    pass_rect, restart_rect, blue_ai_rect, orange_ai_rect = get_button_rects()
    mouse_pos = pygame.mouse.get_pos()

    draw_button(screen, small_font, pass_rect, "PASS", pass_rect.collidepoint(mouse_pos))
    draw_button(screen, small_font, restart_rect, "RESTART", restart_rect.collidepoint(mouse_pos))

    blue_fill = AI_ON_FILL_BLUE if state["blue_ai"] else AI_OFF_FILL
    orange_fill = AI_ON_FILL_ORANGE if state["orange_ai"] else AI_OFF_FILL

    draw_button(
        screen,
        small_font,
        blue_ai_rect,
        f"Blue AI {'ON' if state['blue_ai'] else 'OFF'}",
        blue_ai_rect.collidepoint(mouse_pos),
        fill=blue_fill,
    )
    draw_button(
        screen,
        small_font,
        orange_ai_rect,
        f"Orange AI {'ON' if state['orange_ai'] else 'OFF'}",
        orange_ai_rect.collidepoint(mouse_pos),
        fill=orange_fill,
    )

    if state["game_over"] and state["winner_text"]:
        tw = font.render(state["winner_text"], True, (120, 20, 20))
        screen.blit(tw, (300, panel_top + 12))


# =========================
# Game setup / reset
# =========================
def new_game():
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    board[BOARD_SIZE // 2][BOARD_SIZE // 2] = NEUTRAL

    territory_map = compute_territory_map(board)

    return {
        "board": board,
        "territory_map": territory_map,
        "current_player": BLUE,
        "pass_count": 0,
        "game_over": False,
        "winner_text": "",
        "blue_ai": False,
        "orange_ai": False,
        "last_ai_move_time": pygame.time.get_ticks(),
    }


def finish_by_score(state):
    blue_score, orange_score = count_territory(state["territory_map"])
    if blue_score >= orange_score + 3:
        state["winner_text"] = f"Blue wins by territory: {blue_score} vs {orange_score}"
    else:
        state["winner_text"] = f"Orange wins by territory: {orange_score} vs {blue_score}"
    state["game_over"] = True


# =========================
# Main
# =========================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Lee Sedol Castle Game (9x9)")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 34)
    small_font = pygame.font.SysFont(None, 24)

    state = new_game()

    while True:
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = screen_to_board(mouse_pos)
        pass_rect, restart_rect, blue_ai_rect, orange_ai_rect = get_button_rects()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                elif event.key == pygame.K_r:
                    blue_ai = state["blue_ai"]
                    orange_ai = state["orange_ai"]
                    state = new_game()
                    state["blue_ai"] = blue_ai
                    state["orange_ai"] = orange_ai

                elif event.key == pygame.K_p:
                    # 사람이 조작 중일 때만 수동 패스 허용
                    cp = state["current_player"]
                    if not ((cp == BLUE and state["blue_ai"]) or (cp == ORANGE and state["orange_ai"])):
                        do_pass(state)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pass_rect.collidepoint(event.pos):
                    cp = state["current_player"]
                    if not ((cp == BLUE and state["blue_ai"]) or (cp == ORANGE and state["orange_ai"])):
                        do_pass(state)
                    continue

                if restart_rect.collidepoint(event.pos):
                    blue_ai = state["blue_ai"]
                    orange_ai = state["orange_ai"]
                    state = new_game()
                    state["blue_ai"] = blue_ai
                    state["orange_ai"] = orange_ai
                    continue

                if blue_ai_rect.collidepoint(event.pos):
                    state["blue_ai"] = not state["blue_ai"]
                    state["last_ai_move_time"] = pygame.time.get_ticks()
                    continue

                if orange_ai_rect.collidepoint(event.pos):
                    state["orange_ai"] = not state["orange_ai"]
                    state["last_ai_move_time"] = pygame.time.get_ticks()
                    continue

                if state["game_over"]:
                    continue

                player = state["current_player"]
                if (player == BLUE and state["blue_ai"]) or (player == ORANGE and state["orange_ai"]):
                    continue

                if hover_cell is None:
                    continue

                r, c = hover_cell
                board = state["board"]
                territory_map = state["territory_map"]

                if not can_place(board, territory_map, r, c, player):
                    continue

                perform_move(state, r, c)

        maybe_do_ai_turn(state)

        draw_board_background(screen)
        draw_territory(screen, state["territory_map"])
        draw_stones(screen, state["board"])
        draw_hover(
            screen,
            state["board"],
            state["territory_map"],
            hover_cell,
            state["current_player"],
            state["game_over"],
            state["blue_ai"],
            state["orange_ai"],
        )
        draw_info(screen, font, small_font, state)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()

import sys
import pygame

# -----------------------------
# Game constants & utilities
# -----------------------------
BOARD_N = 8
CELL = 80
MARGIN = 40
WIDTH = HEIGHT = BOARD_N * CELL + MARGIN * 2
FPS = 60

# pan values:
#   0 = empty
#  -1 = blocked (corners)
#  1..4 = player stones
def make_initial_board():
    pan = [[0 for _ in range(BOARD_N)] for _ in range(BOARD_N)]
    # Original turtle code visually blocked corners; we mark as -1 (blocked).
    pan[0][0] = -1
    pan[0][BOARD_N-1] = -1
    pan[BOARD_N-1][0] = -1
    pan[BOARD_N-1][BOARD_N-1] = -1
    return pan

# colors/labels (compatible with original)
def colorassign(n, d=4):
    if (n-1) % d == 0:
        return (220, 20, 60)     # red
    elif (n-2) % d == 0:
        return (30, 144, 255)    # blue
    elif (n-3) % d == 0:
        return (255, 140, 0)     # orange
    elif (n-4) % d == 0:
        return (255, 215, 0)     # yellow
    else:
        return (0, 0, 0)

def colorsutza(n, d=4):
    # number color (original: players 1,2 white; 3,4 black)
    if (n-1) % d in (0, 1):
        return (255, 255, 255)
    else:
        return (0, 0, 0)

def playername(n, d=4):
    if (n-1) % d == 0:
        return "Red"
    elif (n-2) % d == 0:
        return "Blue"
    elif (n-3) % d == 0:
        return "Orange"
    elif (n-4) % d == 0:
        return "Yellow"
    else:
        return "Black"

# coordinate transforms
def to_screen(rc):
    r, c = rc  # r: 0..7 (row, top->bottom), c: 0..7 (col, left->right)
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return x, y

def from_mouse(pos):
    mx, my = pos
    if mx < MARGIN or my < MARGIN:
        return None
    c = (mx - MARGIN) // CELL
    r = (my - MARGIN) // CELL
    if 0 <= r < BOARD_N and 0 <= c < BOARD_N:
        return int(r), int(c)
    return None

# -----------------------------
# Win / count logic (ported)
# -----------------------------
def count4(pan, n):
    count = 0
    N = BOARD_N
    # horizontal/vertical
    for i in range(N):
        for j in range(N-3):
            if all(pan[i][j+k] == n for k in range(4)):
                count += 1
            if all(pan[j+k][i] == n for k in range(4)):
                count += 1
    # diagonals
    for i in range(N-3):
        for j in range(N-3):
            if all(pan[i+k][j+k] == n for k in range(4)):
                count += 1
            if all(pan[i+3-k][j+k] == n for k in range(4)):
                count += 1
    return count

def count3(pan, n):
    count = 0
    N = BOARD_N
    # horizontal/vertical
    for i in range(N):
        for j in range(N-2):
            if all(pan[i][j+k] == n for k in range(3)):
                count += 1
            if all(pan[j+k][i] == n for k in range(3)):
                count += 1
    # diagonals
    for i in range(N-2):
        for j in range(N-2):
            if all(pan[i+k][j+k] == n for k in range(3)):
                count += 1
            if all(pan[i+2-k][j+k] == n for k in range(3)):
                count += 1
    return count

def count2(pan, n):
    count = 0
    N = BOARD_N
    # horizontal/vertical
    for i in range(N):
        for j in range(N-1):
            if pan[i][j] == n and pan[i][j+1] == n:
                count += 1
            if pan[j][i] == n and pan[j+1][i] == n:
                count += 1
    # diagonals
    for i in range(N-1):
        for j in range(N-1):
            if pan[i][j] == n and pan[i+1][j+1] == n:
                count += 1
            if pan[i+1][j] == n and pan[i][j+1] == n:
                count += 1
    return count

def row_full(pan, r):
    return all(pan[r][c] != 0 for c in range(BOARD_N))

def col_full(pan, c):
    return all(pan[r][c] != 0 for r in range(BOARD_N))

# -----------------------------
# Drawing
# -----------------------------
def draw_board(screen, font, pan, tx, ty, players, current_idx, phase, msg):
    screen.fill((245, 245, 245))

    # board grid & blocked corners
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            x, y = to_screen((r, c))
            rect = pygame.Rect(x, y, CELL, CELL)

            # central 2x2 (D4,D5,E4,E5)
            center = (3 <= r <= 4) and (3 <= c <= 4)

            # base tile color
            tile_color = (230, 230, 230) if (r + c) % 2 == 0 else (215, 215, 215)

            if pan[r][c] == -1:
                pygame.draw.rect(screen, (30, 30, 30), rect)
            else:
                pygame.draw.rect(screen, tile_color, rect)

                # central emphasis
                if center:
                    border = 3 if phase == "first_moves" else 1
                    pygame.draw.rect(screen, (34, 139, 34), rect, border)

            # grid line
            pygame.draw.rect(screen, (80, 80, 80), rect, 1)

    # crosshair (tx,ty)
    if tx is not None and ty is not None:
        # row highlight
        r = ty
        for c in range(BOARD_N):
            if pan[r][c] != -1:
                x, y = to_screen((r, c))
                pygame.draw.rect(screen, (144, 238, 144), (x, y, CELL, CELL), 2)
        # column highlight
        c = tx
        for r in range(BOARD_N):
            if pan[r][c] != -1:
                x, y = to_screen((r, c))
                pygame.draw.rect(screen, (144, 238, 144), (x, y, CELL, CELL), 2)

    # stones
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            v = pan[r][c]
            if v > 0:
                x, y = to_screen((r, c))
                cx = x + CELL // 2
                cy = y + CELL // 2
                col = colorassign(v, players)
                pygame.draw.circle(screen, col, (cx, cy), CELL // 2 - 8)
                # number
                num_color = colorsutza(v, players)
                text = font.render(str(v), True, num_color)
                text_rect = text.get_rect(center=(cx, cy))
                screen.blit(text, text_rect)

    # HUD / messages
    info_lines = []
    info_lines.append(f"{players}-player Pixel (Pygame)  —  Turn: {playername(current_idx, players)}({current_idx})")
    if phase == "first_moves":
        info_lines.append("Opening move: Each player must place their first stone inside the central 2×2 (D4,D5,E4,E5).")
    else:
        info_lines.append("Main game: You can only place a stone in the same row OR column as the crosshair (not both).")
        info_lines.append("If both the row and column are completely filled, you may move the crosshair without placing.")
    if msg:
        info_lines.append(msg)

    y0 = 10
    for line in info_lines:
        label = font.render(line, True, (10, 10, 10))
        screen.blit(label, (10, y0))
        y0 += 24

def pick_players(screen, clock):
    # simple selection: press 2/3/4 keys
    font = pygame.font.SysFont(None, 28)
    while True:
        screen.fill((250, 250, 255))
        t1 = font.render("How many players? (Press 2/3/4 on keyboard)", True, (40, 40, 60))
        t2 = font.render("ESC: Quit", True, (120, 120, 140))
        screen.blit(t1, (50, 120))
        screen.blit(t2, (50, 160))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
                if event.key in (pygame.K_2, pygame.K_3, pygame.K_4):
                    return int(event.unicode)
        clock.tick(FPS)

# -----------------------------
# Main
# -----------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Pixel (Pygame edition)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    big_font = pygame.font.SysFont(None, 48)

    players = pick_players(screen, clock)

    pan = make_initial_board()

    # original: initial crosshair tx=4, ty=5 (1-indexed) → 0-indexed: tx=3, ty=4
    # and set pan[3][4] = 1 (first stone)
    tx, ty = 3, 4
    pan[ty][tx] = 1
    # player 1 already placed; now players 2..N must do their opening move
    phase = "first_moves" if players > 1 else "main"
    first_move_next_player = 2
    current_player = 2 if phase == "first_moves" else 1
    total_turns = 1  # one stone placed
    msg = ""

    running = True
    game_over = False
    winner_text = None

    def end_game(text):
        nonlocal game_over, winner_text
        game_over = True
        winner_text = text

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if game_over:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sel = from_mouse(event.pos)
                if sel is None:
                    continue
                r, c = sel
                if pan[r][c] == -1:
                    msg = "Blocked cell. You cannot place here."
                    continue

                # opening moves
                if phase == "first_moves":
                    # central 2×2 only: (r,c) ∈ {(3,3),(3,4),(4,3),(4,4)}
                    if not (3 <= r <= 4 and 3 <= c <= 4):
                        msg = "Opening move must be inside the central 2×2 (D4,D5,E4,E5)."
                        continue
                    if pan[r][c] != 0:
                        msg = "That cell is already occupied."
                        continue
                    pan[r][c] = current_player
                    tx, ty = c, r
                    total_turns += 1

                    # instant win checks (4-in-a-row for all, 3-in-a-row for 4-player)
                    if count4(pan, current_player) >= 1:
                        end_game(f"{playername(current_player, players)} wins with a 4-in-a-row!")
                    elif players == 4 and count3(pan, current_player) >= 1:
                        end_game(f"{playername(current_player, players)} wins with a 3-in-a-row!")
                    if game_over:
                        continue

                    first_move_next_player += 1
                    if first_move_next_player > players:
                        phase = "main"
                        current_player = players  # align with turn increment logic
                    else:
                        current_player = first_move_next_player
                    msg = ""
                    continue

                # main game
                # must change exactly one axis relative to (tx,ty): same row OR column
                if (c - tx) != 0 and (r - ty) != 0:
                    msg = "You cannot move both the row and column at the same time."
                    continue

                # if both row and column are full, allow crosshair move without placing (consumes turn)
                if row_full(pan, ty) and col_full(pan, tx):
                    tx, ty = c, r
                    current_player = (current_player % players) + 1
                    total_turns += 1
                    msg = "Row and column are full. Crosshair moved without placing a stone."
                    continue

                # otherwise, target cell must be empty
                if pan[r][c] != 0:
                    msg = "That cell is already occupied."
                    continue

                # place stone
                pan[r][c] = current_player
                tx, ty = c, r
                total_turns += 1

                # win checks
                if count4(pan, current_player) >= 1:
                    end_game(f"{playername(current_player, players)} wins with a 4-in-a-row!")
                    continue
                if players == 4 and count3(pan, current_player) >= 1:
                    end_game(f"{playername(current_player, players)} wins with a 3-in-a-row!")
                    continue

                # filled/end check (based on placeable cells)
                placeable_cells = sum(1 for rr in range(BOARD_N) for cc in range(BOARD_N) if pan[rr][cc] >= 0)
                stones = sum(1 for rr in range(BOARD_N) for cc in range(BOARD_N) if pan[rr][cc] > 0)
                if stones >= placeable_cells:
                    if players == 4:
                        c2 = [count2(pan, 1), count2(pan, 2), count2(pan, 3), count2(pan, 4)]
                        best = max(c2)
                        winners = [i+1 for i, v in enumerate(c2) if v == best]
                        report = (f"No player made 3- or 4-in-a-row.\n"
                                  f"2-in-a-row count: Red={c2[0]}, Blue={c2[1]}, Orange={c2[2]}, Yellow={c2[3]}")
                        if len(winners) == 1:
                            end_game(report + f"\n{playername(winners[0], players)} wins with the most 2-in-a-row!")
                        elif len(winners) == 4:
                            end_game(report + "\nAll players tied with the same number of 2-in-a-row. Draw!")
                        else:
                            names = ", ".join(playername(w, players) for w in winners)
                            end_game(report + f"\nJoint winners: {names}")
                    elif players == 3:
                        c3 = [count3(pan, 1), count3(pan, 2), count3(pan, 3)]
                        best = max(c3)
                        winners = [i+1 for i, v in enumerate(c3) if v == best]
                        report = (f"No player made 4-in-a-row.\n"
                                  f"3-in-a-row count: Red={c3[0]}, Blue={c3[1]}, Orange={c3[2]}")
                        if len(winners) == 1:
                            end_game(report + f"\n{playername(winners[0], players)} wins with the most 3-in-a-row!")
                        elif len(winners) == 3:
                            end_game(report + "\nAll players tied with the same number of 3-in-a-row. Draw!")
                        else:
                            names = ", ".join(playername(w, players) for w in winners)
                            end_game(report + f"\nJoint winners: {names}")
                    else:  # 2 players
                        c3 = [count3(pan, 1), count3(pan, 2)]
                        best = max(c3)
                        winners = [i+1 for i, v in enumerate(c3) if v == best]
                        report = (f"No player made 4-in-a-row.\n"
                                  f"3-in-a-row count: Red={c3[0]}, Blue={c3[1]}")
                        if len(winners) == 1:
                            end_game(report + f"\n{playername(winners[0], players)} wins with the most 3-in-a-row!")
                        else:
                            end_game(report + "\nBoth players tied with the same number of 3-in-a-row. Draw!")
                    continue

                # next player
                current_player = (current_player % players) + 1
                msg = ""

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break

        # draw
        draw_board(screen, pygame.font.SysFont(None, 22), pan, tx, ty,
                   players, current_player, phase, msg)

        # game-over overlay
        if game_over and winner_text:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            lines = winner_text.split("\n")
            y = HEIGHT // 2 - 20 * len(lines)
            for line in lines:
                t = big_font.render(line, True, (255, 255, 255))
                rect = t.get_rect(center=(WIDTH // 2, y))
                screen.blit(t, rect)
                y += 50

            sub = font.render("Press any key or click → Exit", True, (230, 230, 230))
            rect = sub.get_rect(center=(WIDTH // 2, y + 10))
            screen.blit(sub, rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()

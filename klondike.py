import pygame
import random

pygame.init()

# ================== 설정 ==================
WIDTH, HEIGHT = 1000, 700
CARD_W, CARD_H = 80, 120
BG_COLOR = (0, 120, 0)
FONT = pygame.font.SysFont("arial", 20)

DRAW_MODES = {
    1: "easy",
    2: "medium",
    3: "hard",
    4: "very hard"
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Klondike Solitaire")

# ================== 카드 ==================
SUITS = ["♠", "♥", "♦", "♣"]
COLORS = {"♠": (0,0,0), "♣": (0,0,0), "♥": (200,0,0), "♦": (200,0,0)}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        self.rect = pygame.Rect(0,0,CARD_W,CARD_H)

    def color(self):
        return COLORS[self.suit]

    def draw(self, surf):
        if self.face_up:
            pygame.draw.rect(surf, (245,245,245), self.rect)
            pygame.draw.rect(surf, (0,0,0), self.rect, 2)
            txt = FONT.render(f"{self.rank}{self.suit}", True, self.color())
            surf.blit(txt, (self.rect.x+5, self.rect.y+5))
        else:
            pygame.draw.rect(surf, (40,40,150), self.rect)
            pygame.draw.rect(surf, (0,0,0), self.rect, 2)

# ================== 게임 상태 ==================
class Game:
    def __init__(self, draw_n=1):
        self.draw_n = draw_n
        self.reset()

    def reset(self):
        deck = [Card(s, r) for s in SUITS for r in list(range(1,11))+["J","Q","K"]]
        random.shuffle(deck)

        self.tableau = [[] for _ in range(7)]
        idx = 0
        for i in range(7):
            for j in range(i+1):
                self.tableau[i].append(deck[idx])
                idx += 1
            self.tableau[i][-1].face_up = True

        self.stock = deck[idx:]
        self.waste = []
        self.foundations = [[] for _ in range(4)]

        self.drag_cards = []
        self.drag_offset = (0,0)
        self.drag_from = None
        self.last_draw_k = 0
        self.waste_window_start = 0
    # ================== 규칙 ==================
    def can_tableau(self, card, pile):
        if not pile:
            return card.rank == "K"
        top = pile[-1]
        if not top.face_up:
            return False
        if card.color() == top.color():
            return False
        return self.rank_val(card.rank) + 1 == self.rank_val(top.rank)

    def can_foundation(self, card, pile):
        if not pile:
            return card.rank == 1
        top = pile[-1]
        return card.suit == top.suit and self.rank_val(card.rank) == self.rank_val(top.rank)+1

    def rank_val(self, r):
        if isinstance(r, int): return r
        return {"J":11,"Q":12,"K":13}[r]

    # ================== 드로우 ==================
    def draw_stock(self):
        if self.stock:
            # 이번 draw가 시작되는 waste 인덱스 기록
            self.waste_window_start = len(self.waste)

            k = min(self.draw_n, len(self.stock))
            for _ in range(k):
                c = self.stock.pop()
                c.face_up = True
                self.waste.append(c)

            self.last_draw_k = k
        else:
            # 리사이클: waste -> stock (뒤집어서)
            while self.waste:
                c = self.waste.pop()
                c.face_up = False
                self.stock.append(c)

            self.last_draw_k = 0
            self.waste_window_start = 0


    # ================== 입력 ==================
    def pick_card(self, pos):
        # tableau
        for i,pile in enumerate(self.tableau):
            for j in range(len(pile)-1, -1, -1):
                c = pile[j]
                if c.face_up and c.rect.collidepoint(pos):
                    self.drag_cards = pile[j:]
                    self.drag_from = ("tableau", i, j)
                    self.drag_offset = (pos[0]-c.rect.x, pos[1]-c.rect.y)
                    return
        # waste
        if self.waste and self.waste[-1].rect.collidepoint(pos):
            self.drag_cards = [self.waste[-1]]
            self.drag_from = ("waste",)
            self.drag_offset = (pos[0]-self.waste[-1].rect.x, pos[1]-self.waste[-1].rect.y)

    def drop_card(self, pos):
        if not self.drag_cards:
            return

        card = self.drag_cards[0]

        # foundation
        for i,f in enumerate(self.foundations):
            if self.foundation_rect(i).collidepoint(pos):
                if self.can_foundation(card, f):
                    self.commit(("foundation", i))
                    return

        # tableau
        for i,p in enumerate(self.tableau):
            if self.tableau_rect(i).collidepoint(pos):
                if self.can_tableau(card, p):
                    self.commit(("tableau", i))
                    return

        self.cancel_drag()

    def commit(self, target):
        src = self.drag_from
        cards = self.drag_cards

        # remove
        if src[0]=="tableau":
            self.tableau[src[1]] = self.tableau[src[1]][:src[2]]
            if self.tableau[src[1]]:
                self.tableau[src[1]][-1].face_up = True
        elif src[0]=="waste":
            self.waste.pop()
            # 이번 window 안에서 카드가 빠지면 그냥 줄어들어야지, 이전 카드가 끼면 안 됨
            if self.waste_window_start > len(self.waste):
                self.waste_window_start = len(self.waste)
        # add
        if target[0]=="tableau":
            self.tableau[target[1]].extend(cards)
        elif target[0]=="foundation":
            self.foundations[target[1]].append(cards[0])

        self.drag_cards = []
        self.drag_from = None

    def cancel_drag(self):
        self.drag_cards = []
        self.drag_from = None

    # ================== 좌표 ==================
    def stock_rect(self):
        return pygame.Rect(50,50,CARD_W,CARD_H)

    def waste_rect(self):
        return pygame.Rect(150,50,CARD_W,CARD_H)

    def foundation_rect(self, i):
        return pygame.Rect(400+i*100,50,CARD_W,CARD_H)

    def tableau_rect(self, i):
        return pygame.Rect(50+i*130,200,CARD_W,HEIGHT)

    # ================== 그리기 ==================
    def draw(self, surf):
        surf.fill(BG_COLOR)

        # stock
        if self.stock:
            pygame.draw.rect(surf,(40,40,150),self.stock_rect())
        else:
            pygame.draw.rect(surf,(100,100,100),self.stock_rect(),2)

        # waste (이번 draw window만 표시)
        visible = []
        if self.waste:
            visible = self.waste[self.waste_window_start:]  # 이전 턴 카드는 절대 끼지 않음

        offset = 18
        for i, c in enumerate(visible):
            c.rect.topleft = (150 + i*offset, 50)
            c.draw(surf)


        # foundations
        for i,f in enumerate(self.foundations):
            r = self.foundation_rect(i)
            pygame.draw.rect(surf,(100,100,100),r,2)
            if f:
                f[-1].rect.topleft = r.topleft
                f[-1].draw(surf)

        # tableau
        for i,p in enumerate(self.tableau):
            x,y = 50+i*130,200
            for j,c in enumerate(p):
                c.rect.topleft = (x, y+j*25)
                c.draw(surf)

        # drag
        if self.drag_cards:
            mx,my = pygame.mouse.get_pos()
            ox,oy = self.drag_offset
            for i,c in enumerate(self.drag_cards):
                c.rect.topleft = (mx-ox, my-oy+i*25)
                c.draw(surf)

        txt = FONT.render(
            f"Draw: {self.draw_n} cards ({DRAW_MODES[self.draw_n]}) | 1~4 change | R reset",
            True,(255,255,255))
        surf.blit(txt,(20,HEIGHT-30))


# ================== 메인 루프 ==================
game = Game(1)
clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if game.stock_rect().collidepoint(e.pos):
                game.draw_stock()
            else:
                game.pick_card(e.pos)
        elif e.type == pygame.MOUSEBUTTONUP:
            game.drop_card(e.pos)
        elif e.type == pygame.KEYDOWN:
            if e.key in [pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4]:
                game = Game(int(e.unicode))
            elif e.key == pygame.K_r:
                game = Game(game.draw_n)

    game.draw(screen)
    pygame.display.flip()

pygame.quit()

import pygame
from typing import Dict, List, Tuple, Optional

# ================== Deal code (MSVC-style RNG) ==================
SUITS_CDHS = ["C", "D", "H", "S"]
RANKS_CDHS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

def msvc_rand_step(state: int) -> tuple[int, int]:
    state = (state * 214013 + 2531011) & 0xFFFFFFFF
    r = (state >> 16) & 0x7FFF
    return state, r

def card_str(card_id: int) -> str:
    suit = SUITS_CDHS[card_id % 4]
    rank = RANKS_CDHS[card_id // 4]
    return f"{rank}{suit}"

def tokki_deal(gamenumber: int) -> List[List[int]]:
    """
    TokkiCell deal:
    - 10 cascades total
    - casc[0] gets 1 Joker (added later as special card object)
    - casc[1] gets 2 Jokers
    - remaining 8 cascades receive 52 cards as 3..10 cards respectively:
        casc[2]=3, casc[3]=4, ..., casc[9]=10  (sum=52)
    """
    state = gamenumber & 0xFFFFFFFF
    deck = list(range(52))
    wLeft = 52

    # shuffle-by-deal, then we will pop in order
    shuffled: List[int] = []
    for _ in range(52):
        state, r = msvc_rand_step(state)
        j = r % wLeft
        shuffled.append(deck[j])
        wLeft -= 1
        deck[j] = deck[wLeft]

    casc = [[] for _ in range(10)]
    sizes = [0, 0, 3, 4, 5, 6, 7, 8, 9, 10]  # 52 cards distributed here
    idx = 0
    for ci in range(10):
        need = sizes[ci]
        if need > 0:
            casc[ci] = shuffled[idx:idx+need]
            idx += need
    return casc

CardStr = str
Board = List[List[CardStr]]

# (옵션) 이스터 배치: 토끼셀은 10줄이 필요함. 없으면 그냥 MSVC 모드만 써도 됨.
EASTER_DEALS: Dict[int, Board] = {
    # 예시(빈): 실제로 쓸 거면 10개 리스트로 맞춰줘야 함.
    1: [[], [], [], [], [], [], [], [], [], []],
}


BLANK = "__"

EASTER_DEALS: Dict[int, Board] = {
    1: [
        [BLANK],                 # 새로 추가: 빈서판 1장
        [BLANK, BLANK],          # 새로 추가: 빈서판 2장

        # 아래 8줄은 네가 준 이스터 배치 그대로
        ['KS', 'QS', 'JS'],
        ['10S', '9S', '8S', '7S'],
        ['KH', 'QH', 'JH', '10H', '9H'],
        ['8H', '7H', 'KD', 'QD', 'JD', '10D'],
        ['9D', '8D', '7D', 'KC', 'QC', 'JC', '10C'],
        ['9C', '8C', '7C', '6S', '5S', '4S', '3S', '2S'],
        ['AS', '6H', '5H', '4H', '3H', '2H', 'AH', '6D', '5D'],
        ['4D', '3D', '2D', 'AD', '6C', '5C', '4C', '3C', '2C', 'AC'],
    ]
}
# ================== Pygame setup ==================
pygame.init()

WIDTH, HEIGHT = 1250, 720
CARD_W, CARD_H = 80, 120
BG_COLOR = (0, 120, 0)
FONT = pygame.font.SysFont("arial", 20)
BIGFONT = pygame.font.SysFont("arial", 42)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TokkiCell")

COLORS = {"♠": (0, 0, 0), "♣": (0, 0, 0), "♥": (200, 0, 0), "♦": (200, 0, 0)}
GLYPH_BY_CDHS = {"S":"♠", "H":"♥", "D":"♦", "C":"♣"}
RANK_TO_VAL = {"A":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":11,"Q":12,"K":13}

def is_red(suit_glyph: str) -> bool:
    return suit_glyph in ("♥", "♦")

class Card:
    def __init__(self, suit_glyph: Optional[str], rank: str, is_joker: bool = False):
        self.suit = suit_glyph  # None for Joker
        self.rank = rank
        self.is_joker = is_joker
        self.face_up = True
        self.rect = pygame.Rect(0, 0, CARD_W, CARD_H)

    def color(self):
        if self.is_joker:
            return (30, 30, 30)
        return COLORS[self.suit]  # type: ignore[index]

    def rank_val(self) -> int:
        if self.is_joker:
            return -1
        return RANK_TO_VAL[self.rank]

    def draw(self, surf):
        if self.is_joker:
            pygame.draw.rect(surf, (210,210,210), self.rect)
            pygame.draw.rect(surf, (50,50,50), self.rect, 2)
            txt = FONT.render("?", True, (40,40,40))
            surf.blit(txt, (self.rect.x + 8, self.rect.y + 5))
            sub = FONT.render("JOKER", True, (40,40,40))
            surf.blit(sub, (self.rect.x + 8, self.rect.y + 30))
            return

        pygame.draw.rect(surf, (245,245,245), self.rect)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2)
        txt = FONT.render(f"{self.rank}{self.suit}", True, self.color())
        surf.blit(txt, (self.rect.x+5, self.rect.y+5))

def parse_card_str(s: str) -> Card:
    if s == "__":
        return joker_card()
    suit_cdhs = s[-1]
    rank = s[:-1]
    suit_glyph = GLYPH_BY_CDHS[suit_cdhs]
    return Card(suit_glyph, rank, is_joker=False)

def card_from_id(card_id: int) -> Card:
    suit_cdhs = SUITS_CDHS[card_id % 4]
    rank = RANKS_CDHS[card_id // 4]
    return parse_card_str(f"{rank}{suit_cdhs}")

def joker_card() -> Card:
    return Card(None, "J", is_joker=True)

# ================== TokkiCell game ==================
class TokkiCellGame:
    def __init__(self, deal_mode: str = "msvc", deal_number: int = 1, easter_id: int = 1):
        self.deal_mode = deal_mode
        self.deal_number = deal_number
        self.easter_id = easter_id
        self.reset()

    def reset(self):
        self.foundations: List[List[Card]] = [[] for _ in range(4)]
        self.cascades: List[List[Card]] = [[] for _ in range(10)]

        if self.deal_mode == "easter":
            board = EASTER_DEALS[self.easter_id]
            self.cascades = [[parse_card_str(cs) for cs in col] for col in board]
        else:
            cols = tokki_deal(self.deal_number)
            self.cascades = [[card_from_id(cid) for cid in col] for col in cols]

        # place jokers: casc[0]=1, casc[1]=2
        # (이스터 모드에서도 똑같이 넣고 싶으면 여기서 그대로 넣으면 됨)
        if self.deal_mode != "easter":
            self.cascades[0].append(joker_card())
            self.cascades[1].append(joker_card())
            self.cascades[1].append(joker_card())

        self.drag_cards: List[Card] = []
        self.drag_from: Optional[Tuple] = None
        self.drag_offset = (0,0)

        self.typing = ""
        self.message = ""
        self.msg_timer = 0

        self.last_click_time = 0
        self.last_click_pos = (0, 0)
        self.double_click_ms = 300

    # ---------- rules ----------
    def can_to_foundation(self, card: Card, fidx: int) -> bool:
        if card.is_joker:
            return False
        pile = self.foundations[fidx]
        if not pile:
            return card.rank_val() == 1
        top = pile[-1]
        return (not top.is_joker) and card.suit == top.suit and card.rank_val() == top.rank_val() + 1

    def can_to_cascade(self, card: Card, cidx: int) -> bool:
        pile = self.cascades[cidx]
        if not pile:
            return True
        top = pile[-1]

        # Joker adjacency: always allowed either direction
        if card.is_joker or top.is_joker:
            return True

        # normal FreeCell tableau rule
        if is_red(card.suit) == is_red(top.suit):  # type: ignore[arg-type]
            return False
        return card.rank_val() == top.rank_val() - 1

    def movable_limit(self) -> int:
        # No freecells in TokkiCell. Keep classic empty-cascade multiplier only.
        empty_cas = sum(1 for p in self.cascades if len(p) == 0)
        return 1 * (2 ** empty_cas)

    def is_valid_run(self, cards: List[Card]) -> bool:
        # Run validity generalized with Joker bridges:
        # if either adjacent pair contains a Joker -> always ok for that adjacency
        for i in range(len(cards)-1):
            a = cards[i]
            b = cards[i+1]
            if a.is_joker or b.is_joker:
                continue
            if a.rank_val() != b.rank_val() + 1:
                return False
            if is_red(a.suit) == is_red(b.suit):  # type: ignore[arg-type]
                return False
        return True

    # ---------- "Hanoi" safety rule (same logic; jokers excluded automatically) ----------
    def min_foundation_rank_by_color(self, want_red: bool) -> int:
        ranks = []
        for f in self.foundations:
            if f:
                if is_red(f[-1].suit) == want_red:  # type: ignore[arg-type]
                    ranks.append(f[-1].rank_val())
        return min(ranks) if ranks else 0

    def safe_to_auto_foundation(self, card: Card, fidx: int) -> bool:
        if card.is_joker:
            return False
        if not self.can_to_foundation(card, fidx):
            return False
        opp_min = self.min_foundation_rank_by_color(not is_red(card.suit))  # type: ignore[arg-type]
        return opp_min >= card.rank_val() - 1

    # ---------- geometry ----------
    def foundation_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(680 + i*110, 50, CARD_W, CARD_H)

    def cascade_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(40 + i*115, 210, CARD_W, HEIGHT - 230)

    # ---------- toasts ----------
    def toast(self, text: str, frames: int = 150):
        self.message = text
        self.msg_timer = frames

    # ---------- locate top card under mouse ----------
    def locate_top_card_at(self, pos) -> Optional[Tuple[str, int]]:
        for i in range(10):
            if not self.cascades[i]:
                continue
            c = self.cascades[i][-1]
            if c.rect.collidepoint(pos):
                return ("cascade", i)
        return None

    # ---------- auto move ----------
    def try_auto_move_once(self, safe_only: bool = True) -> bool:
        for ci in range(10):
            if not self.cascades[ci]:
                continue
            c = self.cascades[ci][-1]
            if c.is_joker:
                continue
            for f in range(4):
                ok = self.safe_to_auto_foundation(c, f) if safe_only else self.can_to_foundation(c, f)
                if ok:
                    self.cascades[ci].pop()
                    self.foundations[f].append(c)
                    return True
        return False

    def auto_move_all(self, safe_only: bool = True):
        moved = True
        while moved:
            moved = self.try_auto_move_once(safe_only=safe_only)

    # ---------- picking (drag) ----------
    def pick(self, pos):
        if self.drag_cards:
            return

        for i in range(10):
            pile = self.cascades[i]
            for j in range(len(pile)-1, -1, -1):
                c = pile[j]
                if c.rect.collidepoint(pos):
                    run = pile[j:]
                    if not self.is_valid_run(run):
                        run = [pile[-1]]
                        j = len(pile)-1

                    if len(run) > self.movable_limit():
                        run = [pile[-1]]
                        j = len(pile)-1

                    self.drag_cards = run
                    self.drag_from = ("cascade", i, j)
                    self.drag_offset = (pos[0]-c.rect.x, pos[1]-c.rect.y)
                    return

    # ---------- dropping / commit ----------
    def drop(self, pos, force_unsafe: bool = False):
        if not self.drag_cards:
            return
        cards = self.drag_cards
        first = cards[0]

        # foundation (single non-joker)
        if len(cards) == 1 and (not first.is_joker):
            for i in range(4):
                if self.foundation_rect(i).collidepoint(pos):
                    if self.can_to_foundation(first, i):
                        self._commit(("foundation", i))
                        self.auto_move_all(safe_only=True)
                        return

        # cascade
        for i in range(10):
            if self.cascade_rect(i).collidepoint(pos):
                if self.is_valid_run(cards) and len(cards) <= self.movable_limit() and self.can_to_cascade(first, i):
                    self._commit(("cascade", i))
                    self.auto_move_all(safe_only=True)
                    return

        self._cancel_drag()

    def _remove_from_source(self):
        src = self.drag_from
        if not src:
            return
        if src[0] == "cascade":
            cidx, start = src[1], src[2]
            self.cascades[cidx] = self.cascades[cidx][:start]

    def _commit(self, target):
        cards = self.drag_cards
        self._remove_from_source()

        if target[0] == "foundation":
            self.foundations[target[1]].append(cards[0])
        elif target[0] == "cascade":
            self.cascades[target[1]].extend(cards)

        self.drag_cards = []
        self.drag_from = None

    def _cancel_drag(self):
        self.drag_cards = []
        self.drag_from = None

    # ---------- double-click ----------
    def handle_click(self, pos, force_unsafe: bool = False):
        now = pygame.time.get_ticks()
        dx = pos[0] - self.last_click_pos[0]
        dy = pos[1] - self.last_click_pos[1]
        is_double = (now - self.last_click_time) <= self.double_click_ms and (dx*dx + dy*dy) <= (12*12)

        self.last_click_time = now
        self.last_click_pos = pos

        if is_double:
            loc = self.locate_top_card_at(pos)
            if not loc:
                return
            _, idx = loc
            if not self.cascades[idx]:
                return
            c = self.cascades[idx][-1]
            if c.is_joker:
                return
            for f in range(4):
                ok = self.safe_to_auto_foundation(c, f) if not force_unsafe else self.can_to_foundation(c, f)
                if ok:
                    self.cascades[idx].pop()
                    self.foundations[f].append(c)
                    self.auto_move_all(safe_only=True)
                    return
            return

        self.pick(pos)

    # ---------- win ----------
    def won(self) -> bool:
        total = sum(len(f) for f in self.foundations)
        return total == 52 and all(len(f) == 13 for f in self.foundations)

    # ---------- draw ----------
    def draw(self, surf):
        surf.fill(BG_COLOR)

        # foundations
        for i in range(4):
            r = self.foundation_rect(i)
            pygame.draw.rect(surf, (100,100,100), r, 2)
            if self.foundations[i]:
                top = self.foundations[i][-1]
                top.rect.topleft = r.topleft
                top.draw(surf)

        # cascades (10)
        for i in range(10):
            pile = self.cascades[i]
            x, y = 40 + i*115, 210
            if not pile:
                pygame.draw.rect(surf, (100,100,100), pygame.Rect(x, y, CARD_W, CARD_H), 2)
            for j, c in enumerate(pile):
                c.rect.topleft = (x, y + j*25)
                c.draw(surf)

        # drag on top
        if self.drag_cards:
            mx, my = pygame.mouse.get_pos()
            ox, oy = self.drag_offset
            for k, c in enumerate(self.drag_cards):
                c.rect.topleft = (mx-ox, my-oy + k*25)
                c.draw(surf)

        mode_txt = f"Deal: {self.deal_mode.upper()} "
        mode_txt += f"#{self.deal_number}" if self.deal_mode == "msvc" else f"(Easter {self.easter_id})"
        limit_txt = f"Move limit: {self.movable_limit()}"
        typing_txt = f"Type deal #: {self.typing}" if self.typing else "Type deal #: (none)"

        help1 = "LMB drag/drop | Double-click: auto to Foundation | Shift: force (unsafe) | Enter: deal #"
        help2 = "E: next Easter | M: MSVC mode | R: reset | Esc: clear typing | Backspace: delete digit"

        surf.blit(FONT.render(f"{mode_txt} | {limit_txt}", True, (255,255,255)), (20, HEIGHT-90))
        surf.blit(FONT.render(typing_txt, True, (255,255,255)), (20, HEIGHT-70))
        surf.blit(FONT.render(help1, True, (255,255,255)), (20, HEIGHT-45))
        surf.blit(FONT.render(help2, True, (255,255,255)), (20, HEIGHT-25))

        if self.msg_timer > 0 and self.message:
            self.msg_timer -= 1
            surf.blit(FONT.render(self.message, True, (255,255,0)), (20, 10))

        if self.won():
            win = BIGFONT.render("YOU WIN!", True, (255,255,0))
            surf.blit(win, (WIDTH//2 - win.get_width()//2, HEIGHT//2 - win.get_height()//2))

# ================== main loop ==================
game = TokkiCellGame(deal_mode="msvc", deal_number=1)
clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    shift_down = pygame.key.get_mods() & pygame.KMOD_SHIFT

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                game.handle_click(e.pos, force_unsafe=bool(shift_down))

        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1:
                game.drop(e.pos, force_unsafe=bool(shift_down))

        elif e.type == pygame.KEYDOWN:
            if pygame.K_0 <= e.key <= pygame.K_9:
                game.typing += chr(e.key)
            elif e.key == pygame.K_BACKSPACE:
                game.typing = game.typing[:-1]
            elif e.key == pygame.K_ESCAPE:
                game.typing = ""

            elif e.key == pygame.K_RETURN:
                if game.typing:
                    try:
                        n = int(game.typing)
                        game.deal_mode = "msvc"
                        game.deal_number = n
                        game.reset()
                        game.toast(f"Dealt TokkiCell MSVC deal #{n}")
                    except ValueError:
                        game.toast("Invalid number")
                    game.typing = ""
                else:
                    game.toast("No deal number typed")

            elif e.key == pygame.K_r:
                mode, dn, ei = game.deal_mode, game.deal_number, game.easter_id
                game = TokkiCellGame(deal_mode=mode, deal_number=dn, easter_id=ei)
                game.toast("Reset")

            elif e.key == pygame.K_e:
                if game.deal_mode != "easter":
                    game.deal_mode = "easter"
                game.easter_id += 1
                if game.easter_id > 1:
                    game.easter_id = 1
                game.reset()
                game.toast(f"Easter deal {game.easter_id}")

            elif e.key == pygame.K_m:
                game.deal_mode = "msvc"
                if not isinstance(game.deal_number, int):
                    game.deal_number = 1
                game.reset()
                game.toast(f"MSVC deal #{game.deal_number}")

            elif e.key == pygame.K_a:
                game.auto_move_all(safe_only=not bool(shift_down))
                game.toast("Auto-move (safe)" if not shift_down else "Auto-move (UNSAFE)")

    game.draw(screen)
    pygame.display.flip()

pygame.quit()

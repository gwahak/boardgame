import pygame
import numpy as np
players = 2
quasars = [0,6,6,4,3,2,2] #인원수별 쿼저 개수 함수
usedquasars = [0,0,0,0,0,0,0] #사용한 쿼저 개수 저장
def initpan(n):
    pans=np.zeros([n,n],dtype=int)
    pans[0,0]=7
    pans[0,-1]=7
    pans[-1,0]=7
    pans[-1,-1]=7
    return pans
def count4gon(n,pan):
    count=0
    size=pan.shape[0]
    for gg in range(1,size):
        for hh in range(gg):
            for ii in range(size-gg):
                for jj in range(size-gg):
                    if pan[ii][jj+hh]==n and pan[ii+hh][jj+gg]==n and pan[ii+gg-hh][jj]==n and pan[ii+gg][jj+gg-hh]==n:
                        count+=1
    return count

class Quodboard:
    def __init__(self, players):
        self.grid_size = 26
        self.start_x, self.start_y = 30, 50
        self.edge_size = self.grid_size / 2
        self.grid_count = 11
        self.stone_size = 10
        self.quods= 20
        self.stone_edge = 2
        self.piece = 1
        self.winner = 0
        self.game_over = False
        self.exhausted = False
        self.quasar = False
        self.quasars = [0,6,6,4,3,2,2]
        self.players = players
        self.players = max(1,min(self.players,6))
        self.player = 1
        self.grid = initpan(self.grid_count)
        self.usedquasars = [0,0,0,0,0,0,0] #사용한 쿼저 개수 저장
        self.unusedstones = [0]+[self.quods for i in range(1,self.players+1)]+[0 for i in range(self.players+1,7)]
        self.box_x, self.box_y = 2, 6
    def handle_key_event(self, e):
        origin_x = self.start_x - self.edge_size
        origin_y = self.start_y - self.edge_size
        size = self.grid_count * self.grid_size + self.edge_size * 2
        pos = e.pos
        if origin_x <= pos[0] <= origin_x + size and origin_y <= pos[1] <= origin_y + size:
            if not self.game_over:
                x = pos[0] - origin_x
                y = pos[1] - origin_y
                r = int(y // self.grid_size)
                c = int(x // self.grid_size)
                if self.set_piece(r, c):
                    count=count4gon(self.player,self.grid)
                    if count > 0:
                        self.winner = self.player
                        self.game_over = True
                    if np.count_nonzero(self.grid==0)==0:
                        self.exhausted = True
                        self.game_over = True
                    if np.sum(self.unusedstones)<=0:
                        self.exhausted = True
                        self.game_over = True
                    if self.exhausted == True:
                        temp=np.min(self.usedquasars[1:self.players+1])
                        if np.count_nonzero(temp==self.usedquasars[1:self.players+1])>1:
                            self.usedquasars[0]=temp
                        else:
                            self.usedquasars[0]=100
                        self.winner = np.argmin(self.usedquasars[0:self.players+1])
                        self.usedquasars[0]=0
                    self.player = ((self.player- self.quasar) % self.players) + 1
            self.piece=(self.player*(1-self.quasar)-1)%7+1
    def set_piece(self, r, c):
        if self.grid[r,c] == 0:
            if self.quasar == True:
                if self.usedquasars[self.player] < quasars[self.players]:
                    self.grid[r,c] = 7
                    self.usedquasars[self.player]+=1
                    return True
                else:
                    self.quasar == False
                    return False
            else:
                if self.unusedstones[self.player]:
                    self.grid[r,c] = self.player
                    self.unusedstones[self.player]-=1
                    return True
                else:
                    return False

            return True
        return False
    def draw(self, screen):
        pygame.draw.rect(screen, (185, 122, 87),
                         [self.start_x - self.edge_size, self.start_y - self.edge_size,
                          (self.grid_count - 1) * self.grid_size + self.edge_size * 2, (self.grid_count - 1) * self.grid_size + self.edge_size * 2], 0)
        pygame.draw.rect(screen, (0, 0, 0),
                         [self.start_x - self.edge_size+(self.grid_count + 1) * self.grid_size, self.start_y - self.edge_size,
                          (self.box_x - 1) * self.grid_size + self.edge_size * 2, (self.box_y - 1) * self.grid_size + self.edge_size * 2], 0)
        
        for r in range(self.grid_count):
            for c in range(self.grid_count):
                piece = self.grid[r,c]
                if (r==0 or r==self.grid_count-1) and (c==0 or c==self.grid_count-1):
                    color = (255, 255, 255)
                else:
                    if piece == 0:
                        color = (255, 255, 255)
                    elif piece == 1:
                        color = (255, 0, 0)
                    elif piece == 2:
                        color = (0, 0, 255)
                    elif piece == 3:
                        color = (255, 127, 0)
                    elif piece == 4:
                        color = (255, 255, 0)
                    elif piece == 5:
                        color = (0, 127, 0)
                    elif piece == 6:
                        color = (127, 0, 255)
                    else:
                        color = (0, 0, 0)

                    x = self.start_x + c * self.grid_size
                    y = self.start_y + r * self.grid_size
                    pygame.draw.circle(screen, color, [x, y], self.grid_size // 2)
                    
        k=0
        for i in range(1,self.players+1):
            for j in range(self.quasars[self.players]-self.usedquasars[i]):
                r= k//self.box_x
                c= k%self.box_x
                piece = i

                if piece == 0:
                    color = (255, 255, 255)
                elif piece == 1:
                    color = (255, 0, 0)
                elif piece == 2:
                    color = (0, 0, 255)
                elif piece == 3:
                    color = (255, 127, 0)
                elif piece == 4:
                    color = (255, 255, 0)
                elif piece == 5:
                    color = (0, 127, 0)
                elif piece == 6:
                    color = (127, 0, 255)
                else:
                    color = (0, 0, 0)

                x = self.start_x +(self.grid_count + c+1) * self.grid_size
                y = self.start_y + r * self.grid_size
                pygame.draw.circle(screen, color, [x, y], self.grid_size // 2)
                k+=1
class Quod():

    def __init__(self,players):
        pygame.init()

        self.screen = pygame.display.set_mode((400, 400))
        pygame.display.set_caption("Quod")
        self.font = pygame.font.Font(r"C:\Windows\Fonts\consola.ttf", 24)
        self.going = True
        self.players= players
        self.Quodboard = Quodboard(self.players)
        self.colorname= ["White","Red","Blue","Orange","Yellow","Green","Violet","Black"]
        self.stonename= ["Quod","Quasar"]
    def loop(self):
        while self.going:
            self.update()
            self.draw()

        pygame.quit()

    def update(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.going = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.Quodboard.handle_key_event(e)
                self.screen.blit(self.font.render("{} Turn".format(self.colorname[self.Quodboard.winner]), True, (0, 0, 0)), (10, 10))
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    self.Quodboard.quasar = False
                elif e.key == pygame.K_DOWN:
                    self.Quodboard.quasar = True
                self.screen.blit(self.font.render("Using {}".format(self.stonename[self.Quodboard.quasar]), True, (0, 0, 0)), (10, 350))            
    def draw(self):
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.font.render("{} Turn".format(self.colorname[self.Quodboard.player]), True, (0, 0, 0)), (10, 10))
        self.screen.blit(self.font.render("Using {}".format(self.stonename[self.Quodboard.quasar]), True, (0, 0, 0)), (10, 350))
        self.Quodboard.draw(self.screen)
        if self.Quodboard.game_over and self.Quodboard.winner !=0:
            self.screen.blit(self.font.render("{0} Win".format(self.colorname[self.Quodboard.winner]), True, (0, 0, 0)), (200, 10))
        if self.Quodboard.game_over and self.Quodboard.winner ==0:
            self.screen.blit(self.font.render("Draw", True, (0, 0, 0)), (200, 10))
        pygame.display.flip()

if __name__ == '__main__':
    game = Quod(players=2)
    game.loop()

        

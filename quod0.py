import turtle
def colorassign(n):
    if n == 0:
        colorname="white"
    elif n == 1:
        colorname="red"
    elif n == 2:
        colorname="blue"
    elif n == 3:
        colorname="orange"
    elif n == 4:
        colorname="yellow"
    elif n == 5:
        colorname="green"
    elif n == 6:
        colorname="violet"
    elif n == 7:
        colorname="black"
    return colorname
def colorsutza(n):
    if n == 0:
        colorname="white"
    elif n == 1:
        colorname="white"
    elif n == 2:
        colorname="white"
    elif n == 3:
        colorname="black"
    elif n == 4:
        colorname="black"
    elif n == 5:
        colorname="white"
    elif n == 6:
        colorname="white"
    elif n == 7:
        colorname="white"
    else:
        colorname="white"
    return colorname
def playername(n):
    if n == 0:
        colorname="하양"
    elif n == 1:
        colorname="빨강"
    elif n == 2:
        colorname="파랑"
    elif n == 3:
        colorname="주황"
    elif n == 4:
        colorname="노랑"
    elif n == 5:
        colorname="초록"
    elif n == 6:
        colorname="보라"
    elif n == 7:
        colorname="검정"
    return colorname
def colorcode(n, d=2):
    if (n-1)%d == 0:
        colorname="1"
    elif (n-2)%d == 0:
        colorname="2"
    elif (n-3)%d == 0:
        colorname="3"
    elif (n-4)%d == 0:
        colorname="4"
    elif (n-5)%d == 0:
        colorname="5"
    elif (n-6)%d == 0:
        colorname="6"
    else:
        colorname="7"
    return colorname
def drawing(a,b,c,d):
    tcoin.color(colorassign(d))
    tcoin.up()
    tcoin.goto(a*32-192, b*32-192)
    tcoin.setheading(0)
    tcoin.forward(12)
    tcoin.down()
    tcoin.begin_fill()
    tcoin.setheading(90)
    tcoin.circle(12)
    tcoin.end_fill()
    tcoin.up()
    tcoin.setheading(180)
    tcoin.forward(12)
    tcoin.setheading(270)
    tcoin.forward(5)
    tcoin.color(colorsutza(d))
    tcoin.write(c, False, "center", ("", 13))
pan = [[7,0,0,0,0,0,0,0,0,0,7],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0],[7,0,0,0,0,0,0,0,0,0,7]]
def count4gon(n):
    count=0
    for gg in range(1,11):
        for hh in range(gg):
            for ii in range(11-gg):
                for jj in range(11-gg):
                    if pan[ii][jj+hh]==n and pan[ii+hh][jj+gg]==n and pan[ii+gg-hh][jj]==n and pan[ii+gg][jj+gg-hh]==n:
                        count+=1
    return count
turtle.tracer(True)
t1=turtle.Turtle()
tcoin=turtle.Turtle()
tjwapyo=turtle.Turtle()
tcoin.speed(0)
t1.speed(0)
tjwapyo.speed(0)
screen=t1.getscreen()
w=200
screen.setworldcoordinates(-w,-w,w,w)
#가로세로 그리기
tjwapyo.up()
for i in range(11):
    tjwapyo.goto(i*32-160,178)
    tjwapyo.write(chr(65+i), False, "center", ("", 20))
tjwapyo.up()
for i in range(11):
    tjwapyo.goto(-188,i*32-170)
    tjwapyo.write(i+1, False, "center", ("", 20))
tjwapyo.hideturtle()
t1.up()
t1.home()
t1.color("black")
t1.goto(-144,-144)
t1.down()
t1.sety(176)
t1.setx(144)
t1.sety(-176)
t1.setx(-144)
t1.sety(-144)
t1.setx(-176)
t1.sety(144)
t1.setx(176)
t1.sety(-144)
t1.setx(-144)
t1.sety(-176)
for i in range(4):
    t1.setheading(0)
    t1.forward(32)
    t1.sety(176)
    t1.forward(32)
    t1.sety(-176)
t1.up()
t1.goto(176,-144)
t1.down()
for i in range(4):
    t1.setheading(90)
    t1.forward(32)
    t1.setx(-176)
    t1.forward(32)
    t1.setx(176)
t1.up()
t1.hideturtle()
t1.home()
tcoin.hideturtle()
#바둑판 그리기 끝.
players = 2
quasars = [0,6,6,4,3,2,2] #인원수별 쿼저 개수 함수
usedquasars = [0,0,0,0,0,0,0] #사용한 쿼저 개수 저장
while (1):
    print("몇명이서 게임을 두실 건가요?")
    imsi = int(input())
    if imsi not in [2,3,4,5,6]:
        print("다시 입력하세요")
        continue
    else:
        players = imsi
        print(players, "인용 쿼드(Quod) 게임을 시작합니다")
        break
i = 0
j = 0
while i in range(0,players*20) and j in range (0,117):
    i += 1
    print(playername((i-1)%players+1),"이 둘 차례입니다. 돌을 놓을 칸의 번호를 입력하세요. 쿼저를 놓을 경우 소문자로 입력하셔야 합니다.")
    kan = input()
    tyi = int(kan[1:])
    txj = kan[0]
    txi = ord(kan[0])%32
    if tyi not in [1,2,3,4,5,6,7,8,9,10,11]:
        print("판 범위 밖에 돌을 놓을 수 없습니다")
        i -=1
        continue
    elif txj not in ['A','B','C','D','E','F','G','H','I','J','K','a','b','c','d','e','f','g','h','i','j','k']:
        print("판 범위 밖에 돌을 놓을 수 없습니다")
        i -=1
        continue
    elif pan[txi-1][tyi-1] != 0:
        print("돌이 놓여있는 칸에 새 돌을 놓을 수 없습니다.")
        i -=1
        continue
    elif txj in ['a','b','c','d','e','f','g','h','i','j','k'] and usedquasars[(i-1)%players+1] >= quasars[players]:
        print("이미 쿼저를 모두 사용하여 새 쿼저를 놓을 수 없습니다.")
        i -=1
        continue
    elif txj in ['a','b','c','d','e','f','g','h','i','j','k']:
        tx = txi
        ty = tyi
        pan[tx-1][ty-1] = 7
        drawing(tx,ty,i,7)
        usedquasars[(i-1)%players+1] +=1
        j +=1
        i -=1
        continue
    else:
        tx = txi
        ty = tyi
        pan[tx-1][ty-1] = (i-1)%players +1
        drawing(tx,ty,i,(i-1)%players+1)
        j +=1
    if count4gon((i-1)%players+1) >=1:
        print(playername((i-1)%players+1),"이 정사각형을 만들어 이겼습니다")
        break

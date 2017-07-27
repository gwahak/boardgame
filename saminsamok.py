import turtle
pan = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
def count4(n):
    count=0
    for ii in range(19):
        for jj in range(16):
            if pan[ii][jj]==n and pan[ii][jj+1]==n and pan[ii][jj+2]==n and pan[ii][jj+3]==n:
                count+=1
            if pan[jj][ii]==n and pan[jj+1][ii]==n and pan[jj+2][ii]==n and pan[jj+3][ii]==n:
                count+=1
    for ii in range(16):
        for jj in range(16):
            if pan[ii][jj]==n and pan[ii+1][jj+1]==n and pan[ii+2][jj+2]==n and pan[ii+3][jj+3]==n:
                count+=1
            if pan[ii+3][jj]==n and pan[ii+2][jj+1]==n and pan[ii+1][jj+2]==n and pan[ii][jj+3]==n:
                count+=1
    return count
def colorassign(n):
    if n%3 == 1:
        colorname="black"
    elif n%3 == 2:
        colorname="white"
    elif n%3 == 0:
        colorname="red"
    else:
        colorname="orange"
    return colorname
def colorsutza(n):
    if n%3 == 1:
        colorname="white"
    elif n%3 == 2:
        colorname="black"
    elif n%3 == 0:
        colorname="white"
    else:
        colorname="black"
    return colorname
def playername(n):
    if n%3 == 1:
        colorname="검정"
    elif n%3 == 2:
        colorname="하양"
    elif n%3 == 0:
        colorname="빨강"
    else:
        colorname="주황"
    return colorname
turtle.tracer(True)
t1=turtle.Turtle()
tcoin=turtle.Turtle()
t1.speed(0)
screen=t1.getscreen()
w=200
screen.setworldcoordinates(-w,-w,w,w)
t1.up()
t1.goto(190,190)
t1.begin_fill()
t1.color("yellow")
t1.goto(190,-190)
t1.goto(-190,-190)
t1.goto(-190,190)
t1.goto(190,190)
t1.end_fill()
t1.up()
t1.home()
t1.color("black")
t1.down()
t1.goto(180,0)
t1.goto(180,180)
t1.goto(-180,180)
for i in range(9):
    t1.setheading(-90)
    t1.forward(20)
    t1.setx(180)
    t1.setheading(-90)
    t1.forward(20)
    t1.setx(-180)
for i in range(9):
    t1.setheading(90)
    t1.sety(180)
    t1.setheading(0)
    t1.forward(20)
    t1.sety(-180)
    t1.setheading(0)
    t1.forward(20)
t1.setheading(90)
t1.sety(0)
t1.setx(0)
i=0
winner=0
#바둑판 그리기 끝.
while i in range(0,361):
    i += 1
    print(playername(i),"이 둘 차례입니다. 바둑알을 놓을 칸의 번호를 입력하세요")
    kan = input()
    ty = int(kan[1:])
    tx = ord(kan[0])%32
    if pan[tx-1][ty-1] != 0:
        print("돌이 놓여있는 칸에 새 돌을 놓을 수 없습니다.")
        i -=1
        continue
    else:
        tcoin.color(colorassign(i))
        tcoin.up()
        tcoin.goto(tx*20-200, ty*20-200)
        tcoin.setheading(0)
        tcoin.forward(8)
        tcoin.down()
        tcoin.begin_fill()
        tcoin.setheading(90)
        tcoin.circle(8)
        tcoin.end_fill()
        tcoin.up()
        tcoin.setheading(180)
        tcoin.forward(8)
        tcoin.setheading(270)
        tcoin.forward(5)
        tcoin.color(colorsutza(i))
        tcoin.write(i, False, "center", ("", 13))
        pan[tx-1][ty-1] = (i-1)%3+1
    if count4((i-1)%3+1) >=1:
        winner = (i-1)%3+1
        print(playername(i),"이 4목을 만들어 이겼습니다")
        break
if winner==0:
    print("어느 선수도 4목을 만들지 못해 무승부 입니다")

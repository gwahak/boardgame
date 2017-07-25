import turtle
def colorassign(n):
    if n%4 == 1:
        colorname="red"
    elif n%4 == 2:
        colorname="blue"
    elif n%4 == 3:
        colorname="orange"
    elif n%4 == 0:
        colorname="yellow"
    else:
        colorname="black"
    return colorname
def colorsutza(n):
    if n%4 == 1:
        colorname="white"
    elif n%4 == 2:
        colorname="white"
    elif n%4 == 3:
        colorname="black"
    elif n%4 == 0:
        colorname="black"
    else:
        colorname="black"
    return colorname
def playername(n):
    if n%4 == 1:
        colorname="빨강"
    elif n%4 == 2:
        colorname="파랑"
    elif n%4 == 3:
        colorname="주황"
    elif n%4 == 0:
        colorname="노랑"
    else:
        colorname="검정"
    return colorname
pan = [[5,0,0,0,0,0,0,5],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[5,0,0,0,0,0,0,5]]
turtle.tracer(True)
t1=turtle.Turtle()
tcoin=turtle.Turtle()
tgaro=turtle.Turtle()
tsero=turtle.Turtle()
tcoin.speed(0)
t1.speed(0)
tgaro.speed(0)
tsero.speed(0)
screen=t1.getscreen()
w=200
screen.setworldcoordinates(-w,-w,w,w)
#슬라이드 그리기
tgaro.up()
tgaro.goto(160,-177)
tgaro.begin_fill()
tgaro.goto(160,-183)
tgaro.goto(-160,-183)
tgaro.goto(-160,-177)
tgaro.goto(160,-177)
tgaro.end_fill()
tgaro.setheading(90)
tgaro.color("green")
tsero.up()
tsero.goto(-177,160)
tsero.begin_fill()
tsero.goto(-183,160)
tsero.goto(-183,-160)
tsero.goto(-177,-160)
tsero.goto(-177,160)
tsero.end_fill()
tsero.color("green")
t1.up()
t1.home()
t1.color("black")
t1.down()
t1.goto(160,0)
t1.goto(160,160)
t1.goto(-160,160)
for i in range(4):
    t1.setheading(-90)
    t1.forward(40)
    t1.setx(160)
    t1.setheading(-90)
    t1.forward(40)
    t1.setx(-160)
for i in range(4):
    t1.setheading(90)
    t1.sety(160)
    t1.setheading(0)
    t1.forward(40)
    t1.sety(-160)
    t1.setheading(0)
    t1.forward(40)
t1.setheading(90)
t1.sety(0)
t1.setx(0)
#빈칸 지우기
t1.up()
t1.begin_fill()
t1.goto(160,160)
t1.goto(160,120)
t1.goto(120,120)
t1.goto(120,160)
t1.goto(160,160)
t1.end_fill()
t1.begin_fill()
t1.goto(-160,160)
t1.goto(-160,120)
t1.goto(-120,120)
t1.goto(-120,160)
t1.goto(-160,160)
t1.end_fill()
t1.begin_fill()
t1.goto(160,-160)
t1.goto(160,-120)
t1.goto(120,-120)
t1.goto(120,-160)
t1.goto(160,-160)
t1.end_fill()
t1.begin_fill()
t1.goto(-160,-160)
t1.goto(-160,-120)
t1.goto(-120,-120)
t1.goto(-120,-160)
t1.goto(-160,-160)
t1.end_fill()
#바둑판 그리기 끝.
#슬라이드 초기화
tx = 4
ty = 5
tgaro.setx(40*tx-180)
tsero.sety(40*ty-180)
#대국
i = 0
while i in range(0,64):
    i += 1
    print(playername(i),"이 둘 차례입니다. 돌을 놓을 칸의 번호를 입력하세요")
    kan = input()
    tyi = int(kan[1])
    txi = (ord(kan[0])-1)%8+1
    bn = (i-1)%4+1 #몇 번째 플레이어인지 표시
    if (txi-tx)*(tyi-ty)!=0:
        print("동시에 두 개의 슬라이드를 움직일 수 없습니다")
        i -= 1
        continue #놓을 곳이 없을 경우 슬라이드만 움직이는 코드
    elif pan[tx-1][0]*pan[tx-1][1]*pan[tx-1][2]*pan[tx-1][3]*pan[tx-1][4]*pan[tx-1][5]*pan[tx-1][6]*pan[tx-1][7]*pan[0][ty-1]*pan[1][ty-1]*pan[2][ty-1]*pan[3][ty-1]*pan[4][ty-1]*pan[5][ty-1]*pan[6][ty-1]*pan[7][ty-1] != 0:
        tx = txi
        ty = tyi
        tgaro.setx(40*tx-180)
        tsero.sety(40*ty-180)
        continue
    elif pan[txi-1][tyi-1] != 0:
        print("돌이 놓여있는 칸에 새 돌을 놓을 수 없습니다.")
        i -=1
        continue
    else:
        tx = txi
        ty = tyi
        tgaro.setx(40*tx-180)
        tsero.sety(40*ty-180)
        pan[tx-1][ty-1] = (i-1)%4 +1
        tcoin.color(colorassign(i))
        tcoin.up()
        tcoin.goto(tx*40-180, ty*40-180)
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
        tcoin.color(colorsutza(i))
        tcoin.write(i, False, "center", ("", 13))

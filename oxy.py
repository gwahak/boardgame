import turtle
import turtle
def colorassign(n, d=3):
    if (n-1)%d == 0:
        colorname="red"
    elif (n-2)%d == 0:
        colorname="blue"
    elif (n-3)%d == 0:
        colorname="orange"
    elif (n-4)%d == 0:
        colorname="yellow"
    else:
        colorname="black"
    return colorname
def colorsutza(n, d=3):
    if (n-1)%d == 0:
        colorname="white"
    elif (n-2)%d == 0:
        colorname="white"
    elif (n-3)%d == 0:
        colorname="black"
    elif (n-4)%d == 0:
        colorname="black"
    else:
        colorname="black"
    return colorname
def playername(n, d=3):
    if (n-1)%d == 0:
        colorname="빨강"
    elif (n-2)%d == 0:
        colorname="파랑"
    elif (n-3)%d == 0:
        colorname="주황"
    elif (n-4)%d == 0:
        colorname="노랑"
    else:
        colorname="검정"
    return colorname
def drawing(a,b,c,d=3):
    tcoin.color(colorassign(c,d))
    tcoin.up()
    tcoin.goto(a*60-180, b*60-180)
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
    tcoin.color(colorsutza(c,d))
    tcoin.write(c, False, "center", ("", 13))
pan = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]
def count4gon(n):
    count=0
    for gg in range(1,5):
        for hh in range(gg):
            for ii in range(5-gg):
                for jj in range(5-gg):
                    if pan[ii][jj+hh]==n and pan[ii+hh][jj+gg]==n and pan[ii+gg-hh][jj]==n and pan[ii+gg][jj+gg-hh]==n:
                        count+=1
    return count
def count3(n):
    count=0
    for ii in range(5):
        for jj in range(3):
            if pan[ii][jj]==n and pan[ii][jj+1]==n and pan[ii][jj+2]==n:
                count+=1
            if pan[jj][ii]==n and pan[jj+1][ii]==n and pan[jj+2][ii]==n:
                count+=1
#    for ii in range(3):
#        for jj in range(3):
#            if pan[ii][jj]==n and pan[ii+1][jj+1]==n and pan[ii+2][jj+2]==n:
#                count+=1
#            if pan[ii+2][jj]==n and pan[ii+1][jj+1]==n and pan[ii][jj+2]==n:
#                count+=1
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
for i in range(5):
    tjwapyo.goto(i*60-120,160)
    tjwapyo.write(chr(65+i), False, "center", ("", 30))
tjwapyo.up()
for i in range(5):
    tjwapyo.goto(-175,i*60-135)
    tjwapyo.write(i+1, False, "center", ("", 30))
tjwapyo.hideturtle()
t1.up()
t1.home()
t1.color("black")
t1.goto(-30,-90)
t1.down()
t1.goto(-30,150)
t1.goto(-150,150)
t1.goto(-150,30)
t1.goto(150,30)
t1.goto(150,150)
t1.goto(30,150)
t1.goto(30,-150)
t1.goto(150,-150)
t1.goto(150,-30)
t1.goto(-150,-30)
t1.goto(-150,-150)
t1.goto(-30,-150)
t1.goto(-30,-90)
t1.goto(-150,-90)
t1.goto(-150,90)
t1.goto(150,90)
t1.goto(150,-90)
t1.goto(-90,-90)
t1.goto(-90,150)
t1.goto(90,150)
t1.goto(90,-150)
t1.goto(-90,-150)
t1.goto(-90,-90)
t1.up()
t1.home()
#바둑판 그리기 끝.
players = 3
i = 0
while i in range(0,24):
    i += 1
    print(playername(i,players),"이 둘 차례입니다. 돌을 놓을 칸의 번호를 입력하세요")
    kan = input()
    tyi = (int(kan[1])-1)%5+1
    txi = ((ord(kan[0])-1)%8)%5+1
    if pan[txi-1][tyi-1] != 0:
        print("돌이 놓여있는 칸에 새 돌을 놓을 수 없습니다.")
        i -=1
        continue
    else:
        tx = txi
        ty = tyi
        pan[tx-1][ty-1] = (i-1)%players +1
        drawing(tx,ty,i,players)
    if count4gon((i-1)%players+1) >=1:
        print(playername(i,players),"이 정사각형을 만들어 이겼습니다")
        break
    elif players ==4 and count3((i-1)%players+1) >=1:
        print(playername(i,players),"이 3목을 만들어 이겼습니다")
        break
if i == 24:
    for j in range(25):
        if pan[j//5][j%5]==0:
            break
    check = [0,0,0]
    for k in range(3):
        pan[j//5][j%5]=k+1
        check[k]=count4gon(k+1)+count3(k+1)
    pan[j//5][j%5]=0
    winners = check.count(max(check))
    if winners == 1:
        pan[j//5][j%5]=k+1
        print(playername(check.index(max(check))+1),"이 마지막에 3목을 만들어 이겼습니다.")
    else:
        print("무승부입니다")
                

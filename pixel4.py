import turtle
def colorassign(n, d=4):
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
def colorsutza(n, d=4):
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
def playername(n, d=4):
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
def drawing(a,b,c,d=4):
    tcoin.color(colorassign(c,d))
    tcoin.up()
    tcoin.goto(a*40-180, b*40-180)
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
pan = [[5,0,0,0,0,0,0,5],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[5,0,0,0,0,0,0,5]]
def count4(n):
    count=0
    for ii in range(8):
        for jj in range(5):
            if pan[ii][jj]==n and pan[ii][jj+1]==n and pan[ii][jj+2]==n and pan[ii][jj+3]==n:
                count+=1
            if pan[jj][ii]==n and pan[jj+1][ii]==n and pan[jj+2][ii]==n and pan[jj+3][ii]==n:
                count+=1
    for ii in range(5):
        for jj in range(5):
            if pan[ii][jj]==n and pan[ii+1][jj+1]==n and pan[ii+2][jj+2]==n and pan[ii+3][jj+3]==n:
                count+=1
            if pan[ii+3][jj]==n and pan[ii+2][jj+1]==n and pan[ii+1][jj+2]==n and pan[ii][jj+3]==n:
                count+=1
    return count
def count3(n):
    count=0
    for ii in range(8):
        for jj in range(6):
            if pan[ii][jj]==n and pan[ii][jj+1]==n and pan[ii][jj+2]==n:
                count+=1
            if pan[jj][ii]==n and pan[jj+1][ii]==n and pan[jj+2][ii]==n:
                count+=1
    for ii in range(6):
        for jj in range(6):
            if pan[ii][jj]==n and pan[ii+1][jj+1]==n and pan[ii+2][jj+2]==n:
                count+=1
            if pan[ii+2][jj]==n and pan[ii+1][jj+1]==n and pan[ii][jj+2]==n:
                count+=1
    return count
def count2(n):
    count=0
    for ii in range(8):
        for jj in range(7):
            if pan[ii][jj]==n and pan[ii][jj+1]==n:
                count+=1
            if pan[jj][ii]==n and pan[jj+1][ii]==n:
                count+=1
    for ii in range(7):
        for jj in range(7):
            if pan[ii][jj]==n and pan[ii+1][jj+1]==n:
                count+=1
            if pan[ii+1][jj]==n and pan[ii][jj+1]==n:
                count+=1
    return count
def poseok(d =4):

    i = 1
    while i in range(1,d):
        i += 1
        print(playername(i),"이 둘 차례입니다. 돌을 놓을 칸의 번호를 입력하세요")
        kan = input()
        tyi = int(kan[1])
        txi = (ord(kan[0])-1)%8+1
        if kan not in ['D4','D5','E4','E5']:
            print("각 대국자의 첫 착수는 정 가운데 4칸 안에만 가능합니다.")
            i -= 1
            continue
        elif pan[txi-1][tyi-1] != 0:
            print("돌이 놓여있는 칸에 새 돌을 놓을 수 없습니다.")
            i -=1
            continue
        else:
            pan[txi-1][tyi-1] = i
            drawing(txi,tyi,i)
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
for i in range(8):
    tgaro.goto(i*40-140,170)
    tgaro.write(chr(65+i), False, "center", ("", 20))
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
for i in range(8):
    tsero.goto(180,i*40-150)
    tsero.write(i+1, False, "center", ("", 20))
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
while (1):
    print("몇명이서 게임을 두실 건가요?")
    imsi = int(input())
    if imsi not in [2,3,4]:
        print("다시 입력하세요")
        continue
    else:
        players = imsi
        print(players, "인용 픽셀(Pixel) 게임을 시작합니다")
        break
tx = 4
ty = 5
tgaro.setx(40*tx-180)
tsero.sety(40*ty-180)
pan[3][4] = 1
drawing(4,5,1)
poseok(players)
#대국
i = players
while i in range(players,64):
    i += 1
    print(playername(i,players),"이 둘 차례입니다. 돌을 놓을 칸의 번호를 입력하세요")
    kan = input()
    tyi = int(kan[1])
    txi = (ord(kan[0])-1)%8+1
#    bn = (i-1)%4players+1 몇 번째 플레이어인지 표시, 활용 예정
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
        pan[tx-1][ty-1] = (i-1)%players +1
        drawing(tx,ty,i,players)
    if count4((i-1)%players+1) >=1:
        print(playername(i,players),"이 4목을 만들어 이겼습니다")
        break
    elif players ==4 and count3((i-1)%players+1) >=1:
        print(playername(i,players),"이 3목을 만들어 이겼습니다")
        break
if i>=64:
    if players == 4:
        print("어느 선수도 3목을 만들지 못했습니다.")
        check = [count2(1), count2(2), count2(3), count2(4)]
        winners = check.count(max(check))
        print(playername(1),"2목을", check[0], "개 만들었습니다.")
        print(playername(2),"2목을", check[1], "개 만들었습니다.")
        print(playername(3),"2목을", check[2], "개 만들었습니다.")
        print(playername(4),"2목을", check[3], "개 만들었습니다.")
        if winners == 1:
            print(playername(check.count(max(check)))+1,"이 2목을 제일 많이 만들어 이겼습니다.")
        elif winners == 4:
            print("모든 선수가 같은 갯수의 2목을 만들어 무승부 입니다")
        else:
            winnernames = [playername(k+1) for k, x in enumerate(check) if x == max(check)]
            print(winnernames, "선수들이 공동 승리하였습니다.")
    elif players == 3:
        print("어느 선수도 4목을 만들지 못했습니다.")
        check = [count3(1), count3(2), count3(3)]
        winners = check.count(max(check))
        print(playername(1),"3목을", check[0], "개 만들었습니다.")
        print(playername(2),"3목을", check[1], "개 만들었습니다.")
        print(playername(3),"3목을", check[2], "개 만들었습니다.")
        if winners == 1:
            print(playername(check.count(max(check)))+1,"이 3목을 제일 많이 만들어 이겼습니다.")
        elif winners == 3:
            print("모든 선수가 같은 갯수의 3목을 만들어 무승부 입니다")
        else:
            winnernames = [playername(k+1) for k, x in enumerate(check) if x == max(check)]
            print(winnernames, "선수들이 공동 승리하였습니다.")
    else:
        print("어느 선수도 4목을 만들지 못했습니다.")
        check = [count3(1), count3(2)]
        winners = check.count(max(check))
        print(playername(1),"3목을", check[0], "개 만들었습니다.")
        print(playername(2),"3목을", check[1], "개 만들었습니다.")
        if winners == 1:
            print(playername(check.count(max(check)))+1,"이 3목을 제일 많이 만들어 이겼습니다.")
        else:
            print("모든 선수가 같은 갯수의 3목을 만들어 무승부 입니다")

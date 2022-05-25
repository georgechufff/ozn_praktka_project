import socket
import time
import pygame
import random

main_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind(('localhost',10000))
main_socket.setblocking(0)
main_socket.listen(30)

#Параметры комнаты
WIDTH_ROOM, HEIGHT_ROOM = 5000,5000
WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW = 500,500

#Начальный размер игроков
START_PLAYER_R = 50

MICROBES_SIZE = 30
#Чем больше плотность тем меньше микробов
MICROBS_ANTI_DENSITY = 80000
MICROBS_QUANTITY = WIDTH_ROOM * HEIGHT_ROOM // MICROBS_ANTI_DENSITY

#Частота игры макс.
FPS = 144

#Словарь всех цветов игроков доступных в игре
colors = {'0':(255,255,0), '1':(255,0,0), '2':(0,255,255), '3':(0,0,255), '4':(255,0,255)} 

def find(s):
    otkr = None
    for i in range(len(s)):
        if s[i] == '<':
            otkr = i
        if s[i] == '>' and otkr != None:
            zakr = i
            res = s[otkr+1:zakr]
            res = list(map(int,res.split(',')))
            return res
    return ""

#Создание класса объектов корма
class Microbe():
    def __init__(self,x,y,r,color):
        self.x = x
        self.y = y
        self.r = r
        self.c = color
        
#Создание класса объектов игрока
class Player():
    def __init__(self, conn, addr, x, y, r, color):
        self.conn = conn
        self.addr = addr
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.errors = 0
        self.name = "UserName"

        self.L = 1
        self.width_window = 1000
        self.height_window = 800
        self.w_vision = 1000
        self.h_vision = 800
        self.ready = False

        self.speed_x = 0
        self.speed_y = 0
        self.abs_speed = 30/(self.r**0.5)

    def set_options(self, data):
        data = data[1:-1].split(' ')
        self.name = data[0]
        self.width_window = int(data[1])
        self.height_window = int(data[2])
        self.w_vision = int(data[1])
        self.h_vision = int(data[2])
        
    def change_speed(self, v):
        if (v[0] == 0) and (v[1] == 0):
            self.speed_x = 0;
            self.speed_y = 0;
        else:
            lenv = (v[0]**2 + v[1]**2)**0.5
            v = (v[0]/lenv,v[1]/lenv)
            v = (v[0]*self.abs_speed,v[1]*self.abs_speed)
            self.speed_x = v[0]
            self.speed_y = v[1]
            
    def update(self):
        #По-горизонтали
        if self.x <= 0:
            if self.speed_x >= 0:
                self.x += self.speed_x
        elif self.x >= WIDTH_ROOM:
            if self.speed_x <= 0:
                self.x += self.speed_x
        else:
            self.x += self.speed_x
        
        #По-вертикали
        if self.y <= 0:
            if self.speed_y >= 0:
                self.y += self.speed_y
        elif self.y >= HEIGHT_ROOM:
            if self.speed_y <= 0:
                self.y += self.speed_y
        else:
            self.y += self.speed_y

        self.abs_speed = 30/(self.r**0.5)

        #Постепенное уменьшение радиуса игрока со временем до предела(100)
        if self.r >= 100:
            self.r -= self.r/18000

        if self.r >= self.w_vision/4 or self.r >= self.h_vision/4:
            if self.w_vision <= WIDTH_ROOM or self.h_vision <= HEIGHT_ROOM:
                self.L*=2
                self.w_vision = self.width_window*self.L
                self.h_vision = self.height_window*self.L
                
        if self.r < self.w_vision/8 and self.r < self.h_vision/8:
            if self.L > 1:
                self.L = self.L//2
                self.w_vision = self.width_window*self.L
                self.h_vision = self.height_window*self.L

#Создание окна сервера
pygame.init()
screen = pygame.display.set_mode((WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW))
clock = pygame.time.Clock();
running = True

#Массив с сокетами игроков
players = []

#Массив с именами и размерами игроков
top = ""

#Создание стартового набора микробов
microbes = [Microbe(random.randint(0,WIDTH_ROOM),
                    random.randint(0,HEIGHT_ROOM),
                    MICROBES_SIZE,
                    str(random.randint(0,4)))
            for i in range (MICROBS_QUANTITY)]

#Цикл игры
while running:

    clock.tick(FPS)
    
    #Прием подключений от игроков, если они есть
    try:
        new_socket, addr = main_socket.accept()
        print("Игрок ", addr, " подключился")
        new_socket.setblocking(0)
        new_player = Player(new_socket,addr,random.randint(0,WIDTH_ROOM),random.randint(0,HEIGHT_ROOM),START_PLAYER_R,str(random.randint(0,4)))
        players.append(new_player)
    except:
        pass
    
    #Считываем команды игроков
    for player in players:
        try:
            #Чтение данных из сокетов клиентов в объеме 1024 байт
            data = player.conn.recv(1024)
            #Перевод полученной инфы из байт в необходимый тип данных
            data = data.decode()
            if data[0] == '!':
                player.ready = True
            else:
                if data[0] == '.' and data[-1] == '.':
                    player.set_options(data)
                    player.conn.send((str(START_PLAYER_R)+' '+player.color).encode())
                else: 
                    data = find(data)
                    #Обрабатываем полученные от игрока данные
                    player.change_speed(data)
        except:
            pass
        player.update()

    #Определим, что видит каждый игрок
    #Каждый подмассив содержит объекты видимых игроков для данного
    visible_balls = [[] for i in range(len(players))]
    
    for i in range(len(players)):
        #Каких микробов видит i
        for k in range(len(microbes)):
            dist_x = microbes[k].x - players[i].x
            dist_y = microbes[k].y - players[i].y

            #микроб в поле видимости i
            if ((abs(dist_x) <= (players[i].w_vision)//2 + microbes[k].r)
                and (abs(dist_y) <= (players[i].h_vision)//2 + microbes[k].r)):

                #Подготовим данные к добавлению в список видимых микробов                
                x_ = str(round(dist_x/players[i].L))
                y_ = str(round(dist_y/players[i].L))
                r_ = str(round(microbes[k].r/players[i].L))
                c_ = str(microbes[k].c)
                
                visible_balls[i].append(x_+' '+y_+' '+r_+' '+c_)
                
                #i ест микроба
                if ((dist_x**2 + dist_y**2)**0.5 <= players[i].r):
                    #Меняем положение микроба и его цвет
                    microbes[k].x = random.randint(0,WIDTH_ROOM)
                    microbes[k].y = random.randint(0,HEIGHT_ROOM)
                    microbes[k].c = str(random.randint(0,4))
                    players[i].r = (players[i].r**2 + microbes[k].r**2)**0.5
                    
        for j in range(i+1, len(players)):
            dist_x = players[j].x - players[i].x
            dist_y = players[j].y - players[i].y
            
            #j в поле видимости i
            if (abs(dist_x) <= (players[i].w_vision)//2 + players[j].r
                and abs(dist_y) <= (players[i].h_vision)//2 + players[j].r):
                
                #Может ли i съесть j
                if ((dist_x**2 + dist_y**2)**0.5 <= players[i].r) and players[i].r > 1.1 * players[j].r:
                    #Удаляем игрока с поля добавляя радиус поглотившего его игрока
                    players[i].r = (players[i].r**2 + players[j].r**2)**0.5
                    players[j].r, players[j].speed_x, players[j].speed_y = 0, 0, 0

                #Подготовим данные к добавлению в список видимых шаров                
                x_ = str(round(dist_x/players[i].L))
                y_ = str(round(dist_y/players[i].L))
                r_ = str(round(players[j].r/players[i].L))
                c_ = str(players[j].color)
                n_ = players[j].name

                if players[j].r >= 30*players[i].L:
                    visible_balls[i].append(x_+' '+y_+' '+r_+' '+c_+' '+n_)
                else:
                    visible_balls[i].append(x_+' '+y_+' '+r_+' '+c_)

            #i в поле видимости j
            if (abs(dist_x) <= (players[j].w_vision)//2 + players[i].r
                and abs(dist_y) <= (players[j].h_vision)//2 + players[i].r):

                #Может ли j съесть i
                if ((dist_x**2 + dist_y**2)**0.5 <= players[j].r) and players[j].r > 1.1 * players[i].r:
                    #Удаляем игрока с поля добавляя радиус поглотившего его игрока
                    players[j].r = (players[j].r**2 + players[i].r**2)**0.5
                    players[i].r, players[i].speed_x, players[i].speed_y = 0, 0, 0

                #Подготовим данные к добавлению в список видимых шаров
                x_ = str(round(-dist_x/players[j].L))
                y_ = str(round(-dist_y/players[j].L))
                r_ = str(round(players[i].r/players[j].L))
                c_ = str(players[i].color)
                n_ = players[i].name
                
                if players[i].r >= 30*players[j].L:
                    visible_balls[j].append(x_+' '+y_+' '+r_+' '+c_+' '+n_)
                else:
                    visible_balls[j].append(x_+' '+y_+' '+r_+' '+c_)
                
    #Формируем ответ каждому игроку
    responses = ['' for i in range(len(players))]
    for i in range(len(players)):
        r_ = str(round(players[i].r/players[i].L))
        x_ = str(round(players[i].x/players[i].L))
        y_ = str(round(players[i].y/players[i].L))
        L_ = str(players[i].L)
        top = ""
        for j in range(len(players)):
            top += (players[j].name + ' ' + str(round(players[j].r))) + ' '*(j!=len(players)-1)
        #print(top)
        responses[i] = '<' + (','.join([r_+' '+x_+' '+y_+' '+L_] + visible_balls[i] + [str(len(players))] + [top])) + '>'
        #print(responses[i])
    #Отправляем обновленное состояние игрового поля 100 раз в секунду
    for i in range(len(players)):
        if players[i].ready:
            try:
                players[i].conn.send(responses[i].encode())
                players[i].errors = 0
            except:
                players[i].errors += 1

    #Чистим список от отвалившихся игроков
    for player in players:
        if player.errors >= 500 or player.r == 0:
            player.conn.close()
            players.remove(player)
            
    #Нарисуем состояние комнаты на сервере
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
           running = False

    screen.fill('grey25')
    for player in players:
        x = round(player.x*WIDTH_SERVER_WINDOW/WIDTH_ROOM)
        y = round(player.y*HEIGHT_SERVER_WINDOW/HEIGHT_ROOM)
        r = round(player.r*WIDTH_SERVER_WINDOW/WIDTH_ROOM)
        c = colors[player.color]
        
        pygame.draw.circle(screen,c,(x,y),r)


    pygame.display.update();

pygame.quit()

main_socket.close()

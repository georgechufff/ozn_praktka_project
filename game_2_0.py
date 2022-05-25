import socket
import pygame

colors = {'0':(255,255,0), '1':(255,0,0), '2':(0,255,255), '3':(0,0,255), '4':(255,0,255)} 

#Массив с игроками карты и их очками в каждом подмассиве
top = []

#Дефолтное имя игрока
UserName = "User"

print("Введите ваше имя: ")
#Ввод имени игрока с клавиатуры в консоли
UserName = input()

#Параметры окна игры
WIDTH_WINDOW = 1000
HEIGHT_WINDOW = 800

#Ввод параметров окна с клавиатуры в консоли
print("Введите желаемую ширину окна: ")
WIDTH_WINDOW = int(input())
print("Введите желаемую длину окна: ")
HEIGHT_WINDOW = int(input())

# Начальное направление движения
# old_v - прежний вектор движения, v - новый
old_v = (0,0)
v = (0,0)

# функция преобразования получаемой с сервера информации
# из формата - "<'строковые данные','строковые данные'>"
# в формат массива из этих данных - [данные,данные]
def find(s):
    otkr = None
    for i in range(len(s)):
        # Найдена окрывающая скобка - фиксируем ее индекс
        if s[i] == '<':
            otkr = i
        # Найдена закрывающая скобка - фиксируем ее индекс
        if s[i] == '>' and otkr != None:
            zakr = i
            # Формируем массив полученной инфы с сервера
            res = s[otkr+1:zakr]
            # Возвращаем данные как результат метода
            return res
    return ''

# Функция отрисовки имени игрока на кружочке
# Принимаемые параметры x - коорд. x, y - коорд. y, r - размер кружочка, name - имя игрока
def write_name(x, y, r, name):
    font = pygame.font.Font(None, r)
    text = font.render(name,True, (0,0,0)) 
    rect = text.get_rect(center=(x,y))
    screen.blit(text,rect)

# Функция отрисовки имени, очков игровка и позиции в топе
# Ориентир по данному игроку
def print_pl_info(name, r, i):
    font = pygame.font.Font(None, 30)
    # Отрисовка имени игрока и его позиции в топе
    text = font.render(str(i+1) + ". " +name,True, (0,0,0)) 
    rect = text.get_rect(topleft = (WIDTH_WINDOW-230,70 + 30*i))
    screen.blit(text,rect)
    # Отрисовка очков игрока
    text = font.render(str(r),True, (0,0,0)) 
    rect = text.get_rect(topright = (WIDTH_WINDOW-20,70 + 30*i))
    screen.blit(text,rect)
    
def print_top():
    # Индекс данного игрока в топе
    p = 0
    # Абсолютная позиция того или иного игрока в топе
    in_top = 0
    
    font = pygame.font.Font(None, 30)
    # Отрисовка 
    text = font.render("Топ игроков",True, (0,0,0)) 
    rect = text.get_rect(topleft = (WIDTH_WINDOW-230,20))
    screen.blit(text,rect)
    text = font.render("Очки",True, (0,0,0)) 
    rect = text.get_rect(topright = (WIDTH_WINDOW-20,20))
    screen.blit(text,rect)
    for i in range(len(top)):
        if (top[i][0] == UserName):
            p = i
            break
    for j in range(p):
        curr = top[p-j-1]
        print_pl_info(curr[0], curr[1], in_top)
        in_top+= 1;
    print_pl_info(top[p][0],top[p][1],p)
    for k in range(len(top)-p if len(top)-p <= 3 else 3):
        curr = top[p+k]
        print_pl_info(curr[0], curr[1], in_top)
        in_top+= 1;
    
def draw_opponents(data):
    for i in range(len(data)):
        j = data[i].split(' ')
        x = WIDTH_WINDOW//2 + int(j[0])
        y = HEIGHT_WINDOW//2 + int(j[1])
        r = int(j[2])
        c = colors[j[3]]
        pygame.draw.circle(screen,c,(x,y),r)

        if len(j) == 5:
            write_name(x,y,r,j[4])
        
class Me():
    def __init__(self, data):
        data = data.split()
        self.r = int(data[0])
        self.color = data[1]
        
    def update(self, new_r):
        self.r = new_r

    def draw(self):
        if self.r != 0:
            pygame.draw.circle(screen, colors[self.color],
                       (WIDTH_WINDOW//2,HEIGHT_WINDOW//2), self.r)
        write_name(WIDTH_WINDOW//2,HEIGHT_WINDOW//2,self.r,UserName)

GRID_COLOR = (0,0,0)

class Grid():
    def __init__(self,screen):
        self.screen = screen
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size
        
    def update(self, r_x, r_y, L):
        self.size = self.start_size//L
        self.x = -self.size + (-r_x) % (self.size)
        self.y = -self.size + (-r_y) % (self.size)

    def draw(self):
        #Вертикальные
        for i in range(WIDTH_WINDOW//self.size+1):
            pygame.draw.line(self.screen,GRID_COLOR,
                             [self.x+i*self.size,0],[self.x+i*self.size,HEIGHT_WINDOW],1)
        #Горизонтальные
        for i in range(WIDTH_WINDOW//self.size+1):
            pygame.draw.line(self.screen,GRID_COLOR,
                             [0,self.y+i*self.size],[WIDTH_WINDOW,self.y+i*self.size],1)

#Создание игрового окна
pygame.init();
screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
pygame.display.set_caption("InfiniteHunger")

#Подключение к серверу
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.connect(('localhost', 10000))

#Получение данных о цвете игрока с сервера
sock.send(('.'+UserName+' '+str(WIDTH_WINDOW)+' '+str(HEIGHT_WINDOW)+'.').encode())
data = sock.recv(64).decode()
sock.send('!'.encode())
myPl = Me(data)
GameGrid = Grid(screen)

running = True



while running:
    #Обработка событиый
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
           running = False
           break
        
    #Считаем положение мышки игрока если курсор находится в окне игры
    if pygame.mouse.get_focused():
        pos = pygame.mouse.get_pos()
        #Вектор направления движения игрока
        v = (pos[0] - WIDTH_WINDOW//2, pos[1] - HEIGHT_WINDOW//2)
        
        if myPl.r**2 > (v[0]**2 + v[1]**2):
            v = (0,0)
    
    #Отправляем вектор направления движения, если он был изменен
    if old_v != v:
        old_v = v;
        message = '<'+str(v[0])+','+str(v[1])+'>'
        sock.send(message.encode())

    #Получаем от сервера новое состояние игрового поля
    data = sock.recv(2**20)
    data = data.decode()
    data = find(data)
    data = data.split(',')
    
    #Рисуем новое состояние игрового поля при получении сообщения с сервера
    if data != [""]:
        #Массив с игроками карты и их очками в каждом подмассиве
        top = []
        parameters = list(map(int, data[0].split(' ')))
        players = list(map(str, data[-1].split(' ')))
        i = 0
        #print(data[0])
        #print(data[1])
        #print(data[-2])
        #print(data[-1])
        while i < 2*int(data[-2]):
            top.append([players[i],int(players[i+1])])
            i+=2
        top.sort(key = lambda elem: elem[1], reverse = True)
        myPl.update(parameters[0])
        GameGrid.update(parameters[1],parameters[2],parameters[3])
        screen.fill((255,255,255))
        GameGrid.draw()
        draw_opponents(data[1:-2])
        myPl.draw()
    print_top()
    pygame.display.update()

#Закрытие игрового окна
pygame.quit()

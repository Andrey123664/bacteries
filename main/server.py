import socket
import time
import random
from sqlalchemy.orm import sessionmaker
from models import engine, Player
import pygame

Session = sessionmaker(engine)
session = Session()


class Grid():
    def __init__(self, rows, columns, width, height):
        self.color = '#202020'
        self.rows = rows
        self.columns = columns
        self.width = width
        self.height = height

        self.steps_rows = self.height / self.rows
        self.steps_columns = self.width / self.columns

    def draw(self, screen):
        for i in range(1, self.columns):
            pygame.draw.line(screen, self.color, (i * self.steps_columns, 0), (i * self.steps_columns, self.height - 1),
                             1)
        for i in range(1, self.rows):
            pygame.draw.line(screen, self.color, (0, i * self.steps_rows), (self.width - 1, i * self.steps_rows), 1)


def draw_text(screen, text, x, y, size):
    font = pygame.font.SysFont('Consolas', size)
    image = font.render(text, True, 'white', 'black')
    rect = image.get_rect(centerx=x, centery=y)
    screen.blit(image, rect)


class Food:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color


class LocalPlayer:
    def __init__(self, id, name, sock, address):
        self.id = id
        self.db = session.get(Player, self.id)
        self.name = name
        self.sock = sock
        self.address = address
        self.x = 500
        self.y = 500
        self.size = 50
        self.errors = 0
        self.abs_speed = 1
        self.speed_x = 0
        self.speed_y = 0
        self.color = 'green'
        self.w_vision = 800
        self.h_vision = 600

    def __repr__(self):
        return self.name

    def new_speed(self):
        self.abs_speed = 10 / (self.size ** 0.5)

    def change_speed(self, data):
        data = find_vector(data)
        if data[0] == 0 and data[1] == 0:
            self.speed_x = self.speed_y = 0
        else:
            data = data[0] * self.abs_speed, data[1] * self.abs_speed
            self.speed_x, self.speed_y = data

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        if self.x < 0 + self.size:
            self.x = self.size
        elif self.x > width_room - self.size:
            self.x = width_room - self.size
        if self.y < 0 + self.size:
            self.y = self.size
        elif self.y > height_room - self.size:
            self.y = height_room - self.size

    def load(self):
        self.x = self.db.x
        self.y = self.db.y
        self.size = self.db.size
        self.errors = self.db.errors
        self.abs_speed = self.db.abs_speed
        self.speed_x = self.db.speed_x
        self.speed_y = self.db.speed_y
        self.color = self.db.color
        self.w_vision = self.db.w_vision
        self.h_vision = self.db.h_vision
        return self


def find_vector(vector: str):
    first = None
    for i, char in enumerate(vector):
        if char == '<':
            first = i
        elif char == '>' and first is not None:
            last = i
            result = vector[first + 1:last].split(',')
            result = list(map(float, result))
            return result
    return ''


def find_color(color: str):
    first = None
    for i, char in enumerate(color):
        if char == "<":
            first = i
        elif char == '>' and first is not None:
            last = i
            result = color[first + 1:last].split(',')
            return result
    return ''


main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind(('localhost', 10000))
main_socket.setblocking(False)
main_socket.listen(5)
print('готово')
players = {}
run = True
width_room, height_room = 4000, 4000
width_window, height_window = 400, 400
FPS = 60
pygame.init()
screen = pygame.display.set_mode((width_window, height_window))
pygame.display.set_caption('Бактерии')
clock = pygame.time.Clock()
color_list = ['blue', 'red', 'green', 'yellow']
names = ('Jack', 'Cindy', 'Will', 'Harry', 'German', 'Wendy', 'Kunkka', 'Luna', 'Carl', 'Riki')
for i in range(50):
    player = Player(names[i % len(names)], None)
    player.color = random.choice(color_list)
    player.size = random.randint(10, 100)
    player.x = random.randint(player.size, width_room - 1 - player.size)
    player.y = random.randint(player.size, height_room - 1 - player.size)
    player.speed_x = random.random() * random.choice([-1, 1])
    player.speed_y = (1 - player.speed_x ** 2) ** 0.5 * random.choice([-1, 1])
    session.add(player)
    session.commit()
    player_ = LocalPlayer(player.id, player.name, None, None).load()
    players[player.id] = player_
tick = -1
foods = []
food_size = 10
for x in range(100):
    food = Food(random.randint(0, width_room - 1), random.randint(0, height_room - 1), food_size,
                random.choice(['red', 'blue', 'green', 'yellow']))
    foods.append(food)
grid = Grid(10, 10, width_window, height_window)

while run:
    clock.tick(FPS)
    tick += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    try:
        new_socket, address = main_socket.accept()

        new_socket.setblocking(False)
        player = Player('John', address)
        data = new_socket.recv(1024).decode()
        if data.startswith('color'):
            player.name, player.color = find_color(data)

        session.add(player)
        session.commit()

        address_ = f'({address[0]},{address[1]})'
        data = session.query(Player).filter(Player.address == address_).first()
        if data:
            player_ = LocalPlayer(data.id, data.name, new_socket, data.address).load()
            players[data.id] = player_

    except BlockingIOError:
        pass
    for _, player in players.items():
        if player.sock is not None:
            try:
                data = player.sock.recv(1024).decode()

                player.change_speed(data)

            except BlockingIOError:
                pass
        else:
            if tick % 400 == 0:
                speed_x = random.random() * random.choice([-1, 1])
                speed_y = (1 - speed_x ** 2) ** 0.5 * random.choice([-1, 1])
                data = f'<{speed_x},{speed_y}>'
                player.change_speed(data)

    """словарь с информацией о том, кто кого видит"""
    visible_bacteries = {}
    for id in players:
        visible_bacteries[id] = []
    pairs = list(players.items())
    for i in range(len(pairs)):
        player_1 = pairs[i][1]
        for food in foods:
            dist_x = food.x - player_1.x
            dist_y = food.y - player_1.y
            if abs(dist_x) <= player_1.w_vision // 2 + food.size and abs(dist_y) <= player_1.h_vision // 2 + food.size:
                dist = (dist_x ** 2 + dist_y ** 2) ** 0.5
                if dist < player_1.size:
                    player_1.size = (player_1.size ** 2 + 10 * food.size ** 2) ** 0.5
                    player_1.new_speed()
                    food.size = 0
                    foods.remove(food)
                    print(f'{player_1=}, {player_1.size=}')
                if player_1.address is not None and food.size != 0:
                    pass

        for j in range(i + 1, len(pairs)):

            player_2 = pairs[j][1]
            dist_x = player_2.x - player_1.x
            dist_y = player_2.y - player_1.y
            dist = (dist_x ** 2 + dist_y ** 2) ** 0.5

            """"может ли первый игрок видеть или съесть второго"""
            if abs(dist_x) <= player_1.w_vision // 2 + player_2.size and abs(
                    dist_y) <= player_1.h_vision // 2 + player_2.size:
                if dist <= player_1.size and player_1.size > player_2.size * 1.1:
                    player_2.size, player_2.speed_x, player_2.speed_y = 0, 0, 0
                if player_1.address is not None:
                    x_ = str(round(dist_x))
                    y_ = str(round(dist_y))
                    size_ = str(round(player_2.size))
                    color_ = player_2.color
                    name_ = player_2.name
                    data = f'{x_} {y_} {size_} {color_} {name_}'
                    visible_bacteries[player_1.id].append(data)

            """"может ли второй игрок видеть или съесть первого"""
            if abs(dist_x) <= player_2.w_vision // 2 + player_1.size and abs(
                    dist_y) <= player_2.h_vision // 2 + player_1.size:
                if dist <= player_2.size and player_2.size > player_1.size * 1.1:
                    player_1.size, player_1.speed_x, player_1.speed_y = 0, 0, 0
                if player_2.address is not None:
                    x_ = str(round(-dist_x))
                    y_ = str(round(-dist_y))
                    size_ = str(round(player_1.size))
                    color_ = player_1.color
                    name_ = player_1.name
                    data = f'{x_} {y_} {size_} {color_} {name_}'
                    visible_bacteries[player_2.id].append(data)

    for id, lst in visible_bacteries.items():
        visible_bacteries[id] = '<' + '|'.join(lst) + '>'

    """отправляем клиентам видимых игроков"""
    for id, player in players.items():
        if player.sock is not None:
            try:
                player.sock.send(visible_bacteries[id].encode())
            except:
                player.sock.close()
                players.pop(id)
                p = session.get(Player, id)
                session.delete(p)
                session.commit()
    for id, player in players.copy().items():
        if player.errors >= 500 or player.size == 0:
            if player.sock is not None:
                player.sock.close()
            players.pop(id)
            p = session.get(Player, id)
            session.delete(p)
            session.commit()
    for player in players.values():
        player.update()
    """визуализация"""
    screen.fill('black')
    grid.draw(screen)
    for player in players.values():
        x = player.x * width_window // width_room
        y = player.y * height_window // height_room

        size = player.size * width_window // width_room
        pygame.draw.circle(screen, player.color, (x, y), size)
        draw_text(screen, player.name, x, y, int(size))

    for food in foods:
        x = food.x * width_window // width_room
        y = food.y * height_window // height_room
        size = food.size * width_window // width_room
        pygame.draw.circle(screen, food.color, (x, y), size)

    pygame.display.update()
pygame.quit()
main_socket.close()

import socket
import time
from sqlalchemy.orm import sessionmaker
from models import engine, Player
import pygame

Session = sessionmaker(engine)
session = Session()


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
width_server, height_server = 400, 400
FPS = 60
pygame.init()
screen = pygame.display.set_mode((width_server, height_server))
pygame.display.set_caption('Бактерии')
clock = pygame.time.Clock()
while run:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    try:
        new_socket, address = main_socket.accept()
        print(new_socket, address)
        new_socket.setblocking(False)
        player = Player('John', address)
        data = new_socket.recv(1024).decode()
        if data.startswith('color'):
            player.name, player.color = find_color(data)
            print(player.name, player.color)
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
        try:
            data = player.sock.recv(1024).decode()
            print(player.name, data)
            player.change_speed(data)

        except BlockingIOError:
            pass
    visible_bacteries = {}
    for id in players:
        visible_bacteries[id] = []
    pairs = list(players.items())
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            player_1 = pairs[i][1]
            player_2 = pairs[j][1]
            dist_x = player_2.x - player_1.x
            dist_y = player_2.y - player_1.y
            if abs(dist_x) <= player_1.w_vision // 2 + player_2.size and abs(
                    dist_y) <= player_1.h_vision // 2 + player_2.size:
                x_ = str(round(dist_x))
                y_ = str(round(dist_y))
                size_ = str(round(player_2.size))
                color_ = player_2.color
                data = f'{x_} {y_} {size_} {color_}'
                visible_bacteries[player_1.id].append(data)
            if abs(dist_x) <= player_2.w_vision // 2 + player_1.size and abs(
                    dist_y) <= player_2.h_vision // 2 + player_1.size:
                x_ = str(round(-dist_x))
                y_ = str(round(-dist_y))
                size_ = str(round(player_1.size))
                color_ = player_1.color
                data = f'{x_} {y_} {size_} {color_}'
                visible_bacteries[player_2.id].append(data)

    screen.fill('black')
    for player in players.values():
        x = player.x * width_server // width_room
        y = player.y * height_server // height_room
        size = player.size * width_server // width_room
        pygame.draw.circle(screen, player.color, (x, y), size)

    pygame.display.update()
pygame.quit()
main_socket.close()

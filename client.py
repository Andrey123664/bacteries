import socket
import pygame
import math
from PySide6 import QtGui, QtCore, QtWidgets
import sys

player_name = ''
player_color = ''


class Grid:
    def __init__(self):
        self.color = '#808080'
        self.step = 20

    def draw(self, screen, width, height):
        for i in range(self.step, width, self.step):
            pygame.draw.line(screen, self.color, (i, 0), (i, height - 1), 1)
        for i in range(self.step, height, self.step):
            pygame.draw.line(screen, self.color, (0, i), (width - 1, i), 1)


grid = Grid()


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 300)
        self.setWindowTitle('Окно')
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.layout = QtWidgets.QVBoxLayout(self.central)
        self.name_label = QtWidgets.QLabel('Имя игрока')
        self.layout.addWidget(self.name_label)
        self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.input = QtWidgets.QLineEdit()
        self.layout.addWidget(self.input)
        self.input.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.color_list = ['blue', 'red', 'green', 'yellow']
        self.color_label = QtWidgets.QLabel('Цвет игрока')
        self.layout.addWidget(self.color_label)
        self.color_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.color_combo_box = QtWidgets.QComboBox()
        self.color_combo_box.addItems(self.color_list)
        self.layout.addWidget(self.color_combo_box)
        self.layout.addStretch()

        self.play_button = QtWidgets.QPushButton('ИГРАТЬ')
        self.layout.addWidget(self.play_button)
        self.play_button.clicked.connect(self.play)

    def play(self):
        name = self.input.text().strip()
        if not name:
            return
        global player_name, player_color
        color = self.color_combo_box.currentText()
        player_name = name
        player_color = color

        self.close()


def draw_text(screen, text, color, x, y):
    font = pygame.font.SysFont('impact', 30)
    image = font.render(text, True, color)
    rect = image.get_rect(centerx=x, centery=y)
    screen.blit(image, rect)


def draw_bacteries(data):
    first = None
    result = ''
    for i, char in enumerate(data):
        if char == '<':
            first = i
        elif char == '>' and first is not None:
            last = i
            result = data[first + 1:last]
    bacteries = result.split('|')
    if bacteries == ['']:
        return
    for i, b in enumerate(bacteries):
        data = b.split(' ')
        x = center[0] + int(data[0])
        y = center[1] + int(data[1])
        size = int(data[2])
        color = data[3]
        pygame.draw.circle(screen, color, (x, y), size)
        if len(data) > 4:
            name = data[4]
            draw_text(screen, name, 'black', x, y)


app = QtWidgets.QApplication(sys.argv)
window = Window()
window.show()
app.exec()
if not player_name or not player_color:
    sys.exit()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
client_socket.connect(('localhost', 10000))
client_socket.send(f'color:<{player_name},{player_color}>'.encode())

pygame.init()
width, height = 800, 600
center = width // 2, height // 2
FPS = 5
old_vector = 0, 0
radius = 50
clock = pygame.time.Clock()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Бактерии')
run = True
while run:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            vector = pos[0] - center[0], pos[1] - center[1]
            length = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
            vector = vector[0] / length, vector[1] / length

            if length <= radius:
                vector = 0, 0
            if vector != old_vector:
                old_vector = vector

                client_socket.send(f'<{vector[0]},{vector[1]}>'.encode())

    data = client_socket.recv(1024).decode()
    screen.fill('white')
    grid.draw(screen, width, height)
    draw_bacteries(data)
    pygame.draw.circle(screen, player_color, center, radius)
    draw_text(screen, player_name, 'black', *center)

    pygame.display.update()

pygame.quit()
client_socket.close()

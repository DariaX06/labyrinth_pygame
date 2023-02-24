import pygame
import pytmx
from button import Button
from PIL import Image
import os
import sys


WINDOW_SIZE = WIN_WIDTH, WIN_HEIGHT = 480, 480
FPS = 10
MAPS_DIR = "maps"
TILE_SIZE = 32
ENEMY_EVENT_TYPE = 30


class Labyrinth:
    def __init__(self, filename, free_tiles, finish_tile):
        self.map = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")
        self.height = self.map.height
        self.width = self.map.width
        self.tile_size = self.map.tilewidth
        self.free_tiles = free_tiles
        self.finish_tile = finish_tile

    def render(self, screen, hero_pos, light_radius):
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(change_tile_image(image, (x, y), hero_pos, light_radius), (x * self.tile_size, y * self.tile_size))

    def get_tile_id(self, pos):
        return self.map.tiledgidmap[self.map.get_tile_gid(*pos, 0)]

    def is_free(self, pos):
        return self.get_tile_id(pos) in self.free_tiles

    def find_path(self, start):
        x, y = start
        hor, ver, hor1, ver1 = [], [], [], []
        for i in range(1, 5):
            hor.append((x + i, y))
            hor1.append((x - i, y))
            ver.append((x, y + i))
            ver1.append((x, y - i))
        try:
            if all(map(lambda x: self.is_free(x), hor)):
                return hor
            if all(map(lambda x: self.is_free(x), hor1)):
                return hor1
            if all(map(lambda x: self.is_free(x), ver)):
                return ver
            if all(map(lambda x: self.is_free(x), ver1)):
                return ver1
        except Exception:
            pass


class Hero:
    def __init__(self, pos, pic, pic2):
        self.health = 3
        self.x, self.y = pos
        self.health_image = pygame.image.load("images/health.png")
        self.images = [pygame.image.load(f"images/{pic}"), pygame.image.load(f"images/{pic2}")]
        self.image_i = 0

    def get_damage(self):
        self.health -= 1

    def get_health(self):
        return self.health

    def get_position(self):
        return self.x, self.y

    def set_position(self, pos):
        self.x, self.y = pos

    def render(self, screen):
        delta = (self.images[self.image_i].get_width() - TILE_SIZE) // 2
        screen.blit(self.images[self.image_i], (self.x * TILE_SIZE - delta, self.y * TILE_SIZE - delta))
        for i in range(self.health):
            screen.blit(self.health_image, ((14 - i) * TILE_SIZE - delta, 14 * TILE_SIZE - delta))
        #center = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        #pygame.draw.circle(screen, (255, 255, 255), center, TILE_SIZE // 2)


class Enemy:
    def __init__(self, pos, pic, pic2, health):
        self.killed = False
        self.health = health
        self.x, self.y = pos
        self.delay = 100
        self.images = [pygame.image.load(f"images/{pic}"), pygame.image.load(f"images/{pic2}")]
        pygame.time.set_timer(ENEMY_EVENT_TYPE, self.delay)
        self.image_i = 0
        self.path = []

    def set_path(self, path):
        self.path = path.copy()
        self.path.insert(0, self.get_position())

    def get_path(self):
        return self.path

    def get_damage(self):
        self.health -= 1
        if self.health == 0:
            self.kill()

    def kill(self):
        self.killed = True
        self.set_position((1000, 1000))

    def get_position(self):
        return self.x, self.y

    def set_position(self, pos):
        self.x, self.y = pos

    def render(self, screen, hero_pos, light_radius):
        delta = (self.images[self.image_i].get_width() - TILE_SIZE) // 2
        screen.blit(change_tile_image(self.images[self.image_i], self.get_position(), hero_pos, light_radius),
                    (self.x * TILE_SIZE - delta, self.y * TILE_SIZE - delta))


class Flashlight:
    def __init__(self, pos, pic):
        self.killed = False
        self.x, self.y = pos
        self.image = pygame.image.load(f"images/{pic}")

    def kill(self):
        self.killed = True
        self.set_position((1000, 1000))

    def get_position(self):
        return self.x, self.y

    def set_position(self, pos):
        self.x, self.y = pos

    def render(self, screen, hero_pos, light_radius):
        delta = (self.image.get_width() - TILE_SIZE) // 2
        screen.blit(change_tile_image(self.image, self.get_position(), hero_pos, light_radius),
                    (self.x * TILE_SIZE - delta, self.y * TILE_SIZE - delta))


class Game:
    def __init__(self, labyrinth, hero, enemys, flashlights):
        self.labyrinth = labyrinth
        self.hero = hero
        self.enemys = enemys
        self.flashlights = flashlights
        self.light_radius = 1
        for enemy in self.enemys:
            enemy.set_path(self.labyrinth.find_path(enemy.get_position()))

    def render(self, screen):
        self.labyrinth.render(screen, self.hero.get_position(), self.light_radius)
        self.hero.render(screen)
        for light in self. flashlights:
            light.render(screen, self.hero.get_position(), self.light_radius)
        for enemy in self.enemys:
            enemy.render(screen, self.hero.get_position(), self.light_radius)

    def update_hero(self):
        next_x, next_y = self.hero.get_position()
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            next_x -= 1
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_x += 1
        if pygame.key.get_pressed()[pygame.K_UP]:
            next_y -= 1
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            next_y += 1
        if self.labyrinth.is_free((next_x, next_y)):
            self.hero.set_position((next_x, next_y))

    def move_enemy(self, index):
        for enemy in self.enemys:
            if enemy.killed:
                continue
            enemy.image_i = 0
            path = enemy.get_path()
            if index // len(path) % 2 == 1:
                path = list(reversed(path))
            enemy.set_position(path[index % len(path)])

    def attack_enemys(self):
        x, y = self.hero.get_position()
        for enemy in self.enemys:
            xe, ye = enemy.get_position()
            if abs(xe - x) <= 1 and abs(ye - y) <= 1:
                enemy.image_i = 1
                enemy.get_damage()

    def check_win(self):
        return self.labyrinth.get_tile_id(self.hero.get_position()) == self.labyrinth.finish_tile

    def check_lose(self):
        return self.hero.get_health() < 1


def change_tile_image(image, tile_pos, hero_pos, light_radius):
    strFormat = 'RGBA'
    raw_str = pygame.image.tostring(image, strFormat, False)
    image_pil = Image.frombytes(strFormat, image.get_size(), raw_str)
    pixels = image_pil.load()
    x1, y1 = image_pil.size
    tx, ty = tile_pos
    hx, hy = hero_pos

    for i in range(x1):
        for j in range(y1):
            if not (abs(tx - hx) <= light_radius and abs(ty - hy) <= light_radius):
                r, g, b, a = pixels[i, j]
                pixels[i, j] = 0, 0, 0, a
            elif abs(tx - hx) == light_radius or abs(ty - hy) == light_radius:
                r, g, b, a = pixels[i, j]
                pixels[i, j] = r // 2, g // 2, b // 2, a

    return pygame.image.fromstring(image_pil.tobytes(), image_pil.size, strFormat)


def get_font(size):
    return pygame.font.Font("font1.ttf", size)


def show_msg(screen, msg):
    font = get_font(50)
    text = font.render(msg, 1, (24, 31, 44))
    text_x = WIN_WIDTH // 2 - text.get_width() // 2
    text_y = WIN_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (143, 136, 179), (text_x - 10, text_y - 10, text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def load_image(name):
    fullname = name
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


current_scene = None
pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)


def switch_scene(scene):
    global current_scene
    current_scene = scene


def scene_1():
    labyrinth = Labyrinth("map2.tmx", [*list(range(86, 92)), *list(range(103, 108)), 110], 110)
    hero = Hero((2, 13), 'hero1.png', 'hero1_dmg.png')
    enemy = Enemy((8, 1), 'enemy1.png', 'enemy1_dmg.png', 3)
    enemy2 = Enemy((1, 5), 'enemy1.png', 'enemy1_dmg.png', 3)
    enemy3 = Enemy((5, 7), 'enemy1.png', 'enemy1_dmg.png', 3)
    enemy4 = Enemy((1, 9), 'enemy1.png', 'enemy1_dmg.png', 3)
    scene_builder(labyrinth, hero, [enemy, enemy2, enemy3, enemy4], [Flashlight((1, 5), 'light.png'),
                                                             Flashlight((5, 7), 'light.png')])


def scene_2():
    labyrinth = Labyrinth("map3.tmx", [1, 18, 35, 52, 110], 110)
    hero = Hero((2, 13), 'hero1.png', 'hero1_dmg.png')
    enemy = Enemy((13, 3), 'enemy2.png', 'enemy2_dmg.png', 4)
    enemy2 = Enemy((6, 11), 'enemy2.png', 'enemy2_dmg.png', 4)
    enemy3 = Enemy((4, 5), 'enemy2.png', 'enemy2_dmg.png', 4)
    enemy4 = Enemy((11, 1), 'enemy2.png', 'enemy2_dmg.png', 4)
    scene_builder(labyrinth, hero, [enemy, enemy2, enemy3, enemy4], [Flashlight((13, 1), 'light.png'),
                                                             Flashlight((6, 1), 'light.png')])


def scene_3():
    labyrinth = Labyrinth("map4.tmx", [*list(range(86, 92)), *list(range(103, 108)), 110], 110)
    hero = Hero((12, 13), 'hero1.png', 'hero1_dmg.png')
    enemy = Enemy((3, 10), 'enemy3.png', 'enemy3_dmg.png', 5)
    enemy2 = Enemy((3, 1), 'enemy3.png', 'enemy3_dmg.png', 5)
    enemy3 = Enemy((11, 8), 'enemy3.png', 'enemy3_dmg.png', 5)
    enemy4 = Enemy((1, 3), 'enemy3.png', 'enemy3_dmg.png', 5)
    scene_builder(labyrinth, hero, [enemy, enemy2, enemy3, enemy4], [Flashlight((4, 6), 'light.png'),
                                                             Flashlight((9, 3), 'light.png')])

def menu():
    global current_scene

    # Заголовок
    font = get_font(50)
    text = font.render('Labyrinth', 1, (24, 31, 44))
    text_x = WIN_WIDTH // 2 - text.get_width() // 2
    text_y = 82
    text_w = text.get_width()
    text_h = text.get_height()

    screen.blit(pygame.image.load(f"images/fon_menu.png"), (0, 0))
    # pygame.draw.rect(screen, (143, 136, 179), (text_x - 10, text_y - 10, text_w + 20, text_h + 20))
    fon_btn = pygame.transform.scale(load_image('images/button.png'), (text_w + 30, text_h + 20))
    screen.blit(fon_btn, (text_x - 20, text_y - 10))
    screen.blit(text, (text_x, text_y))

    # Уровни
    btn_1 = Button(image=pygame.image.load("images/button.png"), pos=(WIN_WIDTH // 2, WIN_HEIGHT // 2 - 50),
                      text_input=" Level 1", font=get_font(30), base_color="#d7fcd4")
    btn_2 = Button(image=pygame.image.load("images/button.png"), pos=(WIN_WIDTH // 2, WIN_HEIGHT // 2 + 10),
                   text_input=" Level 2", font=get_font(30), base_color="#d7fcd4")
    btn_3 = Button(image=pygame.image.load("images/button.png"), pos=(WIN_WIDTH // 2, WIN_HEIGHT // 2 + 70),
                   text_input=" Level 3", font=get_font(30), base_color="#d7fcd4")
    btn_exit = Button(image=pygame.image.load("images/button.png"), pos=(WIN_WIDTH // 2, WIN_HEIGHT // 2 + 130),
                   text_input="exit", font=get_font(30), base_color="#d7fcd4")
    clock = pygame.time.Clock()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                current_scene = None
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_1.checkForInput(mouse_pos):
                    current_scene = scene_1
                    running = False
                if btn_2.checkForInput(mouse_pos):
                    current_scene = scene_2
                    running = False
                if btn_3.checkForInput(mouse_pos):
                    current_scene = scene_3
                    running = False
                if btn_exit.checkForInput(mouse_pos):
                    current_scene = None
                    running = False
        btn_1.update(screen)
        btn_2.update(screen)
        btn_3.update(screen)
        btn_exit.update(screen)
        pygame.display.flip()
        clock.tick(FPS)


def scene_builder(labyrinth, hero, enemys, flashlights):
    global current_scene
    game = Game(labyrinth, hero, enemys, flashlights)

    attack_btn = Button(image=pygame.image.load("images/attack.png"), pos=(16, 432),
                         text_input="", font=get_font(75), base_color="#d7fcd4")
    menu_btn = Button(image=pygame.image.load("images/home1.png"), pos=(464, 16),
                      text_input="", font=get_font(75), base_color="#d7fcd4")
    up_btn = Button(image=pygame.image.load("images/arrow.png"), pos=(48, 432),
                      text_input="", font=get_font(75), base_color="#d7fcd4")
    down_btn = Button(image=pygame.image.load("images/arrow_bottom.png"), pos=(48, 464),
                    text_input="", font=get_font(75), base_color="#d7fcd4")
    left_btn = Button(image=pygame.image.load("images/arrow_left.png"), pos=(16, 464),
                    text_input="", font=get_font(75), base_color="#d7fcd4")
    right_btn = Button(image=pygame.image.load("images/arrow_right.png"), pos=(80, 464),
                    text_input="", font=get_font(75), base_color="#d7fcd4")
    clock = pygame.time.Clock()
    running = True
    game_over = False
    count = 0
    while running:
        game.hero.image_i = 0
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                current_scene = None
                running = False
            if event.type == ENEMY_EVENT_TYPE and not game_over:
                game.move_enemy(count - 1)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    game.attack_enemys()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_btn.checkForInput(mouse_pos):
                    current_scene = menu
                    running = False
                if attack_btn.checkForInput(mouse_pos) and not game_over:
                    game.attack_enemys()
                if up_btn.checkForInput(mouse_pos) and not game_over:
                    next_x, next_y = game.hero.get_position()
                    next_y -= 1
                    if game.labyrinth.is_free((next_x, next_y)):
                        game.hero.set_position((next_x, next_y))
                if down_btn.checkForInput(mouse_pos) and not game_over:
                    next_x, next_y = game.hero.get_position()
                    next_y += 1
                    if game.labyrinth.is_free((next_x, next_y)):
                        game.hero.set_position((next_x, next_y))
                if left_btn.checkForInput(mouse_pos) and not game_over:
                    next_x, next_y = game.hero.get_position()
                    next_x -= 1
                    if game.labyrinth.is_free((next_x, next_y)):
                        game.hero.set_position((next_x, next_y))
                if right_btn.checkForInput(mouse_pos) and not game_over:
                    next_x, next_y = game.hero.get_position()
                    next_x += 1
                    if game.labyrinth.is_free((next_x, next_y)):
                        game.hero.set_position((next_x, next_y))

        if not game_over:
            lights_pos = list(map(lambda x: x.get_position(), game.flashlights))
            if game.hero.get_position() in lights_pos:
                game.light_radius += 1
                game.flashlights[lights_pos.index(game.hero.get_position())].kill()
            if hero.get_position() in list(map(lambda x: x.get_position(), game.enemys)) and not game_over:
                hero.image_i = 1
                hero.get_damage()
            game.update_hero()

        screen.fill((0, 0, 0))
        game.render(screen)

        if game.check_win():
            game_over = True
            show_msg(screen, "Victory")
        if game.check_lose():
            game_over = True
            show_msg(screen, "Game over")

        menu_btn.update(screen)
        attack_btn.update(screen)
        up_btn.update(screen)
        down_btn.update(screen)
        left_btn.update(screen)
        right_btn.update(screen)

        pygame.display.flip()
        count += 1
        clock.tick(FPS)


def main():
    switch_scene(menu)
    while current_scene is not None:
        current_scene()
    pygame.quit()


if __name__ == "__main__":
    main()
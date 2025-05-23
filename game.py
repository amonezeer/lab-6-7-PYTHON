import pygame
import random
import math
import sys
import json
import time
import os

# Основні константи гри
WIDTH, HEIGHT = 800, 600  # Розмір вікна
FPS = 60  # Частота кадрів
ASTEROID_COUNT = 5  # Кількість астероїдів
STAR_COUNT = 3  # Кількість зірок
INITIAL_LIVES = 3  # Початкова кількість життів
BONUS_SPAWN_CHANCE = 0.02  # Шанс появи бонусу

# Ініціалізація Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Створюю вікно гри
pygame.display.set_caption("Космічний Втеча")  # Назва вікна
clock = pygame.time.Clock()  # Контроль частоти кадрів
font = pygame.font.SysFont("Arial", 24, bold=True)  # Шрифт для тексту
small_font = pygame.font.SysFont("Arial", 18)  # Менший шрифт
title_font = pygame.font.SysFont("Arial", 36, bold=True)  # Шрифт для заголовків

# Кольори для гри
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
GRAY = (100, 100, 100)
DARKGRAY = (60, 60, 60)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
DARKBLUE = (10, 10, 40)
GREEN = (50, 200, 50)
CYAN = (0, 255, 255)

# Налаштування музики
pygame.mixer.init()
try:
    if os.path.exists("врубай.mp3"):
        pygame.mixer.music.load("врубай.mp3")  
        pygame.mixer.music.set_volume(0.3)  # Встановлюю гучність
    else:
        print("Файл 'врубай.mp3' не знайдено. Музика відключена.")
except Exception as e:
    print("Помилка завантаження музики:", e)

# Клас для ефекту вибуху
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x  # Координата X вибуху
        self.y = y  # Координата Y вибуху
        self.frame = 0  # Поточний кадр анімації
        self.frames = 10  # Загальна кількість кадрів
        self.size = 20  # Початковий розмір вибуху
        self.timer = 0  # Таймер анімації
        self.duration = 0.5  # Тривалість анімації

    def update(self, dt):
        # Оновлюю таймер і кадр анімації, видаляю об'єкт після завершення
        self.timer += dt
        self.frame = int(self.timer / self.duration * self.frames)
        if self.frame >= self.frames:
            self.kill()

    def draw(self, surface):
        # Малюю вибух з ефектом затухання і збільшення розміру
        if self.frame < self.frames:
            size = self.size + self.frame * 5
            alpha = 255 - int(self.frame / self.frames * 255)
            color = (255, 100 + self.frame * 10, 0)
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            surf.set_alpha(alpha)
            surface.blit(surf, (self.x - size, self.y - size))

# Клас для паралакс-фону зі зірками
class ParallaxBackground:
    def __init__(self):
        # Створюю два шари зірок з різною швидкістю і розмірами
        self.layers = [
            {"speed": 0.5, "stars": [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1.0)] for _ in range(50)]},
            {"speed": 1.0, "stars": [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(1.0, 2.0)] for _ in range(30)]},
        ]

    def update(self):
        # Рухаю зірки вліво, переношу за межі екрана на початок
        for layer in self.layers:
            for star in layer["stars"]:
                star[0] -= star[2] * layer["speed"]
                if star[0] < 0:
                    star[0] = WIDTH
                    star[1] = random.randint(0, HEIGHT)

    def draw(self, surface):
        # Малюю зірки з яскравістю залежно від розміру
        for layer in self.layers:
            for star in layer["stars"]:
                brightness = min(255, int(150 + 105 * star[2]))
                pygame.draw.circle(surface, (brightness, brightness, brightness), (int(star[0]), int(star[1])), int(star[2]))

# Функція для малювання корабля гравця
def draw_player_ship(surface, pos, angle):
    # Малюю трикутний корабель з обертанням і полум'ям при русі
    x, y = pos
    size = 20
    points = [(0, -size), (size/2, size/2), (-size/2, size/2)]
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    rotated_points = []
    for px, py in points:
        rx = px * cos_a - py * sin_a
        ry = px * sin_a + py * cos_a
        rotated_points.append((x + rx, y + ry))
    pygame.draw.polygon(surface, BLUE, rotated_points)
    pygame.draw.polygon(surface, WHITE, rotated_points, 2)
    if abs(angle) > 0:
        flame_points = [
            (x - size/2 * cos_a, y - size/2 * sin_a),
            (x - size * cos_a + size/4 * sin_a, y - size * sin_a - size/4 * cos_a),
            (x - size * cos_a - size/4 * sin_a, y - size * sin_a + size/4 * cos_a)
        ]
        pygame.draw.polygon(surface, RED, flame_points)

# Функція для малювання астероїда
def draw_asteroid(surface, pos, radius):
    # Малюю астероїд як коло з деталями для нерівної поверхні
    x, y = pos
    pygame.draw.circle(surface, GRAY, (int(x), int(y)), radius)
    for _ in range(5):
        dx = random.randint(-radius//2, radius//2)
        dy = random.randint(-radius//2, radius//2)
        pygame.draw.circle(surface, DARKGRAY, (int(x+dx), int(y+dy)), radius//6)

# Функція для малювання зірки
def draw_star(surface, pos, size=10, pulse=0):
    # Малюю зірку як п'ятикутник з пульсацією розміру
    x, y = pos
    size = size + math.sin(pulse) * 2
    points = []
    for i in range(5):
        outer_angle = math.radians(i * 72 - 90)
        inner_angle = math.radians(i * 72 + 36 - 90)
        ox = x + math.cos(outer_angle) * size
        oy = y + math.sin(outer_angle) * size
        ix = x + math.cos(inner_angle) * size * 0.5
        iy = y + math.sin(inner_angle) * size * 0.5
        points.append((ox, oy))
        points.append((ix, iy))
    pygame.draw.polygon(surface, YELLOW, points)
    pygame.draw.polygon(surface, WHITE, points, 1)

# Функція для малювання бонусу
def draw_bonus(surface, pos, bonus_type, pulse=0):
    # Малюю бонус (щит або життя) з пульсацією
    x, y = pos
    size = 15 + math.sin(pulse) * 3
    if bonus_type == "shield":
        pygame.draw.circle(surface, CYAN, (int(x), int(y)), size, 3)
        pygame.draw.circle(surface, WHITE, (int(x), int(y)), size // 2)
    elif bonus_type == "life":
        points = [(x, y - size), (x + size/2, y + size/2), (x - size/2, y + size/2)]
        pygame.draw.polygon(surface, RED, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

# Клас корабля гравця
class PlayerShip(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.x = WIDTH // 2  # Початкова координата X
        self.y = HEIGHT // 2  # Початкова координата Y
        self.speed = 5  # Швидкість руху
        self.angle = 0  # Кут повороту
        self.rect = pygame.Rect(self.x - 10, self.y - 10, 20, 20)  # Хітбокс корабля
        self.shield_active = False  # Статус щита
        self.shield_timer = 0  # Таймер щита
        self.shield_duration = 5.0  # Тривалість щита

    def update(self, keys, use_wasd, dt):
        # Оновлюю позицію і кут корабля залежно від натиснутих клавіш
        dx = dy = 0
        if use_wasd:
            if keys[pygame.K_a]: dx = -self.speed
            if keys[pygame.K_d]: dx = self.speed
            if keys[pygame.K_w]: dy = -self.speed
            if keys[pygame.K_s]: dy = self.speed
        else:
            if keys[pygame.K_LEFT]: dx = -self.speed
            if keys[pygame.K_RIGHT]: dx = self.speed
            if keys[pygame.K_UP]: dy = -self.speed
            if keys[pygame.K_DOWN]: dy = self.speed

        self.x += dx
        self.y += dy

        if dx != 0 or dy != 0:
            angle_rad = math.atan2(-dy, dx)
            self.angle = math.degrees(angle_rad)
        else:
            self.angle = 0

        # Обмежую рух межами екрана
        self.x = max(10, min(WIDTH - 10, self.x))
        self.y = max(10, min(HEIGHT - 10, self.y))
        self.rect.center = (self.x, self.y)

        # Оновлюю таймер щита
        if self.shield_active:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shield_active = False

    def draw(self, surface):
        # Малюю корабель і щит, якщо активний
        draw_player_ship(surface, (self.x, self.y), self.angle)
        if self.shield_active:
            pygame.draw.circle(surface, CYAN, (int(self.x), int(self.y)), 25, 2)

# Клас астероїда
class Asteroid(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.radius = random.randint(15, 25)  # Радіус астероїда
        self.x = random.randint(WIDTH + 20, WIDTH + 100)  # Початкова координата X
        self.y = random.randint(self.radius, HEIGHT - self.radius)  # Початкова координата Y
        self.speed = random.uniform(2.5, 5.5)  # Швидкість руху
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)  # Хітбокс

    def update(self, speed_modifier):
        # Рухаю астероїд вліво, переношу за межі екрана
        self.x -= self.speed * speed_modifier
        if self.x < -self.radius:
            self.x = random.randint(WIDTH + 20, WIDTH + 100)
            self.y = random.randint(self.radius, HEIGHT - self.radius)
            self.speed = random.uniform(2.5, 5.5)
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        # Малюю астероїд
        draw_asteroid(surface, (self.x, self.y), self.radius)

# Клас зірки для збору
class StarCollectible(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 10  # Розмір зірки
        self.x = random.randint(WIDTH + 10, WIDTH + 300)  # Початкова координата X
        self.y = random.randint(self.size, HEIGHT - self.size)  # Початкова координата Y
        self.speed = 1.5  # Швидкість руху
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)  # Хітбокс
        self.pulse = 0  # Пульсація для анімації

    def update(self, speed_modifier, dt):
        # Рухаю зірку вліво, оновлюю пульсацію
        self.x -= self.speed * speed_modifier
        self.pulse += dt * 5
        if self.x < -self.size:
            self.x = random.randint(WIDTH + 10, WIDTH + 300)
            self.y = random.randint(self.size, HEIGHT - self.size)
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        # Малюю зірку з пульсацією
        draw_star(surface, (self.x, self.y), self.size, self.pulse)

# Клас бонусу
class Bonus(pygame.sprite.Sprite):
    def __init__(self, bonus_type):
        super().__init__()
        self.bonus_type = bonus_type  # Тип бонусу (щит або життя)
        self.size = 15  # Розмір бонусу
        self.x = random.randint(WIDTH + 10, WIDTH + 100)  # Початкова координата X
        self.y = random.randint(self.size, HEIGHT - self.size)  # Початкова координата Y
        self.speed = 2.0  # Швидкість руху
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)  # Хітбокс
        self.pulse = 0  # Пульсація для анімації

    def update(self, speed_modifier, dt):
        # Рухаю бонус вліво, видаляю за межами екрана
        self.x -= self.speed * speed_modifier
        self.pulse += dt * 5
        if self.x < -self.size:
            self.kill()
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        # Малюю бонус з пульсацією
        draw_bonus(surface, (self.x, self.y), self.bonus_type, self.pulse)

# Функція для виведення тексту по центру
def draw_text_center(surface, text, y, font, color=WHITE, alpha=255):
    # Виводжу текст по центру з заданою прозорістю
    text_surf = font.render(text, True, color)
    text_surf.set_alpha(alpha)
    rect = text_surf.get_rect(center=(WIDTH // 2, y))
    surface.blit(text_surf, rect)

# Функція для створення кнопки
def button(surface, text, y, font, inactive_color, active_color, action=None, alpha=255):
    # Малюю кнопку, активую дію при кліку
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    text_surf = font.render(text, True, WHITE)
    text_surf.set_alpha(alpha)
    rect = text_surf.get_rect(center=(WIDTH // 2, y))
    active = rect.collidepoint(mouse)
    color = active_color if active else inactive_color
    btn_surf = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
    pygame.draw.rect(btn_surf, color, (0, 0, rect.inflate(20, 10).width, rect.inflate(20, 10).height), border_radius=8)
    btn_surf.set_alpha(alpha)
    surface.blit(btn_surf, rect.inflate(20, 10))
    surface.blit(text_surf, rect)
    if active and click[0] == 1 and action is not None:
        pygame.time.delay(150)
        action()

# Функція для малювання життів
def draw_lives(surface, lives):
    # Малюю іконки життів у верхньому лівому куті
    for i in range(lives):
        x = 10 + i * 30
        y = 40
        pygame.draw.polygon(surface, RED, [(x, y), (x + 10, y + 20), (x - 10, y + 20)])
        pygame.draw.polygon(surface, WHITE, [(x, y), (x + 10, y + 20), (x - 10, y + 20)], 2)

# Функція для збереження рекорду
def save_high_score(score, name="Player"):
    # Зберігаю рекорд у JSON, тримаю топ-5
    try:
        with open("highscores.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"scores": []}
    data["scores"].append({"name": name, "score": score})
    data["scores"] = sorted(data["scores"], key=lambda x: x["score"], reverse=True)[:5]
    with open("highscores.json", "w") as f:
        json.dump(data, f)

# Функція для завантаження рекордів
def load_high_scores():
    # Завантажую рекорди з JSON, повертаю порожній список при помилці
    try:
        with open("highscores.json", "r") as f:
            data = json.load(f)
            return data.get("scores", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Глобальні змінні
game_state = 'MENU'  # Поточний стан гри
score = 0  # Рахунок гравця
lives = INITIAL_LIVES  # Кількість життів
combo = 0  # Поточне комбо
combo_timer = 0  # Таймер комбо
player = None  # Об'єкт корабля гравця
asteroids = []  # Список астероїдів
stars = []  # Список зірок
bonuses = []  # Список бонусів
explosions = []  # Список вибухів
background = ParallaxBackground()  # Фон гри
speed_modifier = 1.0  # Модифікатор швидкості гри
user_settings = {
    "music_volume": 0.3,  # Гучність музики
    "use_wasd": False  # Використання WASD для керування
}
notifications = []  # Список сповіщень
menu_alpha = 255  # Прозорість меню
menu_fade = 0  # Ефект пульсації меню

# Функція для застосування гучності музики
def apply_volume_settings():
    # Встановлюю гучність музики з налаштувань
    pygame.mixer.music.set_volume(user_settings["music_volume"])

# Функція для початку гри
def start_game():
    # Ініціалізую нову гру, скидаю всі параметри
    global game_state, player, asteroids, stars, bonuses, explosions, score, lives, combo, combo_timer, speed_modifier
    player = PlayerShip()
    asteroids = [Asteroid() for _ in range(ASTEROID_COUNT)]
    stars = [StarCollectible() for _ in range(STAR_COUNT)]
    bonuses = []
    explosions = []
    score = 0
    lives = INITIAL_LIVES
    combo = 0
    combo_timer = 0
    speed_modifier = 1.0
    game_state = 'RUNNING'
    apply_volume_settings()
    if os.path.exists("врубай.mp3"):
        pygame.mixer.music.play(-1)

# Функція для продовження гри
def resume_game():
    # Продовжую гру після паузи
    global game_state
    if game_state == 'PAUSE':
        game_state = 'RUNNING'

# Функція для виходу з гри
def exit_game():
    pygame.quit()
    sys.exit()

# Функція для завершення гри
def game_over():
    # Зупиняю музику, зберігаю рекорд, переходжу до екрана програшу
    global game_state
    if os.path.exists("врубай.mp3"):
        pygame.mixer.music.stop()
    save_high_score(score)
    game_state = 'GAMEOVER'

# Функція для додавання сповіщення
def add_notification(text, duration=2.0):
    # Додаю сповіщення з текстом і тривалістю
    notifications.append({"text": text, "timer": duration, "alpha": 255})

# Функція для обробки подій
def handle_events():
    # Обробляю події (вихід, пауза, вихід з меню)
    global game_state, lives, menu_alpha, menu_fade
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit_game()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                if game_state == 'RUNNING':
                    game_state = 'PAUSE'
                elif game_state == 'PAUSE':
                    game_state = 'RUNNING'
            if event.key == pygame.K_ESCAPE:
                if game_state in ['PAUSE', 'GAMEOVER', 'MENU', 'SETTINGS', 'LEADERBOARD']:
                    game_state = 'MENU'
                    menu_alpha = 255
                    menu_fade = 0

# Функція для малювання головного меню
def draw_menu():
    # Малюю меню з кнопками і ефектом пульсації
    global menu_alpha, menu_fade
    screen.fill(DARKBLUE)
    background.draw(screen)
    menu_fade += 0.05
    menu_alpha = 255 * (1 - abs(math.sin(menu_fade)))
    draw_text_center(screen, "Космічний Втеча", HEIGHT // 4, title_font, YELLOW, menu_alpha)
    draw_text_center(screen, "Q - Пауза / Продовжити", HEIGHT // 4 + 60, small_font, WHITE, menu_alpha)
    draw_text_center(screen, "ESC - Вийти з гри", HEIGHT // 4 + 90, small_font, WHITE, menu_alpha)

    def start_or_resume():
        global menu_alpha, menu_fade
        if game_state == 'PAUSE':
            resume_game()
        else:
            start_game()
        menu_alpha = 255
        menu_fade = 0

    btn_text = "Продовжити" if game_state == 'PAUSE' else "Почати гру"
    button(screen, btn_text, HEIGHT // 2, font, BLUE, YELLOW, start_or_resume, menu_alpha)
    button(screen, "Налаштування", HEIGHT // 2 + 60, font, GREEN, YELLOW, lambda: set_game_state('SETTINGS'), menu_alpha)
    button(screen, "Лідери", HEIGHT // 2 + 120, font, CYAN, YELLOW, lambda: set_game_state('LEADERBOARD'), menu_alpha)
    button(screen, "Вийти", HEIGHT // 2 + 180, font, RED, YELLOW, exit_game, menu_alpha)

# Функція для малювання екрана програшу
def draw_game_over():
    # Малюю екран програшу з рахунком і кнопкою повернення
    screen.fill(DARKBLUE)
    background.draw(screen)
    draw_text_center(screen, "Гра Закінчена!", HEIGHT // 4, title_font, RED)
    draw_text_center(screen, f"Рахунок: {score}", HEIGHT // 4 + 60, font, WHITE)
    high_scores = load_high_scores()
    if high_scores and score >= high_scores[-1]["score"]:
        draw_text_center(screen, "Новий рекорд!", HEIGHT // 4 + 90, font, YELLOW)
    button(screen, "Повернутися в меню", HEIGHT // 2 + 60, font, BLUE, YELLOW, lambda: set_game_state('MENU'))

# Функція для малювання таблиці лідерів
def draw_leaderboard():
    # Малюю таблицю топ-5 рекордів
    screen.fill(DARKBLUE)
    background.draw(screen)
    draw_text_center(screen, "Таблиця Лідерів", HEIGHT // 4, title_font, YELLOW)
    high_scores = load_high_scores()
    for i, entry in enumerate(high_scores[:5]):
        text = f"{i+1}. {entry['name']}: {entry['score']}"
        draw_text_center(screen, text, HEIGHT // 4 + 60 + i * 30, font, WHITE)
    button(screen, "Повернутися в меню", HEIGHT // 2 + 180, font, BLUE, YELLOW, lambda: set_game_state('MENU'))

# Функція для малювання рахунку і життів
def draw_lives_and_score():
    # Виводжу рахунок, комбо, життя і таймер щита
    score_text = font.render(f"Рахунок: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    if combo > 1:
        combo_text = small_font.render(f"Комбо: x{combo}", True, YELLOW)
        screen.blit(combo_text, (10, 70))
    draw_lives(screen, lives)
    if player.shield_active:
        shield_text = small_font.render(f"Щит: {int(player.shield_timer)}с", True, CYAN)
        screen.blit(shield_text, (10, 100))

# Функція для малювання інформації на паузі
def draw_pause_info():
    # Виводжу текст паузи і керування
    info_texts = [
        "ГРА ПАУЗУВАНА",
        "Q - Продовжити",
        "ESC - Вийти з гри",
        f"Управління: {'WASD' if user_settings['use_wasd'] else 'Стрілки'}"
    ]
    for i, text in enumerate(info_texts):
        draw_text_center(screen, text, HEIGHT // 3 + i * 30, font if i == 0 else small_font, YELLOW if i == 0 else WHITE)

# Функція для малювання налаштувань
def draw_settings():
    # Малюю екран налаштувань (гучність, керування)
    screen.fill(DARKBLUE)
    background.draw(screen)
    draw_text_center(screen, "--- Налаштування ---", HEIGHT // 8, title_font, YELLOW)
    music_text = f"Гучність музики: {int(user_settings['music_volume'] * 100)}% (+/-)"
    control_text = f"Управління: {'WASD' if user_settings['use_wasd'] else 'Стрілки'} (C)"
    draw_text_center(screen, music_text, HEIGHT // 4, font)
    draw_text_center(screen, control_text, HEIGHT // 4 + 40, font)
    draw_text_center(screen, "ESC - Повернутися у меню", HEIGHT // 4 + 80, small_font, WHITE)

# Функція для обробки подій у налаштуваннях
def settings_handle_events():
    # Обробляю клавіші для зміни гучності і керування
    global game_state
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit_game()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                set_game_state('MENU')
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                user_settings['music_volume'] = min(1.0, user_settings['music_volume'] + 0.1)
                apply_volume_settings()
            elif event.key == pygame.K_MINUS:
                user_settings['music_volume'] = max(0.0, user_settings['music_volume'] - 0.1)
                apply_volume_settings()
            elif event.key == pygame.K_c:
                user_settings['use_wasd'] = not user_settings['use_wasd']

# Функція для зміни стану гри
def set_game_state(state):
    # Змінюю стан гри і скидаю ефект меню
    global game_state, menu_alpha, menu_fade
    game_state = state
    menu_alpha = 255
    menu_fade = 0

# Основна функція гри
def main():
    # Головний цикл гри
    global score, lives, game_state, combo, combo_timer, speed_modifier
    last_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        clock.tick(FPS)

        if game_state == 'RUNNING':
            # Оновлюю гру: керування, об'єкти, колізії
            keys = pygame.key.get_pressed()
            handle_events()
            background.update()
            player.update(keys, user_settings['use_wasd'], dt)
            for a in asteroids:
                a.update(speed_modifier)
            for s in stars:
                s.update(speed_modifier, dt)
            for b in bonuses:
                b.update(speed_modifier, dt)
            for e in explosions:
                e.update(dt)

            # Обробляю колізії з астероїдами
            player_rect = player.rect
            collision = False
            for a in asteroids:
                if player_rect.colliderect(a.rect):
                    collision = True
                    break
            if collision and not player.shield_active:
                lives -= 1
                explosions.append(Explosion(a.x, a.y))
                combo = 0
                combo_timer = 0
                if lives <= 0:
                    game_over()
                else:
                    a.x = WIDTH + random.randint(20, 100)
                    a.y = random.randint(a.radius, HEIGHT - a.radius)
                    a.rect.center = (a.x, a.y)
            elif collision and player.shield_active:
                explosions.append(Explosion(a.x, a.y))
                a.x = WIDTH + random.randint(20, 100)
                a.y = random.randint(a.radius, HEIGHT - a.radius)
                a.rect.center = (a.x, a.y)

            # Обробляю збір зірок
            for s in stars[:]:
                if player_rect.colliderect(s.rect):
                    score += 10 * (combo + 1)
                    combo += 1
                    combo_timer = 5.0
                    stars.remove(s)
                    stars.append(StarCollectible())
                    if random.random() < BONUS_SPAWN_CHANCE:
                        bonus_type = random.choice(["shield", "life"])
                        bonuses.append(Bonus(bonus_type))

            # Обробляю збір бонусів
            for b in bonuses[:]:
                if player_rect.colliderect(b.rect):
                    if b.bonus_type == "shield":
                        player.shield_active = True
                        player.shield_timer = player.shield_duration
                        add_notification("Щит активовано!")
                    elif b.bonus_type == "life":
                        lives = min(lives + 1, INITIAL_LIVES)
                        add_notification("Додаткове життя!")
                    bonuses.remove(b)

            # Оновлюю комбо
            if combo > 0:
                combo_timer -= dt
                if combo_timer <= 0:
                    combo = 0
                    combo_timer = 0

            # Збільшую швидкість гри з ростом рахунку
            speed_modifier = 1.0 + score / 1000.0

            # Оновлюю сповіщення
            for n in notifications[:]:
                n["timer"] -= dt
                n["alpha"] = max(0, n["alpha"] - dt * 255 / 2)
                if n["timer"] <= 0:
                    notifications.remove(n)

            # Малюю гру
            screen.fill(BLACK)
            background.draw(screen)
            for s in stars:
                s.draw(screen)
            for a in asteroids:
                a.draw(screen)
            for b in bonuses:
                b.draw(screen)
            for e in explosions:
                e.draw(screen)
            player.draw(screen)
            draw_lives_and_score()
            for i, n in enumerate(notifications):
                draw_text_center(screen, n["text"], HEIGHT // 2 + i * 30, small_font, WHITE, n["alpha"])
            instr_text = font.render("Q - пауза | ESC - вихід", True, DARKGRAY)
            screen.blit(instr_text, (10, HEIGHT - 30))

        elif game_state == 'PAUSE':
            handle_events()
            background.update()
            screen.fill(BLACK)
            background.draw(screen)
            for s in stars:
                s.draw(screen)
            for a in asteroids:
                a.draw(screen)
            for b in bonuses:
                b.draw(screen)
            for e in explosions:
                e.draw(screen)
            player.draw(screen)
            draw_lives_and_score()
            draw_pause_info()

        elif game_state == 'MENU':
            handle_events()
            background.update()
            draw_menu()

        elif game_state == 'SETTINGS':
            settings_handle_events()
            background.update()
            draw_settings()

        elif game_state == 'GAMEOVER':
            handle_events()
            background.update()
            draw_game_over()

        elif game_state == 'LEADERBOARD':
            handle_events()
            background.update()
            draw_leaderboard()

        pygame.display.flip()

if __name__ == "__main__":
    game_state = 'MENU'
    main()
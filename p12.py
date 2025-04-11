import pygame
import random
import pymongo
import subprocess
import os
import sys
import time

# MongoDB Setup
mongod_path = "C:/Program Files/MongoDB/Server/8.0/bin/mongod.exe"
db_path = "C:/data/db"
if not os.path.exists(db_path):
    os.makedirs(db_path)
subprocess.Popen([mongod_path, "--dbpath", db_path])
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["game_database"]
scores_collection = db["scores"]

# Pygame Init
pygame.init()
pygame.mixer.init()
shoot_sound = pygame.mixer.Sound("C:/Users/tupka/Downloads/gt-ia2/space-shooter/gun-shots.mp3")
explosion_sound = pygame.mixer.Sound("C:/Users/tupka/Downloads/gt-ia2/space-shooter/explosion.mp3")
game_over_sound = pygame.mixer.Sound("C:/Users/tupka/Downloads/gt-ia2/space-shooter/Loosing.mp3")

WIDTH, HEIGHT = 800, 600
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
PLAYER_SPEED = 5
BULLET_SPEED = 7
ENEMY_SPEED = 3

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Space Shooter")
background_img = pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/space-background.jpg")
player_img = pygame.transform.scale(pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/player.png"), (64, 64))
ai_img = pygame.transform.scale(pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/enemy.png"), (64, 64))
bullet_img = pygame.transform.scale(pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/bullet.png"), (8, 16))
font = pygame.font.SysFont(None, 36)

def draw_text(text, x, y, color=WHITE):
    screen.blit(font.render(text, True, color), (x, y))

class Player:
    def __init__(self, x, y, image, speed=PLAYER_SPEED):
        self.image = image
        self.x = x
        self.y = y
        self.speed = speed
        self.bullets_left = 1000
        self.hits = 0

    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < WIDTH - 64:
            self.x += self.speed

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

class Bullet:
    def __init__(self, x, y, direction):
        self.image = bullet_img
        self.x = x + 28
        self.y = y
        self.speed = BULLET_SPEED
        self.direction = direction

    def move(self):
        self.y += self.speed * self.direction

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

def reset_phase():
    global player_bullets, ai_bullets
    player_bullets = []
    ai_bullets = []
    player.bullets_left = 1000
    ai.bullets_left = 1000
    draw_text("Switching Phase...", WIDTH // 2 - 150, HEIGHT // 2)
    pygame.display.flip()
    time.sleep(2)

def prompt_name():
    input_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 40)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        screen.blit(background_img, (0, 0))
        draw_text("Enter Your Name:", WIDTH // 2 - 100, HEIGHT // 2 - 50)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Unknown"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        pygame.draw.rect(screen, color, input_box, 2)
        txt_surface = font.render(text, True, WHITE)
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.display.flip()
    return text.strip() if text.strip() != "" else "Anonymous"

def end_screen(winner, player_hits, ai_hits):
    game_over_sound.play()
    name = prompt_name()
    scores_collection.insert_one({"name": name, "player_hits": player_hits, "ai_hits": ai_hits})

    while True:
        screen.blit(background_img, (0, 0))
        draw_text(f"Game Over! Winner: {winner}", WIDTH // 2 - 150, HEIGHT // 2 - 80)
        draw_text("Press R to Restart or Q to Quit", WIDTH // 2 - 180, HEIGHT // 2)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    return

while True:
    player = Player(WIDTH // 2, HEIGHT - 80, player_img)
    ai = Player(WIDTH // 2, 20, ai_img)
    player_bullets = []
    ai_bullets = []
    clock = pygame.time.Clock()
    phase = "attack"
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        screen.blit(background_img, (0, 0))
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) // 1000
        timer = 60 - elapsed_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        draw_text(f"Time Left: {timer}s", WIDTH // 2 - 80, 10)
        draw_text(f"Player Bullets: {player.bullets_left}", 20, 10)
        draw_text(f"Player Hits: {player.hits}", 20, 40)
        draw_text(f"AI Bullets: {ai.bullets_left}", WIDTH - 250, 10)
        draw_text(f"AI Hits: {ai.hits}", WIDTH - 250, 40)

        if phase == "attack":
            if keys[pygame.K_LEFT]:
                player.move("left")
            if keys[pygame.K_RIGHT]:
                player.move("right")
            if keys[pygame.K_SPACE] and player.bullets_left > 0:
                shoot_sound.play()
                player_bullets.append(Bullet(player.x, player.y, -1))
                player.bullets_left -= 1

            for bullet in player_bullets:
                if bullet.direction == -1 and abs(bullet.y - ai.y) < 100:
                    if bullet.x < ai.x + 32 and ai.x < WIDTH - 64:
                        ai.move("right")
                    elif bullet.x > ai.x + 32 and ai.x > 0:
                        ai.move("left")
                    else:
                        if random.random() < 0.5:
                            ai.move("left")
                        else:
                            ai.move("right")
                    break

            for bullet in player_bullets[:]:
                bullet.move()
                bullet.draw()
                if ai.y < bullet.y < ai.y + 64 and ai.x < bullet.x < ai.x + 64:
                    explosion_sound.play()
                    player.hits += 1
                    player_bullets.remove(bullet)

        elif phase == "defend":
            if keys[pygame.K_LEFT]:
                player.move("left")
            if keys[pygame.K_RIGHT]:
                player.move("right")

            if player.x < ai.x and ai.x > 0:
                ai.x -= ENEMY_SPEED
            elif player.x > ai.x and ai.x < WIDTH - 64:
                ai.x += ENEMY_SPEED
            ai.x = max(0, min(WIDTH - 64, ai.x))

            if ai.bullets_left > 0 and random.randint(0, 5) == 1:
                shoot_sound.play()
                ai_bullets.append(Bullet(ai.x, ai.y, 1))
                ai.bullets_left -= 1

            for bullet in ai_bullets[:]:
                bullet.move()
                bullet.draw()
                if player.y < bullet.y < player.y + 64 and player.x < bullet.x < player.x + 64:
                    explosion_sound.play()
                    ai.hits += 1
                    ai_bullets.remove(bullet)

        player.draw()
        ai.draw()

        if timer <= 0:
            if phase == "attack":
                phase = "defend"
            else:
                winner = "Player" if player.hits > ai.hits else "AI"
                running = False
                end_screen(winner, player.hits, ai.hits)
            start_time = pygame.time.get_ticks()
            reset_phase()

        pygame.display.flip()
        clock.tick(60)

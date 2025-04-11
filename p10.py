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

# Start MongoDB server
subprocess.Popen([mongod_path, "--dbpath", db_path])

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Load Sounds
shoot_sound = pygame.mixer.Sound("C:/Users/tupka/Downloads/gt-ia2/space-shooter/gun-shots.mp3")
explosion_sound = pygame.mixer.Sound("C:/Users/tupka/Downloads/gt-ia2/space-shooter/explosion.mp3")
game_over_sound = pygame.mixer.Sound("C:/Users/tupka/Downloads/gt-ia2/space-shooter/Loosing.mp3")

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["game_database"]
scores_collection = db["high_scores"]

# Game Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_SPEED = 5
BULLET_SPEED = 7
ENEMY_SPEED = 3

# Fullscreen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Space Shooter")

# Load Assets
background_img = pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/space-background.jpg")
player_img = pygame.transform.scale(pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/player.png"), (64, 64))
ai_img = pygame.transform.scale(pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/enemy.png"), (64, 64))
bullet_img = pygame.transform.scale(pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/bullet.png"), (8, 16))

font = pygame.font.SysFont(None, 36)

def draw_text(text, x, y, color=WHITE):
    screen.blit(font.render(text, True, color), (x, y))

def load_high_scores():
    return list(scores_collection.find().sort("score", -1).limit(5))

def save_high_score(name, score):
    scores_collection.insert_one({"name": name, "score": score})

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

# Game loop
player = Player(WIDTH // 2, HEIGHT - 80, player_img)
ai = Player(WIDTH // 2, 20, ai_img)
player_bullets = []
ai_bullets = []

clock = pygame.time.Clock()
running = True
phase = "attack"
start_time = pygame.time.get_ticks()

def reset_phase():
    global player_bullets, ai_bullets
    player_bullets = []
    ai_bullets = []
    player.bullets_left = 1000
    ai.bullets_left = 1000
    draw_text("Switching Phase...", WIDTH // 2 - 150, HEIGHT // 2)
    pygame.display.flip()
    time.sleep(10)

while running:
    screen.blit(background_img, (0, 0))
    current_time = pygame.time.get_ticks()
    elapsed_time = (current_time - start_time) // 1000
    timer = 60 - elapsed_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Top Center HUD
    draw_text(f"Time Left: {timer}s", WIDTH // 2 - 80, 10)

    # Player Stats - Left
    draw_text(f"Player Bullets: {player.bullets_left}", 20, 10)
    draw_text(f"Player Hits: {player.hits}", 20, 40)

    # AI Stats - Right
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

        # AI Dodging
        for bullet in player_bullets:
            if bullet.direction == -1 and abs(bullet.y - ai.y) < 100:
                if bullet.x < ai.x + 32 and ai.x < WIDTH - 64:
                    ai.move("right")
                elif bullet.x > ai.x + 32 and ai.x > 0:
                    ai.move("left")
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

        # AI chases the player
        if player.x < ai.x and ai.x > 0:
            ai.x -= ENEMY_SPEED
        elif player.x > ai.x and ai.x < WIDTH - 64:
            ai.x += ENEMY_SPEED
        ai.x = max(0, min(WIDTH - 64, ai.x))

        # AI fires randomly
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
            running = False
            winner = "Player" if player.hits > ai.hits else "AI"
            draw_text(f"Game Over! Winner: {winner}", WIDTH // 2 - 200, HEIGHT // 2)
            pygame.display.flip()
            time.sleep(5)
        start_time = pygame.time.get_ticks()
        reset_phase()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

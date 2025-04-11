import pygame
import random
import pymongo

import os
import sys


# Initialize pygame
pygame.init()

# Load Sounds
pygame.mixer.init()
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
ENEMY_SPEED = 2

# Create Game Window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Load Assets
background_img = pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/space-background.jpg")
player_img = pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/player.png")
player_img = pygame.transform.scale(player_img, (64, 64))

enemy_img = pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/enemy.png")
enemy_img = pygame.transform.scale(enemy_img, (64, 64))

bullet_img = pygame.image.load("C:/Users/tupka/Downloads/gt-ia2/space-shooter/bullet.png")
bullet_img = pygame.transform.scale(bullet_img, (8, 16))

# Load High Scores from MongoDB
def load_high_scores():
    return list(scores_collection.find().sort("score", -1).limit(5))

# Save High Score to MongoDB
def save_high_score(name, score):
    scores_collection.insert_one({"name": name, "score": score})

# Player Class
class Player:
    def __init__(self):
        self.image = player_img
        self.x = WIDTH // 2 - 32
        self.y = HEIGHT - 80
        self.speed = PLAYER_SPEED
    
    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < WIDTH - 64:
            self.x += self.speed
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

# Bullet Class
class Bullet:
    def __init__(self, x, y):
        self.image = bullet_img
        self.x = x + 28
        self.y = y
        self.speed = BULLET_SPEED
    
    def move(self):
        self.y -= self.speed
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

# Enemy Class
class Enemy:
    def __init__(self):
        self.image = enemy_img
        self.x = random.randint(0, WIDTH - 64)
        self.y = random.randint(50, 150)
        self.speed = ENEMY_SPEED
    
    def move(self):
        self.y += self.speed
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

# Main Game Loop
def show_game_over_screen(score, name):
    game_over_sound.play()
    save_high_score(name, score)
    high_scores = load_high_scores()
    
    screen.fill(BLACK)
    font = pygame.font.Font(None, 48)
    game_over_text = font.render("GAME OVER", True, WHITE)
    score_text = font.render(f"Final Score: {score}", True, WHITE)
    
    screen.blit(game_over_text, (WIDTH // 2 - 100, HEIGHT // 2 - 50))
    screen.blit(score_text, (WIDTH // 2 - 100, HEIGHT // 2))
    
    y_offset = HEIGHT // 2 + 40
    for entry in high_scores:
        high_score_text = font.render(f"{entry['name']}: {entry['score']}", True, WHITE)
        screen.blit(high_score_text, (WIDTH // 2 - 100, y_offset))
        y_offset += 30
    
    restart_text = font.render("Press R to Restart or Q to Quit", True, WHITE)
    screen.blit(restart_text, (WIDTH // 2 - 200, y_offset + 20))
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def main():
    screen.fill(BLACK)
    font = pygame.font.Font(None, 36)
    input_text = "Enter your name: "
    name = ""
    
    while True:
        screen.fill(BLACK)
        text_surface = font.render(input_text + name, True, WHITE)
        screen.blit(text_surface, (WIDTH // 2 - 150, HEIGHT // 2))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name:
                    game_loop(name)
                    return
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode.isalnum():
                    name += event.unicode

def game_loop(name):
    player = Player()
    bullets = []
    enemies = [Enemy() for _ in range(5)]
    score = 0
    clock = pygame.time.Clock()
    running = True
    
    while running:
        screen.blit(background_img, (0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.move("left")
        if keys[pygame.K_RIGHT]:
            player.move("right")
        if keys[pygame.K_SPACE]:
            bullets.append(Bullet(player.x, player.y))
            shoot_sound.play()
        
        for bullet in bullets[:]:
            bullet.move()
            if bullet.y < 0:
                bullets.remove(bullet)
            bullet.draw(screen)
        
        for enemy in enemies[:]:
            enemy.move()
            if enemy.y > HEIGHT:
                show_game_over_screen(score, name)
            enemy.draw(screen)
        
        for bullet in bullets[:]:
            for enemy in enemies[:]:
                if enemy.x < bullet.x < enemy.x + 64 and enemy.y < bullet.y < enemy.y + 64:
                    if bullet in bullets:
                        bullets.remove(bullet)
                    if enemy in enemies:
                        enemies.remove(enemy)
                        enemies.append(Enemy())
                        score += 1
                        explosion_sound.play()
        
        player.draw(screen)
        
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        pygame.display.update()
        clock.tick(30)

main()
pygame.quit()
